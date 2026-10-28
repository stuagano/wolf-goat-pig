"""Lossless offline inventory and deterministic, non-secret manifest digests."""

import json
from copy import deepcopy
from dataclasses import asdict
from datetime import date, datetime
from uuid import uuid4

from sqlalchemy import select

from app import models
from app.services.round_evidence import fingerprint
from app.services.round_identity import candidate_games

# Explicit table allowlist, not SELECT * and not another application data root.
TABLES = (
    models.LegacyRound,
    models.GameStateModel,
    models.GameRecord,
    models.GamePlayerResult,
    models.RoundSource,
    models.RoundObservation,
    models.RoundFieldHead,
    models.RoundIssue,
    models.RoundResolution,
    models.RoundAlias,
    models.RoundComment,
    models.RoundReaction,
    models.PendingSheetSync,
    models.RoundDelivery,
    models.RoundRequest,
)


def primitive(value):
    return json.loads(json.dumps(value, default=lambda x: x.isoformat() if isinstance(x, (date, datetime)) else str(x)))


def rows(db, model):
    table = model.__table__
    return [primitive(dict(r)) for r in db.execute(select(*table.c).order_by(*table.primary_key)).mappings()]


def inventory(db):
    return {m.__tablename__: [{"before": r, "decision": None} for r in rows(db, m)] for m in TABLES}


def snapshot_data(snapshot):
    data = asdict(snapshot)
    data["rounds"] = [
        {
            "source": item.source.model_dump(mode="json"),
            "draft": item.draft.model_dump(mode="json"),
            "raw_payload": primitive(item.raw_payload),
            "observation_key": item.observation_key,
            "continuity_verified": item.continuity_verified,
        }
        for item in snapshot.rounds
    ]
    return primitive(data)


def seal_manifest(manifest):
    """Operator reseals reviewed decisions; apply never silently reseals changes."""
    result = deepcopy(manifest)
    result.pop("checksum", None)
    result["checksum"] = fingerprint(result)
    return result


def validate_checksum(manifest, expected=None):
    if manifest.get("checksum") != seal_manifest(manifest)["checksum"] or (
        expected and expected != manifest["checksum"]
    ):
        raise ValueError("Manifest checksum mismatch")
    if fingerprint(manifest["snapshot"]) != manifest["raw_source_checksum"]:
        raise ValueError("Raw source checksum mismatch")


def standings(db, season):
    """Actual accepted eligibility, separate from pre-cutover legacy counting."""
    result = {}
    for record in db.query(models.GameRecord).order_by(models.GameRecord.id):
        if (
            record.is_retracted
            or record.accepted_revision < 1
            or not record.played_on
            or record.played_on.year != season
        ):
            continue
        if not db.query(models.GameStateModel).filter_by(game_id=record.game_id).first():
            continue
        players = db.query(models.GamePlayerResult).filter_by(game_record_id=record.id, is_retracted=False).all()
        eligible = bool(
            record.score_eligible
            and record.roster_complete
            and len(players) == record.player_count
            and players
            and all(p.participant_id and p.total_earnings is not None for p in players)
        )
        for player in players:
            key = (
                f"profile:{player.player_profile_id}" if player.player_profile_id else f"guest:{player.participant_id}"
            )
            item = result.setdefault(key, {"score": 0.0, "scored": 0, "participation": 0})
            item["participation"] += 1
            if eligible:
                item["score"] += player.total_earnings
                item["scored"] += 1
    return result


def baseline(db, season):
    """Capture the *current pre-cutover caller*, including its duplicate policy.

    No network: include_sheet=True is explicitly backed by the retained cache.
    Keep member labels as evidence, not an implicit profile/name merge.
    """
    from .unified_data_service import UnifiedDataService

    result = {}
    for row in UnifiedDataService(db=db).get_all_rounds(use_sheet_cache=True):
        if not row.date_sortable or not row.date_sortable.startswith(f"{season}-"):
            continue
        key = row.member
        item = result.setdefault(key, {"score": 0.0, "scored": 0, "participation": 0})
        item["participation"] += 1
        if row.score is not None:
            item["score"] += row.score
            item["scored"] += 1
    return result


def build(db, snapshot):
    if db.new or db.dirty or db.deleted:
        raise ValueError("Dry run requires a clean read-only caller")
    if not snapshot.complete or snapshot.errors or not snapshot.rounds or snapshot.season_year is None:
        raise ValueError("Complete fixed-season snapshot required")
    data = snapshot_data(snapshot)
    config = db.get(models.AppConfig, "round_identity")
    value = primitive(config.value if config else {"mode": "legacy", "epoch": 0})
    work = []
    seen = set()
    for item in sorted(snapshot.rounds, key=lambda r: (r.source.kind, r.source.scope, r.source.round_token)):
        identity = tuple(item.source.model_dump().values())
        if identity in seen or item.source.scope != snapshot.scope:
            raise ValueError("Duplicate or mismatched source identity; quarantine snapshot")
        seen.add(identity)
        bound = db.query(models.RoundSource).filter_by(**item.source.model_dump()).one_or_none()
        candidates = candidate_games(db, item.draft)
        work.append(
            {
                "operation_key": fingerprint(item.source.model_dump()),
                "source": item.source.model_dump(),
                "game_id": bound.game_id if bound and bound.game_id else str(uuid4()),
                "candidate_game_ids": candidates,
                "draft": item.draft.model_dump(mode="json"),
                "raw_payload": primitive(item.raw_payload),
                "observation_key": item.observation_key,
                "continuity_verified": item.continuity_verified,
                "decision": None,
            }
        )
    return seal_manifest(
        {
            "version": 1,
            "snapshot": data,
            "raw_source_checksum": fingerprint(data),
            "configuration": value,
            "epoch": value.get("epoch", 0),
            "games": work,
            "inventory": inventory(db),
            "baseline_pre_cutover": baseline(db, snapshot.season_year),
            "baseline_canonical_eligibility": standings(db, snapshot.season_year),
            "approval": None,
        }
    )


def current_inventory_digest(db):
    return fingerprint({m.__tablename__: rows(db, m) for m in TABLES})


def check_original_rows(db, manifest, *, applied=False):
    """Strict drift detection; association changes only allowed after checkpoint.

    New rows from our batches are accounted by checkpoint post-state digests.
    Existing rows cannot disappear, including pending, retired and orphan rows.
    """
    for model in TABLES:
        current = {str(r[model.__table__.primary_key.columns.keys()[0]]): r for r in rows(db, model)}
        for entry in manifest["inventory"][model.__tablename__]:
            before = entry["before"]
            pk = str(before[model.__table__.primary_key.columns.keys()[0]])
            actual = current.get(pk)
            if actual is None:
                raise ValueError(f"Database drift: missing {model.__tablename__} row")
            expected = dict(before)
            decision = entry.get("decision") or {}
            if applied and decision.get("action") == "attach":
                expected["game_id"] = decision["game_id"]
                if model is models.LegacyRound:
                    expected["participant_id"] = decision["participant_id"]
            # Shared reconciliation legitimately advances existing source/head/
            # projection rows. Its exact post-state is bound by the durable
            # checkpoint digest; immutable and social evidence must still match.
            mutable_projection = model not in (
                models.LegacyRound,
                models.RoundComment,
                models.RoundReaction,
                models.RoundObservation,
                models.RoundResolution,
            )
            if actual != expected and not (applied and mutable_projection):
                raise ValueError(f"Database drift: {model.__tablename__} evidence changed")

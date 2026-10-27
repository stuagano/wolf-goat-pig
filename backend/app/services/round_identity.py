"""Persisted source identity and globally serialized candidate discovery.

Legacy summary helpers below remain pre-cutover compatibility only. They are
never evidence for canonical binding and are retired with the legacy readers.
"""

import re
from datetime import date
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .unified_data_service import UnifiedRound

_CLUB_SUFFIX = re.compile(r"(\s+(golf|country|club|course|&|and|g&cc|gcc|gc|cc))+$")


def acquire_reconciliation_lock(db) -> None:
    """One application transaction lock, before fresh candidate reads.

    SQLite test fixtures serialize transactions themselves; this is not a
    substitute for PostgreSQL concurrency verification.
    """
    from sqlalchemy import text

    if db.get_bind().dialect.name == "postgresql":
        db.execute(text("SELECT pg_advisory_xact_lock(:key)"), {"key": 870284190311})


def resolve_round_alias(db, date_key: str, group: str, location: str) -> list[str]:
    from app.models import RoundAlias

    return sorted(
        {r.game_id for r in db.query(RoundAlias).filter_by(date_key=date_key, group=group, location=location).all()}
    )


def candidate_games(db, draft) -> list[str]:
    """Conservative identity candidates, never score matching or auto-binding."""
    from app import models

    candidates = set()
    for record in db.query(models.GameRecord).populate_existing().all():
        if draft.played_on and record.played_on and draft.played_on != record.played_on:
            continue
        if (
            draft.course_name
            and record.course_name
            and course_name(draft.course_name) != course_name(record.course_name)
        ):
            continue
        candidates.add(record.game_id)
    # Include live containers and orphan UUIDs lacking a record. Unknown dates
    # cannot evade coordination, and no total signature grants identity.
    for game in db.query(models.GameStateModel).populate_existing().all():
        if db.query(models.GameRecord).filter_by(game_id=game.game_id).first() is None:
            candidates.add(game.game_id)
    return sorted(candidates)


def retain_alias(db, game_id, draft):
    from app.models import RoundAlias

    for key in {draft.raw_date, draft.played_on.isoformat() if draft.played_on else None} - {None}:
        values = {"date_key": key, "group": draft.group or "", "location": draft.course_name or "", "game_id": game_id}
        if db.query(RoundAlias).filter_by(**values).first() is None:
            db.add(RoundAlias(**values, evidence={"kind": "accepted_projection"}))
    db.flush()


def sync_round_snapshot(db, snapshot):
    """One complete-snapshot boundary, committing only whole source rounds.

    Production continuity requires reviewed snapshot evidence. Repetition can
    replay trusted evidence, but a changed token/data association cannot fill
    even an unknown accepted field without review (Gate B remains unsatisfied).
    """
    from sqlalchemy.orm import Session

    from app import models
    from app.schemas.round_identity import IngestOutcome, RoundDraft, SourceRef, read_round_identity_config

    from . import spreadsheet_sync_service as sheet
    from .round_reconciliation import observe_round
    from .round_source_lease import SourceLeaseLostError, fence, heartbeat, source_lease

    if not snapshot.complete or snapshot.errors or not snapshot.rounds:
        return [IngestOutcome(status="held")]
    engine = db.get_bind()
    # Caller may have read configuration, but must not carry a transaction or
    # stale identity map across network reads / dedicated lease ownership.
    if db.new or db.dirty or db.deleted:
        raise ValueError("Snapshot ingestion requires a clean caller session")
    db.rollback()
    outcomes = []
    try:
        with source_lease(engine, snapshot.scope) as lease:
            with Session(engine) as config_db:
                config = read_round_identity_config(config_db)
                epoch = config.epoch
                approval = config_db.get(models.AppConfig, "round_source_reviews")
                reviewed = (approval.value if approval else {}).get(snapshot.scope, {})
                approved = reviewed.get("fingerprint") == snapshot.fingerprint and bool(
                    reviewed.get("reviewer_profile_id")
                )
            if config.mode != "canonical" or config.season != snapshot.season_year:
                return [IngestOutcome(status="held")]
            # Resolve immutable exact-snapshot mappings before source lookup or
            # disappearance accounting, independently of the mutable review doc.
            with Session(engine) as known_db:
                known = [
                    (r.round_token, r.id)
                    for r in known_db.query(models.RoundSource).filter_by(kind="sheet", scope=snapshot.scope)
                ]
                evidence = (
                    known_db.query(models.RoundObservation)
                    .join(models.RoundSource)
                    .filter(models.RoundSource.kind == "sheet", models.RoundSource.scope == snapshot.scope)
                    .all()
                )
                prior_snapshot = [
                    o
                    for o in evidence
                    if o.raw_payload.get("payload", {}).get("snapshot_fingerprint") == snapshot.fingerprint
                ]
                durable = {
                    o.raw_payload["payload"]["snapshot_mapping"]["observation_key"]: o.raw_payload["payload"][
                        "snapshot_mapping"
                    ]
                    for o in prior_snapshot
                    if o.continuity_verified and o.raw_payload.get("payload", {}).get("snapshot_mapping")
                }
            work = []
            for item in snapshot.rounds:
                binding = durable.get(item.observation_key) or (
                    reviewed.get("round_bindings", {}).get(item.observation_key) if approved else None
                )
                if binding:
                    from dataclasses import replace

                    slots = binding.get("participant_ids", [])
                    if len(slots) != len(item.draft.players) or not binding.get("round_token"):
                        return [IngestOutcome(status="held")]
                    draft_data = item.draft.model_dump(mode="json")
                    for player, slot in zip(draft_data["players"], slots, strict=True):
                        player["participant_id"] = slot
                    raw = {
                        **item.raw_payload,
                        "snapshot_mapping": {
                            "observation_key": item.observation_key,
                            "round_token": binding["round_token"],
                            "participant_ids": slots,
                        },
                    }
                    raw["parse_errors"] = [e for e in raw.get("parse_errors", []) if e != "missing_participant_token"]
                    item = replace(
                        item,
                        source=SourceRef(kind="sheet", scope=snapshot.scope, round_token=binding["round_token"]),
                        draft=RoundDraft.model_validate(draft_data),
                        raw_payload=raw,
                        continuity_verified=True,
                    )
                work.append(item)
            present = {r.source.round_token for r in work}
            for token, source_id in known:
                if token in present:
                    continue
                with Session(engine) as evidence_db:
                    old = (
                        evidence_db.query(models.RoundObservation)
                        .filter_by(source_id=source_id)
                        .order_by(models.RoundObservation.observed_at.desc())
                        .first()
                    )
                    if old:
                        work.append(
                            sheet.SheetRound(
                                SourceRef(kind="sheet", scope=snapshot.scope, round_token=token),
                                RoundDraft.model_validate(old.parsed_values),
                                {
                                    "parse_errors": ["source_round_missing"],
                                    "snapshot_fingerprint": snapshot.fingerprint,
                                },
                                f"missing:{snapshot.fingerprint}:{token}",
                                False,
                            )
                        )
            for item in work:
                heartbeat(engine, lease)
                # Sheets has no atomic revision precondition: content and grid
                # are read again under lease outside the game transaction.
                current = sheet.fetch_round_snapshot(snapshot.scope, season_year=snapshot.season_year)
                if (
                    not current.complete
                    or current.errors
                    or current.source_version != snapshot.source_version
                    or current.fingerprint != snapshot.fingerprint
                ):
                    outcomes.append(IngestOutcome(status="held"))
                    break
                with Session(engine) as tx:
                    with tx.begin():
                        lease_row = fence(tx, lease)
                        acquire_reconciliation_lock(tx)
                        # A cutover update cannot race between this epoch check
                        # and publication of the whole round.
                        tx.query(models.AppConfig).filter_by(name="round_identity").with_for_update().one()
                        fresh = read_round_identity_config(tx)
                        if fresh.mode != "canonical" or fresh.epoch != epoch or fresh.season != snapshot.season_year:
                            raise SourceLeaseLostError("Writer fence advanced")
                        row = tx.query(models.RoundSource).filter_by(**item.source.model_dump()).one_or_none()
                        game = (
                            tx.query(models.GameStateModel).filter_by(game_id=row.game_id).one_or_none()
                            if row and row.game_id
                            else None
                        )
                        before_revision = game.revision if game else None
                        publication = (row.binding_evidence or {}).get("sheet_publication", {}) if row else {}
                        seen_generations = [
                            o.raw_payload.get("payload", {}).get("connector_generation", 0)
                            for o in evidence
                            if row
                            and o.source_id == row.id
                            and o.raw_payload.get("payload", {}).get("snapshot_fingerprint") == snapshot.fingerprint
                        ]
                        if (
                            seen_generations
                            and publication.get("snapshot_fingerprint") != snapshot.fingerprint
                            and max(seen_generations) < publication.get("generation", 0)
                        ):
                            outcomes.append(IngestOutcome(status="held", game_id=row.game_id))
                            continue
                        trusted = approved or (
                            bool(item.raw_payload.get("snapshot_mapping")) and item.continuity_verified
                        )
                        if snapshot.scope.startswith("fixture:") and row is None:
                            trusted = item.continuity_verified
                        if row:
                            prior = (
                                tx.query(models.RoundObservation)
                                .filter_by(source_id=row.id, continuity_verified=True)
                                .all()
                            )
                            trusted = trusted or any(
                                o.raw_payload.get("payload", {}).get("snapshot_fingerprint") == snapshot.fingerprint
                                for o in prior
                            )
                        raw = {
                            **item.raw_payload,
                            "snapshot_fingerprint": snapshot.fingerprint,
                            "connector_generation": lease[2],
                        }
                        outcome = observe_round(
                            tx,
                            item.source,
                            item.draft,
                            observation_key=f"{lease[2]}:{item.observation_key}",
                            raw_payload=raw,
                            continuity_verified=trusted and not raw.get("parse_errors"),
                        )
                        # A held outcome can still publish safe unknown-field
                        # fills before raising another field/integrity issue.
                        # Track actual accepted revision changes per source, not
                        # status or the lease's merely processed fingerprint.
                        published_source = tx.query(models.RoundSource).filter_by(**item.source.model_dump()).one()
                        published_game = (
                            tx.query(models.GameStateModel).filter_by(game_id=outcome.game_id).one_or_none()
                            if outcome.game_id
                            else None
                        )
                        if published_game and published_game.revision != before_revision:
                            published_source.binding_evidence = {
                                **(published_source.binding_evidence or {}),
                                "sheet_publication": {
                                    "snapshot_fingerprint": snapshot.fingerprint,
                                    "generation": lease[2],
                                    "accepted_revision": published_game.revision,
                                },
                            }
                        lease_row.snapshot_fingerprint = snapshot.fingerprint
                        lease_row.source_version = snapshot.source_version
                        fence(tx, lease)
                    outcomes.append(outcome)
    except SourceLeaseLostError:
        outcomes.append(IngestOutcome(status="held"))
    db.expire_all()
    return outcomes


def normalized(value: str) -> str:
    return " ".join(value.casefold().split())


def course_name(value: str) -> str:
    # The sheet says "Wing Point"; saved games say "Wing Point Golf & Country Club".
    value = _CLUB_SUFFIX.sub("", normalized(value))
    return "" if value in {"", "unknown", "n/a"} else value


def round_day(rows: list["UnifiedRound"]) -> date | None:
    try:
        return date.fromisoformat(rows[0].date_sortable)
    except ValueError:
        return None


def group_rounds(rows: list["UnifiedRound"]) -> list[list["UnifiedRound"]]:
    groups: dict[tuple, list[UnifiedRound]] = {}
    for row in rows:
        groups.setdefault(row.game_key or (row.source, id(row)), []).append(row)
    return list(groups.values())


def _signature(rows: list["UnifiedRound"]) -> tuple | None:
    day = round_day(rows)
    course = course_name(rows[0].location)
    players = [(normalized(row.member), row.score) for row in rows]
    # Repeated names cannot establish individual hole ownership. Missing names,
    # dates, courses and mixed game metadata cannot establish identity either.
    if (
        not day
        or not course
        or any(not name for name, _ in players)
        or len({name for name, _ in players}) != len(players)
        or any(row.date_sortable != rows[0].date_sortable or course_name(row.location) != course for row in rows)
    ):
        return None
    return day, course, tuple(sorted(players))


def link_saved_cards(sheet_games: list[list["UnifiedRound"]], other_games: list[list["UnifiedRound"]]) -> None:
    """Copy identity only for a mutual one-to-one whole-game match.

    Count even orphan app records without reachable state, so a missing UUID
    cannot make an ambiguous match appear unique. App group A is a placeholder,
    not evidence; sheet groups remain distinct candidates.
    """
    sheets: dict[tuple, list[list[UnifiedRound]]] = {}
    apps: dict[tuple, list[list[UnifiedRound]]] = {}
    for groups, index in ((sheet_games, sheets), (other_games, apps)):
        for rows in groups:
            if index is apps and rows[0].source != "database":
                continue
            signature = _signature(rows)
            if signature is not None:
                index.setdefault(signature, []).append(rows)
    for signature, candidates in sheets.items():
        matches = apps.get(signature, [])
        if len(candidates) != 1 or len(matches) != 1:
            continue
        sheet, app = candidates[0], matches[0]
        ids = {row.game_id for row in app}
        if len(ids) != 1 or None in ids:
            continue
        game_id = app[0].game_id
        holes = {normalized(row.member): row.hole_scores for row in app}
        for row in sheet:
            row.game_id = game_id
            if not row.hole_scores:
                row.hole_scores = holes[normalized(row.member)]

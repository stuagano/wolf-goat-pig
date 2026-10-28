"""Explicit offline whole-game migration on the existing writer/evidence root.

No boot backfill, source reads/writes, transport calls or generated apply UUIDs.
Every accepted manifest is checksum-bound to its raw snapshot and DB inventory.
"""

from copy import deepcopy

from sqlalchemy import text

from app import models
from app.schemas.round_identity import RoundDraft, SourceRef, read_round_identity_config

from .round_cutover import configuration_lock
from .round_evidence import fingerprint
from .round_identity import retain_alias
from .round_migration_accounting import (
    TABLES,
    build,
    check_original_rows,
    current_inventory_digest,
    inventory,
    standings,
    validate_checksum,
)
from .round_migration_accounting import (
    seal_manifest as seal_manifest,
)


def build_manifest(db, snapshot):
    return build(db, snapshot)


def _reviewed(decision):
    return bool(decision and decision.get("actor_profile_id") and str(decision.get("reason", "")).strip())


def _validate_review(manifest):
    if not _reviewed(manifest.get("approval")) or "expected_standings" not in manifest["approval"]:
        raise ValueError("Explicit reviewed counting deltas and reason required")
    targets = {g["game_id"] for g in manifest["games"]}
    snapshot = manifest["snapshot"]
    if not snapshot.get("complete") or snapshot.get("errors") or snapshot.get("season_year") is None:
        raise ValueError("Complete fixed-season snapshot required")
    expected = {fingerprint(r["source"]): r for r in snapshot["rounds"]}
    if len(expected) != len(snapshot["rounds"]) or len(manifest["games"]) != len(expected):
        raise ValueError("Every snapshot round must be accounted exactly once")
    seen = set()
    source_tokens = set()
    for game in manifest["games"]:
        original = expected.get(game["operation_key"])
        if original is None or game["operation_key"] in seen:
            raise ValueError("Duplicate or unknown source operation")
        seen.add(game["operation_key"])
        for key in ("source", "draft", "raw_payload", "observation_key", "continuity_verified"):
            if game[key] != original[key]:
                raise ValueError("Reviewed source evidence cannot diverge from snapshot")
        decision = game.get("decision")
        if not _reviewed(decision) or decision.get("action") not in {"bind_existing", "confirm_distinct", "hold"}:
            raise ValueError("Every source round requires an explicit reviewed decision")
        if decision["action"] == "hold":
            continue
        if not game["continuity_verified"] or game["raw_payload"].get("parse_errors"):
            raise ValueError("Source continuity/parse review must be corrected before acceptance")
        if decision["action"] == "bind_existing" and game["game_id"] not in game["candidate_game_ids"]:
            raise ValueError("Binding target missing from reviewed candidates")
        RoundDraft.model_validate(game["draft"])
        tokens = decision.get("source_participant_tokens", {})
        for token in tokens.values():
            identity = (game["source"]["kind"], game["source"]["scope"], token)
            if not isinstance(token, str) or not token.strip() or identity in source_tokens:
                raise ValueError("Source participant token collision requires explicit quarantine")
            source_tokens.add(identity)
    for table, entries in manifest["inventory"].items():
        for entry in entries:
            d = entry.get("decision")
            if not _reviewed(d) or d.get("action") not in {"preserve", "attach", "hold", "retire"}:
                raise ValueError("Every old row requires explicit accounting")
            if d["action"] == "attach":
                if (
                    table not in {"legacy_rounds", "round_comments", "round_reactions"}
                    or d.get("game_id") not in targets
                ):
                    raise ValueError("Invalid association decision")
                if table == "legacy_rounds":
                    game = next(g for g in manifest["games"] if g["game_id"] == d["game_id"])
                    if d.get("participant_id") not in {p["participant_id"] for p in game["draft"]["players"]}:
                        raise ValueError("Legacy participant requires explicit stable slot")
                    if entry["before"]["status"] == "pending":
                        raise ValueError("Pending legacy submissions cannot become accepted scores")
            # Retire is evidence accounting only, never deletion or silent status change.


def _checkpoints(db, manifest):
    return (
        db.query(models.RoundMigrationCheckpoint)
        .filter_by(manifest_checksum=manifest["checksum"])
        .order_by(models.RoundMigrationCheckpoint.created_at, models.RoundMigrationCheckpoint.id)
        .all()
    )


def _drift(db, manifest):
    checkpoints = _checkpoints(db, manifest)
    if checkpoints:
        if checkpoints[-1].outcome["inventory_digest"] != current_inventory_digest(db):
            raise ValueError("Database drift invalidates reviewed decisions; rebuild manifest")
    else:
        before = {t: [e["before"] for e in entries] for t, entries in manifest["inventory"].items()}
        actual = {t: [e["before"] for e in entries] for t, entries in inventory(db).items()}
        if before != actual:
            raise ValueError("Database drift invalidates reviewed decisions; rebuild manifest")
    return checkpoints


def _associate(db, manifest, game_id):
    for model in (models.LegacyRound, models.RoundComment, models.RoundReaction):
        for entry in manifest["inventory"][model.__tablename__]:
            decision = entry["decision"]
            if decision["action"] != "attach" or decision.get("game_id") != game_id:
                continue
            row = db.get(model, entry["before"]["id"])
            if row.game_id not in (None, game_id):
                raise ValueError("Cannot reassign existing social/source ownership")
            row.game_id = game_id
            if model is models.LegacyRound:
                row.participant_id = decision["participant_id"]
            date = entry["before"].get("round_date", entry["before"].get("date"))
            group = entry["before"].get("round_group", entry["before"].get("group")) or ""
            location = entry["before"].get("location") or ""
            values = {"date_key": date, "group": group, "location": location, "game_id": game_id}
            if date and not db.query(models.RoundAlias).filter_by(**values).first():
                db.add(models.RoundAlias(**values, evidence={"manifest_checksum": manifest["checksum"]}))
    db.flush()


def _apply_game(db, manifest, item):
    from .round_reconciliation import _bind, observe_round

    draft = RoundDraft.model_validate(item["draft"])
    source = SourceRef.model_validate(item["source"])
    decision = item["decision"]
    if decision["action"] == "hold":
        outcome = observe_round(
            db,
            source,
            draft,
            observation_key=item["observation_key"],
            raw_payload=item["raw_payload"],
            continuity_verified=False,
        )
    else:
        row = db.query(models.RoundSource).filter_by(**source.model_dump()).one_or_none()
        if row is None:
            row = models.RoundSource(**source.model_dump(), revision=0)
            db.add(row)
            db.flush()
        if row.game_id not in (None, item["game_id"]):
            raise ValueError("Source is already bound to a different UUID")
        # Mapping is by original result ID, never by names, order or scores.
        record = db.query(models.GameRecord).filter_by(game_id=item["game_id"]).one_or_none()
        if record:
            original_results = db.query(models.GamePlayerResult).filter_by(game_record_id=record.id).all()
            mapping = decision.get("result_slots", {})
            slots = {p.participant_id for p in draft.players}
            for result in original_results:
                if result.participant_id is None:
                    slot = mapping.get(str(result.id))
                    if slot not in slots:
                        raise ValueError("Every old result requires a reviewed original-ID to stable-slot mapping")
                    result.participant_id = slot
            db.flush()
        tokens = decision.get("source_participant_tokens")
        previous = (row.binding_evidence or {}).get("participant_tokens")
        if previous and tokens and tokens != previous:
            raise ValueError("Trusted source participant tokens cannot be reassigned")
        if tokens:
            if set(tokens) != {p.participant_id for p in draft.players} or len(set(tokens.values())) != len(tokens):
                raise ValueError("Explicit unique source-token to canonical-slot mapping required")
            row.binding_evidence = {**(row.binding_evidence or {}), "participant_tokens": tokens}
            # _bind retains the same UUID's trusted mapping only.
            if row.game_id is None:
                row.game_id = item["game_id"]
        game = _bind(db, row, draft, game_id=item["game_id"], actor=decision["actor_profile_id"])
        if record and record.accepted_revision < 1:
            # Adopt the reviewed stable slots without accepting competing source
            # values. Original scores, dates and roster remain the baseline.
            from .completed_game_service import persist_final_results
            from .round_evidence import accepted_draft

            original = accepted_draft(db, item["game_id"])
            if original is None:
                raise ValueError("Reviewed original participant projection required")
            persist_final_results(db, game, original)
            if record.accepted_revision < 1:
                game.revision = max(game.revision or 0, 1)
                record.accepted_revision = game.revision
        outcome = observe_round(
            db,
            source,
            draft,
            observation_key=item["observation_key"],
            raw_payload=item["raw_payload"],
            continuity_verified=True,
        )
        retain_alias(db, item["game_id"], draft)
        _associate(db, manifest, item["game_id"])
    db.flush()
    return outcome.model_dump()


def apply_manifest(db, manifest, *, expected_checksum, batch_size=50):
    """Commit exactly one whole source game/checkpoint at a time, safely resumable.

    batch_size is a bounded operational hint, never a participant split. A
    checkpoint and all social/evidence/results updates commit in one transaction.
    """
    validate_checksum(manifest, expected_checksum)
    _validate_review(manifest)
    if batch_size < 1:
        raise ValueError("Positive batch size required")
    if db.new or db.dirty or db.deleted:
        raise ValueError("Apply requires a clean session")
    db.rollback()
    try:
        for item in manifest["games"]:
            configuration_lock(db, exclusive=True)
            config = read_round_identity_config(db)
            if config.mode != "paused" or config.epoch != manifest["epoch"]:
                raise ValueError("Matching paused writer epoch required")
            checkpoints = _drift(db, manifest)
            if any(c.operation_key == item["operation_key"] for c in checkpoints):
                db.rollback()
                continue
            db.info["round_migration_transaction"] = True
            outcome = _apply_game(db, manifest, item)
            db.add(
                models.RoundMigrationCheckpoint(
                    manifest_checksum=manifest["checksum"],
                    game_id=item["game_id"],
                    operation_key=item["operation_key"],
                    outcome={"result": outcome, "inventory_digest": current_inventory_digest(db)},
                )
            )
            db.commit()
        return {"game_ids": [g["game_id"] for g in manifest["games"]], "checksum": manifest["checksum"]}
    except Exception:
        db.rollback()
        raise
    finally:
        db.info.pop("round_migration_transaction", None)


def verify_manifest(db, manifest):
    """Recompute physical readback, never trust report booleans from JSON."""
    validate_checksum(manifest)
    errors = []
    try:
        _validate_review(manifest)
        checkpoints = _drift(db, manifest)
        check_original_rows(db, manifest, applied=True)
    except ValueError as exc:
        checkpoints = _checkpoints(db, manifest)
        errors.append(str(exc))
    completed = {c.operation_key for c in checkpoints}
    missing = [g for g in manifest["games"] if g["operation_key"] not in completed]
    for item in manifest["games"]:
        if item["operation_key"] not in completed or (item.get("decision") or {}).get("action") == "hold":
            continue
        row = db.query(models.RoundSource).filter_by(**item["source"]).one_or_none()
        if not row or row.game_id != item["game_id"]:
            errors.append("Source UUID readback mismatch")
        game = db.query(models.GameStateModel).filter_by(game_id=item["game_id"]).one_or_none()
        if not game:
            errors.append("Missing canonical UUID container")
    actual = standings(db, manifest["snapshot"]["season_year"])
    approved = (manifest.get("approval") or {}).get("expected_standings")
    if actual != approved:
        errors.append("Standings correction delta requires fresh explicit approval")
    for table in ("round_comments", "round_reactions"):
        model = next(m for m in TABLES if m.__tablename__ == table)
        for entry in manifest["inventory"][table]:
            row = db.get(model, entry["before"]["id"])
            if not row:
                errors.append("Social ID missing")
    held = [g["operation_key"] for g in manifest["games"] if (g.get("decision") or {}).get("action") == "hold"]
    return {
        "manifest_checksum": manifest["checksum"],
        "errors": errors,
        "unaccounted_source_rows": sum(len(g["draft"]["players"]) for g in missing),
        "preserved_comment_ids": [
            e["before"]["id"]
            for e in manifest["inventory"]["round_comments"]
            if db.get(models.RoundComment, e["before"]["id"])
        ],
        "preserved_reaction_ids": [
            e["before"]["id"]
            for e in manifest["inventory"]["round_reactions"]
            if db.get(models.RoundReaction, e["before"]["id"])
        ],
        "held_operation_keys": held,
        "baseline_pre_cutover": manifest["baseline_pre_cutover"],
        "baseline_canonical_eligibility": manifest["baseline_canonical_eligibility"],
        "current_standings": actual,
        "delta_approval": deepcopy(manifest.get("approval")),
    }


def finalize_constraints(db, manifest):
    """Offline only: reject duplicates/orphans, never delete to satisfy an index."""
    configuration_lock(db, exclusive=True)
    config = read_round_identity_config(db)
    if config.mode != "paused" or config.epoch != manifest["epoch"]:
        raise ValueError("Matching paused writer epoch required")
    report = verify_manifest(db, manifest)
    if report["errors"] or report["unaccounted_source_rows"]:
        raise ValueError("Verified accounting required before constraint contraction")
    duplicate = db.execute(
        text(
            "SELECT game_record_id, participant_id FROM game_player_results "
            "GROUP BY game_record_id, participant_id HAVING COUNT(*) > 1"
        )
    ).first()
    orphan = db.execute(
        text(
            "SELECT p.id FROM game_player_results p LEFT JOIN game_records r "
            "ON r.id=p.game_record_id WHERE r.id IS NULL OR p.participant_id IS NULL"
        )
    ).first()
    if duplicate or orphan:
        raise ValueError("Duplicate/orphan results quarantined; explicit reviewed mapping required")
    db.execute(
        text(
            "CREATE UNIQUE INDEX IF NOT EXISTS uq_game_result_participant "
            "ON game_player_results(game_record_id, participant_id)"
        )
    )
    db.execute(
        text("CREATE UNIQUE INDEX IF NOT EXISTS uq_round_source_token ON round_sources(kind, scope, round_token)")
    )
    db.execute(text("DROP INDEX IF EXISTS ux_member_round_per_day"))
    return report

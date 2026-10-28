"""Reviewed migration of saved games, independent of external sheet membership."""

import math
from copy import deepcopy
from types import SimpleNamespace

from app import models
from app.schemas.round_identity import RoundDraft

from .completed_game_service import persist_final_results
from .round_evidence import accepted_draft, fingerprint


def saved_work(db):
    return [
        {
            "record_id": record.id,
            "game_id": record.game_id,
            "operation_key": "saved:" + fingerprint([record.id, record.game_id]),
            "decision": None,
        }
        for record in db.query(models.GameRecord).order_by(models.GameRecord.id)
    ]


def validate_saved(manifest, reviewed):
    records = {e["before"]["id"]: e["before"] for e in manifest["inventory"]["game_records"]}
    work = manifest.get("saved_games", [])
    if len(work) != len(records) or {w["record_id"] for w in work} != set(records):
        raise ValueError("Every saved game requires exactly one reviewed work item")
    for item in work:
        original = records[item["record_id"]]
        if item["game_id"] != original["game_id"] or item["operation_key"] != "saved:" + fingerprint(
            [original["id"], original["game_id"]]
        ):
            raise ValueError("Saved game identity cannot change")
        decision = item.get("decision")
        if not reviewed(decision) or decision.get("action") not in {"publish_original", "hold", "retire"}:
            raise ValueError("Every saved game requires publication or explicit held/retired accounting")
        if decision["action"] == "publish_original" and type(decision.get("roster_complete")) is not bool:
            raise ValueError("Original saved roster completeness requires explicit review")


def original_history(record, results):
    """Transpose only original scalar cells; never infer missing scores or slots.

    Unknown/contradictory layouts require a reviewed hold. Auxiliary result notes
    remain on the immutable original result payload, not public gameplay facts.
    """
    history = {}
    for row in results:
        cells = row.hole_scores or []
        if not isinstance(cells, list):
            raise ValueError("Original detail requires explicit hold: invalid cells")
        seen = set()
        for cell in cells:
            if not isinstance(cell, dict):
                raise ValueError("Original detail requires explicit hold: invalid cell")
            hole, value = cell.get("hole"), cell.get("quarters")
            if (
                type(hole) is not int
                or hole not in range(1, 19)
                or hole in seen
                or isinstance(value, bool)
                or not isinstance(value, (float, int))
                or not math.isfinite(value)
            ):
                raise ValueError("Original detail requires explicit hold: missing/duplicate score")
            seen.add(hole)
            target = history.setdefault(hole, {"hole": hole, "points_delta": {}})
            target["points_delta"][row.participant_id] = value
            if cell.get("points_delta") is not None and (
                not isinstance(cell["points_delta"], dict) or cell["points_delta"].get(row.participant_id) != value
            ):
                raise ValueError("Original detail requires explicit hold: contradictory slot evidence")
            if cell.get("gross_score") is not None:
                target.setdefault("gross_scores", {})[row.participant_id] = cell["gross_score"]
            if cell.get("par") is not None:
                if "par" in target and target["par"] != cell["par"]:
                    raise ValueError("Original detail requires explicit hold: contradictory par")
                target["par"] = cell["par"]
    slots = {r.participant_id for r in results}
    if history and any(r.is_retracted for r in results):
        raise ValueError("Original detail requires explicit hold: historical retracted roster needs review")
    for row in results:
        for cell in row.hole_scores or []:
            for key in ("points_delta", "gross_scores"):
                supplied = cell.get(key)
                if supplied is not None and (
                    not isinstance(supplied, dict)
                    or any(
                        slot not in slots or history[cell["hole"]].get(key, {}).get(slot) != value
                        for slot, value in supplied.items()
                    )
                ):
                    raise ValueError("Original detail requires explicit hold: contradictory cross-player cells")
    if any(set(h["points_delta"]) != slots for h in history.values()):
        raise ValueError("Original detail requires explicit hold: incomplete roster cells")
    coverage = "per_hole_complete" if set(history) == set(range(1, 19)) else "partial" if history else "totals_only"
    if (record.detail_coverage is not None and record.detail_coverage != coverage) or (
        record.total_holes_played is not None and record.total_holes_played != len(history)
    ):
        raise ValueError("Original detail requires explicit hold: coverage/hole count cannot be reconstructed")
    return [history[h] for h in sorted(history)]


def apply_saved(db, item):
    decision = item["decision"]
    if decision["action"] != "publish_original":
        return {"status": decision["action"], "game_id": item["game_id"]}
    record = db.get(models.GameRecord, item["record_id"])
    results = (
        db.query(models.GamePlayerResult).filter_by(game_record_id=record.id).order_by(models.GamePlayerResult.id).all()
    )
    mapping = decision.get("result_slots", {})
    for result in results:
        if result.participant_id is None:
            slot = mapping.get(str(result.id))
            if not isinstance(slot, str) or not slot.strip():
                raise ValueError("Original result ID requires reviewed stable slot")
            result.participant_id = slot
        elif str(result.id) in mapping and mapping[str(result.id)] != result.participant_id:
            raise ValueError("Original stable slots cannot be reassigned")
    slots = [r.participant_id for r in results]
    if len(slots) != len(set(slots)) or not results:
        raise ValueError("Original saved roster requires distinct nonempty slots")
    record.roster_complete = decision["roster_complete"]
    db.flush()
    draft = accepted_draft(db, record.game_id)
    # Only original record facts are supplied; no source values, invented dates,
    # holes, scores, courses or profile/name guesses can enter this publication.
    draft = RoundDraft.model_validate(draft.model_dump())
    game = db.query(models.GameStateModel).filter_by(game_id=record.game_id).one_or_none()
    if game is None:
        game = models.GameStateModel(game_id=record.game_id, state={}, game_status="completed")
        db.add(game)
        db.flush()
    # accepted_draft deliberately omits history for ordinary scalar corrections.
    # Repair cannot rely on missing state to carry original evidence forward.
    history = original_history(record, results)
    old_history = (game.state or {}).get("hole_history") or []
    if old_history and not history:
        raise ValueError("Original detail requires explicit hold: state-only detail needs review")
    if old_history and history and old_history != history:
        # Existing richer gameplay is not replaced by a transposed sparse copy.
        for hole in history:
            existing = next((h for h in old_history if h.get("hole") == hole["hole"]), {})
            if any(existing.get(k) != v for k, v in hole.items()):
                raise ValueError("Original detail requires explicit hold: state conflicts with result cells")
    draft = draft.model_copy(
        update={
            "hole_history": history,
            "detail_coverage": "per_hole_complete" if len(history) == 18 else "partial" if history else "totals_only",
        }
    )
    metadata = deepcopy(record.game_settings)
    preserved = {
        r.id: {
            key: deepcopy(getattr(r, key))
            for key in ("hole_scores", "holes_won", "performance_metrics", "final_position")
        }
        for r in results
    }
    persist_final_results(db, game, draft)
    # The shared writer materializes state; repair does not rewrite original
    # result notes, derived metrics, or audit metadata as new accepted evidence.
    record.game_settings = metadata
    for row in results:
        for key, value in preserved[row.id].items():
            setattr(row, key, value)
    if record.accepted_revision < 1:
        game.revision = max(game.revision or 0, 1)
        record.accepted_revision = game.revision
    return {"status": "published_original", "game_id": record.game_id}


def verify_saved(db, manifest):
    from .round_migration_accounting import primitive

    errors = []
    for item in manifest.get("saved_games", []):
        record = db.get(models.GameRecord, item["record_id"])
        game = db.query(models.GameStateModel).filter_by(game_id=item["game_id"]).one_or_none()
        results = db.query(models.GamePlayerResult).filter_by(game_record_id=item["record_id"]).all()
        original = [
            e["before"]
            for e in manifest["inventory"]["game_player_results"]
            if e["before"]["game_record_id"] == item["record_id"]
        ]
        current = {r.id: r for r in results}
        before_record = next(
            e["before"] for e in manifest["inventory"]["game_records"] if e["before"]["id"] == item["record_id"]
        )
        for key in (
            "detail_coverage",
            "total_holes_played",
            "game_settings",
            "played_on",
            "raw_date",
            "course_name",
            "group",
            "game_mode",
            "game_duration_minutes",
            "created_at",
            "completed_at",
            "is_retracted",
        ):
            if before_record[key] is not None and (not record or primitive(getattr(record, key)) != before_record[key]):
                errors.append("Original saved detail metadata changed")
        for before in original:
            row = current.get(before["id"])
            if not row or any(getattr(row, key) != before[key] for key in before if key != "participant_id"):
                errors.append("Original saved detail/result metadata changed")
        if item["decision"]["action"] != "publish_original":
            continue
        try:
            mapped = [
                SimpleNamespace(
                    **{
                        **r,
                        "participant_id": r["participant_id"]
                        or item["decision"].get("result_slots", {}).get(str(r["id"])),
                    }
                )
                for r in original
            ]
            for original_row in mapped:
                if (
                    original_row.id not in current
                    or current[original_row.id].participant_id != original_row.participant_id
                ):
                    errors.append("Original saved detail slot mapping changed")
            expected_history = original_history(SimpleNamespace(**before_record), mapped)
            actual_history = (game.state or {}).get("hole_history", []) if game else []
            for hole in expected_history:
                actual = next((h for h in actual_history if h.get("hole") == hole["hole"]), {})
                if any(actual.get(k) != value for k, value in hole.items()):
                    errors.append("Original saved detail missing from shared projection")
            expected_coverage = (
                "per_hole_complete" if len(expected_history) == 18 else "partial" if expected_history else "totals_only"
            )
            if (
                not record
                or record.detail_coverage != expected_coverage
                or record.total_holes_played != (len(expected_history) or None)
                or (game and game.state.get("detail_coverage") != expected_coverage)
            ):
                errors.append("Original saved detail capabilities changed")
        except ValueError as exc:
            errors.append(str(exc))
        if (
            not game
            or not record
            or record.accepted_revision < 1
            or not results
            or any(not r.participant_id for r in results)
        ):
            errors.append("Saved game missing original accepted publication")
        for before in original:
            row = current.get(before["id"])
            if not row or any(
                getattr(row, k) != before[k]
                for k in ("total_earnings", "player_name", "player_profile_id", "is_retracted")
            ):
                errors.append("Original saved contribution changed")
    return errors

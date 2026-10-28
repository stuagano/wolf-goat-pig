"""Reviewed migration of saved games, independent of external sheet membership."""

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
    persist_final_results(db, game, draft)
    if record.accepted_revision < 1:
        game.revision = max(game.revision or 0, 1)
        record.accepted_revision = game.revision
    return {"status": "published_original", "game_id": record.game_id}


def verify_saved(db, manifest):
    errors = []
    for item in manifest.get("saved_games", []):
        if item["decision"]["action"] != "publish_original":
            continue
        record = db.get(models.GameRecord, item["record_id"])
        game = db.query(models.GameStateModel).filter_by(game_id=item["game_id"]).one_or_none()
        results = db.query(models.GamePlayerResult).filter_by(game_record_id=item["record_id"]).all()
        original = [
            e["before"]
            for e in manifest["inventory"]["game_player_results"]
            if e["before"]["game_record_id"] == item["record_id"]
        ]
        current = {r.id: r for r in results}
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

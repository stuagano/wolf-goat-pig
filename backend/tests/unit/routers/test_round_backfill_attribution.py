"""Actual PATCH interpretation of the UUID page's full-roster index payload."""

from app import models
from app.schemas.round_identity import RoundDraft
from app.services.completed_game_service import persist_final_results
from tests.unit.routers.test_round_reconciliation_api import login, round_api, seed


def test_backfill_full_state_indices_keep_retracted_slot_and_revision_contract(round_api):
    client, app, sessions = round_api
    game_id, *_ = seed(sessions)
    login(app, sessions)
    with sessions() as db:
        game = db.query(models.GameStateModel).filter_by(game_id=game_id).one()
        draft = RoundDraft(
            players=[
                {"participant_id": "removed", "name": "Removed", "quarters": None},
                {"participant_id": "a", "name": "Avery", "quarters": -36},
                {"participant_id": "b", "name": "Blair", "quarters": 36},
            ]
        )
        persist_final_results(db, game, draft)
        # Result order differs from state roster; filtering this first result
        # must not make the visible participant index address the wrong slot.
        record = db.query(models.GameRecord).filter_by(game_id=game_id).one()
        results = db.query(models.GamePlayerResult).filter_by(game_record_id=record.id).all()
        next(r for r in results if r.participant_id == "removed").is_retracted = True
        state = dict(game.state)
        state["players"] = [{"id": p.participant_id, "name": p.name} for p in draft.players]
        game.state = state
        revision = game.revision
        db.commit()
    payload = {
        "expected_revision": revision,
        "per_hole_quarters": [
            {"player_index": index, "hole": hole, "quarters": points}
            for index, points in [(2, 2), (1, -2)]
            for hole in range(1, 19)
        ],
    }
    stale = client.patch(f"/games/{game_id}/scorecard", json={**payload, "expected_revision": revision - 1})
    assert stale.status_code == 409, stale.text
    response = client.patch(f"/games/{game_id}/scorecard", json=payload)
    assert response.status_code == 409, response.text  # Competing detail is held, never silently accepted.
    with sessions() as db:
        # Inspect the actual proposed detail through its issue, independent of
        # generated observation keys and keeping accepted totals untouched.
        detail = db.query(models.RoundIssue).filter_by(game_id=game_id, field="detail", status="open").one()
        holes = detail.proposed_value["holes"]
        assert len(holes) == 18
        assert all(h["points_delta"] == {"b": 2, "a": -2} for h in holes)
        assert db.query(models.GameRecord).filter_by(game_id=game_id).one().final_scores["b"] == 36
        assert db.query(models.RoundIssue).filter_by(game_id=game_id, field="detail").count() == 1

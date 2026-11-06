"""Actual UUID PATCH → reviewed acceptance → independent persisted readback."""

from copy import deepcopy

import pytest
from sqlalchemy import text

from app import models
from app.schemas.round_identity import RoundDraft
from app.services.completed_game_service import persist_final_results
from tests.unit.routers.test_round_reconciliation_api import login, round_api, seed


def prepare(round_api):
    client, app, sessions = round_api
    game_id, *_ = seed(sessions)
    login(app, sessions)
    with sessions() as db:
        game = db.query(models.GameStateModel).filter_by(game_id=game_id).one()
        draft = RoundDraft(
            players=[
                {"participant_id": "removed", "name": "Removed", "quarters": 7},
                {"participant_id": "a", "name": "Avery", "quarters": -36},
                {"participant_id": "b", "name": "Blair", "quarters": 36},
            ],
            detail_coverage="partial",
            hole_history=[{"hole": 1, "points_delta": {"removed": 7, "a": -1, "b": 1}, "note": "Historical"}],
        )
        persist_final_results(db, game, draft)
        # Retract through the existing accepted operation, retaining history.
        persist_final_results(
            db,
            game,
            draft.model_copy(
                update={"detail_coverage": "totals_only", "hole_history": [], "removed_participant_ids": ["removed"]}
            ),
        )
        record = db.query(models.GameRecord).filter_by(game_id=game_id).one()
        results = (
            db.query(models.GamePlayerResult)
            .filter_by(game_record_id=record.id)
            .order_by(models.GamePlayerResult.id)
            .all()
        )
        assert [r.participant_id for r in results] != ["removed", "a", "b"]
        removed = next(r for r in results if r.participant_id == "removed")
        original = {
            "result_id": removed.id,
            "history": deepcopy(removed.hole_scores),
            "totals": deepcopy(record.final_scores),
        }
        # The UUID page can encounter a historical earlier state slot. PATCH
        # indices must still address this full state array, not result order.
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
    return client, app, sessions, game_id, payload, original


def review(client, issue_id):
    detail = client.get(f"/round-reconciliation/issues/{issue_id}").json()
    return {
        "action": "accept",
        "reason": "Reviewed active slot detail",
        "expected_game_revision": detail["game_revision"],
        "expected_issue_revision": detail["revision"],
        "expected_head_revision": detail["current_head_revision"],
    }


def test_backfill_full_state_indices_keep_retracted_slot_and_revision_contract(round_api):
    client, app, sessions, game_id, payload, original = prepare(round_api)
    revision = payload["expected_revision"]
    stale = client.patch(f"/games/{game_id}/scorecard", json={**payload, "expected_revision": revision - 1})
    assert stale.status_code == 409, stale.text
    response = client.patch(f"/games/{game_id}/scorecard", json=payload)
    assert response.status_code == 409, response.text  # Proposed, not silently accepted.
    with sessions() as db:
        detail = db.query(models.RoundIssue).filter_by(game_id=game_id, field="detail", status="open").one()
        issue_id = detail.id
        holes = detail.proposed_value["holes"]
        assert len(holes) == 18
        assert all(h["points_delta"] == {"b": 2, "a": -2} for h in holes)
        assert db.query(models.GameRecord).filter_by(game_id=game_id).one().final_scores == original["totals"]
    decision = review(client, issue_id)
    login(app, sessions, 1)
    assert client.post(f"/round-reconciliation/issues/{issue_id}/resolve", json=decision).status_code == 403
    login(app, sessions)
    assert (
        client.post(
            f"/round-reconciliation/issues/{issue_id}/resolve",
            json={**decision, "expected_game_revision": revision - 1},
        ).status_code
        == 409
    )
    accepted = client.post(f"/round-reconciliation/issues/{issue_id}/resolve", json=decision)
    assert accepted.status_code in (200, 202), accepted.text
    # Separate session + direct SQL, not the resolver's identity map or response.
    # PostgreSQL fixture uses NullPool: this is also a new physical connection.
    with sessions() as db:
        record = db.query(models.GameRecord).filter_by(game_id=game_id).one()
        game = db.query(models.GameStateModel).filter_by(game_id=game_id).one()
        assert game.revision > revision and record.accepted_revision == game.revision
        assert record.final_scores == original["totals"] == {"a": -36, "b": 36}
        physical = db.execute(
            text(
                "SELECT participant_id, is_retracted, total_earnings FROM game_player_results WHERE game_record_id=:id"
            ),
            {"id": record.id},
        ).all()
        assert {pid: (bool(removed), total) for pid, removed, total in physical} == {
            "removed": (True, 7),
            "a": (False, -36),
            "b": (False, 36),
        }
        removed = db.get(models.GamePlayerResult, original["result_id"])
        assert removed.hole_scores == original["history"]
        history = game.state["hole_history"]
        assert len(history) == 18 and history[0]["points_delta"] == {"removed": 7, "a": -2, "b": 2}
        assert history[0]["note"] == "Historical"
        assert all(h["points_delta"] == {"a": -2, "b": 2} for h in history[1:])
        for row in db.query(models.GamePlayerResult).filter_by(game_record_id=record.id):
            if row.participant_id in {"a", "b"}:
                assert len(row.hole_scores) == 18
                assert all(h["quarters"] == (-2 if row.participant_id == "a" else 2) for h in row.hole_scores)
        audit = db.query(models.RoundResolution).filter_by(issue_id=issue_id).one()
        assert audit.actor_profile_id == 8 and audit.action == "accept" and audit.reason == decision["reason"]
        assert audit.game_revision == game.revision
        assert db.get(models.RoundIssue, issue_id).status == "resolved"
    assert client.post(f"/round-reconciliation/issues/{issue_id}/resolve", json=decision).status_code == 409
    assert client.patch(f"/games/{game_id}/scorecard", json=payload).status_code == 409
    with sessions() as db:
        assert db.query(models.RoundResolution).filter_by(issue_id=issue_id).count() == 1


@pytest.mark.parametrize("malformed", ["missing_active", "extra_unknown", "extra_removed"])
def test_review_rejects_malformed_active_detail_without_changing_history(round_api, malformed):
    client, _, sessions, game_id, payload, original = prepare(round_api)
    assert client.patch(f"/games/{game_id}/scorecard", json=payload).status_code == 409
    with sessions() as db:
        issue_id = db.query(models.RoundIssue).filter_by(game_id=game_id, field="detail", status="open").one().id
    decision = review(client, issue_id)
    detail = {
        "coverage": "per_hole_complete",
        "holes": [{"hole": h, "points_delta": {"a": -2, "b": 2}} for h in range(1, 19)],
    }
    if malformed == "missing_active":
        del detail["holes"][0]["points_delta"]["b"]
    else:
        detail["holes"][0]["points_delta"]["unknown" if malformed == "extra_unknown" else "removed"] = 3
    bad = client.post(
        f"/round-reconciliation/issues/{issue_id}/resolve", json={**decision, "action": "correct", "value": detail}
    )
    assert bad.status_code == 422, bad.text
    with sessions() as db:
        assert db.query(models.GameStateModel).filter_by(game_id=game_id).one().revision == payload["expected_revision"]
        assert db.get(models.GamePlayerResult, original["result_id"]).hole_scores == original["history"]
        assert db.query(models.RoundResolution).filter_by(issue_id=issue_id).count() == 0
        assert db.get(models.RoundIssue, issue_id).status == "open"

"""Conditional legacy roster corrections; synthetic production-shaped state."""

from copy import deepcopy

import pytest

from app import models
from tests.unit.routers.test_participant_correction import PATH, body, correction_api, preview
from tests.unit.routers.test_round_posting_p1 import round_api

GAME = "a93b258a-3c0e-4531-b0ff-cab5a22d5073"


def state_blob():
    return {
        "source": "scorecard_scan",
        "players": [
            {"id": "p1", "name": "Other", "player_profile_id": 22, "handicap": 18},
            {"id": "p3", "name": "Stuart Gano", "player_profile_id": 21, "handicap": 18},
        ],
        "standings": {"p1": 257, "p3": -257},
        "hole_history": [{"hole": 18, "points_delta": {"p1": 257, "p3": -257}}],
    }


def seed(sessions, *, lobby=False, state=None, revision=0, status="completed", user_id=None):
    blob = state_blob() if state is None else state
    with sessions() as db:
        db.add(models.PlayerProfile(id=22, name="Other", is_active=1))
        db.add(models.GameStateModel(game_id=GAME, revision=revision, game_status=status, state=blob))
        if lobby:
            db.add(
                models.GamePlayer(
                    game_id=GAME,
                    player_slot_id="p3",
                    player_name="Stuart Gano",
                    player_profile_id=21,
                    user_id=user_id,
                )
            )
        db.commit()
    return deepcopy(blob)


def corrected(state):
    expected = deepcopy(state)
    next(p for p in expected["players"] if p["id"] == "p3")["player_profile_id"] = 20
    return expected


@pytest.mark.parametrize("lobby", [False, True])
def test_mapped_links_correct_atomically(correction_api, lobby):
    client, _, sessions = correction_api
    state = seed(sessions, lobby=lobby)
    view = preview(client)
    assert view["eligibility"] == {
        "protected_blockers": {
            "accepted_revision": False,
            "record_retracted": False,
            "participant_identity": False,
            "result_retracted": False,
            "source_binding": False,
            "issue_reference": False,
            "migration_checkpoint": False,
            "mapped_legacy_round": False,
            "game_revision": False,
        },
        "roster_slot": "p3",
    }
    request = body(view)
    response = client.post(PATH + "/correct", json=request)
    assert response.status_code == 200, response.text
    with sessions() as db:
        game = db.query(models.GameStateModel).filter_by(game_id=GAME).one()
        assert game.state == corrected(state)
        assert game.revision == 0 and game.game_status == "completed"
        row = db.get(models.GamePlayerResult, 20)
        assert (row.player_profile_id, row.total_earnings, row.player_name) == (20, -257.0, "Stuart Gano")
        assert db.get(models.GameRecord, 10).final_scores == {"unchanged": -257}
        assert [(p.player_slot_id, p.player_profile_id) for p in db.query(models.GamePlayer)] == (
            [("p3", 20)] if lobby else []
        )
        assert db.get(models.PlayerProfile, 21).name == "Kevin Gent"
        assert db.query(models.PlayerStatistics).count() == 0 and db.query(models.Notification).count() == 0
        audit = db.query(models.ParticipantCorrectionAudit).one()
        assert audit.before["_roster"]["game"]["state"] == state
        assert audit.after["_roster"]["game"]["state"] == corrected(state)
        assert [p["player_profile_id"] for p in audit.before["_roster"]["players"]] == ([21] if lobby else [])
        assert [p["player_profile_id"] for p in audit.after["_roster"]["players"]] == ([20] if lobby else [])
    retry = client.post(PATH + "/correct", json=request)
    assert retry.status_code == 200 and retry.json()["audit_id"] == response.json()["audit_id"]
    with sessions() as db:
        assert db.query(models.ParticipantCorrectionAudit).count() == 1


@pytest.mark.parametrize(
    ("protection", "code"),
    [
        ("accepted_revision", "accepted_revision"),
        ("record_retracted", "record_retracted"),
        ("participant_identity", "participant_identity"),
        ("result_retracted", "result_retracted"),
        ("source_binding", "source_binding"),
        ("closed_issue", "issue_reference"),
        ("migration_checkpoint", "migration_checkpoint"),
        ("mapped_legacy_round", "mapped_legacy_round"),
        ("game_revision", "game_revision"),
    ],
)
def test_protected_categories_stay_fail_closed_with_named_reason(correction_api, protection, code):
    client, _, sessions = correction_api
    seed(sessions, revision=2 if protection == "game_revision" else 0)
    with sessions() as db:
        if protection == "accepted_revision":
            db.get(models.GameRecord, 10).accepted_revision = 3
        elif protection == "record_retracted":
            db.get(models.GameRecord, 10).is_retracted = True
        elif protection == "participant_identity":
            db.get(models.GamePlayerResult, 20).participant_id = "stable-slot"
        elif protection == "result_retracted":
            db.get(models.GamePlayerResult, 20).is_retracted = True
        elif protection == "source_binding":
            db.add(models.RoundSource(kind="sheet", scope="s", round_token="t", game_id=GAME))
        elif protection == "closed_issue":
            db.add(models.RoundSource(id="s2", kind="sheet", scope="s", round_token="t2"))
            db.flush()
            db.add(models.RoundIssue(source_id="s2", game_id=GAME, kind="identity", fingerprint="f", status="resolved"))
        elif protection == "migration_checkpoint":
            db.add(models.RoundMigrationCheckpoint(game_id=GAME, manifest_checksum="m", operation_key="roster"))
        elif protection == "mapped_legacy_round":
            db.add(models.LegacyRound(member="Stuart Gano", date="2026-06-26", score=-257, game_id=GAME))
        db.commit()
    response = client.get(PATH, params={"replacement_profile_id": 20})
    assert response.status_code == 409
    assert code in response.json()["detail"], response.text
    with sessions() as db:
        assert db.get(models.GamePlayerResult, 20).player_profile_id == 21
        assert db.query(models.ParticipantCorrectionAudit).count() == 0
        assert (
            next(
                p
                for p in db.query(models.GameStateModel).filter_by(game_id=GAME).one().state["players"]
                if p["id"] == "p3"
            )["player_profile_id"]
            == 21
        )


@pytest.mark.parametrize(
    ("shape", "code"),
    [
        ("malformed", "malformed_state_roster"),
        ("duplicate_name", "ambiguous_state_slot"),
        ("normalized_duplicate", "ambiguous_state_slot"),
        ("duplicate_slot_id", "ambiguous_state_slot"),
        ("missing_name", "ambiguous_state_slot"),
        ("other_profile", "inconsistent_state_link"),
        ("replacement_present", "duplicate_state_profile"),
        ("old_profile_duplicate", "ambiguous_old_state_profile"),
        ("in_progress", "completed_legacy_roster_required"),
    ],
)
def test_inconsistent_or_ambiguous_rosters_refuse(correction_api, shape, code):
    client, _, sessions = correction_api
    blob = state_blob()
    if shape == "malformed":
        blob["players"] = ["Stuart Gano"]
    elif shape == "duplicate_name":
        blob["players"].append({"id": "p4", "name": "Stuart Gano", "player_profile_id": None})
    elif shape == "normalized_duplicate":
        blob["players"].append({"id": "p4", "name": "  STUART Gano ", "player_profile_id": None})
    elif shape == "duplicate_slot_id":
        blob["players"].append({"id": "p3", "name": "Another", "player_profile_id": None})
    elif shape == "missing_name":
        blob["players"][1]["name"] = "Stuart  Gano"
    elif shape == "other_profile":
        blob["players"][1]["player_profile_id"] = 22
    elif shape == "replacement_present":
        blob["players"][0]["player_profile_id"] = 20
    elif shape == "old_profile_duplicate":
        blob["players"][0]["player_profile_id"] = 21
    seed(sessions, state=blob, status="in_progress" if shape == "in_progress" else "completed")
    response = client.get(PATH, params={"replacement_profile_id": 20})
    assert response.status_code == 409
    assert code in response.json()["detail"], response.text
    with sessions() as db:
        assert db.get(models.GamePlayerResult, 20).player_profile_id == 21
        assert db.query(models.ParticipantCorrectionAudit).count() == 0


@pytest.mark.parametrize("drift", ["name", "profile", "slot", "authenticated"])
def test_game_player_rows_must_match_state_exactly(correction_api, drift):
    client, _, sessions = correction_api
    seed(sessions, lobby=True, user_id="auth0|slot" if drift == "authenticated" else None)
    with sessions() as db:
        player = db.query(models.GamePlayer).one()
        if drift == "name":
            player.player_name = "Someone Else"
        elif drift == "profile":
            player.player_profile_id = 22
        elif drift == "slot":
            player.player_slot_id = "p9"
        db.commit()
    response = client.get(PATH, params={"replacement_profile_id": 20})
    assert response.status_code == 409
    expected = (
        "authenticated_slot_requires_identity_review" if drift == "authenticated" else "inconsistent_game_player_roster"
    )
    assert expected in response.json()["detail"], response.text
    with sessions() as db:
        assert db.get(models.GamePlayerResult, 20).player_profile_id == 21
        assert db.query(models.GamePlayer).one().player_profile_id in (21, 22)


def test_all_blocking_categories_are_reported_together(correction_api):
    client, _, sessions = correction_api
    seed(sessions, revision=1)
    with sessions() as db:
        db.get(models.GameRecord, 10).accepted_revision = 2
        db.get(models.GamePlayerResult, 20).is_retracted = True
        db.add(models.RoundSource(kind="sheet", scope="all", round_token="all", game_id=GAME))
        db.commit()
    response = client.get(PATH, params={"replacement_profile_id": 20})
    assert response.status_code == 409
    for code in ("accepted_revision", "result_retracted", "source_binding", "game_revision"):
        assert code in response.json()["detail"]


def test_roster_change_after_preview_is_stale(correction_api):
    client, _, sessions = correction_api
    seed(sessions, lobby=True)
    request = body(preview(client))
    with sessions() as db:
        game = db.query(models.GameStateModel).filter_by(game_id=GAME).one()
        state = deepcopy(game.state)
        state["players"][0]["handicap"] = 12
        game.state = state
        db.commit()
    assert client.post(PATH + "/correct", json=request).status_code == 409
    with sessions() as db:
        assert db.query(models.ParticipantCorrectionAudit).count() == 0
        assert db.get(models.GamePlayerResult, 20).player_profile_id == 21
        assert db.query(models.GamePlayer).one().player_profile_id == 21


def test_audit_failure_rolls_back_roster_and_result(correction_api):
    from sqlalchemy import text
    from sqlalchemy.exc import IntegrityError

    client, _, sessions = correction_api
    state = seed(sessions, lobby=True)
    request = body(preview(client))
    with sessions() as db:
        db.execute(
            text(
                "CREATE TRIGGER reject_mapped_correction BEFORE INSERT ON participant_correction_audits "
                "BEGIN SELECT RAISE(ABORT, 'synthetic audit failure'); END"
            )
        )
        db.commit()
    with pytest.raises(IntegrityError, match="synthetic audit failure"):
        client.post(PATH + "/correct", json=request)
    with sessions() as db:
        assert db.query(models.GameStateModel).filter_by(game_id=GAME).one().state == state
        assert db.get(models.GamePlayerResult, 20).player_profile_id == 21
        assert db.query(models.GamePlayer).one().player_profile_id == 21
        assert db.query(models.ParticipantCorrectionAudit).count() == 0

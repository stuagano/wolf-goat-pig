"""Admin-only saved participant repair; synthetic HTTP and independent SQL reads."""

from types import SimpleNamespace

import pytest

from app import models
from app.routers import admin
from app.services.auth_service import get_current_user
from tests.unit.participant_audit_guard_support import MUTATIONS, assert_audit_guard
from tests.unit.routers.test_round_posting_p1 import round_api

GAME = "a93b258a-3c0e-4531-b0ff-cab5a22d5073"
PATH = "/admin/participant-results/20"


@pytest.fixture
def correction_api(round_api):
    client, app, sessions = round_api
    app.include_router(admin.router)
    with sessions() as db:
        db.add_all(
            [
                models.PlayerProfile(id=1, name="Admin", email="admin@example.invalid", admin_granted=1, is_active=1),
                models.PlayerProfile(id=20, name="Stuart Gano", is_active=1),
                models.PlayerProfile(id=21, name="Kevin Gent", is_active=1),
                models.GameRecord(id=10, game_id=GAME, final_scores={"unchanged": -257}),
                models.GamePlayerResult(
                    id=20,
                    game_record_id=10,
                    player_name="Stuart Gano",
                    player_profile_id=21,
                    total_earnings=-257,
                    hole_scores=[{"hole": 1, "quarters": -2}],
                ),
            ]
        )
        db.commit()
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(id=1)
    return client, app, sessions


def preview(client):
    response = client.get(PATH, params={"replacement_profile_id": 20})
    assert response.status_code == 200, response.text
    return response.json()


def body(view):
    return {
        "replacement_profile_id": 20,
        "expected_old_profile_id": view["result"]["player_profile_id"],
        "expected_epoch": view["epoch"],
        "expected_snapshot": view["snapshot"],
        "reason": "Correct independently verified participant identity",
        "confirmed": True,
        "request_key": "synthetic-correction-1",
    }


@pytest.mark.parametrize("operation", MUTATIONS)
def test_audit_rejects_physical_mutation(correction_api, operation):
    client, _, sessions = correction_api
    response = client.post(PATH + "/correct", json=body(preview(client)))
    assert response.status_code == 200, response.text
    assert_audit_guard(sessions, operation)


def test_correction_changes_only_link_with_durable_audit_and_fresh_retry(correction_api):
    client, _, sessions = correction_api
    view = preview(client)
    assert view["game_id"] == GAME
    assert view["current_profile"]["name"] == "Kevin Gent"
    assert view["replacement_profile"]["name"] == "Stuart Gano"
    request = body(view)
    response = client.post(PATH + "/correct", json=request)
    assert response.status_code == 200, response.text
    saved = response.json()
    assert saved["result"] == {**view["result"], "player_profile_id": 20}
    assert saved["game_id"] == GAME
    with sessions() as db:
        row = db.get(models.GamePlayerResult, 20)
        assert row.player_profile_id == 20
        assert row.total_earnings == -257
        assert row.hole_scores == [{"hole": 1, "quarters": -2}]
        audit = db.query(models.ParticipantCorrectionAudit).one()
        assert (audit.actor_profile_id, audit.old_profile_id, audit.new_profile_id) == (1, 21, 20)
        assert audit.reason == request["reason"] and audit.created_at
        assert db.get(models.GameRecord, 10).final_scores == {"unchanged": -257}
        assert db.query(models.PlayerStatistics).count() == 0
        assert db.query(models.Notification).count() == 0
    retry = client.post(PATH + "/correct", json=request)
    assert retry.status_code == 200, retry.text
    assert retry.json()["audit_id"] == saved["audit_id"]
    assert preview(client)["result"]["player_profile_id"] == 20


@pytest.mark.parametrize("state", ["anonymous", "normal", "inactive", "missing"])
def test_requires_authenticated_active_admin(correction_api, state):
    client, app, sessions = correction_api
    request = body(preview(client))
    if state == "anonymous":
        app.dependency_overrides.pop(get_current_user)
    else:
        with sessions() as db:
            actor = db.get(models.PlayerProfile, 1)
            if state == "normal":
                actor.admin_granted = 0
            elif state == "inactive":
                actor.is_active = 0
            else:
                db.delete(actor)
            db.commit()
    assert client.get(PATH, params={"replacement_profile_id": 20}).status_code in (401, 403)
    assert client.post(PATH + "/correct", json=request).status_code in (401, 403)
    with sessions() as db:
        assert db.get(models.GamePlayerResult, 20).player_profile_id == 21
        assert db.query(models.ParticipantCorrectionAudit).count() == 0


@pytest.mark.parametrize(
    "change",
    [
        "old_link",
        "score",
        "profile_name",
        "epoch",
        "duplicate",
        "same_name",
        "canonical",
        "paused",
        "token",
        "source",
        "live_mapping",
        "issue",
    ],
)
def test_stale_or_unsupported_states_fail_closed(correction_api, change):
    client, _, sessions = correction_api
    request = body(preview(client))
    with sessions() as db:
        row = db.get(models.GamePlayerResult, 20)
        if change == "old_link":
            row.player_profile_id = None
        elif change == "score":
            row.total_earnings = -258
        elif change == "profile_name":
            db.get(models.PlayerProfile, 20).name = "Changed identity"
        elif change in ("epoch", "canonical", "paused"):
            db.add(
                models.AppConfig(
                    name="round_identity", value={"mode": "legacy" if change == "epoch" else change, "epoch": 3}
                )
            )
        elif change in ("duplicate", "same_name"):
            db.add(
                models.GamePlayerResult(
                    game_record_id=10,
                    player_name="Other" if change == "duplicate" else "  STUART  Gano ",
                    player_profile_id=20 if change == "duplicate" else None,
                )
            )
        elif change == "token":
            row.participant_id = "stable-slot"
        elif change == "source":
            db.add(models.RoundSource(kind="sheet", scope="test", round_token="test", game_id=GAME))
        elif change == "live_mapping":
            db.add(models.GameStateModel(game_id=GAME, state={"players": [{"id": "x", "player_profile_id": 21}]}))
        elif change == "issue":
            db.add(models.RoundSource(id="s", kind="sheet", scope="test", round_token="test"))
            db.flush()
            db.add(models.RoundIssue(source_id="s", game_id=GAME, kind="identity", fingerprint="test"))
        db.commit()
    response = client.post(PATH + "/correct", json=request)
    assert response.status_code == 409, response.text
    with sessions() as db:
        assert db.query(models.ParticipantCorrectionAudit).count() == 0
        assert db.get(models.GamePlayerResult, 20).player_profile_id != 20


@pytest.mark.parametrize(
    "update",
    [
        {"reason": "  "},
        {"reason": "x" * 1001},
        {"confirmed": False},
        {"confirmed": 1},
        {"actor_profile_id": 99},
        {"request_key": " "},
        {"expected_old_profile_id": "21"},
    ],
)
def test_strict_reason_confirmation_and_server_actor(correction_api, update):
    client, _, sessions = correction_api
    response = client.post(PATH + "/correct", json={**body(preview(client)), **update})
    assert response.status_code == 422, response.text
    with sessions() as db:
        assert db.get(models.GamePlayerResult, 20).player_profile_id == 21
        assert db.query(models.ParticipantCorrectionAudit).count() == 0


def test_null_original_link_is_explicitly_supported(correction_api):
    client, _, sessions = correction_api
    with sessions() as db:
        db.get(models.GamePlayerResult, 20).player_profile_id = None
        db.commit()
    view = preview(client)
    assert view["current_profile"] is None
    assert client.post(PATH + "/correct", json=body(view)).status_code == 200
    with sessions() as db:
        assert db.query(models.ParticipantCorrectionAudit).one().old_profile_id is None


def test_noop_and_reused_request_key_rejected(correction_api):
    client, _, sessions = correction_api
    request = body(preview(client))
    assert client.post(PATH + "/correct", json=request).status_code == 200
    assert client.post(PATH + "/correct", json={**request, "reason": "Different"}).status_code == 409
    assert client.post(PATH + "/correct", json={**body(preview(client)), "request_key": "second"}).status_code == 409
    with sessions() as db:
        assert db.query(models.ParticipantCorrectionAudit).count() == 1


def test_stale_old_link_is_checked_even_with_current_snapshot(correction_api):
    client, _, _ = correction_api
    request = {**body(preview(client)), "expected_old_profile_id": None}
    assert client.post(PATH + "/correct", json=request).status_code == 409


def test_missing_current_profile_fails_closed(correction_api):
    client, _, sessions = correction_api
    with sessions() as db:
        db.delete(db.get(models.PlayerProfile, 21))
        db.commit()
    assert client.get(PATH, params={"replacement_profile_id": 20}).status_code == 409


def test_audit_failure_rolls_back_link(correction_api):
    from sqlalchemy import text
    from sqlalchemy.exc import IntegrityError

    client, _, sessions = correction_api
    request = body(preview(client))
    with sessions() as db:
        db.execute(
            text(
                "CREATE TRIGGER reject_correction BEFORE INSERT ON participant_correction_audits BEGIN SELECT RAISE(ABORT, 'synthetic audit failure'); END"
            )
        )
        db.commit()
    with pytest.raises(IntegrityError, match="synthetic audit failure"):
        client.post(PATH + "/correct", json=request)
    with sessions() as db:
        assert db.get(models.GamePlayerResult, 20).player_profile_id == 21
        assert db.query(models.ParticipantCorrectionAudit).count() == 0

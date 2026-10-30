"""Task 7 review regressions through HTTP and physical isolated sessions."""

from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from threading import Event
from time import monotonic, sleep

import pytest
from sqlalchemy import text

from app import models
from app.services.completed_game_service import persist_final_results
from app.services.round_evidence import accepted_draft
from app.utils.time import utc_now
from tests.unit.routers.test_round_reconciliation_api import login, round_api, seed


def attest(client, app, sessions):
    login(app, sessions, 7)
    return client.post("/round-reconciliation/recipient/attest", json={"confirmed": True})


def select(client, app, sessions, proof):
    login(app, sessions, 8)
    return client.put(
        "/round-reconciliation/recipient",
        json={"profile_id": 7, "confirmed": True, "reason": "Synthetic selection", "attestation_id": proof},
    )


def test_actual_partial_writer_is_not_reconciled(round_api):
    client, _, sessions = round_api
    game, _, _ = seed(sessions)
    with sessions() as db:
        state = db.query(models.GameStateModel).filter_by(game_id=game).one()
        draft = accepted_draft(db, game)
        draft.detail_coverage = "partial"
        draft.hole_history = [{"hole": 1, "points_delta": {"a": 1, "b": -1}}]
        persist_final_results(db, state, draft)
        assert not db.query(models.GameRecord).filter_by(game_id=game).one().game_settings["detail_discrepancies"]
        db.commit()
    data = client.get(f"/games/{game}/round-summary").json()
    assert data["detail_coverage"] == "partial" and data["hole_history"]
    assert data["detail_reconciled"] is False


@pytest.mark.parametrize("damage", ["hole", "participant", "total"])
def test_complete_actual_writer_agreement(round_api, damage):
    client, _, sessions = round_api
    game, _, _ = seed(sessions)
    with sessions() as db:
        state = db.query(models.GameStateModel).filter_by(game_id=game).one()
        draft = accepted_draft(db, game)
        draft.detail_coverage = "per_hole_complete"
        draft.hole_history = [
            {"hole": h, "points_delta": {"a": 1 if h == 1 else 0, "b": -1 if h == 1 else 0}} for h in range(1, 19)
        ]
        persist_final_results(db, state, draft)
        db.commit()
    assert client.get(f"/games/{game}/round-summary").json()["detail_reconciled"] is True
    with sessions() as db:
        state = db.query(models.GameStateModel).filter_by(game_id=game).one()
        history = list(state.state["hole_history"])
        if damage == "hole":
            history.pop()
        elif damage == "participant":
            history[-1] = {**history[-1], "points_delta": {"a": 0}}
        else:
            history[-1] = {**history[-1], "points_delta": {"a": 1, "b": -1}}
        state.state = {**state.state, "hole_history": history}
        db.commit()
    assert client.get(f"/games/{game}/round-summary").json()["detail_reconciled"] is False


def test_b_attests_a_selects_b_reviews_no_alerts(round_api):
    client, app, sessions = round_api
    _, issue, _ = seed(sessions)
    response = attest(client, app, sessions)
    assert response.status_code == 200, response.text
    proof = response.json()["attestation_id"]
    with sessions() as db:
        assert db.get(models.AppConfig, "round_identity").value.get("reviewer_profile_id") is None
    response = select(client, app, sessions, proof)
    assert response.status_code == 200, response.text
    login(app, sessions, 7)
    assert client.get(f"/round-reconciliation/issues/{issue}").status_code == 200
    with sessions() as db:
        assert db.query(models.Notification).count() == 0
        assert {row.status for row in db.query(models.RoundDelivery)} == {"unconfigured"}
        assert db.get(models.AppConfig, "round_identity").value["routing_attestation_id"] == proof


@pytest.mark.parametrize("invalid", ["forged", "expired", "mismatched", "revoked", "config_changed"])
def test_unusable_attestation_rejected(round_api, monkeypatch, invalid):
    client, app, sessions = round_api
    response = attest(client, app, sessions)
    assert response.status_code == 200, response.text
    proof = response.json()["attestation_id"]
    if invalid == "forged":
        proof = "forged-proof"
    elif invalid == "expired":
        from app.services import round_recipient

        future = utc_now() + timedelta(days=2)
        monkeypatch.setattr(round_recipient, "utc_now", lambda: future)
    elif invalid == "mismatched":
        with sessions() as db:
            db.get(models.PlayerProfile, 7).email = "changed@example.invalid"
            db.commit()
    elif invalid == "revoked":
        assert client.post("/round-reconciliation/recipient/attest/revoke").status_code == 200
    else:
        with sessions() as db:
            row = db.get(models.AppConfig, "round_identity")
            row.value = {**row.value, "epoch": 5}
            db.commit()
    assert select(client, app, sessions, proof).status_code == 422
    with sessions() as db:
        assert not db.get(models.AppConfig, "round_identity").value.get("routing_confirmed")


@pytest.mark.parametrize("invalid", ["claims", "duplicate", "inactive", "ai", "client_flags"])
def test_attestation_cannot_be_forged(round_api, invalid):
    from app.services.auth_service import get_current_auth0_user

    client, app, sessions = round_api
    login(app, sessions, 7)
    if invalid == "claims":
        app.dependency_overrides[get_current_auth0_user] = lambda: {
            "sub": "auth0|someone-else",
            "email": "review@example.invalid",
            "email_verified": True,
        }
    elif invalid == "client_flags":
        pass
    else:
        with sessions() as db:
            profile = db.get(models.PlayerProfile, 7)
            if invalid == "duplicate":
                db.add(models.PlayerProfile(id=9, name="Duplicate", preferences={"auth0_id": "auth0|review"}))
            elif invalid == "inactive":
                profile.is_active = 0
            else:
                profile.is_ai = 1
            db.commit()
    body = {"confirmed": True}
    if invalid == "client_flags":
        body.update(email="forged@example.invalid", email_verified=True)
    assert client.post("/round-reconciliation/recipient/attest", json=body).status_code == 422


@pytest.mark.parametrize("revocation", ["confirmation", "linkage", "admin", "confirming_admin"])
def test_waiting_resolution_rechecks_locked_authority(round_api, monkeypatch, revocation):
    from app.routers import round_reconciliation as router
    from app.services.round_identity import acquire_reconciliation_lock

    client, app, sessions = round_api
    if sessions.kw["bind"].dialect.name != "postgresql":
        return  # PostgreSQL branch executes the actual lock interleaving.
    game, issue, decision = seed(sessions)
    response = attest(client, app, sessions)
    assert response.status_code == 200, response.text
    assert select(client, app, sessions, response.json()["attestation_id"]).status_code == 200
    login(app, sessions, 8 if revocation == "admin" else 7)
    checked = Event()
    original = router.require_reviewer

    def observed_auth(db, actor):
        result = original(db, actor)
        checked.set()
        return result

    monkeypatch.setattr(router, "require_reviewer", observed_auth)
    with sessions() as blocker, ThreadPoolExecutor(max_workers=1) as pool:
        acquire_reconciliation_lock(blocker)
        before = blocker.query(models.GameRecord).filter_by(game_id=game).one().final_scores
        future = pool.submit(client.post, f"/round-reconciliation/issues/{issue}/resolve", json=decision)
        try:
            assert checked.wait(5), "Request must pass initial authorization before revocation"
            deadline = monotonic() + 5
            while not blocker.execute(
                text("SELECT EXISTS (SELECT 1 FROM pg_locks WHERE locktype = 'advisory' AND NOT granted)")
            ).scalar():
                assert monotonic() < deadline, "Request must actually wait on the global lock"
                sleep(0.01)
            # A physically distinct transaction retains the lock until the
            # config/profile revocation commits, while request identity map is stale.
            if revocation == "confirmation":
                row = blocker.get(models.AppConfig, "round_identity")
                row.value = {**row.value, "routing_confirmed": False}
            elif revocation == "linkage":
                blocker.get(models.PlayerProfile, 7).preferences = {"auth0_id": "auth0|changed"}
            else:
                blocker.get(models.PlayerProfile, 8).admin_granted = 0
            blocker.commit()
        finally:
            blocker.rollback()
        response = future.result(timeout=10)
    assert response.status_code == 403, response.text
    with sessions() as db:
        assert db.query(models.RoundResolution).count() == 0
        assert db.get(models.RoundIssue, issue).status == "open"
        assert db.query(models.GameRecord).filter_by(game_id=game).one().final_scores == before


def test_resolution_openapi_models_held_response(round_api):
    _, app, _ = round_api
    responses = app.openapi()["paths"]["/round-reconciliation/issues/{issue_id}/resolve"]["post"]["responses"]
    assert responses["202"]["content"]["application/json"]["schema"] == {"$ref": "#/components/schemas/IngestOutcome"}

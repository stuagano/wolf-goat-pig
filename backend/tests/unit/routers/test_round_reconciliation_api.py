"""Real HTTP/session reconciliation contracts; synthetic evidence only."""

import os
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool, StaticPool

from app import models
from app.database import get_db
from app.routers import admin, games
from app.schemas.round_identity import RoundDraft, SourceRef
from app.services.auth_service import get_current_auth0_user, get_current_user
from app.services.round_reconciliation import observe_round


@pytest.fixture(params=["sqlite", "postgres"])
def round_api(request):
    from app.routers import round_reconciliation

    pg_admin = None
    if request.param == "postgres":
        raw = os.environ.get("ROUND_IDENTITY_TEST_DATABASE_URL")
        if not raw:
            pytest.skip("Requires disposable localhost PostgreSQL *_test database")
        url = make_url(raw)
        assert url.host in {"localhost", "127.0.0.1", "::1"} and url.database.endswith("_test") and not url.query
        schema = "review_" + uuid4().hex
        pg_admin = create_engine(url.set(drivername="postgresql+psycopg2"), poolclass=NullPool)
        with pg_admin.begin() as tx:
            tx.execute(text(f'CREATE SCHEMA "{schema}"'))
        engine = create_engine(
            url.set(drivername="postgresql+psycopg2"),
            poolclass=NullPool,
            connect_args={"options": f"-csearch_path={schema} -cstatement_timeout=10000"},
        )
    else:
        engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    models.Base.metadata.create_all(engine)
    sessions = sessionmaker(engine)
    app = FastAPI()
    for router in (games.router, admin.router, round_reconciliation.router):
        app.include_router(router)

    def database():
        with sessions() as db:
            yield db

    app.dependency_overrides[get_db] = database
    with sessions() as db:
        db.add_all(
            [
                models.PlayerProfile(id=1, name="Participant", is_active=1),
                models.PlayerProfile(
                    id=7,
                    name="Reviewer",
                    email="review@example.invalid",
                    is_active=1,
                    preferences={"auth0_id": "auth0|review"},
                ),
                models.PlayerProfile(
                    id=8,
                    name="Admin",
                    email="admin@example.invalid",
                    is_active=1,
                    admin_granted=1,
                    preferences={"auth0_id": "auth0|admin"},
                ),
                models.AppConfig(name="round_identity", value={"mode": "canonical", "epoch": 4}),
            ]
        )
        db.commit()
    yield TestClient(app), app, sessions
    engine.dispose()
    if pg_admin:
        with pg_admin.begin() as tx:
            tx.execute(text(f'DROP SCHEMA "{schema}" CASCADE'))
        pg_admin.dispose()


def login(app, sessions, profile=8):
    with sessions() as db:
        user = db.get(models.PlayerProfile, profile)
        db.expunge(user)
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_current_auth0_user] = lambda: {
        "sub": f"auth0|{'admin' if profile == 8 else 'review'}",
        "email": user.email,
        "email_verified": True,
    }


def seed(sessions, changed=2):
    with sessions() as db:
        draft = RoundDraft(
            raw_date="unknown-year",
            group="A",
            roster_complete=True,
            players=[
                {"participant_id": "a", "name": "One", "profile_id": 1, "quarters": 1},
                {"participant_id": "b", "name": "Two", "quarters": -1},
            ],
        )
        source = SourceRef(kind="sheet", scope="private-scope", round_token="secret-token")
        outcome = observe_round(
            db,
            source,
            draft,
            observation_key="first",
            raw_payload={"private": "secret"},
            continuity_verified=True,
            create_without_candidate=True,
        )
        game_id = outcome.game_id
        draft.players[0].quarters = changed
        draft.players[1].quarters = -changed
        outcome = observe_round(
            db, source, draft, observation_key=str(changed), raw_payload={"private": "secret"}, continuity_verified=True
        )
        issue = db.query(models.RoundIssue).filter_by(field="quarters", participant_id="a", status="open").one()
        decision = {
            "action": "keep",
            "reason": "Reviewed",
            "expected_game_revision": outcome.revision,
            "expected_issue_revision": issue.revision,
            "expected_head_revision": issue.head_revision,
        }
        issue_id = issue.id
        db.commit()
        return game_id, issue_id, decision


def test_anonymous_auth_before_lookup(round_api):
    client, _, sessions = round_api
    for path in ("missing", "issue-1"):
        response = client.post(
            f"/round-reconciliation/issues/{path}/resolve",
            json={"action": "keep", "reason": "review", "expected_issue_revision": 1, "expected_head_revision": 1},
        )
        assert response.status_code in (401, 403)
    with sessions() as db:
        assert db.query(models.RoundResolution).count() == 0


def test_participant_has_no_review_rights(round_api):
    client, app, sessions = round_api
    _, issue, decision = seed(sessions)
    login(app, sessions, 1)
    for path in ("/issues", f"/issues/{issue}", "/health"):
        assert client.get("/round-reconciliation" + path).status_code == 403
    assert client.post(f"/round-reconciliation/issues/{issue}/resolve", json=decision).status_code == 403


def test_review_resolution_and_stale_rollback(round_api):
    client, app, sessions = round_api
    game, issue, decision = seed(sessions)
    login(app, sessions)
    assert client.get("/round-reconciliation/issues/missing").status_code == 404
    detail = client.get(f"/round-reconciliation/issues/{issue}")
    assert detail.status_code == 200 and detail.json()["observation"]["raw_payload"]["payload"] == {"private": "secret"}
    response = client.post(f"/round-reconciliation/issues/{issue}/resolve", json=decision)
    assert response.status_code == 202, response.text
    assert response.json()["status"] == "held"
    assert client.post(f"/round-reconciliation/issues/{issue}/resolve", json=decision).status_code == 409
    with sessions() as db:
        assert db.query(models.RoundResolution).count() == 1
        assert db.query(models.GameRecord).filter_by(game_id=game).one().final_scores["a"] == 1


@pytest.mark.parametrize("change", [{"reason": "   "}, {"action": "correct", "value": "not-a-number"}])
def test_invalid_decisions_rollback(round_api, change):
    client, app, sessions = round_api
    _, issue, decision = seed(sessions)
    login(app, sessions)
    response = client.post(f"/round-reconciliation/issues/{issue}/resolve", json={**decision, **change})
    assert response.status_code == 422, response.text
    with sessions() as db:
        assert db.get(models.RoundIssue, issue).status == "open"
        assert db.query(models.RoundResolution).count() == 0


def test_public_summary_redaction_and_alias_many(round_api):
    client, _, sessions = round_api
    game, _, _ = seed(sessions)
    with sessions() as db:
        db.add_all(
            [
                models.RoundAlias(date_key="old", group="A", location="", game_id=g)
                for g in (game, "other", "unavailable")
            ]
        )
        db.add(models.GameStateModel(game_id="other", state={}, game_status="completed"))
        db.add(models.GameRecord(game_id="other"))
        db.commit()
    response = client.get(f"/games/{game}/round-summary")
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["players"][0]["quarters"] == 1
    assert data["played_on"] is None and data["course_name"] is None
    assert data["hole_history"] == [] and data["detail_coverage"] == "totals_only"
    assert data["conflict_count"] == 2 and data["accepted_label"] == "accepted"
    for secret in ("secret", "private-scope", "candidate_game_ids", "@"):
        assert secret not in response.text
    aliases = client.get("/round-reconciliation/aliases", params={"date": "old", "group": "A"}).json()
    assert aliases == {"status": "ambiguous", "game_ids": sorted([game, "other"])}
    assert client.get(f"/games/{game}/state").status_code == 200
    assert client.get("/games/unavailable/round-summary").status_code == 404


def test_superseded_head_and_pause_cannot_resolve(round_api):
    client, app, sessions = round_api
    _, issue, decision = seed(sessions)
    seed(sessions, changed=3)
    login(app, sessions)
    assert client.post(f"/round-reconciliation/issues/{issue}/resolve", json=decision).status_code == 409
    with sessions() as db:
        row = db.get(models.AppConfig, "round_identity")
        row.value = {**row.value, "mode": "paused"}
        current = db.query(models.RoundIssue).filter_by(field="quarters", participant_id="a", status="open").one()
        current_id = current.id
        decision.update(expected_issue_revision=current.revision, expected_head_revision=current.head_revision)
        db.commit()
    assert client.post(f"/round-reconciliation/issues/{current_id}/resolve", json=decision).status_code == 409
    with sessions() as db:
        assert db.query(models.RoundResolution).count() == 0


def test_requeue_transaction_and_confirmed_reviewer(round_api):
    client, app, sessions = round_api
    _, issue, _ = seed(sessions)
    login(app, sessions)
    assert (
        client.put(
            "/round-reconciliation/recipient", json={"profile_id": 8, "confirmed": True, "reason": "synthetic consent"}
        ).status_code
        == 200
    )
    response = client.post(
        "/round-reconciliation/requeue", json={"issue_ids": [issue, "zz-missing"], "reason": "synthetic selection"}
    )
    assert response.status_code == 409
    with sessions() as db:
        assert db.query(models.RoundResolution).count() == 0
        assert {row.status for row in db.query(models.RoundDelivery)} == {"unconfigured"}
    assert (
        client.post(
            "/round-reconciliation/requeue", json={"issue_ids": [issue], "reason": "synthetic selection"}
        ).status_code
        == 200
    )
    with sessions() as db:
        assert db.query(models.RoundResolution).one().action == "routing_requeue"
        assert db.query(models.RoundDelivery).filter_by(recipient_profile_id=8, status="pending").count() == 2
    # Exercise the real self-attestation -> explicit other-admin selection path.
    login(app, sessions, 7)
    proof = client.post("/round-reconciliation/recipient/attest", json={"confirmed": True})
    assert proof.status_code == 200
    login(app, sessions)
    assert (
        client.put(
            "/round-reconciliation/recipient",
            json={
                "profile_id": 7,
                "attestation_id": proof.json()["attestation_id"],
                "confirmed": True,
                "reason": "Synthetic explicit selection",
            },
        ).status_code
        == 200
    )
    login(app, sessions, 7)
    assert client.get("/round-reconciliation/issues", params={"limit": 1}).json()["total"] == 2
    assert client.get(f"/round-reconciliation/issues/{issue}").status_code == 200
    assert client.get("/round-reconciliation/health").status_code == 200
    assert client.post("/round-reconciliation/requeue", json={"issue_ids": [issue], "reason": "x"}).status_code == 403
    with sessions() as db:
        config = db.get(models.AppConfig, "round_identity")
        config.value = {**config.value, "routing_confirmed": False}
        db.commit()
    assert client.get(f"/round-reconciliation/issues/{issue}").status_code == 403


def test_public_unknown_retracted_and_alias_zero_one(round_api):
    client, _, sessions = round_api
    game, _, _ = seed(sessions)
    with sessions() as db:
        record = db.query(models.GameRecord).filter_by(game_id=game).one()
        record.is_retracted = True
        result = db.query(models.GamePlayerResult).filter_by(game_record_id=record.id, participant_id="a").one()
        result.total_earnings = None
        result.is_retracted = True
        db.add(models.RoundAlias(date_key="old", group="A", location="", game_id=game))
        db.commit()
    data = client.get(f"/games/{game}/round-summary").json()
    assert data["is_retracted"] and not data["score_eligible"]
    assert data["players"][0]["quarters"] is None and data["players"][0]["is_retracted"]
    assert client.get("/round-reconciliation/aliases", params={"date": "none", "group": "A"}).json() == {
        "status": "missing",
        "game_ids": [],
    }
    assert client.get("/round-reconciliation/aliases", params={"date": "old", "group": "A"}).json() == {
        "status": "resolved",
        "game_ids": [game],
    }


def test_bound_target_revision_is_forwarded_and_held(round_api):
    client, app, sessions = round_api
    game, _, _ = seed(sessions)
    with sessions() as db:
        record = db.query(models.GameRecord).filter_by(game_id=game).one()
        draft = RoundDraft(
            raw_date=record.raw_date,
            group="A",
            roster_complete=True,
            players=[
                {"participant_id": "a", "name": "One", "profile_id": 1, "quarters": 1},
                {"participant_id": "b", "name": "Two", "quarters": -1},
            ],
        )
        held = observe_round(
            db,
            SourceRef(kind="scan", scope="private", round_token="other"),
            draft,
            observation_key="candidate",
            raw_payload={},
            continuity_verified=True,
        )
        identity = db.query(models.RoundIssue).filter_by(kind="identity", game_id=None).one()
        issue_id = identity.id
        revision = db.query(models.GameStateModel).filter_by(game_id=game).one().revision
        body = {
            "action": "bind_existing",
            "target_game_id": game,
            "reason": "reviewed candidate",
            "expected_game_revision": None,
            "expected_target_game_revision": revision + 1,
            "expected_issue_revision": identity.revision,
            "expected_head_revision": identity.head_revision,
        }
        assert held.status == "held"
        db.commit()
    login(app, sessions)
    assert client.post(f"/round-reconciliation/issues/{issue_id}/resolve", json=body).status_code == 409
    body["expected_target_game_revision"] = revision
    response = client.post(f"/round-reconciliation/issues/{issue_id}/resolve", json=body)
    assert response.status_code in (200, 202), response.text
    with sessions() as db:
        assert db.query(models.RoundSource).filter_by(kind="scan").one().game_id == game
        assert db.query(models.RoundResolution).filter_by(issue_id=issue_id).one().target_game_id == game


def test_recorded_detail_labels_preserve_accepted_totals(round_api):
    client, _, sessions = round_api
    game, _, _ = seed(sessions)
    with sessions() as db:
        state = db.query(models.GameStateModel).filter_by(game_id=game).one()
        state.state = {
            **state.state,
            "hole_history": [{"hole": 1, "points_delta": {"a": 2, "b": -2}, "private_source": "never-public"}],
        }
        record = db.query(models.GameRecord).filter_by(game_id=game).one()
        record.detail_coverage = "partial"
        record.game_settings = {"detail_discrepancies": {"a": {"accepted": 1, "computed": 2}}}
        db.commit()
    response = client.get(f"/games/{game}/round-summary")
    data = response.json()
    assert data["players"][0]["quarters"] == 1
    assert data["hole_history"] == [{"hole": 1, "points_delta": {"a": 2, "b": -2}}]
    assert not data["detail_reconciled"] and data["detail_label"] == "accepted_recorded_detail"
    assert data["detail_discrepancies"]["a"] == {"accepted": 1, "computed_detail": 2}
    assert "never-public" not in response.text


def test_recipient_health_and_mode_guards(round_api):
    client, app, sessions = round_api
    login(app, sessions)
    assert (
        client.put(
            "/round-reconciliation/recipient", json={"profile_id": 8, "confirmed": False, "reason": "fixture"}
        ).status_code
        == 422
    )
    assert (
        client.put(
            "/round-reconciliation/recipient", json={"profile_id": 7, "confirmed": True, "reason": "fixture"}
        ).status_code
        == 422
    )
    response = client.put(
        "/round-reconciliation/recipient", json={"profile_id": 8, "confirmed": True, "reason": "synthetic consent"}
    )
    assert response.status_code == 200, response.text
    health = client.get("/round-reconciliation/health")
    assert health.status_code == 200 and health.json()["configured"] is True
    assert "@" not in health.text and "auth0" not in health.text
    for body, status in [
        ({"mode": "canonical", "expected_epoch": 3, "verification_report": {}}, 409),
        ({"mode": "canonical", "expected_epoch": 4, "verification_report": {"passed": True}}, 409),
        ({"mode": "canonical", "verification_report": {}}, 422),
    ]:
        response = client.put("/admin/round-identity/mode", json=body)
        assert response.status_code == status, response.text
    with sessions() as db:
        assert db.get(models.AppConfig, "round_identity").value["epoch"] == 4

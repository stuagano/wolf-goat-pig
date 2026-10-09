"""Player side of claims: picking a taken name, and /players/me reporting it."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.models import AccountClaim, LegacyRosterPlayer, PlayerProfile
from app.services import account_claim_service
from app.services.auth_service import get_current_auth0_user


@pytest.fixture
def env(monkeypatch):
    monkeypatch.setattr("app.services.auth_service._send_welcome_email", lambda *args: None)
    notified = []
    monkeypatch.setattr(account_claim_service, "notify_admins_of_claim", lambda *args: notified.append(args))
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    sessions = sessionmaker(bind=engine)
    with sessions() as db:
        for name in ["Gregg Colburn", "Kevin Gent"]:
            db.add(LegacyRosterPlayer(name=name, source="seed", added_at="2026-01-01"))
        db.add_all(
            [
                PlayerProfile(id=1, name="Gregg Colburn", legacy_name="Gregg Colburn", created_at="2025-01-01"),
                PlayerProfile(
                    id=2,
                    name="gregg@example.com",
                    email="gregg@example.com",
                    preferences={"auth0_id": "auth0|gregg"},
                    created_at="2026-10-09",
                ),
                PlayerProfile(
                    id=3,
                    name="Kevin Gent",
                    legacy_name="Kevin Gent",
                    preferences={"auth0_id": "google-oauth2|kevin"},
                    created_at="2025-01-01",
                ),
            ]
        )
        db.commit()

    def database():
        with sessions() as db:
            yield db

    app.dependency_overrides[get_db] = database
    app.dependency_overrides[get_current_auth0_user] = lambda: {
        "sub": "auth0|gregg",
        "email": "gregg@example.com",
        "email_verified": True,
        "name": "gregg@example.com",
    }
    yield TestClient(app), sessions, notified
    app.dependency_overrides.pop(get_db, None)
    app.dependency_overrides.pop(get_current_auth0_user, None)
    engine.dispose()


def pick(client, name):
    return client.put("/players/me/legacy-name", json={"legacy_name": name})


def test_picking_a_name_held_by_a_login_less_original_returns_202_and_notifies(env):
    client, sessions, notified = env
    resp = pick(client, "Gregg Colburn")
    assert resp.status_code == 202, resp.text
    assert resp.json() == {
        "status": "claim_pending",
        "canonical_name": "Gregg Colburn",
        "message": "Request sent — a club admin will connect you to your history.",
    }
    assert notified == [("Gregg Colburn", "gregg@example.com")]
    with sessions() as db:
        assert db.query(AccountClaim).filter_by(status="pending").count() == 1


def test_repeat_pick_does_not_notify_twice(env):
    client, _, notified = env
    pick(client, "Gregg Colburn")
    assert pick(client, "Gregg Colburn").status_code == 202
    assert len(notified) == 1


def test_name_held_by_a_profile_with_a_login_is_still_409(env):
    client, sessions, notified = env
    resp = pick(client, "Kevin Gent")
    assert resp.status_code == 409
    assert notified == []
    with sessions() as db:
        assert db.query(AccountClaim).count() == 0


def test_unverified_email_gets_403(env):
    client, _, _ = env
    app.dependency_overrides[get_current_auth0_user] = lambda: {
        "sub": "auth0|gregg",
        "email": "gregg@example.com",
        "email_verified": False,
    }
    resp = pick(client, "Gregg Colburn")
    assert resp.status_code == 403
    assert "Verify your email" in resp.json()["detail"]


def test_me_reports_the_pending_claim(env):
    client, _, _ = env
    assert client.get("/players/me").json()["pending_claim"] is None
    pick(client, "Gregg Colburn")
    claim = client.get("/players/me").json()["pending_claim"]
    assert claim["canonical_name"] == "Gregg Colburn" and claim["created_at"]


def test_other_profile_responses_never_carry_pending_claim(env):
    client, _, _ = env
    pick(client, "Gregg Colburn")
    assert client.get("/players/name/gregg@example.com").json().get("pending_claim") is None

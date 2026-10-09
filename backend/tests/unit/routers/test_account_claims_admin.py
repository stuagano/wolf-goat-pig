"""Admin side of claims: approve moves the login onto the original and retires the stray."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.models import AccountClaim, LegacyRosterPlayer, PlayerProfile
from app.services.auth_service import AuthService, get_current_auth0_user

ADMIN = {"sub": "auth0|admin", "email": "admin@example.com"}


@pytest.fixture
def env(monkeypatch):
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    sessions = sessionmaker(bind=engine)
    with sessions() as db:
        db.add(LegacyRosterPlayer(name="Gregg Colburn", source="seed", added_at="2026-01-01"))
        db.add_all(
            [
                PlayerProfile(id=1, name="Gregg Colburn", legacy_name="Gregg Colburn", created_at="2025-01-01"),
                PlayerProfile(
                    id=2,
                    name="gregg@example.com",
                    email="gregg@example.com",
                    preferences={"auth0_id": "auth0|gregg", "display_hints": True},
                    created_at="2026-10-09",
                ),
                AccountClaim(
                    id=10,
                    requester_profile_id=2,
                    target_profile_id=1,
                    canonical_name="Gregg Colburn",
                    requester_email="gregg@example.com",
                    status="pending",
                    created_at="2026-10-09T10:00:00",
                ),
            ]
        )
        db.commit()

    def database():
        with sessions() as db:
            yield db

    monkeypatch.setenv("SUPER_ADMIN_EMAILS", "admin@example.com")
    app.dependency_overrides[get_db] = database
    app.dependency_overrides[get_current_auth0_user] = lambda: ADMIN
    yield TestClient(app), sessions
    app.dependency_overrides.pop(get_db, None)
    app.dependency_overrides.pop(get_current_auth0_user, None)
    engine.dispose()


def test_list_shows_pending_claims_with_both_profiles(env):
    client, _ = env
    claims = client.get("/players/admin/claims").json()["claims"]
    assert [c["id"] for c in claims] == [10]
    assert claims[0]["requester"]["id"] == 2 and claims[0]["requester"]["login"] == "auth0"
    assert claims[0]["target"]["id"] == 1 and claims[0]["target"]["login"] is None


def test_approve_moves_login_onto_original_and_retires_the_stray(env):
    client, sessions = env
    resp = client.post("/players/admin/claims/10/approve")
    assert resp.status_code == 200, resp.text
    assert (resp.json()["status"], resp.json()["resolved_by"]) == ("approved", "admin@example.com")
    with sessions() as db:
        original, stray = db.get(PlayerProfile, 1), db.get(PlayerProfile, 2)
        assert (original.email, original.preferences["auth0_id"], original.legacy_name, original.name) == (
            "gregg@example.com",
            "auth0|gregg",
            "Gregg Colburn",
            "Gregg Colburn",
        )
        assert not stray.is_active and stray.email is None and "auth0_id" not in (stray.preferences or {})
        resolved = AuthService.get_or_create_player_profile(
            db, {"sub": "auth0|gregg", "email": "gregg@example.com", "email_verified": True, "name": "Gregg"}
        )
        assert resolved.id == 1


def test_second_approve_is_409(env):
    client, _ = env
    client.post("/players/admin/claims/10/approve")
    resp = client.post("/players/admin/claims/10/approve")
    assert resp.status_code == 409
    assert "already approved" in resp.json()["detail"]


def test_approve_refused_when_original_already_has_a_login(env):
    client, sessions = env
    with sessions() as db:
        db.get(PlayerProfile, 1).preferences = {"auth0_id": "google-oauth2|someone"}
        db.commit()
    resp = client.post("/players/admin/claims/10/approve")
    assert resp.status_code == 409
    with sessions() as db:
        assert db.get(PlayerProfile, 2).is_active and db.get(AccountClaim, 10).status == "pending"


def test_approve_refused_when_requester_was_retired(env):
    client, sessions = env
    with sessions() as db:
        db.get(PlayerProfile, 2).is_active = 0
        db.commit()
    assert client.post("/players/admin/claims/10/approve").status_code == 409


def test_approve_email_collision_is_409_not_500(env):
    client, sessions = env
    with sessions() as db:
        db.get(AccountClaim, 10).requester_email = "taken@example.com"
        db.get(PlayerProfile, 2).email = None
        db.add(PlayerProfile(id=3, name="Someone Else", email="taken@example.com", created_at="2025-01-01"))
        db.commit()
    resp = client.post("/players/admin/claims/10/approve")
    assert resp.status_code == 409
    with sessions() as db:
        assert db.get(PlayerProfile, 2).is_active and db.get(AccountClaim, 10).status == "pending"


def test_dismiss_once(env):
    client, _ = env
    resp = client.post("/players/admin/claims/10/dismiss")
    assert resp.status_code == 200 and resp.json()["status"] == "dismissed"
    assert client.post("/players/admin/claims/10/dismiss").status_code == 409
    assert client.get("/players/admin/claims").json()["claims"] == []


def test_unknown_claim_404_and_non_admin_403(env):
    client, _ = env
    assert client.post("/players/admin/claims/999/approve").status_code == 404
    app.dependency_overrides[get_current_auth0_user] = lambda: {"sub": "auth0|x", "email": "player@example.com"}
    assert client.get("/players/admin/claims").status_code == 403
    assert client.post("/players/admin/claims/10/approve").status_code == 403


def test_approve_when_stray_already_holds_the_roster_name(env):
    client, sessions = env
    with sessions() as db:
        db.get(PlayerProfile, 1).name = "Gregg C"
        db.get(PlayerProfile, 2).name = "Gregg Colburn"
        db.commit()
    resp = client.post("/players/admin/claims/10/approve")
    assert resp.status_code == 200, resp.text
    with sessions() as db:
        assert db.get(PlayerProfile, 1).name == "Gregg Colburn"
        assert db.get(PlayerProfile, 2).name == "retired-profile-2"


def test_approve_refused_when_a_third_profile_holds_the_roster_name(env):
    client, sessions = env
    with sessions() as db:
        db.add(PlayerProfile(id=3, name="Other", legacy_name="Gregg Colburn", created_at="2025-01-01"))
        db.commit()
    resp = client.post("/players/admin/claims/10/approve")
    assert resp.status_code == 409
    assert "already linked to profile #3" in resp.json()["detail"]
    with sessions() as db:
        assert db.get(PlayerProfile, 2).is_active and db.get(AccountClaim, 10).status == "pending"


def test_approve_refused_when_a_third_profile_holds_the_login(env):
    client, sessions = env
    with sessions() as db:
        db.add(PlayerProfile(id=3, name="Other", preferences={"auth0_id": "auth0|gregg"}, created_at="2025-01-01"))
        db.commit()
    resp = client.post("/players/admin/claims/10/approve")
    assert resp.status_code == 409 and "profile #3" in resp.json()["detail"]

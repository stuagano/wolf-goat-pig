"""Effective admin = env allowlist OR a flagged, active, uniquely-linked profile."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.models import PlayerProfile
from app.services.auth_service import get_current_auth0_user


@pytest.fixture
def env(monkeypatch):
    monkeypatch.setattr("app.services.auth_service._send_welcome_email", lambda *args: None)
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    sessions = sessionmaker(bind=engine)
    with sessions() as db:
        db.add_all(
            [
                PlayerProfile(
                    id=1,
                    name="Flagged",
                    email="flagged@example.com",
                    admin_granted=1,
                    preferences={"auth0_id": "auth0|flagged"},
                    created_at="2026-01-01",
                ),
                PlayerProfile(
                    id=2,
                    name="Plain",
                    email="plain@example.com",
                    preferences={"auth0_id": "auth0|plain"},
                    created_at="2026-01-01",
                ),
                PlayerProfile(
                    id=3,
                    name="Retired",
                    email=None,
                    admin_granted=1,
                    is_active=0,
                    preferences={"auth0_id": "auth0|retired"},
                    created_at="2026-01-01",
                ),
            ]
        )
        db.commit()

    def database():
        with sessions() as db:
            yield db

    monkeypatch.setenv("SUPER_ADMIN_EMAILS", "env@example.com")
    app.dependency_overrides[get_db] = database
    yield TestClient(app), sessions
    app.dependency_overrides.pop(get_db, None)
    app.dependency_overrides.pop(get_current_auth0_user, None)
    engine.dispose()


def login(sub, email):
    app.dependency_overrides[get_current_auth0_user] = lambda: {"sub": sub, "email": email}


ADMIN_ONLY = "/players/admin/account-links?query=xx"


def test_env_admin_passes_without_profile(env):
    client, _ = env
    login("auth0|nobody", "env@example.com")
    assert client.get(ADMIN_ONLY).status_code == 200


def test_flagged_linked_profile_passes(env):
    client, _ = env
    login("auth0|flagged", "flagged@example.com")
    assert client.get(ADMIN_ONLY).status_code == 200


def test_unflagged_profile_is_forbidden(env):
    client, _ = env
    login("auth0|plain", "plain@example.com")
    assert client.get(ADMIN_ONLY).status_code == 403


def test_flagged_but_inactive_is_forbidden(env):
    client, _ = env
    login("auth0|retired", "retired@example.com")
    assert client.get(ADMIN_ONLY).status_code == 403


def test_subject_matching_two_profiles_is_forbidden(env):
    client, sessions = env
    with sessions() as db:
        db.add(
            PlayerProfile(
                id=4, name="Dupe", admin_granted=1, preferences={"auth0_id": "auth0|flagged"}, created_at="2026-01-01"
            )
        )
        db.commit()
    login("auth0|flagged", "flagged@example.com")
    assert client.get(ADMIN_ONLY).status_code == 403


def test_revoke_takes_effect_on_next_request(env):
    client, sessions = env
    login("auth0|flagged", "flagged@example.com")
    assert client.get(ADMIN_ONLY).status_code == 200
    with sessions() as db:
        db.get(PlayerProfile, 1).admin_granted = 0
        db.commit()
    assert client.get(ADMIN_ONLY).status_code == 403


def test_me_reports_admin_role_for_flagged_profile(env):
    client, _ = env
    login("auth0|flagged", "flagged@example.com")
    body = client.get("/players/me").json()
    assert (body["role"], body["is_admin"], body["is_super_admin"]) == ("admin", True, False)


def test_stored_flag_does_not_leak_into_profile_responses(env):
    client, _ = env
    login("auth0|plain", "plain@example.com")
    resp = client.get("/players/name/Flagged")
    assert resp.status_code == 200
    assert resp.json()["is_admin"] is False

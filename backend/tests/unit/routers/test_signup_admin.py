"""Admins add a linked player to an upcoming day's sign-up sheet."""

from datetime import timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.models import DailySignup, PlayerProfile
from app.routers import signup_admin
from app.services.auth_service import get_current_auth0_user
from app.utils.time import club_today

ADMIN = {"sub": "auth0|admin", "email": "admin@example.com"}


@pytest.fixture
def env(monkeypatch):
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    sessions = sessionmaker(bind=engine)
    with sessions() as db:
        db.add_all(
            [
                PlayerProfile(
                    id=1,
                    name="Gregg Colburn",
                    legacy_name="Gregg Colburn",
                    email="gregg@example.com",
                    created_at="2025-01-01",
                ),
                PlayerProfile(id=2, name="Unlinked Person", email="u@example.com", created_at="2025-01-01"),
                PlayerProfile(id=3, name="Retired", legacy_name="Old Name", is_active=0, created_at="2025-01-01"),
                PlayerProfile(id=4, name="Chip Halbert", legacy_name="Chip Halbert", created_at="2025-01-01"),
            ]
        )
        db.commit()

    def database():
        with sessions() as db:
            yield db

    sent = []
    monkeypatch.setattr(signup_admin, "_send_signup_confirmation", lambda *args: sent.append(args))
    monkeypatch.setenv("SUPER_ADMIN_EMAILS", "admin@example.com")
    app.dependency_overrides[get_db] = database
    app.dependency_overrides[get_current_auth0_user] = lambda: ADMIN
    yield TestClient(app), sessions, sent
    app.dependency_overrides.pop(get_db, None)
    app.dependency_overrides.pop(get_current_auth0_user, None)
    engine.dispose()


def upcoming(days=3):
    return (club_today() + timedelta(days=days)).isoformat()


def test_players_list_has_only_active_linked_profiles_sorted(env):
    client, _, _ = env
    body = client.get("/signups/admin/players").json()
    assert body["players"] == [{"id": 4, "legacy_name": "Chip Halbert"}, {"id": 1, "legacy_name": "Gregg Colburn"}]


def test_admin_adds_a_player_as_if_they_signed_up(env):
    client, sessions, sent = env
    day = upcoming()
    resp = client.post("/signups/admin", json={"date": day, "player_profile_id": 1, "notes": "Texted Jeff"})
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert (body["player_profile_id"], body["player_name"], body["date"], body["status"]) == (
        1,
        "Gregg Colburn",
        day,
        "signed_up",
    )
    assert body["notes"] == "Texted Jeff"
    assert sent == [(body["id"], "gregg@example.com", "Gregg Colburn", day)]
    with sessions() as db:
        assert db.query(DailySignup).filter_by(date=day, player_profile_id=1).count() == 1


def test_today_is_allowed(env):
    client, _, _ = env
    assert client.post("/signups/admin", json={"date": upcoming(0), "player_profile_id": 4}).status_code == 200


def test_duplicate_is_400(env):
    client, _, _ = env
    day = upcoming()
    client.post("/signups/admin", json={"date": day, "player_profile_id": 1})
    resp = client.post("/signups/admin", json={"date": day, "player_profile_id": 1})
    assert resp.status_code == 400
    assert "already signed up" in resp.json()["detail"]


def test_past_date_is_400(env):
    client, _, _ = env
    resp = client.post("/signups/admin", json={"date": upcoming(-1), "player_profile_id": 1})
    assert resp.status_code == 400
    assert "today or a future date" in resp.json()["detail"]


@pytest.mark.parametrize("pid", [2, 3, 999])
def test_unlinked_inactive_or_missing_profile_is_400(env, pid):
    client, sessions, _ = env
    resp = client.post("/signups/admin", json={"date": upcoming(), "player_profile_id": pid})
    assert resp.status_code == 400
    with sessions() as db:
        assert db.query(DailySignup).count() == 0


def test_non_admin_is_403(env):
    client, _, _ = env
    app.dependency_overrides[get_current_auth0_user] = lambda: {"sub": "auth0|x", "email": "player@example.com"}
    assert client.get("/signups/admin/players").status_code == 403
    assert client.post("/signups/admin", json={"date": upcoming(), "player_profile_id": 1}).status_code == 403

"""PUT /players/me/name: a golfer named with their email sets their real name once."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.models import PendingLegacyPlayer, PlayerProfile
from app.services.auth_service import get_current_auth0_user

CLAIMS = {
    "sub": "auth0|casey",
    "email": "casey@example.com",
    "email_verified": True,
    "name": "casey@example.com",
}


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
                    name="casey@example.com",
                    email="casey@example.com",
                    preferences={"auth0_id": "auth0|casey"},
                    created_at="2026-11-01",
                ),
                PlayerProfile(id=2, name="Taken Name", created_at="2025-01-01"),
                PendingLegacyPlayer(
                    id=10,
                    name="casey@example.com",
                    email="casey@example.com",
                    player_profile_id=1,
                    status="pending",
                    created_at="2026-11-01",
                ),
                PendingLegacyPlayer(
                    id=11,
                    name="someone@example.com",
                    player_profile_id=2,
                    status="pending",
                    created_at="2026-11-01",
                ),
            ]
        )
        db.commit()

    def database():
        with sessions() as db:
            yield db

    claims = dict(CLAIMS)
    app.dependency_overrides[get_db] = database
    app.dependency_overrides[get_current_auth0_user] = lambda: claims
    yield TestClient(app), sessions
    app.dependency_overrides.pop(get_db, None)
    app.dependency_overrides.pop(get_current_auth0_user, None)
    engine.dispose()


def put_name(client, first, last):
    return client.put("/players/me/name", json={"first_name": first, "last_name": last})


def test_sets_name_and_renames_own_pending_signup(env):
    client, sessions = env
    resp = put_name(client, "  Casey ", " McFarland  ")
    assert resp.status_code == 200, resp.text
    assert resp.json()["name"] == "Casey McFarland"
    with sessions() as db:
        assert db.get(PlayerProfile, 1).name == "Casey McFarland"
        assert db.get(PendingLegacyPlayer, 10).name == "Casey McFarland"
        # Another golfer's pending row is untouched.
        assert db.get(PendingLegacyPlayer, 11).name == "someone@example.com"


def test_name_can_only_be_set_once(env):
    client, _ = env
    assert put_name(client, "Casey", "McFarland").status_code == 200
    resp = put_name(client, "Someone", "Else")
    assert resp.status_code == 409
    assert "already set" in resp.json()["detail"]


@pytest.mark.parametrize(
    ("first", "last"),
    [("", "McFarland"), ("Casey", "   "), ("casey@example.com", "x"), ("Casey", "x" * 51)],
)
def test_rejects_blank_email_or_long_parts(env, first, last):
    client, sessions = env
    assert put_name(client, first, last).status_code == 400
    with sessions() as db:
        assert db.get(PlayerProfile, 1).name == "casey@example.com"


def test_rejects_name_used_by_another_profile(env):
    client, sessions = env
    resp = put_name(client, "taken", "name")
    assert resp.status_code == 409
    assert "Find my player history" in resp.json()["detail"]
    with sessions() as db:
        assert db.get(PlayerProfile, 1).name == "casey@example.com"
        assert db.get(PendingLegacyPlayer, 10).name == "casey@example.com"

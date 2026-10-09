"""In-app admin grants: list, grant, revoke, and their guard rails."""

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
def grants(monkeypatch):
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    sessions = sessionmaker(bind=engine)
    with sessions() as db:
        db.add_all(
            [
                PlayerProfile(
                    id=1,
                    name="Env Admin",
                    email="env@example.com",
                    preferences={"auth0_id": "auth0|env"},
                    created_at="2026-01-01",
                ),
                PlayerProfile(
                    id=2,
                    name="Linked",
                    email="linked@example.com",
                    preferences={"auth0_id": "auth0|linked"},
                    created_at="2026-01-01",
                ),
                PlayerProfile(id=3, name="Unlinked", created_at="2026-01-01"),
            ]
        )
        db.commit()

    def database():
        with sessions() as db:
            yield db

    monkeypatch.setenv("SUPER_ADMIN_EMAILS", "env@example.com")
    app.dependency_overrides[get_db] = database
    app.dependency_overrides[get_current_auth0_user] = lambda: {"sub": "auth0|env", "email": "env@example.com"}
    yield TestClient(app), sessions
    app.dependency_overrides.pop(get_db, None)
    app.dependency_overrides.pop(get_current_auth0_user, None)
    engine.dispose()


def test_list_shows_env_admins_and_flagged_profiles(grants):
    client, _ = grants
    client.post("/players/admin/admins/2")
    body = client.get("/players/admin/admins").json()
    assert body["env_admins"] == ["env@example.com"]
    assert [row["id"] for row in body["profile_admins"]] == [2]


def test_grant_records_who_and_when_and_is_idempotent(grants):
    client, _ = grants
    first = client.post("/players/admin/admins/2")
    assert first.status_code == 200, first.text
    assert first.json()["is_admin"] is True
    assert first.json()["admin_granted_by"] == "env@example.com"
    assert first.json()["admin_granted_at"]
    again = client.post("/players/admin/admins/2")
    assert again.status_code == 200
    assert again.json()["admin_granted_at"] == first.json()["admin_granted_at"]


def test_grant_rejects_profile_without_login(grants):
    client, _ = grants
    resp = client.post("/players/admin/admins/3")
    assert resp.status_code == 400
    assert "sign in" in resp.json()["detail"].lower()


def test_grant_unknown_profile_is_404(grants):
    client, _ = grants
    assert client.post("/players/admin/admins/999").status_code == 404


def test_revoke_clears_flag_and_history(grants):
    client, _ = grants
    client.post("/players/admin/admins/2")
    resp = client.delete("/players/admin/admins/2")
    assert resp.status_code == 200
    assert (resp.json()["is_admin"], resp.json()["admin_granted_by"]) == (False, None)


def test_env_admin_cannot_be_revoked(grants):
    client, _ = grants
    resp = client.delete("/players/admin/admins/1")
    assert resp.status_code == 400
    assert "deployment config" in resp.json()["detail"]


def test_non_env_admin_cannot_revoke_self(grants):
    client, _ = grants
    client.post("/players/admin/admins/2")
    app.dependency_overrides[get_current_auth0_user] = lambda: {"sub": "auth0|linked", "email": "linked@example.com"}
    resp = client.delete("/players/admin/admins/2")
    assert resp.status_code == 400
    assert "another admin" in resp.json()["detail"]


def test_flagged_admin_can_grant_others(grants):
    client, sessions = grants
    client.post("/players/admin/admins/2")
    with sessions() as db:
        db.add(
            PlayerProfile(
                id=4,
                name="Third",
                email="third@example.com",
                preferences={"auth0_id": "auth0|third"},
                created_at="2026-01-01",
            )
        )
        db.commit()
    app.dependency_overrides[get_current_auth0_user] = lambda: {"sub": "auth0|linked", "email": "linked@example.com"}
    assert client.post("/players/admin/admins/4").json()["admin_granted_by"] == "linked@example.com"


def test_non_admin_is_forbidden(grants):
    client, _ = grants
    app.dependency_overrides[get_current_auth0_user] = lambda: {"sub": "auth0|linked", "email": "linked@example.com"}
    assert client.get("/players/admin/admins").status_code == 403


def test_retiring_a_profile_clears_admin(grants):
    client, sessions = grants
    client.post("/players/admin/admins/2")
    assert client.delete("/players/2").status_code == 200
    with sessions() as db:
        player = db.get(PlayerProfile, 2)
        assert (player.admin_granted, player.admin_granted_by, player.admin_granted_at) == (0, None, None)


def test_grant_rejects_login_shared_by_several_profiles(grants):
    client, sessions = grants
    with sessions() as db:
        db.add(
            PlayerProfile(
                id=5,
                name="Dupe",
                email="dupe@example.com",
                preferences={"auth0_id": "auth0|linked"},
                created_at="2026-01-01",
            )
        )
        db.commit()
    resp = client.post("/players/admin/admins/2")
    assert resp.status_code == 400
    assert resp.json()["detail"] == (
        "This login matches multiple profiles. Fix it in Account links before making it an admin."
    )
    with sessions() as db:
        assert not db.get(PlayerProfile, 2).admin_granted


def test_non_admin_403_uses_admin_wording_and_is_not_logged_as_db_error(grants, caplog):
    client, _ = grants
    app.dependency_overrides[get_current_auth0_user] = lambda: {"sub": "auth0|linked", "email": "linked@example.com"}
    app.dependency_overrides.pop(get_db, None)  # exercise the real get_db
    with caplog.at_level("ERROR"):
        resp = client.get("/players/admin/admins")
    assert resp.status_code == 403
    assert resp.json()["detail"] == "Admin access required"
    assert not [r for r in caplog.records if "Database error" in r.getMessage()]

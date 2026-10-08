"""Admin account linking against synthetic profiles, never real Auth0 accounts."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.models import LegacyRosterPlayer, LegacyRound, PlayerProfile
from app.services.auth_service import get_current_auth0_user


@pytest.fixture
def accounts(monkeypatch):
    monkeypatch.setattr("app.services.auth_service._send_welcome_email", lambda *args: None)
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    sessions = sessionmaker(bind=engine)
    with sessions() as db:
        db.add_all(
            [
                LegacyRosterPlayer(name="Kevin Gent", source="seed", added_at="2026-01-01"),
                LegacyRosterPlayer(name="Casey McFarland", source="seed", added_at="2026-01-01"),
                PlayerProfile(
                    id=1,
                    name="kevin@example.com",
                    email="kevin@example.com",
                    preferences={"auth0_id": "auth0|test-kevin", "display_hints": True},
                    created_at="2026-01-01",
                ),
                PlayerProfile(
                    id=2,
                    name="Casey McFarland",
                    email="casey@example.com",
                    legacy_name="Casey McFarland",
                    preferences={"auth0_id": "auth0|test-casey"},
                    created_at="2026-01-01",
                ),
                LegacyRound(
                    member="Kevin Gent",
                    date="2026-10-01",
                    score=10,
                    player_profile_id=1,
                    source="member",
                    status="posted",
                ),
            ]
        )
        db.commit()

    def database():
        with sessions() as db:
            yield db

    monkeypatch.setenv("SUPER_ADMIN_EMAILS", "admin@example.com")
    app.dependency_overrides[get_db] = database
    app.dependency_overrides[get_current_auth0_user] = lambda: {"sub": "auth0|test-admin", "email": "admin@example.com"}
    yield TestClient(app, raise_server_exceptions=True), sessions
    app.dependency_overrides.pop(get_db, None)
    app.dependency_overrides.pop(get_current_auth0_user, None)
    engine.dispose()


def link_payload(**changes):
    return {
        "player_id": 1,
        "legacy_name": "Kevin Gent",
        "email": "kevin@example.com",
        "auth0_id": "auth0|test-kevin",
        "expected_updated_at": None,
        **changes,
    }


def test_search_by_email_and_roster_name_exposes_only_link_fields(accounts):
    client, _ = accounts
    response = client.get("/players/admin/account-links", params={"query": "KEVIN@"})
    assert response.status_code == 200, response.text
    assert response.json()["players"][0]["id"] == 1
    assert "preferences" not in response.json()["players"][0]
    assert (
        client.get("/players/admin/account-links", params={"query": "Casey"}).json()["players"][0]["legacy_name"]
        == "Casey McFarland"
    )
    assert client.get("/players/admin/account-links", params={"query": "%_"}).json()["players"] == []


def test_admin_links_explicit_profile_and_preserves_history_and_preferences(accounts):
    client, sessions = accounts
    response = client.post(
        "/players/admin/relink-auth0", json=link_payload(email=" KEVIN@EXAMPLE.COM ", legacy_name="kevin gent")
    )
    assert response.status_code == 200, response.text
    assert response.json()["name"] == "Kevin Gent"
    with sessions() as db:
        player = db.get(PlayerProfile, 1)
        assert player.legacy_name == player.name == "Kevin Gent"
        assert player.email == "kevin@example.com"
        assert player.preferences == {"auth0_id": "auth0|test-kevin", "display_hints": True}
        assert db.query(LegacyRound).one().player_profile_id == 1
        assert db.query(LegacyRound).one().score == 10
        assert db.query(PlayerProfile).count() == 2


@pytest.mark.parametrize(
    "change",
    [
        {"legacy_name": "Casey McFarland"},
        {"email": "CASEY@example.com"},
        {"auth0_id": "auth0|test-casey"},
    ],
)
def test_conflicting_identity_rejected_without_mutation(accounts, change):
    client, sessions = accounts
    response = client.post("/players/admin/relink-auth0", json=link_payload(**change))
    assert response.status_code == 409, response.text
    with sessions() as db:
        assert db.get(PlayerProfile, 1).legacy_name is None
        assert db.get(PlayerProfile, 1).name == "kevin@example.com"
        assert db.get(PlayerProfile, 2).preferences["auth0_id"] == "auth0|test-casey"


def test_stale_edit_is_rejected(accounts):
    client, _ = accounts
    assert client.post("/players/admin/relink-auth0", json=link_payload()).status_code == 200
    response = client.post("/players/admin/relink-auth0", json=link_payload(auth0_id="google-oauth2|new"))
    assert response.status_code == 409
    assert "changed" in response.json()["detail"].lower()


@pytest.mark.parametrize(
    "change", [{"email": "not-an-email"}, {"auth0_id": "not-a-subject"}, {"legacy_name": "Unknown Golfer"}]
)
def test_invalid_link_rejected(accounts, change):
    client, _ = accounts
    assert client.post("/players/admin/relink-auth0", json=link_payload(**change)).status_code in (400, 422)


def test_non_admin_cannot_search_or_link(accounts):
    client, _ = accounts
    app.dependency_overrides[get_current_auth0_user] = lambda: {"sub": "auth0|test-kevin", "email": "kevin@example.com"}
    assert client.get("/players/admin/account-links", params={"query": "Kevin"}).status_code == 403
    assert client.post("/players/admin/relink-auth0", json=link_payload()).status_code == 403


def test_blank_auth0_keeps_existing_login(accounts):
    client, sessions = accounts
    assert client.post("/players/admin/relink-auth0", json=link_payload(auth0_id=None)).status_code == 200
    with sessions() as db:
        assert db.get(PlayerProfile, 1).preferences["auth0_id"] == "auth0|test-kevin"


def test_email_only_link_resolves_same_profile_on_case_insensitive_login(accounts):
    from app.services.auth_service import AuthService

    client, sessions = accounts
    with sessions() as db:
        player = db.get(PlayerProfile, 1)
        player.preferences = {"display_hints": True}
        db.commit()
    assert client.post("/players/admin/relink-auth0", json=link_payload(auth0_id=None)).status_code == 200
    with sessions() as db:
        player = AuthService.get_or_create_player_profile(
            db,
            {
                "sub": "auth0|new-email-login",
                "email_verified": True,
                "email": "KEVIN@EXAMPLE.COM",
                "name": "kevin@example.com",
            },
        )
        assert player.id == 1
        assert player.name == player.legacy_name == "Kevin Gent"
        assert player.preferences["auth0_id"] == "auth0|new-email-login"
        assert db.query(PlayerProfile).count() == 2


def test_old_login_cannot_silently_replace_an_admin_selected_auth0_link(accounts):
    from fastapi import HTTPException

    from app.services.auth_service import AuthService

    client, sessions = accounts
    assert (
        client.post("/players/admin/relink-auth0", json=link_payload(auth0_id="google-oauth2|new-kevin")).status_code
        == 200
    )
    with sessions() as db:
        with pytest.raises(HTTPException) as error:
            AuthService.get_or_create_player_profile(
                db,
                {
                    "sub": "auth0|test-kevin",
                    "email": "kevin@example.com",
                    "name": "kevin@example.com",
                },
            )
        assert error.value.status_code == 409
        assert db.get(PlayerProfile, 1).preferences["auth0_id"] == "google-oauth2|new-kevin"


def test_ambiguous_case_variants_of_email_do_not_choose_an_arbitrary_profile(accounts):
    from fastapi import HTTPException

    from app.services.auth_service import AuthService

    _, sessions = accounts
    with sessions() as db:
        db.get(PlayerProfile, 1).preferences = {}
        db.add(
            PlayerProfile(
                id=3, name="Other profile", email="KEVIN@EXAMPLE.COM", preferences={}, created_at="2026-01-01"
            )
        )
        db.commit()
        with pytest.raises(HTTPException) as error:
            AuthService.get_or_create_player_profile(
                db,
                {
                    "sub": "auth0|unknown-kevin",
                    "email": "kevin@example.com",
                    "name": "kevin@example.com",
                },
            )
        assert error.value.status_code == 409
        assert not db.get(PlayerProfile, 1).preferences.get("auth0_id")
        assert not db.get(PlayerProfile, 3).preferences.get("auth0_id")


def test_retiring_a_stray_profile_frees_its_login_for_the_original(accounts):
    """The Crowley/McFadden case: a sign-in created a stray profile (#1) holding the
    email + Auth0 ID, while the history lives on an older unlinked profile (#3)."""
    client, sessions = accounts
    with sessions() as db:
        db.add(PlayerProfile(id=3, name="Kevin G", created_at="2025-01-01"))
        db.commit()

    blocked = client.post("/players/admin/relink-auth0", json=link_payload(player_id=3))
    assert blocked.status_code == 409, blocked.text

    assert client.delete("/players/1").status_code == 200
    assert client.get("/players/admin/account-links", params={"query": "kevin@"}).json()["players"] == []

    linked = client.post("/players/admin/relink-auth0", json=link_payload(player_id=3))
    assert linked.status_code == 200, linked.text
    assert linked.json()["auth0_id"] == "auth0|test-kevin"


def _flag_admin(sessions):
    with sessions() as db:
        player = db.get(PlayerProfile, 1)
        player.admin_granted = 1
        player.admin_granted_by = "admin@example.com"
        player.admin_granted_at = "2026-10-01T00:00:00"
        db.commit()


def test_relink_to_different_login_clears_admin_flag(accounts):
    client, sessions = accounts
    _flag_admin(sessions)
    assert client.post("/players/admin/relink-auth0", json=link_payload(auth0_id="auth0|new-kevin")).status_code == 200
    with sessions() as db:
        player = db.get(PlayerProfile, 1)
        assert (player.admin_granted, player.admin_granted_by, player.admin_granted_at) == (0, None, None)


def test_relink_keeping_same_login_keeps_admin_flag(accounts):
    client, sessions = accounts
    _flag_admin(sessions)
    assert client.post("/players/admin/relink-auth0", json=link_payload()).status_code == 200
    with sessions() as db:
        player = db.get(PlayerProfile, 1)
        assert player.admin_granted == 1
        assert player.admin_granted_by == "admin@example.com"

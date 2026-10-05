"""First-login identity boundaries and existing roster recovery."""

from unittest.mock import Mock, patch

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.models import Base, LegacyRosterPlayer, PlayerProfile
from app.services.auth_service import AuthService
from app.services.legacy_player_service import link_profile_to_canonical_name


@pytest.fixture
def db():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        session.add(LegacyRosterPlayer(name="Chris Hill", source="test", added_at="2026-01-01"))
        session.commit()
        with (
            patch("app.services.auth_service._send_welcome_email"),
            patch("app.services.auth_service._notify_admins_of_new_player"),
        ):
            yield session
    engine.dispose()


def seed(db, **values):
    player = PlayerProfile(name="Chris Hill", handicap=7.5, preferences={"display_hints": False}, **values)
    db.add(player)
    db.commit()
    return player


def identity(**values):
    return {"sub": "auth0|new", "email": "chris@example.com", "email_verified": True, "name": "Chris Hill", **values}


def test_verified_email_reuses_roster_and_preserves_history_identity(db):
    roster = seed(db, email="Chris@Example.com")
    player = AuthService.get_or_create_player_profile(db, identity(email=" CHRIS@example.com "))
    assert player.id == roster.id
    assert player.legacy_name == "Chris Hill"
    assert player.handicap == 7.5
    assert player.preferences == {"display_hints": False, "auth0_id": "auth0|new"}
    assert db.query(PlayerProfile).count() == 1


@pytest.mark.parametrize("verified", [None, False, "true"])
def test_unverified_email_cannot_claim_existing_profile(db, verified):
    roster = seed(db, email="chris@example.com")
    with pytest.raises(HTTPException) as error:
        AuthService.get_or_create_player_profile(db, identity(email_verified=verified))
    assert error.value.status_code == 403
    assert not roster.preferences.get("auth0_id")


def test_matching_name_alone_does_not_claim_or_crash_on_seed(db):
    roster = seed(db)
    player = AuthService.get_or_create_player_profile(db, identity())
    assert player.id != roster.id
    assert player.legacy_name is None
    assert player.preferences["auth0_id"] == "auth0|new"
    assert not roster.preferences.get("auth0_id")
    assert link_profile_to_canonical_name(db, player.id, "Chris Hill")["status"] == "claimed"
    assert AuthService.get_or_create_player_profile(db, identity()).id == player.id


def test_userinfo_subject_must_match_verified_token():
    response = Mock(status_code=200)
    response.json.return_value = identity(sub="auth0|someone-else")
    with (
        patch("app.services.auth_service.AUTH0_DOMAIN", "example.auth0.com"),
        patch("app.services.auth_service._httpx.get", return_value=response),
        pytest.raises(HTTPException) as error,
    ):
        AuthService.enrich_user_from_userinfo({"sub": "auth0|new"}, "test-token")
    assert error.value.status_code == 401


def test_userinfo_preserves_verified_email_claim():
    response = Mock(status_code=200)
    response.json.return_value = identity()
    with (
        patch("app.services.auth_service.AUTH0_DOMAIN", "example.auth0.com"),
        patch("app.services.auth_service._httpx.get", return_value=response),
    ):
        enriched = AuthService.enrich_user_from_userinfo({"sub": "auth0|new"}, "test-token")
    assert enriched["email_verified"] is True


def test_userinfo_cannot_verify_a_different_token_email():
    response = Mock(status_code=200)
    response.json.return_value = identity(email="different@example.com")
    with (
        patch("app.services.auth_service.AUTH0_DOMAIN", "example.auth0.com"),
        patch("app.services.auth_service._httpx.get", return_value=response),
    ):
        enriched = AuthService.enrich_user_from_userinfo(identity(email_verified=None), "test-token")
    assert enriched.get("email_verified") is not True


def test_linked_subject_keeps_profile_without_email_claim(db):
    roster = seed(db, email="chris@example.com", legacy_name="Chris Hill")
    roster.preferences = {"auth0_id": "auth0|new"}
    db.commit()
    assert AuthService.get_or_create_player_profile(db, {"sub": "auth0|new"}).id == roster.id


def test_verified_email_uses_existing_roster_name_not_login_display_name(db):
    roster = seed(db, email="chris@example.com")
    db.add(LegacyRosterPlayer(name="Different Golfer", source="test", added_at="2026-01-01"))
    db.commit()
    player = AuthService.get_or_create_player_profile(db, identity(name="Different Golfer"))
    assert player.id == roster.id
    assert player.legacy_name == "Chris Hill"

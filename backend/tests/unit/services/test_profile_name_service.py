"""New golfers are not named with their email when Auth0 has a better name."""

from unittest.mock import Mock

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.models import Base, PendingLegacyPlayer
from app.services import auth_service as auth_module
from app.services import legacy_player_service as svc
from app.services.auth_service import AuthService
from app.services.profile_name_service import display_name_from_claims


@pytest.mark.parametrize(
    ("claims", "expected"),
    [
        ({"name": "Casey McFarland", "given_name": "C", "family_name": "M"}, "Casey McFarland"),
        ({"name": "casey@example.com", "given_name": "Casey", "family_name": "McFarland"}, "Casey McFarland"),
        ({"given_name": "Casey"}, "Casey"),
        ({"name": "casey@example.com", "nickname": "casey"}, "casey@example.com"),
        ({}, "casey"),
    ],
)
def test_display_name_from_claims(claims, expected):
    assert display_name_from_claims(claims, "casey@example.com") == expected


def test_display_name_without_any_claim_or_email():
    assert display_name_from_claims({}, None) == "Unknown Player"


@pytest.fixture
def db(monkeypatch):
    monkeypatch.setattr(auth_module, "_notify_admins_of_new_player", Mock())
    monkeypatch.setattr(auth_module, "_send_welcome_email", lambda *args: None)
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    svc.add_legacy_player("Anchor Player", db=session)
    yield session
    session.close()
    engine.dispose()


def test_new_profile_uses_given_and_family_name_over_email_name(db):
    player = AuthService.get_or_create_player_profile(
        db,
        {
            "sub": "auth0|casey",
            "email": "casey@example.com",
            "name": "casey@example.com",
            "given_name": "Casey",
            "family_name": "McFarland",
        },
    )
    assert player.name == "Casey McFarland"
    pending = db.query(PendingLegacyPlayer).one()
    assert pending.name == "Casey McFarland"


def test_new_profile_with_email_name_keeps_email_so_onboarding_asks(db):
    player = AuthService.get_or_create_player_profile(
        db, {"sub": "auth0|casey", "email": "casey@example.com", "name": "casey@example.com"}
    )
    assert player.name == "casey@example.com"

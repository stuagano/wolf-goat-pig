"""Tests for new-player capture + notify on first Auth0 login.

When a brand-new golfer signs up with no canonical roster match, the profile
is still created (login always works), they are captured into the pending
queue, and admins are notified. A returning player who matches the canonical
roster is linked and NOT captured.
"""

from unittest.mock import Mock

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models import Base, PendingLegacyPlayer, PlayerProfile
from app.services import auth_service as auth_module
from app.services import legacy_player_service as svc
from app.services.auth_service import AuthService

TEST_DATABASE_URL = "sqlite:///./test_auth_capture.db"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture
def db():
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def notify_spy(monkeypatch):
    """Replace the (threaded, external) admin notify with a synchronous spy."""
    spy = Mock()
    monkeypatch.setattr(auth_module, "_notify_admins_of_new_player", spy)
    return spy


def test_unmatched_new_player_is_captured_and_notifies(db, notify_spy):
    # Anchor row → table non-empty → no JSON-seed fallback during lookups.
    svc.add_legacy_player("Anchor Player", db=db)

    auth0_user = {
        "sub": "auth0|brandnew",
        "email": "brandnew@example.com",
        "name": "Brand New Golfer",
        "picture": None,
    }
    player = AuthService.get_or_create_player_profile(db, auth0_user)

    # Account is created regardless (login always works).
    assert player.id is not None
    assert player.legacy_name is None

    # Captured into the pending queue.
    pending = db.query(PendingLegacyPlayer).filter(PendingLegacyPlayer.name == "Brand New Golfer").first()
    assert pending is not None
    assert pending.email == "brandnew@example.com"
    assert pending.player_profile_id == player.id

    notify_spy.assert_called_once()


def test_matched_returning_player_is_not_captured(db, notify_spy):
    svc.add_legacy_player("Returning Golfer", db=db)

    auth0_user = {
        "sub": "auth0|returning",
        "email": "returning@example.com",
        "name": "Returning Golfer",
        "picture": None,
    }
    player = AuthService.get_or_create_player_profile(db, auth0_user)

    assert player.legacy_name == "Returning Golfer"
    assert db.query(PendingLegacyPlayer).count() == 0
    notify_spy.assert_not_called()


def test_exact_name_already_owned_by_another_profile_is_not_auto_linked(db, notify_spy):
    svc.add_legacy_player("Shared Name", db=db)
    owner = PlayerProfile(
        name="Owner Account",
        legacy_name="Shared Name",
        email="owner@example.com",
        preferences={"auth0_id": "auth0|owner"},
    )
    db.add(owner)
    db.commit()

    claimant = AuthService.get_or_create_player_profile(
        db,
        {
            "sub": "auth0|claimant",
            "email": "claimant@example.com",
            "name": "Shared Name",
            "picture": None,
        },
    )

    assert claimant.id != owner.id
    assert claimant.legacy_name is None
    assert db.query(PendingLegacyPlayer).count() == 0
    notify_spy.assert_not_called()


def test_fuzzy_match_is_not_auto_linked(db, notify_spy):
    """A near-but-not-exact name is a GUESS: it must never be written to
    legacy_name automatically (issue #322). It is surfaced as a suggestion in
    onboarding instead, so we also don't add them to the pending roster yet."""
    svc.add_legacy_player("Jonathan Smith", db=db)

    auth0_user = {
        "sub": "auth0|fuzzy",
        "email": "jonathon@example.com",
        "name": "Jonathon Smith",  # one letter off — fuzzy match at cutoff 0.6
        "picture": None,
    }
    player = AuthService.get_or_create_player_profile(db, auth0_user)

    # NOT auto-linked to the near-duplicate roster name.
    assert player.legacy_name is None
    # A plausible suggestion exists → don't capture as a brand-new pending
    # player; onboarding will surface it for the user to accept/reject.
    assert db.query(PendingLegacyPlayer).count() == 0
    notify_spy.assert_not_called()


def test_unrelated_name_is_not_linked_and_is_captured(db, notify_spy):
    """An unrelated name never links to an existing golfer, and (no suggestion)
    is captured as a brand-new pending player (issues #322/#321)."""
    svc.add_legacy_player("Jonathan Smith", db=db)

    auth0_user = {
        "sub": "auth0|unrelated",
        "email": "zzz@example.com",
        "name": "Zebediah Xylophone",  # nothing like any roster name
        "picture": None,
    }
    player = AuthService.get_or_create_player_profile(db, auth0_user)

    assert player.legacy_name is None
    pending = db.query(PendingLegacyPlayer).filter(PendingLegacyPlayer.name == "Zebediah Xylophone").first()
    assert pending is not None
    notify_spy.assert_called_once()


def test_existing_account_relogin_does_not_recapture(db, notify_spy):
    svc.add_legacy_player("Anchor Player", db=db)
    auth0_user = {
        "sub": "auth0|brandnew",
        "email": "brandnew@example.com",
        "name": "Brand New Golfer",
        "picture": None,
    }
    AuthService.get_or_create_player_profile(db, auth0_user)
    notify_spy.reset_mock()

    # Second login for the same email must not capture or notify again.
    AuthService.get_or_create_player_profile(db, auth0_user)
    assert db.query(PendingLegacyPlayer).filter(PendingLegacyPlayer.name == "Brand New Golfer").count() == 1
    assert db.query(PlayerProfile).filter(PlayerProfile.email == "brandnew@example.com").count() == 1
    notify_spy.assert_not_called()


def test_existing_unlinked_account_retries_exact_match_on_relogin(db, notify_spy):
    svc.add_legacy_player("Anchor Player", db=db)
    auth0_user = {
        "sub": "auth0|later-match",
        "email": "later@example.com",
        "name": "Later Match",
        "picture": None,
    }
    player = AuthService.get_or_create_player_profile(db, auth0_user)
    assert player.legacy_name is None

    # The golfer is added to the canonical tee-sheet roster after first login.
    svc.add_legacy_player("Later Match", db=db)
    notify_spy.reset_mock()

    relinked = AuthService.get_or_create_player_profile(db, auth0_user)

    assert relinked.id == player.id
    assert relinked.legacy_name == "Later Match"
    assert db.query(PlayerProfile).filter(PlayerProfile.email == "later@example.com").count() == 1
    notify_spy.assert_not_called()


def test_existing_unlinked_account_never_auto_links_fuzzy_match(db, notify_spy):
    svc.add_legacy_player("Anchor Player", db=db)
    auth0_user = {
        "sub": "auth0|later-fuzzy",
        "email": "jonathon@example.com",
        "name": "Jonathon Smith",
        "picture": None,
    }
    player = AuthService.get_or_create_player_profile(db, auth0_user)
    assert player.legacy_name is None

    svc.add_legacy_player("Jonathan Smith", db=db)
    relogged = AuthService.get_or_create_player_profile(db, auth0_user)

    assert relogged.legacy_name is None

"""Tests for the welcome email sent on first-login profile creation.

When a brand-new account is auto-created on first Auth0 login, the player gets
a one-time welcome email. It fires ONLY on the new-profile branch (never on a
returning login), and it is strictly best-effort: any failure is captured to
Sentry but never blocks or breaks login.
"""

from unittest.mock import Mock

import pytest
import sentry_sdk
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models import Base
from app.services import auth_service as auth_module
from app.services import legacy_player_service as svc
from app.services.auth_service import AuthService

TEST_DATABASE_URL = "sqlite:///./test_auth_welcome.db"
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
def welcome_spy(monkeypatch):
    """Replace the (threaded, external) welcome send with a synchronous spy."""
    spy = Mock()
    monkeypatch.setattr(auth_module, "_send_welcome_email", spy)
    return spy


@pytest.fixture
def notify_spy(monkeypatch):
    """Silence the threaded admin-notify so it can't fire real emails/threads."""
    spy = Mock()
    monkeypatch.setattr(auth_module, "_notify_admins_of_new_player", spy)
    return spy


def test_welcome_email_sent_once_for_new_profile(db, welcome_spy):
    # Canonical match present → isolates the welcome path from pending-capture.
    svc.add_legacy_player("Brand New Golfer", db=db)

    auth0_user = {
        "sub": "auth0|brandnew",
        "email": "brandnew@example.com",
        "name": "Brand New Golfer",
        "picture": None,
    }
    player = AuthService.get_or_create_player_profile(db, auth0_user)

    assert player.id is not None
    welcome_spy.assert_called_once_with("Brand New Golfer", "brandnew@example.com")


def test_welcome_email_not_sent_for_returning_player(db, welcome_spy):
    svc.add_legacy_player("Returning Golfer", db=db)
    auth0_user = {
        "sub": "auth0|returning",
        "email": "returning@example.com",
        "name": "Returning Golfer",
        "picture": None,
    }
    # First login creates the profile (welcome fires once).
    AuthService.get_or_create_player_profile(db, auth0_user)
    welcome_spy.reset_mock()

    # Second login returns the existing profile — welcome must NOT fire again.
    player = AuthService.get_or_create_player_profile(db, auth0_user)
    assert player.email == "returning@example.com"
    welcome_spy.assert_not_called()


def test_welcome_email_failure_is_captured_and_login_survives(db, monkeypatch):
    """When the email send raises, it is reported to Sentry and login still works."""
    svc.add_legacy_player("Brand New Golfer", db=db)

    # Run delivery synchronously (no daemon thread) so we can assert on it,
    # exercising the real dispatch -> deliver -> send path.
    monkeypatch.setattr(auth_module, "_send_welcome_email", auth_module._deliver_welcome_email)

    boom_svc = Mock()
    boom_svc.is_configured.return_value = True
    boom_svc.send_welcome_email.side_effect = RuntimeError("resend down")
    monkeypatch.setattr("app.services.email_service.get_email_service", lambda: boom_svc)

    captured: list[BaseException] = []
    monkeypatch.setattr(sentry_sdk, "capture_exception", lambda e: captured.append(e))

    auth0_user = {
        "sub": "auth0|brandnew",
        "email": "brandnew@example.com",
        "name": "Brand New Golfer",
        "picture": None,
    }
    # Login must still succeed and return the persisted profile.
    player = AuthService.get_or_create_player_profile(db, auth0_user)

    assert player.id is not None
    assert player.email == "brandnew@example.com"
    boom_svc.send_welcome_email.assert_called_once()
    assert len(captured) == 1
    assert isinstance(captured[0], RuntimeError)

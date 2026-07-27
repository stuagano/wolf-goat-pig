"""Tests for the signup confirmation email sent from POST /signups (issue #317).

Covers the delivery helper directly: recipient comes from the authenticated
profile (passed in, never client input), idempotency via
confirmation_email_sent_at, preference opt-out, and observable soft failure.
"""

from unittest.mock import Mock

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models import Base, DailySignup, EmailPreferences
from app.observability import report as report_mod
from app.routers import signups as signups_module
from app.utils.time import utc_now

engine = create_engine("sqlite:///./test_signup_confirm.db", connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture
def db(monkeypatch):
    Base.metadata.create_all(bind=engine)
    monkeypatch.setattr(signups_module.database, "SessionLocal", TestingSessionLocal)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


def _make_signup(db, **kwargs) -> DailySignup:
    signup = DailySignup(
        date="2026-08-02",
        player_profile_id=1,
        player_name="Brett Saks",
        signup_time=utc_now().isoformat(),
        status="signed_up",
        created_at=utc_now().isoformat(),
        updated_at=utc_now().isoformat(),
        **kwargs,
    )
    db.add(signup)
    db.commit()
    db.refresh(signup)
    return signup


def _reread(signup_id: int) -> DailySignup:
    return TestingSessionLocal().query(DailySignup).filter(DailySignup.id == signup_id).first()


def test_confirmation_sent_and_marked(db, monkeypatch):
    signup = _make_signup(db)
    svc = Mock()
    svc.is_configured.return_value = True
    svc.send_signup_confirmation.return_value = True
    monkeypatch.setattr("app.services.email_service.get_email_service", lambda: svc)

    signups_module._deliver_signup_confirmation(signup.id, "brett@example.com", "Brett Saks", "2026-08-02")

    svc.send_signup_confirmation.assert_called_once_with("brett@example.com", "Brett Saks", "2026-08-02")
    assert _reread(signup.id).confirmation_email_sent_at is not None


def test_confirmation_not_resent_when_already_sent(db, monkeypatch):
    signup = _make_signup(db, confirmation_email_sent_at=utc_now().isoformat())
    svc = Mock()
    svc.is_configured.return_value = True
    monkeypatch.setattr("app.services.email_service.get_email_service", lambda: svc)

    signups_module._deliver_signup_confirmation(signup.id, "brett@example.com", "Brett Saks", "2026-08-02")

    svc.send_signup_confirmation.assert_not_called()


def test_confirmation_respects_preference_opt_out(db, monkeypatch):
    signup = _make_signup(db)
    db.add(
        EmailPreferences(
            player_profile_id=1,
            signup_confirmations_enabled=False,
            created_at=utc_now().isoformat(),
            updated_at=utc_now().isoformat(),
        )
    )
    db.commit()
    svc = Mock()
    svc.is_configured.return_value = True
    monkeypatch.setattr("app.services.email_service.get_email_service", lambda: svc)

    signups_module._deliver_signup_confirmation(signup.id, "brett@example.com", "Brett Saks", "2026-08-02")

    svc.send_signup_confirmation.assert_not_called()


def test_confirmation_soft_failure_is_observable_and_not_marked(db, monkeypatch):
    signup = _make_signup(db)
    svc = Mock()
    svc.is_configured.return_value = True
    svc.send_signup_confirmation.return_value = False
    monkeypatch.setattr("app.services.email_service.get_email_service", lambda: svc)

    messages: list[str] = []
    monkeypatch.setattr(report_mod, "report_message", lambda m, *a, **k: messages.append(m))
    monkeypatch.setattr("app.routers.signups.report_message", lambda m, *a, **k: messages.append(m))

    signups_module._deliver_signup_confirmation(signup.id, "brett@example.com", "Brett Saks", "2026-08-02")

    assert _reread(signup.id).confirmation_email_sent_at is None
    assert any("rejected" in m for m in messages)


def test_no_recipient_is_a_noop(db, monkeypatch):
    signup = _make_signup(db)
    svc = Mock()
    monkeypatch.setattr("app.services.email_service.get_email_service", lambda: svc)

    signups_module._send_signup_confirmation(signup.id, None, "Brett Saks", "2026-08-02")

    svc.send_signup_confirmation.assert_not_called()

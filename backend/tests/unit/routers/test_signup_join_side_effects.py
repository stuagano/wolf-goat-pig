"""Joining a day fires its side effects once, whichever path records it (#450).

The tee-sheet mirror used to call the email service directly, skipping the
confirmation_email_sent_at stamp, so every repeat mirror of the same signup
re-sent the confirmation.
"""

from unittest.mock import Mock

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app import database
from app.models import Base, PlayerProfile
from app.routers import signups as signups_module
from app.routers import tee_sheet as tee_sheet_module

engine = create_engine("sqlite:///./test_signup_join.db", connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture
def env(monkeypatch):
    Base.metadata.create_all(bind=engine)
    monkeypatch.setattr(database, "SessionLocal", TestingSessionLocal)
    # Deliver synchronously so the test can count sends.
    monkeypatch.setattr(
        signups_module,
        "_send_signup_confirmation",
        lambda *args: args[1] and signups_module._deliver_signup_confirmation(*args),
    )
    alerts = Mock()
    monkeypatch.setattr(signups_module, "send_same_day_signup_notifications", alerts)
    svc = Mock()
    svc.is_configured.return_value = True
    svc.send_signup_confirmation.return_value = True
    monkeypatch.setattr("app.services.email_service.get_email_service", lambda: svc)

    db = TestingSessionLocal()
    db.add(PlayerProfile(name="Brett Saks", legacy_name="Brett Saks", email="brett@example.com"))
    db.commit()
    db.close()
    try:
        yield svc, alerts
    finally:
        Base.metadata.drop_all(bind=engine)


def test_repeat_tee_sheet_mirror_sends_one_confirmation(env):
    svc, alerts = env

    tee_sheet_module._mirror_signup_to_db("Brett Saks", "2026-11-01")
    tee_sheet_module._mirror_signup_to_db("Brett Saks", "2026-11-01")

    svc.send_signup_confirmation.assert_called_once_with("brett@example.com", "Brett Saks", "2026-11-01")
    alerts.assert_called_once()

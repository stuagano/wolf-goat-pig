"""Tests for the email-preferences endpoints' same-day signup opt-in.

Same-day signup alerts ("someone signed up for today's game") are a separate,
default-off opt-in from signup_confirmations_enabled (your own signup receipt),
so these cover the default, the round-trip, and the independence of the two.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

from app.database import get_db
from app.main import app
from app.models import Base, EmailPreferences, PlayerProfile, SameDaySignupNotification
from app.schemas.signups import EmailPreferencesCreate, EmailPreferencesResponse, EmailPreferencesUpdate
from app.services.auth_service import get_current_user
from app.utils.time import utc_now

_engine = create_engine("sqlite:///./test_email_preferences.db", connect_args={"check_same_thread": False})
_Session = sessionmaker(autocommit=False, autoflush=False, bind=_engine)

client = TestClient(app)


def _make_user() -> PlayerProfile:
    return PlayerProfile(
        id=1,
        name="Test Golfer",
        email="golfer@example.com",
        handicap=18.0,
        is_active=1,
        is_ai=0,
        created_at="2026-01-01T00:00:00",
    )


@pytest.fixture
def db():
    Base.metadata.create_all(bind=_engine)

    def _get_db():
        session = _Session()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = _get_db
    app.dependency_overrides[get_current_user] = _make_user
    session = _Session()
    try:
        yield session
    finally:
        session.close()
        app.dependency_overrides.pop(get_db, None)
        app.dependency_overrides.pop(get_current_user, None)
        Base.metadata.drop_all(bind=_engine)


def test_same_day_alerts_default_off_for_new_preferences(db):
    resp = client.get("/players/me/email-preferences")

    assert resp.status_code == 200
    assert resp.json()["same_day_signups_enabled"] is False


def test_opting_in_is_persisted_and_returned(db):
    resp = client.put("/players/me/email-preferences", json={"same_day_signups_enabled": True})

    assert resp.status_code == 200
    assert resp.json()["same_day_signups_enabled"] is True
    assert client.get("/players/me/email-preferences").json()["same_day_signups_enabled"] is True

    stored = db.query(EmailPreferences).filter(EmailPreferences.player_profile_id == 1).first()
    # Stored as an int for SQLite, like every other flag on this table.
    assert stored.same_day_signups_enabled == 1


def test_opting_out_again_is_persisted(db):
    client.put("/players/me/email-preferences", json={"same_day_signups_enabled": True})

    resp = client.put("/players/me/email-preferences", json={"same_day_signups_enabled": False})

    assert resp.status_code == 200
    assert resp.json()["same_day_signups_enabled"] is False


def test_same_day_opt_in_leaves_own_confirmation_preference_untouched(db):
    resp = client.put("/players/me/email-preferences", json={"same_day_signups_enabled": True})

    assert resp.json()["signup_confirmations_enabled"] is True

    # And the reverse: changing confirmations must not enroll anyone in alerts.
    other = client.put("/players/me/email-preferences", json={"signup_confirmations_enabled": False})
    assert other.json()["signup_confirmations_enabled"] is False
    assert other.json()["same_day_signups_enabled"] is True


def test_schema_defaults_preserve_opt_in_and_legacy_response_compatibility():
    assert EmailPreferencesCreate(player_profile_id=1).same_day_signups_enabled is False
    assert "same_day_signups_enabled" not in EmailPreferencesUpdate().model_dump(exclude_unset=True)
    response = EmailPreferencesResponse(
        id=1,
        player_profile_id=1,
        daily_signups_enabled=True,
        signup_confirmations_enabled=True,
        signup_reminders_enabled=True,
        game_invitations_enabled=True,
        weekly_summary_enabled=True,
        callout_list_enabled=False,
        email_frequency="daily",
        preferred_notification_time="8:00 AM",
        created_at="2026-01-01",
        updated_at="2026-01-01",
    )
    assert response.same_day_signups_enabled is False


def test_same_day_notification_ledger_rejects_duplicate_recipient(db):
    now = utc_now().isoformat()
    db.add(SameDaySignupNotification(signup_id=7, recipient_profile_id=1, sent_at=now))
    db.commit()

    # Same recipient, same signup — the unique constraint is the dedup guard.
    db.add(SameDaySignupNotification(signup_id=7, recipient_profile_id=1, sent_at=now))
    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()

    # A different recipient for that signup, and the same recipient for another
    # signup, both remain allowed.
    db.add(SameDaySignupNotification(signup_id=7, recipient_profile_id=2, sent_at=now))
    db.add(SameDaySignupNotification(signup_id=8, recipient_profile_id=1, sent_at=now))
    db.commit()

    assert db.query(SameDaySignupNotification).count() == 3

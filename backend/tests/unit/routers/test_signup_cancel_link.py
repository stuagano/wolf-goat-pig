"""Email cancel links preview a signup, then cancel only on an explicit POST.

GET must not cancel: mail scanners prefetch links. The token is the
credential, so these routes do not require a logged-in session.
"""

from datetime import datetime
from unittest.mock import Mock
from zoneinfo import ZoneInfo

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app import database
from app.main import app
from app.models import Base, DailySignup
from app.routers import signups as signups_module
from app.services.signup_cancel_token import issue_cancel_token
from app.utils.time import utc_now

engine = create_engine("sqlite:///./test_signup_cancel_link.db", connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
client = TestClient(app)
CLUB = ZoneInfo("America/Los_Angeles")


@pytest.fixture
def db(monkeypatch):
    Base.metadata.create_all(bind=engine)
    monkeypatch.setattr(database, "SessionLocal", TestingSessionLocal)
    monkeypatch.setenv("SIGNUP_CANCEL_SECRET", "cancel-link-test-secret")
    monkeypatch.delenv("FORETEES_ENCRYPTION_KEY", raising=False)
    monkeypatch.delenv("JWT_SECRET_KEY", raising=False)
    legacy = Mock()
    legacy.live_writes_allowed.return_value = True
    legacy.sync_signup_cancelled.return_value = True
    monkeypatch.setattr(signups_module, "get_legacy_signup_service", lambda: legacy)
    session = TestingSessionLocal()
    try:
        yield session, legacy
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


def _signup(db, **kwargs) -> DailySignup:
    now = utc_now().isoformat()
    signup = DailySignup(
        date=kwargs.pop("date", "2026-11-27"),
        player_profile_id=kwargs.pop("player_profile_id", 7),
        player_name=kwargs.pop("player_name", "Stuart Gano"),
        signup_time=now,
        status=kwargs.pop("status", "signed_up"),
        created_at=now,
        updated_at=now,
        **kwargs,
    )
    db.add(signup)
    db.commit()
    db.refresh(signup)
    return signup


def _token(signup: DailySignup) -> str:
    return issue_cancel_token(
        signup_id=signup.id,
        player_profile_id=signup.player_profile_id,
        signup_date=signup.date,
        now=datetime(2026, 11, 23, tzinfo=CLUB),
    )


def _status(signup_id: int) -> str:
    return TestingSessionLocal().get(DailySignup, signup_id).status


def test_get_previews_without_cancelling(db):
    session, legacy = db
    signup = _signup(session)

    response = client.get(f"/signups/cancel/{_token(signup)}")

    assert response.status_code == 200
    body = response.json()
    assert body["player_name"] == "Stuart Gano"
    assert body["date"] == "2026-11-27"
    assert body["can_cancel"] is True
    assert _status(signup.id) == "signed_up"
    legacy.sync_signup_cancelled.assert_not_called()


def test_post_cancels_that_signup_and_mirrors_the_tee_sheet(db):
    session, legacy = db
    signup = _signup(session)
    other = _signup(session, player_profile_id=8, player_name="Someone Else", date="2026-11-28")

    response = client.post(f"/signups/cancel/{_token(signup)}")

    assert response.status_code == 200
    body = response.json()
    assert body["message"] == "Sign-up cancelled successfully"
    assert body["name"] == "Stuart Gano"
    assert body["date"] == "2026-11-27"
    assert body["legacy_sync"] == "mirrored"
    assert body["already_cancelled"] is False
    assert _status(signup.id) == "cancelled"
    assert _status(other.id) == "signed_up"
    legacy.sync_signup_cancelled.assert_called_once()
    mirrored = legacy.sync_signup_cancelled.call_args.args[0]
    assert mirrored.id == signup.id


def test_post_of_an_already_cancelled_signup_does_not_mirror_again(db):
    session, legacy = db
    signup = _signup(session, status="cancelled")

    response = client.post(f"/signups/cancel/{_token(signup)}")

    assert response.status_code == 200
    assert response.json()["already_cancelled"] is True
    assert _status(signup.id) == "cancelled"
    legacy.sync_signup_cancelled.assert_not_called()


def test_get_of_an_already_cancelled_signup_offers_no_second_cancel(db):
    session, _legacy = db
    signup = _signup(session, status="cancelled")

    response = client.get(f"/signups/cancel/{_token(signup)}")

    assert response.status_code == 200
    assert response.json()["can_cancel"] is False
    assert response.json()["status"] == "cancelled"


def test_token_for_a_different_player_does_not_cancel(db):
    session, legacy = db
    signup = _signup(session)
    forged = issue_cancel_token(
        signup_id=signup.id,
        player_profile_id=999,
        signup_date=signup.date,
        now=datetime(2026, 11, 23, tzinfo=CLUB),
    )

    response = client.post(f"/signups/cancel/{forged}")

    assert response.status_code == 404
    assert _status(signup.id) == "signed_up"
    legacy.sync_signup_cancelled.assert_not_called()


def test_expired_link_does_not_cancel(db):
    session, legacy = db
    signup = _signup(session, date="2020-01-01")
    token = issue_cancel_token(
        signup_id=signup.id,
        player_profile_id=signup.player_profile_id,
        signup_date=signup.date,
        now=datetime(2020, 1, 1, tzinfo=CLUB),
    )

    response = client.post(f"/signups/cancel/{token}")

    assert response.status_code == 410
    assert _status(signup.id) == "signed_up"
    legacy.sync_signup_cancelled.assert_not_called()


def test_guessable_id_is_rejected(db):
    session, legacy = db
    signup = _signup(session)

    response = client.post(f"/signups/cancel/{signup.id}")

    assert response.status_code == 404
    assert _status(signup.id) == "signed_up"
    legacy.sync_signup_cancelled.assert_not_called()

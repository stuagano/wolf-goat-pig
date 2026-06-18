"""
Unit tests for the callout service.

Covers the shortfall math, recipient filtering (opt-in only, exclude
already-signed-up / paused / no-email), once-per-window dedup, and the
end-to-end run_callout flow with a stubbed email service.
"""

from datetime import UTC, datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models import Base, CalloutNotification, DailySignup, EmailPreferences, PlayerProfile
from app.services import callout_service

TEST_DATABASE_URL = "sqlite:///./test_callout.db"
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


class StubEmailService:
    """Records callout sends instead of hitting a provider."""

    def __init__(self, configured=True):
        self.configured = configured
        self.sent = []

    def is_configured(self):
        return self.configured

    def send_callout_notification(self, *, to_email, player_name, game_date, signup_count, needed):
        self.sent.append({"to_email": to_email, "needed": needed, "signup_count": signup_count})
        return True


@pytest.fixture
def stub_email(monkeypatch):
    stub = StubEmailService()
    monkeypatch.setattr(callout_service, "get_email_service", lambda: stub)
    return stub


def _now():
    return datetime.now(UTC).isoformat()


def make_player(db, name, email="x@example.com", *, callout=True, frequency="daily", active=1):
    player = PlayerProfile(name=name, email=email, handicap=18.0, is_active=active, created_at=_now())
    db.add(player)
    db.commit()
    db.refresh(player)
    db.add(
        EmailPreferences(
            player_profile_id=player.id,
            callout_list_enabled=1 if callout else 0,
            email_frequency=frequency,
            created_at=_now(),
            updated_at=_now(),
        )
    )
    db.commit()
    return player


def sign_up(db, player, date, status="signed_up"):
    db.add(
        DailySignup(
            date=date,
            player_profile_id=player.id,
            player_name=player.name,
            signup_time=_now(),
            status=status,
            created_at=_now(),
            updated_at=_now(),
        )
    )
    db.commit()


# --- shortfall math ---------------------------------------------------------


@pytest.mark.parametrize(
    "count,expected_target,expected_shortfall",
    [
        (0, 0, 0),  # nobody — no game
        (1, 4, 0),  # below a foursome — don't call out yet (floor)
        (3, 4, 0),  # still below the floor
        (4, 4, 0),  # exactly one foursome — not short
        (5, 8, 3),
        (10, 12, 2),
        (11, 12, 1),
        (12, 12, 0),  # full — not short
        (13, 16, 3),
    ],
)
def test_shortfall_math(count, expected_target, expected_shortfall):
    assert callout_service.foursome_target(count) == expected_target
    assert callout_service.compute_shortfall(count) == expected_shortfall


# --- recipient filtering ----------------------------------------------------


def test_recipients_only_opted_in_and_not_signed_up(db):
    date = "2026-06-21"
    on_list = make_player(db, "OnList", "onlist@x.com", callout=True)
    make_player(db, "OffList", "offlist@x.com", callout=False)
    paused = make_player(db, "Paused", "paused@x.com", callout=True, frequency="never")
    no_email = make_player(db, "NoEmail", "", callout=True)
    already_in = make_player(db, "AlreadyIn", "in@x.com", callout=True)
    sign_up(db, already_in, date)

    recipients = callout_service.get_callout_recipients(db, date)
    names = {p.name for p in recipients}

    assert names == {"OnList"}
    assert on_list.id in {p.id for p in recipients}
    assert paused.name not in names
    assert no_email.name not in names


# --- end-to-end run_callout -------------------------------------------------


def test_run_callout_fires_when_short(db, stub_email):
    date = "2026-06-21"
    # 11 signed up -> 1 short of 12
    for i in range(11):
        sign_up(db, make_player(db, f"Signed{i}", f"s{i}@x.com", callout=False), date)
    make_player(db, "Caller", "caller@x.com", callout=True)

    result = callout_service.run_callout(db, date, "day_before")

    assert result["fired"] is True
    assert result["shortfall"] == 1
    assert result["target"] == 12
    assert result["recipient_count"] == 1
    assert stub_email.sent[0]["needed"] == 1
    # dedup row written
    assert db.query(CalloutNotification).filter_by(game_date=date, callout_window="day_before").count() == 1


def test_run_callout_skips_when_not_short(db, stub_email):
    date = "2026-06-21"
    for i in range(12):  # full foursomes
        sign_up(db, make_player(db, f"Signed{i}", f"s{i}@x.com", callout=False), date)
    make_player(db, "Caller", "caller@x.com", callout=True)

    result = callout_service.run_callout(db, date, "day_before")

    assert result["fired"] is False
    assert result["reason"] == "not_short"
    assert stub_email.sent == []


def test_run_callout_dedups_within_window(db, stub_email):
    date = "2026-06-21"
    for i in range(11):
        sign_up(db, make_player(db, f"Signed{i}", f"s{i}@x.com", callout=False), date)
    make_player(db, "Caller", "caller@x.com", callout=True)

    first = callout_service.run_callout(db, date, "day_before")
    second = callout_service.run_callout(db, date, "day_before")

    assert first["fired"] is True
    assert second["fired"] is False
    assert second["reason"] == "already_called"
    assert len(stub_email.sent) == 1  # only the first send

    # a different window still fires
    third = callout_service.run_callout(db, date, "morning_of")
    assert third["fired"] is True
    assert len(stub_email.sent) == 2


def test_run_callout_skips_below_floor(db, stub_email):
    date = "2026-06-21"
    for i in range(3):  # below one foursome
        sign_up(db, make_player(db, f"Signed{i}", f"s{i}@x.com", callout=False), date)
    make_player(db, "Caller", "caller@x.com", callout=True)

    result = callout_service.run_callout(db, date, "day_before")

    assert result["fired"] is False
    assert result["reason"] == "not_short"
    assert stub_email.sent == []


def test_run_callout_skips_when_email_unconfigured(db, monkeypatch):
    date = "2026-06-21"
    for i in range(11):
        sign_up(db, make_player(db, f"Signed{i}", f"s{i}@x.com", callout=False), date)
    make_player(db, "Caller", "caller@x.com", callout=True)

    monkeypatch.setattr(callout_service, "get_email_service", lambda: StubEmailService(configured=False))

    result = callout_service.run_callout(db, date, "day_before")

    assert result["fired"] is False
    assert result["reason"] == "email_not_configured"
    # nothing logged, so it can retry later
    assert db.query(CalloutNotification).count() == 0

"""
Unit tests for the Thursday "Sunday's game" signup nudge.

Covers the next-Sunday date, who's already in, recipient rules (opt-out via
Sign-up Reminders, already-signed-up skipped), dry run, and once-per-Sunday-
per-player dedup across reruns.
"""

from datetime import date

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.models import Base, DailySignup, EmailPreferences, PlayerProfile, SignupReminderSend
from app.services import sunday_reminder as sr

engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

THURSDAY = date(2026, 10, 15)
SUNDAY = "2026-10-18"


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
    def __init__(self, configured=True, fail_for=()):
        self.configured = configured
        self.fail_for = set(fail_for)
        self.sent = []

    def is_configured(self):
        return self.configured

    def send_sunday_reminder(self, *, to_email, player_name, game_date, signed_up):
        if to_email in self.fail_for:
            return False
        self.sent.append((to_email, game_date, tuple(signed_up)))
        return True


def make_player(db, name, email, *, prefs=True, reminders=1, frequency="daily", active=1):
    player = PlayerProfile(name=name, email=email, is_active=active, created_at="2026-01-01T00:00:00")
    db.add(player)
    db.commit()
    db.refresh(player)
    if prefs:
        db.add(
            EmailPreferences(player_profile_id=player.id, signup_reminders_enabled=reminders, email_frequency=frequency)
        )
        db.commit()
    return player


def sign_up(db, player, game_date=SUNDAY, status="signed_up"):
    db.add(DailySignup(date=game_date, player_profile_id=player.id, player_name=player.name, status=status))
    db.commit()


def test_next_sunday():
    assert sr.next_sunday(THURSDAY) == date(2026, 10, 18)
    assert sr.next_sunday(date(2026, 10, 18)) == date(2026, 10, 18)  # a Sunday run means today
    assert sr.next_sunday(date(2026, 10, 19)) == date(2026, 10, 25)


def test_recipients_skip_signed_up_and_opted_out(db):
    make_player(db, "NoPrefsRow", "a@x.com", prefs=False)
    make_player(db, "WantsIt", "b@x.com")
    signed = make_player(db, "AlreadyIn", "c@x.com")
    sign_up(db, signed)
    cancelled = make_player(db, "Cancelled", "d@x.com")
    sign_up(db, cancelled, status="cancelled")
    other_day = make_player(db, "OtherDay", "e@x.com")
    sign_up(db, other_day, game_date="2026-10-17")
    make_player(db, "RemindersOff", "f@x.com", reminders=0)
    make_player(db, "Never", "g@x.com", frequency="never")
    make_player(db, "Inactive", "h@x.com", active=0)
    make_player(db, "NoEmail", None)

    names = sorted(p.name for p in sr.get_recipients(db, SUNDAY))
    assert names == ["Cancelled", "NoPrefsRow", "OtherDay", "WantsIt"]


def test_signed_up_names(db):
    sign_up(db, make_player(db, "Mike", "m@x.com"))
    sign_up(db, make_player(db, "Bob", "bob@x.com"))
    sign_up(db, make_player(db, "Gone", "g@x.com"), status="cancelled")
    assert sr.signed_up_names(db, SUNDAY) == ["Bob", "Mike"]


def test_run_sends_once_per_player_per_sunday(db):
    sign_up(db, make_player(db, "Mike", "m@x.com"))
    make_player(db, "A", "a@x.com")
    make_player(db, "B", "b@x.com")
    stub = StubEmailService(fail_for={"b@x.com"})

    first = sr.run(db, today=THURSDAY, email_service=stub)
    assert (first["game_date"], first["sent"], first["failed"]) == (SUNDAY, 1, 1)

    stub.fail_for.clear()
    second = sr.run(db, today=THURSDAY, email_service=stub)
    assert (second["sent"], second["already_sent"]) == (1, 1)
    assert stub.sent == [("a@x.com", SUNDAY, ("Mike",)), ("b@x.com", SUNDAY, ("Mike",))]
    assert db.query(SignupReminderSend).count() == 2


def test_dry_run_sends_nothing(db):
    sign_up(db, make_player(db, "Mike", "m@x.com"))
    make_player(db, "A", "a@x.com")
    stub = StubEmailService()
    result = sr.run(db, today=THURSDAY, email_service=stub, dry_run=True)
    assert result == {
        "dry_run": True,
        "game_date": SUNDAY,
        "signed_up": ["Mike"],
        "recipient_count": 1,
        "already_sent": 0,
    }
    assert stub.sent == []
    assert db.query(SignupReminderSend).count() == 0


def test_run_reports_unconfigured_email(db):
    make_player(db, "A", "a@x.com")
    result = sr.run(db, today=THURSDAY, email_service=StubEmailService(configured=False))
    assert result["reason"] == "email_not_configured"

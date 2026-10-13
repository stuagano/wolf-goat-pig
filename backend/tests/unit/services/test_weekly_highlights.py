"""
Unit tests for the weekly league highlights email.

Covers the Monday-noon week window (Pacific), the highlights math over
completed games, opt-out recipient selection, skipping an empty week,
dry-run, and once-per-week-per-player dedup across reruns.
"""

from datetime import datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.models import Base, EmailPreferences, GamePlayerResult, GameRecord, PlayerProfile, WeeklyHighlightSend
from app.services import weekly_highlights as wh

engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Monday 2026-10-12 19:00 UTC == noon PDT. The week that just ended is
# Mon 2026-10-05 00:00 PT .. Mon 2026-10-12 00:00 PT (07:00 UTC both ends).
MONDAY_NOON = datetime(2026, 10, 12, 19, 0)


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

    def send_weekly_highlights(self, *, to_email, player_name, highlights):
        if to_email in self.fail_for:
            return False
        self.sent.append(to_email)
        return True


def make_player(db, name, email, *, prefs=True, weekly=1, frequency="daily", active=1):
    player = PlayerProfile(name=name, email=email, is_active=active, created_at="2026-01-01T00:00:00")
    db.add(player)
    db.commit()
    db.refresh(player)
    if prefs:
        db.add(EmailPreferences(player_profile_id=player.id, weekly_summary_enabled=weekly, email_frequency=frequency))
        db.commit()
    return player


def make_game(db, completed_at, course, results):
    """results: list of (name, total_earnings, [(hole, quarters), ...])."""
    record = GameRecord(game_id=f"g-{completed_at}-{course}", course_name=course, completed_at=completed_at)
    db.add(record)
    db.commit()
    db.refresh(record)
    for name, earnings, holes in results:
        db.add(
            GamePlayerResult(
                game_record_id=record.id,
                player_name=name,
                total_earnings=earnings,
                hole_scores=[{"hole": h, "quarters": q} for h, q in holes],
            )
        )
    db.commit()
    return record


def seed_week(db):
    # Sunday afternoon PT (inside the window, the reason for the Monday send).
    make_game(
        db,
        "2026-10-11T22:30:00",
        "Wing Point",
        [("Mike", 34, [(3, 12), (7, -2)]), ("Bob", -20, [(3, -4)]), ("Al", -14, [(9, 1)])],
    )
    make_game(db, "2026-10-07T20:00:00", "Wing Point", [("Bob", 10, [(18, 16)]), ("Mike", -10, [(18, -16)])])
    # Outside the window on both sides — must be ignored.
    make_game(db, "2026-10-05T06:59:00", "Wing Point", [("Zed", 99, [(1, 99)])])
    make_game(db, "2026-10-12T07:00:00", "Wing Point", [("Zed", 99, [(1, 99)])])


def test_week_window_monday_noon_covers_prior_mon_through_sun_pacific():
    start, end, week_start = wh.week_window(MONDAY_NOON)
    assert (start, end, week_start) == (datetime(2026, 10, 5, 7), datetime(2026, 10, 12, 7), "2026-10-05")


def test_week_window_on_sunday_still_points_at_last_completed_week():
    # A stray Sunday run must not report a half-finished week.
    _, _, week_start = wh.week_window(datetime(2026, 10, 11, 16, 0))
    assert week_start == "2026-09-28"


def test_compute_highlights(db):
    seed_week(db)
    start, end, _ = wh.week_window(MONDAY_NOON)
    h = wh.compute_highlights(db, start, end)

    assert h["rounds"] == 2
    assert h["courses"] == ["Wing Point"]
    assert h["players"] == ["Al", "Bob", "Mike"]
    assert h["biggest_round"] == {"player": "Mike", "quarters": 34, "course": "Wing Point"}
    assert h["top_earner"] == {"player": "Mike", "quarters": 24, "rounds": 2}
    assert h["biggest_hole"] == {"player": "Bob", "hole": 18, "quarters": 16, "course": "Wing Point"}
    assert h["ironman"] == {"players": ["Bob", "Mike"], "rounds": 2}


def test_compute_highlights_empty_week_is_none(db):
    start, end, _ = wh.week_window(MONDAY_NOON)
    assert wh.compute_highlights(db, start, end) is None


def test_recipients_default_in_and_respect_opt_out(db):
    make_player(db, "NoPrefsRow", "a@x.com", prefs=False)
    make_player(db, "OptedIn", "b@x.com")
    make_player(db, "WeeklyFreq", "c@x.com", frequency="weekly")
    make_player(db, "OptedOut", "d@x.com", weekly=0)
    make_player(db, "Never", "e@x.com", frequency="never")
    make_player(db, "Inactive", "f@x.com", active=0)
    make_player(db, "NoEmail", None)

    names = sorted(p.name for p in wh.get_recipients(db))
    assert names == ["NoPrefsRow", "OptedIn", "WeeklyFreq"]


def test_run_sends_once_per_player_per_week(db):
    seed_week(db)
    make_player(db, "A", "a@x.com")
    make_player(db, "B", "b@x.com")
    stub = StubEmailService(fail_for={"b@x.com"})

    first = wh.run(db, now=MONDAY_NOON, email_service=stub)
    assert (first["sent"], first["failed"]) == (1, 1)

    # Retry: A is not emailed twice, B (failed before) is retried.
    stub.fail_for.clear()
    second = wh.run(db, now=MONDAY_NOON, email_service=stub)
    assert (second["sent"], second["already_sent"]) == (1, 1)
    assert stub.sent == ["a@x.com", "b@x.com"]
    assert db.query(WeeklyHighlightSend).count() == 2


def test_run_skips_empty_week(db):
    make_player(db, "A", "a@x.com")
    stub = StubEmailService()
    result = wh.run(db, now=MONDAY_NOON, email_service=stub)
    assert result["reason"] == "no_rounds"
    assert stub.sent == []


def test_dry_run_sends_nothing(db):
    seed_week(db)
    make_player(db, "A", "a@x.com")
    stub = StubEmailService()
    result = wh.run(db, now=MONDAY_NOON, email_service=stub, dry_run=True)
    assert result["dry_run"] is True
    assert result["recipient_count"] == 1
    assert result["highlights"]["rounds"] == 2
    assert stub.sent == []
    assert db.query(WeeklyHighlightSend).count() == 0


def test_run_reports_unconfigured_email(db):
    seed_week(db)
    make_player(db, "A", "a@x.com")
    result = wh.run(db, now=MONDAY_NOON, email_service=StubEmailService(configured=False))
    assert result["reason"] == "email_not_configured"

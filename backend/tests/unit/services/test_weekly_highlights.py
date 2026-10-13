"""
Unit tests for the weekly league highlights email.

Covers the Monday-noon week window (Pacific), the highlights math over
the merged league rounds (sheet + attested member posts + app games), opt-out recipient selection, skipping an empty week,
dry-run, and once-per-week-per-player dedup across reruns.
"""

from datetime import datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.models import (
    Base,
    EmailPreferences,
    GamePlayerResult,
    GameRecord,
    LegacyRound,
    PlayerProfile,
    WeeklyHighlightSend,
)
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


def sheet(db, date, group, member, score, *, source="primary_sheet", status="attested"):
    db.add(
        LegacyRound(
            date=date, group=group, member=member, score=score, location="Wing Point", source=source, status=status
        )
    )
    db.commit()


def app_game(db, completed_at, results):
    """An in-app scored game: results = [(name, quarters, [(hole, quarters), ...])]."""
    record = GameRecord(game_id=f"g-{completed_at}", course_name="Wing Point", completed_at=completed_at)
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


def seed_week(db):
    sheet(db, "2026-09-07", "A", "Season Opener", 0)  # first sheet round = season start
    # Tue Oct 6, group A (sheet)
    sheet(db, "2026-10-06", "A", "Mike", 34)
    sheet(db, "2026-10-06", "A", "Bob", -20)
    sheet(db, "2026-10-06", "A", "Al", -14)
    # Thu Oct 8, group B (sheet)
    sheet(db, "2026-10-08", "B", "Bob", 10)
    sheet(db, "2026-10-08", "B", "Mike", -10)
    # Sun Oct 11, scored in the app (has hole detail)
    app_game(db, "2026-10-11T22:30:00", [("Carl", 8, [(18, 16), (3, -8)]), ("Mike", -8, [(18, -16)])])
    # Ignored: pending self-post, retired writable sheet, and both sides of the window.
    sheet(db, "2026-10-07", "C", "Pending Pete", 99, source="member", status="pending")
    sheet(db, "2026-10-07", "D", "Old Sheet", 99, source="writable_sheet")
    sheet(db, "2026-10-04", "A", "Zed", 99)
    sheet(db, "2026-10-12", "A", "Zed", 99)


def test_week_window_monday_noon_covers_prior_mon_through_sun_pacific():
    assert wh.week_window(MONDAY_NOON) == ("2026-10-05", "2026-10-12")


def test_week_window_late_sunday_utc_is_still_sunday_pacific():
    # Mon 03:00 UTC is Sunday 8pm PT: the week isn't over, so report the one before.
    assert wh.week_window(datetime(2026, 10, 12, 3, 0)) == ("2026-09-28", "2026-10-05")


def test_compute_highlights_merges_sheet_and_app_rounds(db):
    seed_week(db)
    h = wh.compute_highlights(db, *wh.week_window(MONDAY_NOON))

    assert h["rounds"] == 3
    assert h["courses"] == ["Wing Point"]
    assert h["players"] == ["Al", "Bob", "Carl", "Mike"]
    assert h["biggest_round"] == {"player": "Mike", "quarters": 34, "course": "Wing Point"}
    assert h["top_earner"] == {"player": "Mike", "quarters": 16, "rounds": 3}
    assert h["biggest_hole"] == {"player": "Carl", "hole": 18, "quarters": 16, "course": "Wing Point"}
    assert h["ironman"] == {"players": ["Mike"], "rounds": 3}


def test_sheet_only_week_has_no_hole_highlight(db):
    sheet(db, "2026-10-06", "A", "Mike", 34)
    sheet(db, "2026-10-06", "A", "Bob", -34)
    h = wh.compute_highlights(db, *wh.week_window(MONDAY_NOON))
    assert h["rounds"] == 1
    assert h["biggest_hole"] is None
    assert h["ironman"] is None


def test_compute_highlights_empty_week_is_none(db):
    sheet(db, "2026-09-07", "A", "Season Opener", 0)
    assert wh.compute_highlights(db, *wh.week_window(MONDAY_NOON)) is None


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
    assert result["highlights"]["rounds"] == 3
    assert stub.sent == []
    assert db.query(WeeklyHighlightSend).count() == 0


def test_run_reports_unconfigured_email(db):
    seed_week(db)
    make_player(db, "A", "a@x.com")
    result = wh.run(db, now=MONDAY_NOON, email_service=StubEmailService(configured=False))
    assert result["reason"] == "email_not_configured"

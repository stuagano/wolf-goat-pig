"""CTK-grade contracts for EmailScheduler sheet-dedup helpers."""

from datetime import UTC, datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models import Base, LegacyRound, PendingSheetSync
from app.services.email_scheduler import EmailScheduler

TEST_DATABASE_URL = "sqlite:///./test_email_scheduler.db"
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


def _job(player_scores):
    return PendingSheetSync(
        date="2099-01-04",
        group="A",
        location="Wing Point",
        player_scores=player_scores,
        status="pending",
        created_at=datetime.now(UTC).isoformat(),
    )


def _legacy(db, member, score):
    db.add(
        LegacyRound(
            date="2099-01-04",
            group="A",
            member=member,
            score=score,
            location="Wing Point",
            source="sheet",
            synced_at=datetime.now(UTC).isoformat(),
        )
    )
    db.commit()


def test_dedup_action_returns_new_when_no_legacy_rows(db):
    scheduler = EmailScheduler()
    assert scheduler._dedup_action(db, _job({"Stuart": 4, "Jeff": -4})) == "new"


def test_dedup_action_returns_duplicate_for_same_players_and_scores(db):
    _legacy(db, "Stuart", 4)
    _legacy(db, "Jeff", -4)
    scheduler = EmailScheduler()
    assert scheduler._dedup_action(db, _job({"Stuart": 4, "Jeff": -4})) == "duplicate"


def test_dedup_action_returns_update_when_scores_differ(db):
    _legacy(db, "Stuart", 4)
    _legacy(db, "Jeff", -4)
    scheduler = EmailScheduler()
    assert scheduler._dedup_action(db, _job({"Stuart": 6, "Jeff": -6})) == "update"


def test_available_signup_dates_returns_next_seven_days():
    dates = EmailScheduler()._get_available_signup_dates()
    assert len(dates) == 7
    assert all(isinstance(d, str) and "," in d for d in dates)

"""Unit tests for BadgeEngine.check_career_achievements — the stats-only
backfill path used to award badges from legacy/sheet-round history (no
GamePlayerResult row required), and the dedup fix in
check_post_game_achievements (a badge must be earned once regardless of
trigger_type).
"""

from __future__ import annotations

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.badge_engine import BadgeEngine
from app.database import Base
from app.models import (
    Badge,
    GamePlayerResult,
    GameRecord,
    PlayerBadgeEarned,
    PlayerProfile,
    PlayerStatistics,
)
from app.utils.time import utc_now


@pytest.fixture
def db():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(bind=engine)
    session = sessionmaker(autocommit=False, autoflush=False, bind=engine)()
    yield session
    session.close()


def _make_badge(db, *, badge_id, name, trigger_type, trigger_condition, rarity="common"):
    badge = Badge(
        badge_id=badge_id,
        name=name,
        description=name,
        category="progression",
        rarity=rarity,
        emoji="🏅",
        trigger_condition=trigger_condition,
        trigger_type=trigger_type,
        current_supply=0,
        is_active=True,
        created_at=utc_now().isoformat(),
    )
    db.add(badge)
    db.commit()
    db.refresh(badge)
    return badge


def _make_player(db, player_id=1):
    player = PlayerProfile(id=player_id, name=f"Player {player_id}", created_at=utc_now().isoformat())
    db.add(player)
    db.commit()
    return player


class TestCheckCareerAchievements:
    def test_awards_games_played_milestone_from_stats_alone(self, db):
        _make_player(db)
        db.add(PlayerStatistics(player_id=1, games_played=25, total_earnings=0.0))
        db.commit()
        _make_badge(
            db,
            badge_id=1,
            name="Rookie",
            trigger_type="career_milestone",
            trigger_condition={"type": "games_played_milestone", "games_threshold": 10},
        )

        earned = BadgeEngine(db).check_career_achievements(1)

        assert len(earned) == 1
        assert db.query(PlayerBadgeEarned).filter_by(player_profile_id=1, badge_id=1).count() == 1

    def test_awards_earnings_milestone_from_stats_alone(self, db):
        _make_player(db)
        db.add(PlayerStatistics(player_id=1, games_played=5, total_earnings=150.0))
        db.commit()
        _make_badge(
            db,
            badge_id=2,
            name="Bronze Earner",
            trigger_type="career_milestone",
            trigger_condition={"type": "earnings_milestone", "earnings_threshold": 100},
        )

        earned = BadgeEngine(db).check_career_achievements(1)

        assert len(earned) == 1

    def test_does_not_award_below_threshold(self, db):
        _make_player(db)
        db.add(PlayerStatistics(player_id=1, games_played=3, total_earnings=0.0))
        db.commit()
        _make_badge(
            db,
            badge_id=1,
            name="Rookie",
            trigger_type="career_milestone",
            trigger_condition={"type": "games_played_milestone", "games_threshold": 10},
        )

        earned = BadgeEngine(db).check_career_achievements(1)

        assert earned == []

    def test_running_twice_does_not_duplicate(self, db):
        _make_player(db)
        db.add(PlayerStatistics(player_id=1, games_played=25, total_earnings=0.0))
        db.commit()
        _make_badge(
            db,
            badge_id=1,
            name="Rookie",
            trigger_type="career_milestone",
            trigger_condition={"type": "games_played_milestone", "games_threshold": 10},
        )

        engine = BadgeEngine(db)
        engine.check_career_achievements(1)
        engine.check_career_achievements(1)

        assert db.query(PlayerBadgeEarned).filter_by(player_profile_id=1, badge_id=1).count() == 1

    def test_ignores_badges_that_need_per_game_data(self, db):
        """hole_in_one etc. need a GamePlayerResult — must never fire from stats alone."""
        _make_player(db)
        db.add(PlayerStatistics(player_id=1, games_played=25, total_earnings=0.0))
        db.commit()
        _make_badge(
            db,
            badge_id=3,
            name="Unicorn",
            trigger_type="one_time",
            trigger_condition={"type": "hole_in_one"},
        )

        earned = BadgeEngine(db).check_career_achievements(1)

        assert earned == []


class TestPostGameDedup:
    def test_career_milestone_badge_not_reawarded_on_second_game(self, db):
        """Regression: before the fix, only trigger_type == 'one_time' badges were
        deduped, so a still-true career_milestone condition (e.g. games_played
        >= 10) would insert a duplicate award on every subsequent game."""
        _make_player(db)
        db.add(PlayerStatistics(player_id=1, games_played=25, games_won=1, total_earnings=0.0))
        db.commit()
        _make_badge(
            db,
            badge_id=1,
            name="Rookie",
            trigger_type="career_milestone",
            trigger_condition={"type": "games_played_milestone", "games_threshold": 10},
        )

        engine = BadgeEngine(db)
        for game_num in range(2):
            record = GameRecord(
                game_id=f"game-{game_num}",
                course_name="Test Course",
                created_at=utc_now().isoformat(),
                completed_at=utc_now().isoformat(),
            )
            db.add(record)
            db.commit()
            db.add(
                GamePlayerResult(
                    game_record_id=record.id,
                    player_profile_id=1,
                    player_name="Player 1",
                    final_position=1,
                    total_earnings=10.0,
                )
            )
            db.commit()
            engine.check_post_game_achievements(record.id, 1)

        assert db.query(PlayerBadgeEarned).filter_by(player_profile_id=1, badge_id=1).count() == 1

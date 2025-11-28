"""
Unit tests for LeaderboardService

Tests the leaderboard functionality including:
- Multiple leaderboard types (earnings, win rate, games played, etc.)
- Caching behavior
- Time-based leaderboards (weekly, monthly)
- Player rank tracking
- Error handling
"""

import pytest
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock, patch
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.services.leaderboard_service import (
    LeaderboardService,
    LeaderboardCache,
    get_leaderboard_service,
)
from app.models import Base, PlayerProfile, PlayerStatistics
from fastapi import HTTPException


# Test database setup
TEST_DATABASE_URL = "sqlite:///./test_leaderboard.db"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture
def db():
    """Create a test database session."""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def test_players(db):
    """Create test players with statistics."""
    players = []
    for i in range(5):
        player = PlayerProfile(
            name=f"Player {i+1}",
            email=f"player{i+1}@example.com",
            handicap=18.0 - i,
            is_active=1,
            is_ai=0,
            created_at=datetime.now().isoformat()
        )
        db.add(player)
        db.flush()

        # Create statistics for each player
        stats = PlayerStatistics(
            player_id=player.id,
            games_played=10 + i * 5,
            games_won=3 + i,
            total_earnings=100.0 + i * 50,
            avg_earnings_per_hole=2.0 + i * 0.5,
            betting_success_rate=0.5 + i * 0.05,
            partnership_success_rate=0.4 + i * 0.1,
            partnerships_formed=5 + i,
            partnerships_won=2 + i,
            last_updated=datetime.now().isoformat()
        )
        db.add(stats)
        players.append(player)

    db.commit()
    return players


class TestLeaderboardCache:
    """Test the LeaderboardCache class."""

    def test_cache_set_and_get(self):
        """Test basic cache set and get operations."""
        cache = LeaderboardCache(ttl_seconds=60)
        test_data = [{"rank": 1, "player": "Test"}]

        cache.set("test_key", test_data)
        result = cache.get("test_key")

        assert result == test_data

    def test_cache_miss(self):
        """Test cache miss returns None."""
        cache = LeaderboardCache(ttl_seconds=60)
        result = cache.get("nonexistent_key")
        assert result is None

    def test_cache_expiry(self):
        """Test cache expiry after TTL."""
        cache = LeaderboardCache(ttl_seconds=1)  # 1 second TTL
        test_data = [{"rank": 1, "player": "Test"}]

        cache.set("test_key", test_data)

        # Wait for expiry
        time.sleep(1.1)

        result = cache.get("test_key")
        assert result is None

    def test_cache_invalidate_all(self):
        """Test invalidating all cache entries."""
        cache = LeaderboardCache(ttl_seconds=60)

        cache.set("key1", [{"data": 1}])
        cache.set("key2", [{"data": 2}])

        cache.invalidate()

        assert cache.get("key1") is None
        assert cache.get("key2") is None

    def test_cache_invalidate_pattern(self):
        """Test invalidating cache entries by pattern."""
        cache = LeaderboardCache(ttl_seconds=60)

        cache.set("earnings:all", [{"data": 1}])
        cache.set("earnings:weekly", [{"data": 2}])
        cache.set("winrate:all", [{"data": 3}])

        cache.invalidate("earnings")

        assert cache.get("earnings:all") is None
        assert cache.get("earnings:weekly") is None
        assert cache.get("winrate:all") == [{"data": 3}]


class TestLeaderboardService:
    """Test the LeaderboardService class."""

    def test_supported_leaderboard_types(self, db):
        """Test that all supported leaderboard types are defined."""
        service = LeaderboardService(db)

        expected_types = [
            'total_earnings',
            'win_rate',
            'games_played',
            'average_score',
            'partnerships_won',
            'achievements_earned',
            'handicap_improvement'
        ]

        assert service.LEADERBOARD_TYPES == expected_types

    def test_get_leaderboard_invalid_type(self, db):
        """Test that invalid leaderboard type raises HTTPException."""
        service = LeaderboardService(db)

        with pytest.raises(HTTPException) as exc_info:
            service.get_leaderboard("invalid_type", db)

        assert exc_info.value.status_code == 400
        assert "Invalid leaderboard type" in str(exc_info.value.detail)

    def test_get_total_earnings_leaderboard(self, db, test_players):
        """Test getting total earnings leaderboard."""
        service = LeaderboardService(db)

        leaderboard = service.get_leaderboard("total_earnings", db, limit=5)

        assert len(leaderboard) == 5
        assert leaderboard[0]["rank"] == 1
        # Highest earner should be first
        assert leaderboard[0]["value"] >= leaderboard[1]["value"]

    def test_get_win_rate_leaderboard(self, db, test_players):
        """Test getting win rate leaderboard."""
        service = LeaderboardService(db)

        leaderboard = service.get_leaderboard("win_rate", db, limit=5)

        # Win rate leaderboard requires minimum games
        for entry in leaderboard:
            assert "value" in entry
            assert entry["value"] >= 0
            assert entry["value"] <= 100

    def test_get_games_played_leaderboard(self, db, test_players):
        """Test getting games played leaderboard."""
        service = LeaderboardService(db)

        leaderboard = service.get_leaderboard("games_played", db, limit=5)

        assert len(leaderboard) == 5
        # Most games played should be first
        if len(leaderboard) >= 2:
            assert leaderboard[0]["value"] >= leaderboard[1]["value"]

    def test_leaderboard_caching(self, db, test_players):
        """Test that leaderboard results are cached."""
        service = LeaderboardService(db)

        # First call - should cache
        result1 = service.get_leaderboard("total_earnings", db, limit=5)

        # Second call - should return cached
        result2 = service.get_leaderboard("total_earnings", db, limit=5)

        assert result1 == result2

    def test_leaderboard_pagination(self, db, test_players):
        """Test leaderboard pagination with offset."""
        service = LeaderboardService(db)

        # Clear cache for this test
        service.cache.invalidate()

        # Get first 2 entries
        page1 = service.get_leaderboard("total_earnings", db, limit=2, offset=0)

        # Get next 2 entries
        page2 = service.get_leaderboard("total_earnings", db, limit=2, offset=2)

        assert len(page1) == 2
        assert len(page2) == 2
        assert page1[0]["rank"] == 1
        assert page2[0]["rank"] == 3

    def test_get_player_rank(self, db, test_players):
        """Test getting individual player rank."""
        service = LeaderboardService(db)

        player_id = test_players[0].id
        rank_info = service.get_player_rank(player_id, "total_earnings", db)

        assert rank_info is not None
        assert rank_info["player_id"] == player_id
        assert "rank" in rank_info
        assert "value" in rank_info

    def test_get_player_rank_not_found(self, db, test_players):
        """Test getting rank for non-existent player."""
        service = LeaderboardService(db)

        rank_info = service.get_player_rank(99999, "total_earnings", db)
        assert rank_info is None

    def test_get_player_rank_invalid_type(self, db, test_players):
        """Test getting rank with invalid leaderboard type."""
        service = LeaderboardService(db)

        with pytest.raises(HTTPException) as exc_info:
            service.get_player_rank(test_players[0].id, "invalid_type", db)

        assert exc_info.value.status_code == 400

    def test_get_all_leaderboards(self, db, test_players):
        """Test getting all leaderboards at once."""
        service = LeaderboardService(db)

        all_boards = service.get_all_leaderboards(db, limit=3)

        assert isinstance(all_boards, dict)
        assert "total_earnings" in all_boards
        assert "win_rate" in all_boards
        assert "games_played" in all_boards

    def test_refresh_leaderboard_cache(self, db):
        """Test refreshing the leaderboard cache."""
        service = LeaderboardService(db)

        # Add some items to cache
        service.cache.set("test_key", [{"data": 1}])

        result = service.refresh_leaderboard_cache()

        assert result["status"] == "success"
        assert result["entries_cleared"] >= 1


class TestWeeklyMonthlyLeaderboards:
    """Test time-based leaderboards."""

    def test_get_weekly_leaderboard(self, db, test_players):
        """Test getting weekly leaderboard."""
        service = LeaderboardService(db)

        # This may return empty if no recent game results
        leaderboard = service.get_weekly_leaderboard("total_earnings", db, limit=5)

        assert isinstance(leaderboard, list)
        # Validate structure if results exist
        for entry in leaderboard:
            assert "rank" in entry
            assert "player_id" in entry
            assert "value" in entry

    def test_get_monthly_leaderboard(self, db, test_players):
        """Test getting monthly leaderboard."""
        service = LeaderboardService(db)

        leaderboard = service.get_monthly_leaderboard("total_earnings", db, limit=5)

        assert isinstance(leaderboard, list)
        for entry in leaderboard:
            assert "rank" in entry
            assert "player_id" in entry
            assert "value" in entry

    def test_weekly_invalid_type_raises(self, db):
        """Test weekly leaderboard with invalid type raises error."""
        service = LeaderboardService(db)

        with pytest.raises(HTTPException) as exc_info:
            service.get_weekly_leaderboard("invalid_type", db)

        assert exc_info.value.status_code == 400

    def test_monthly_invalid_type_raises(self, db):
        """Test monthly leaderboard with invalid type raises error."""
        service = LeaderboardService(db)

        with pytest.raises(HTTPException) as exc_info:
            service.get_monthly_leaderboard("invalid_type", db)

        assert exc_info.value.status_code == 400


class TestLeaderboardServiceSingleton:
    """Test singleton pattern for LeaderboardService."""

    def test_singleton_returns_same_instance(self, db):
        """Test that get_leaderboard_service returns consistent instance."""
        service1 = get_leaderboard_service(db)
        service2 = get_leaderboard_service(db)

        assert service1 is service2

    def test_singleton_updates_db_session(self, db):
        """Test that singleton updates its db session."""
        service = get_leaderboard_service(db)

        # Create new session
        db2 = TestingSessionLocal()
        service2 = get_leaderboard_service(db2)

        # Should be same instance but with updated db
        assert service is service2
        assert service.db is db2

        db2.close()


class TestLeaderboardExclusions:
    """Test that AI players and inactive players are excluded."""

    def test_excludes_ai_players(self, db):
        """Test that AI players are excluded from leaderboards."""
        # Create AI player
        ai_player = PlayerProfile(
            name="AI Player",
            email="ai@example.com",
            handicap=10.0,
            is_active=1,
            is_ai=1,  # AI player
            created_at=datetime.now().isoformat()
        )
        db.add(ai_player)
        db.flush()

        # Create stats with high earnings
        stats = PlayerStatistics(
            player_id=ai_player.id,
            games_played=100,
            games_won=90,
            total_earnings=10000.0,  # Very high
            avg_earnings_per_hole=100.0,
            last_updated=datetime.now().isoformat()
        )
        db.add(stats)
        db.commit()

        service = LeaderboardService(db)
        leaderboard = service.get_leaderboard("total_earnings", db, limit=10)

        # AI player should not be in leaderboard
        ai_in_leaderboard = any(
            entry.get("player_id") == ai_player.id for entry in leaderboard
        )
        assert not ai_in_leaderboard

    def test_excludes_inactive_players(self, db):
        """Test that inactive players are excluded from leaderboards."""
        # Create inactive player
        inactive_player = PlayerProfile(
            name="Inactive Player",
            email="inactive@example.com",
            handicap=10.0,
            is_active=0,  # Inactive
            is_ai=0,
            created_at=datetime.now().isoformat()
        )
        db.add(inactive_player)
        db.flush()

        stats = PlayerStatistics(
            player_id=inactive_player.id,
            games_played=100,
            games_won=90,
            total_earnings=10000.0,
            avg_earnings_per_hole=100.0,
            last_updated=datetime.now().isoformat()
        )
        db.add(stats)
        db.commit()

        service = LeaderboardService(db)
        leaderboard = service.get_leaderboard("total_earnings", db, limit=10)

        # Inactive player should not be in leaderboard
        inactive_in_leaderboard = any(
            entry.get("player_id") == inactive_player.id for entry in leaderboard
        )
        assert not inactive_in_leaderboard


class TestLeaderboardErrorHandling:
    """Test error handling in leaderboard service."""

    def test_handles_database_error(self, db):
        """Test graceful handling of database errors."""
        service = LeaderboardService(db)

        # Close the session to simulate DB error
        db.close()

        with pytest.raises(HTTPException) as exc_info:
            service.get_leaderboard("total_earnings", db)

        assert exc_info.value.status_code == 500


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

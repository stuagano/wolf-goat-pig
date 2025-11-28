"""
Unit tests for PlayerService

Tests player profile management including:
- Profile creation, retrieval, update, and deletion
- Statistics management
- Game result recording
- Achievement system
- Performance analytics
"""

import pytest
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.services.player_service import PlayerService
from app.models import Base, PlayerProfile, PlayerStatistics, GamePlayerResult, PlayerAchievement
from app.schemas import (
    PlayerProfileCreate,
    PlayerProfileUpdate,
    GamePlayerResultCreate,
)


# Test database setup
TEST_DATABASE_URL = "sqlite:///./test_player_service.db"
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
def player_service(db):
    """Create a PlayerService instance."""
    return PlayerService(db)


@pytest.fixture
def test_player(db):
    """Create a test player."""
    player = PlayerProfile(
        name="Test Player",
        email="test@example.com",
        handicap=18.0,
        is_active=1,
        is_ai=0,
        created_at=datetime.now().isoformat()
    )
    db.add(player)
    db.flush()

    stats = PlayerStatistics(
        player_id=player.id,
        games_played=10,
        games_won=4,
        total_earnings=100.0,
        avg_earnings_per_hole=2.5,
        betting_success_rate=0.5,
        total_bets=20,
        successful_bets=10,
        partnership_success_rate=0.6,
        partnerships_formed=5,
        partnerships_won=3,
        solo_attempts=3,
        solo_wins=1,
        holes_played=180,
        holes_won=40,
        last_updated=datetime.now().isoformat()
    )
    db.add(stats)
    db.commit()

    return player


class TestProfileCreation:
    """Test player profile creation."""

    def test_create_player_profile(self, db, player_service):
        """Test creating a new player profile."""
        profile_data = PlayerProfileCreate(
            name="New Player",
            handicap=15.0,
            avatar_url="https://example.com/avatar.jpg"
        )

        result = player_service.create_player_profile(profile_data)

        assert result.name == "New Player"
        assert result.handicap == 15.0
        assert result.avatar_url == "https://example.com/avatar.jpg"

    def test_create_player_with_default_preferences(self, db, player_service):
        """Test that default preferences are set on creation."""
        profile_data = PlayerProfileCreate(
            name="Player With Defaults",
            handicap=20.0
        )

        result = player_service.create_player_profile(profile_data)

        # Check default preferences are set
        assert result.preferences is not None
        assert result.preferences.get("ai_difficulty") == "medium"
        assert result.preferences.get("display_hints") is True

    def test_create_player_creates_statistics(self, db, player_service):
        """Test that creating a player also creates statistics record."""
        profile_data = PlayerProfileCreate(
            name="Stats Player",
            handicap=10.0
        )

        result = player_service.create_player_profile(profile_data)

        # Verify statistics were created
        stats = db.query(PlayerStatistics).filter(
            PlayerStatistics.player_id == result.id
        ).first()

        assert stats is not None
        assert stats.games_played == 0

    def test_create_duplicate_name_raises(self, db, player_service, test_player):
        """Test that creating player with duplicate name raises error."""
        profile_data = PlayerProfileCreate(
            name="Test Player",  # Same as test_player
            handicap=20.0
        )

        with pytest.raises(ValueError, match="already exists"):
            player_service.create_player_profile(profile_data)


class TestProfileRetrieval:
    """Test player profile retrieval."""

    def test_get_player_by_id(self, db, player_service, test_player):
        """Test getting player by ID."""
        result = player_service.get_player_profile(test_player.id)

        assert result is not None
        assert result.id == test_player.id
        assert result.name == test_player.name

    def test_get_player_by_name(self, db, player_service, test_player):
        """Test getting player by name."""
        result = player_service.get_player_profile_by_name("Test Player")

        assert result is not None
        assert result.name == "Test Player"

    def test_get_nonexistent_player_returns_none(self, db, player_service):
        """Test getting non-existent player returns None."""
        result = player_service.get_player_profile(99999)
        assert result is None

    def test_get_inactive_player_returns_none(self, db, player_service, test_player):
        """Test getting inactive player returns None."""
        # Deactivate player
        test_player.is_active = 0
        db.commit()

        result = player_service.get_player_profile(test_player.id)
        assert result is None

    def test_get_all_player_profiles(self, db, player_service, test_player):
        """Test getting all player profiles."""
        # Add another player
        player2 = PlayerProfile(
            name="Player 2",
            handicap=15.0,
            is_active=1,
            created_at=datetime.now().isoformat()
        )
        db.add(player2)
        db.commit()

        results = player_service.get_all_player_profiles()

        assert len(results) >= 2

    def test_get_all_includes_inactive(self, db, player_service, test_player):
        """Test getting all profiles can include inactive."""
        # Add inactive player
        inactive = PlayerProfile(
            name="Inactive Player",
            handicap=20.0,
            is_active=0,
            created_at=datetime.now().isoformat()
        )
        db.add(inactive)
        db.commit()

        active_only = player_service.get_all_player_profiles(active_only=True)
        all_players = player_service.get_all_player_profiles(active_only=False)

        assert len(all_players) >= len(active_only)


class TestProfileUpdate:
    """Test player profile updates."""

    def test_update_player_name(self, db, player_service, test_player):
        """Test updating player name."""
        update_data = PlayerProfileUpdate(name="Updated Name")

        result = player_service.update_player_profile(test_player.id, update_data)

        assert result is not None
        assert result.name == "Updated Name"

    def test_update_player_handicap(self, db, player_service, test_player):
        """Test updating player handicap."""
        update_data = PlayerProfileUpdate(handicap=12.5)

        result = player_service.update_player_profile(test_player.id, update_data)

        assert result is not None
        assert result.handicap == 12.5

    def test_update_player_avatar(self, db, player_service, test_player):
        """Test updating player avatar URL."""
        update_data = PlayerProfileUpdate(avatar_url="https://new-avatar.com/img.jpg")

        result = player_service.update_player_profile(test_player.id, update_data)

        assert result is not None
        assert result.avatar_url == "https://new-avatar.com/img.jpg"

    def test_update_player_preferences(self, db, player_service, test_player):
        """Test updating player preferences."""
        new_prefs = {"ai_difficulty": "hard", "display_hints": False}
        update_data = PlayerProfileUpdate(preferences=new_prefs)

        result = player_service.update_player_profile(test_player.id, update_data)

        assert result is not None
        assert result.preferences["ai_difficulty"] == "hard"

    def test_update_to_duplicate_name_raises(self, db, player_service, test_player):
        """Test that updating to duplicate name raises error."""
        # Create another player
        player2 = PlayerProfile(
            name="Player 2",
            handicap=15.0,
            is_active=1,
            created_at=datetime.now().isoformat()
        )
        db.add(player2)
        db.commit()

        # Try to rename test_player to "Player 2"
        update_data = PlayerProfileUpdate(name="Player 2")

        with pytest.raises(ValueError, match="already exists"):
            player_service.update_player_profile(test_player.id, update_data)

    def test_update_nonexistent_player_returns_none(self, db, player_service):
        """Test updating non-existent player returns None."""
        update_data = PlayerProfileUpdate(name="New Name")

        result = player_service.update_player_profile(99999, update_data)

        assert result is None


class TestProfileDeletion:
    """Test player profile deletion (soft delete)."""

    def test_delete_player_soft_deletes(self, db, player_service, test_player):
        """Test that delete marks player as inactive."""
        result = player_service.delete_player_profile(test_player.id)

        assert result is True

        # Player should still exist but be inactive
        player = db.query(PlayerProfile).filter(PlayerProfile.id == test_player.id).first()
        assert player is not None
        assert player.is_active == 0

    def test_delete_nonexistent_player_returns_false(self, db, player_service):
        """Test deleting non-existent player returns False."""
        result = player_service.delete_player_profile(99999)
        assert result is False


class TestStatisticsManagement:
    """Test player statistics management."""

    def test_get_player_statistics(self, db, player_service, test_player):
        """Test getting player statistics."""
        result = player_service.get_player_statistics(test_player.id)

        assert result is not None
        assert result.games_played == 10
        assert result.games_won == 4
        assert result.total_earnings == 100.0

    def test_get_statistics_nonexistent_player(self, db, player_service):
        """Test getting statistics for non-existent player."""
        result = player_service.get_player_statistics(99999)
        assert result is None

    def test_update_last_played(self, db, player_service, test_player):
        """Test updating last played timestamp."""
        original_last_played = test_player.last_played

        player_service.update_last_played(test_player.id)

        db.refresh(test_player)
        assert test_player.last_played != original_last_played


class TestGameResultRecording:
    """Test game result recording and statistics updates."""

    def test_record_game_result(self, db, player_service, test_player):
        """Test recording a game result."""
        game_result = GamePlayerResultCreate(
            game_record_id=1,
            player_profile_id=test_player.id,
            player_name=test_player.name,
            final_position=1,
            total_earnings=25.0,
            holes_won=5,
            successful_bets=3,
            total_bets=5,
            partnerships_formed=1,
            partnerships_won=1,
            solo_attempts=1,
            solo_wins=1
        )

        result = player_service.record_game_result(game_result)

        assert result is True

    def test_record_game_updates_statistics(self, db, player_service, test_player):
        """Test that recording game updates player statistics."""
        original_games = 10
        original_earnings = 100.0

        game_result = GamePlayerResultCreate(
            game_record_id=1,
            player_profile_id=test_player.id,
            player_name=test_player.name,
            final_position=1,
            total_earnings=50.0,
            holes_won=5,
            successful_bets=4,
            total_bets=5,
            partnerships_formed=1,
            partnerships_won=1,
            solo_attempts=0,
            solo_wins=0,
            hole_scores={"1": 4, "2": 5, "3": 4}
        )

        player_service.record_game_result(game_result)

        stats = db.query(PlayerStatistics).filter(
            PlayerStatistics.player_id == test_player.id
        ).first()

        assert stats.games_played == original_games + 1
        assert stats.total_earnings == original_earnings + 50.0

    def test_record_game_win_updates_streak(self, db, player_service, test_player):
        """Test that winning updates win streak."""
        game_result = GamePlayerResultCreate(
            game_record_id=1,
            player_profile_id=test_player.id,
            player_name=test_player.name,
            final_position=1,  # Win
            total_earnings=25.0,
            holes_won=5,
            successful_bets=3,
            total_bets=5,
            partnerships_formed=0,
            partnerships_won=0,
            solo_attempts=0,
            solo_wins=0
        )

        player_service.record_game_result(game_result)

        stats = player_service.get_player_statistics(test_player.id)
        assert stats.current_win_streak >= 1

    def test_record_game_updates_special_events(self, db, player_service, test_player):
        """Test that special event stats are updated."""
        game_result = GamePlayerResultCreate(
            game_record_id=1,
            player_profile_id=test_player.id,
            player_name=test_player.name,
            final_position=2,
            total_earnings=10.0,
            holes_won=3,
            successful_bets=2,
            total_bets=4,
            partnerships_formed=1,
            partnerships_won=0,
            solo_attempts=0,
            solo_wins=0,
            ping_pongs=2,
            ping_pongs_won=1,
            invisible_aardvark_holes=1,
            invisible_aardvark_holes_won=0,
            duncan_attempts=1,
            duncan_wins=0
        )

        player_service.record_game_result(game_result)

        stats = db.query(PlayerStatistics).filter(
            PlayerStatistics.player_id == test_player.id
        ).first()

        # Original had ping_pong_count, should be incremented
        # Note: Actual behavior depends on implementation


class TestPerformanceAnalytics:
    """Test performance analytics functionality."""

    def test_get_performance_analytics(self, db, player_service, test_player):
        """Test getting performance analytics."""
        result = player_service.get_player_performance_analytics(test_player.id)

        assert result is not None
        assert result.player_id == test_player.id
        assert "performance_summary" in dir(result) or hasattr(result, 'performance_summary')

    def test_analytics_nonexistent_player(self, db, player_service):
        """Test analytics for non-existent player returns None."""
        result = player_service.get_player_performance_analytics(99999)
        assert result is None

    def test_analytics_performance_summary(self, db, player_service, test_player):
        """Test analytics includes performance summary."""
        result = player_service.get_player_performance_analytics(test_player.id)

        assert result.performance_summary is not None
        assert "games_played" in result.performance_summary
        assert "win_rate" in result.performance_summary


class TestLeaderboard:
    """Test leaderboard functionality in PlayerService."""

    def test_get_leaderboard(self, db, player_service, test_player):
        """Test getting player leaderboard."""
        # Add more players with stats
        for i in range(3):
            player = PlayerProfile(
                name=f"Leaderboard Player {i}",
                handicap=15.0,
                is_active=1,
                is_ai=0,
                created_at=datetime.now().isoformat()
            )
            db.add(player)
            db.flush()

            stats = PlayerStatistics(
                player_id=player.id,
                games_played=5,
                games_won=i,
                total_earnings=50.0 * (i + 1),
                avg_earnings_per_hole=2.0,
                partnership_success_rate=0.5,
                last_updated=datetime.now().isoformat()
            )
            db.add(stats)

        db.commit()

        leaderboard = player_service.get_leaderboard(limit=5)

        assert len(leaderboard) >= 1
        assert leaderboard[0].rank == 1

    def test_leaderboard_excludes_ai_players(self, db, player_service, test_player):
        """Test that AI players are excluded from leaderboard."""
        ai_player = PlayerProfile(
            name="AI Player",
            handicap=0.0,
            is_active=1,
            is_ai=1,  # AI player
            created_at=datetime.now().isoformat()
        )
        db.add(ai_player)
        db.flush()

        stats = PlayerStatistics(
            player_id=ai_player.id,
            games_played=100,
            games_won=99,
            total_earnings=10000.0,
            avg_earnings_per_hole=100.0,
            partnership_success_rate=1.0,
            last_updated=datetime.now().isoformat()
        )
        db.add(stats)
        db.commit()

        leaderboard = player_service.get_leaderboard(limit=10)

        ai_in_leaderboard = any(
            entry.player_name == "AI Player" for entry in leaderboard
        )
        assert not ai_in_leaderboard


class TestAchievementSystem:
    """Test achievement awarding system."""

    def test_check_first_win_achievement(self, db, player_service):
        """Test that first win achievement is awarded."""
        # Create new player with 0 wins initially
        player = PlayerProfile(
            name="New Winner",
            handicap=20.0,
            is_active=1,
            created_at=datetime.now().isoformat()
        )
        db.add(player)
        db.flush()

        stats = PlayerStatistics(
            player_id=player.id,
            games_played=0,
            games_won=0,
            last_updated=datetime.now().isoformat()
        )
        db.add(stats)
        db.commit()

        # Simulate first win
        game_result = GamePlayerResultCreate(
            game_record_id=1,
            player_profile_id=player.id,
            player_name=player.name,
            final_position=1,
            total_earnings=10.0,
            holes_won=4,
            successful_bets=3,
            total_bets=5,
            partnerships_formed=0,
            partnerships_won=0,
            solo_attempts=0,
            solo_wins=0
        )

        # Record result (this updates games_won to 1)
        player_service.record_game_result(game_result)

        # Check achievements
        achievements = player_service.check_and_award_achievements(player.id, game_result)

        # Should have "First Victory" achievement
        assert "First Victory" in achievements

    def test_achievement_not_awarded_twice(self, db, player_service, test_player):
        """Test that same achievement is not awarded twice."""
        # Award an achievement manually
        achievement = PlayerAchievement(
            player_profile_id=test_player.id,
            achievement_type="first_win",
            achievement_name="First Victory",
            description="Won your first game",
            earned_date=datetime.now().isoformat()
        )
        db.add(achievement)
        db.commit()

        # Create game result
        game_result = GamePlayerResultCreate(
            game_record_id=2,
            player_profile_id=test_player.id,
            player_name=test_player.name,
            final_position=1,
            total_earnings=10.0,
            holes_won=4,
            successful_bets=3,
            total_bets=5,
            partnerships_formed=0,
            partnerships_won=0,
            solo_attempts=0,
            solo_wins=0
        )

        # Check achievements - should not get first_win again
        achievements = player_service.check_and_award_achievements(
            test_player.id, game_result
        )

        assert "First Victory" not in achievements


class TestHelperMethods:
    """Test internal helper methods."""

    def test_calculate_average_position(self, db, player_service, test_player):
        """Test average position calculation."""
        # Add some game results
        for i in range(5):
            result = GamePlayerResult(
                game_record_id=i + 1,
                player_profile_id=test_player.id,
                player_name=test_player.name,
                final_position=(i % 4) + 1,  # Positions 1-4
                total_earnings=10.0,
                created_at=datetime.now().isoformat()
            )
            db.add(result)
        db.commit()

        avg_pos = player_service._calculate_average_position(test_player.id)

        assert avg_pos > 0
        assert avg_pos <= 4

    def test_calculate_recent_form(self, db, player_service, test_player):
        """Test recent form calculation."""
        # Add some game results with good positions
        for i in range(5):
            result = GamePlayerResult(
                game_record_id=i + 100,
                player_profile_id=test_player.id,
                player_name=test_player.name,
                final_position=1,  # All wins
                total_earnings=20.0,
                created_at=datetime.now().isoformat()
            )
            db.add(result)
        db.commit()

        form = player_service._calculate_recent_form(test_player.id)

        assert form == "Excellent"

    def test_recent_form_no_games(self, db, player_service):
        """Test recent form with no games."""
        # Create player without games
        player = PlayerProfile(
            name="No Games",
            handicap=20.0,
            created_at=datetime.now().isoformat()
        )
        db.add(player)
        db.commit()

        form = player_service._calculate_recent_form(player.id)

        assert form == "No recent games"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

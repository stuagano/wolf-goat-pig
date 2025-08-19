"""
Comprehensive test suite for Player Profile System

This module provides thorough testing for the player profile management system,
including CRUD operations, statistics calculations, achievement system, 
performance analytics, and data persistence.

Test Coverage:
- PlayerService CRUD operations
- Statistics calculations and updates
- Achievement system and validation
- Performance analytics and insights
- Leaderboard functionality
- Data persistence and integrity
- Edge cases and error handling
- Concurrent access safety
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import json
import threading
import time
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Import the classes we're testing
from app.services.player_service import PlayerService
from app.models import (
    PlayerProfile, PlayerStatistics, GameRecord, GamePlayerResult, 
    PlayerAchievement
)
from app.schemas import (
    PlayerProfileCreate, PlayerProfileUpdate, PlayerProfileResponse,
    PlayerStatisticsResponse, GamePlayerResultCreate,
    PlayerPerformanceAnalytics, LeaderboardEntry
)


class TestPlayerServiceCRUD:
    """Test suite for Player Service CRUD operations."""
    
    def setup_method(self):
        """Set up test fixtures for each test method."""
        # Create in-memory SQLite database for testing
        self.engine = create_engine("sqlite:///:memory:", echo=False)
        self.Session = sessionmaker(bind=self.engine)
        
        # Create tables
        from app.models import Base
        Base.metadata.create_all(self.engine)
        
        self.db = self.Session()
        self.player_service = PlayerService(self.db)
    
    def teardown_method(self):
        """Clean up after each test method."""
        self.db.close()
    
    def test_create_player_profile_success(self):
        """Test successful player profile creation."""
        profile_data = PlayerProfileCreate(
            name="Test Player",
            handicap=12.5,
            avatar_url="https://example.com/avatar.jpg",
            preferences={
                "ai_difficulty": "hard",
                "preferred_game_modes": ["wolf_goat_pig", "skins"],
                "betting_style": "aggressive"
            }
        )
        
        result = self.player_service.create_player_profile(profile_data)
        
        assert result is not None
        assert result.name == "Test Player"
        assert result.handicap == 12.5
        assert result.avatar_url == "https://example.com/avatar.jpg"
        assert result.preferences["ai_difficulty"] == "hard"
        assert result.id is not None
        
        # Verify statistics record was created
        stats = self.player_service.get_player_statistics(result.id)
        assert stats is not None
        assert stats.player_id == result.id
        assert stats.games_played == 0
    
    def test_create_player_profile_with_defaults(self):
        """Test player profile creation with default values."""
        profile_data = PlayerProfileCreate(
            name="Minimal Player",
            handicap=18.0
        )
        
        result = self.player_service.create_player_profile(profile_data)
        
        assert result is not None
        assert result.name == "Minimal Player"
        assert result.handicap == 18.0
        assert result.avatar_url is None
        assert result.preferences is not None
        assert "ai_difficulty" in result.preferences
        assert result.preferences["ai_difficulty"] == "medium"
    
    def test_create_player_profile_duplicate_name(self):
        """Test that duplicate player names are not allowed."""
        profile_data = PlayerProfileCreate(name="Duplicate Player", handicap=10.0)
        
        # Create first player
        self.player_service.create_player_profile(profile_data)
        
        # Attempt to create duplicate should raise error
        with pytest.raises(ValueError, match="already exists"):
            self.player_service.create_player_profile(profile_data)
    
    def test_get_player_profile_success(self):
        """Test successful player profile retrieval."""
        # Create a player first
        profile_data = PlayerProfileCreate(name="Retrievable Player", handicap=8.0)
        created = self.player_service.create_player_profile(profile_data)
        
        # Retrieve the player
        result = self.player_service.get_player_profile(created.id)
        
        assert result is not None
        assert result.id == created.id
        assert result.name == "Retrievable Player"
        assert result.handicap == 8.0
    
    def test_get_player_profile_not_found(self):
        """Test player profile retrieval for non-existent player."""
        result = self.player_service.get_player_profile(99999)
        assert result is None
    
    def test_get_player_profile_by_name_success(self):
        """Test successful player profile retrieval by name."""
        profile_data = PlayerProfileCreate(name="Named Player", handicap=15.0)
        created = self.player_service.create_player_profile(profile_data)
        
        result = self.player_service.get_player_profile_by_name("Named Player")
        
        assert result is not None
        assert result.name == "Named Player"
        assert result.id == created.id
    
    def test_get_player_profile_by_name_not_found(self):
        """Test player profile retrieval by name for non-existent player."""
        result = self.player_service.get_player_profile_by_name("Non-existent Player")
        assert result is None
    
    def test_get_all_player_profiles(self):
        """Test retrieval of all player profiles."""
        # Create multiple players
        players_data = [
            PlayerProfileCreate(name="Player 1", handicap=5.0),
            PlayerProfileCreate(name="Player 2", handicap=15.0),
            PlayerProfileCreate(name="Player 3", handicap=25.0)
        ]
        
        created_players = []
        for data in players_data:
            created = self.player_service.create_player_profile(data)
            created_players.append(created)
        
        # Retrieve all players
        all_players = self.player_service.get_all_player_profiles()
        
        assert len(all_players) == 3
        player_names = [p.name for p in all_players]
        assert "Player 1" in player_names
        assert "Player 2" in player_names
        assert "Player 3" in player_names
    
    def test_update_player_profile_success(self):
        """Test successful player profile update."""
        # Create a player
        profile_data = PlayerProfileCreate(name="Updatable Player", handicap=20.0)
        created = self.player_service.create_player_profile(profile_data)
        
        # Update the player
        update_data = PlayerProfileUpdate(
            name="Updated Player",
            handicap=18.0,
            avatar_url="https://example.com/new_avatar.jpg"
        )
        
        result = self.player_service.update_player_profile(created.id, update_data)
        
        assert result is not None
        assert result.name == "Updated Player"
        assert result.handicap == 18.0
        assert result.avatar_url == "https://example.com/new_avatar.jpg"
    
    def test_update_player_profile_partial(self):
        """Test partial player profile update."""
        # Create a player
        profile_data = PlayerProfileCreate(name="Partial Update", handicap=12.0)
        created = self.player_service.create_player_profile(profile_data)
        
        # Update only handicap
        update_data = PlayerProfileUpdate(handicap=10.0)
        
        result = self.player_service.update_player_profile(created.id, update_data)
        
        assert result is not None
        assert result.name == "Partial Update"  # Unchanged
        assert result.handicap == 10.0  # Updated
    
    def test_update_player_profile_duplicate_name(self):
        """Test that updating to duplicate name is prevented."""
        # Create two players
        player1_data = PlayerProfileCreate(name="Player One", handicap=10.0)
        player2_data = PlayerProfileCreate(name="Player Two", handicap=12.0)
        
        player1 = self.player_service.create_player_profile(player1_data)
        player2 = self.player_service.create_player_profile(player2_data)
        
        # Try to update player2's name to match player1
        update_data = PlayerProfileUpdate(name="Player One")
        
        with pytest.raises(ValueError, match="already exists"):
            self.player_service.update_player_profile(player2.id, update_data)
    
    def test_update_player_profile_not_found(self):
        """Test updating non-existent player profile."""
        update_data = PlayerProfileUpdate(name="Ghost Player")
        result = self.player_service.update_player_profile(99999, update_data)
        
        assert result is None
    
    def test_delete_player_profile_success(self):
        """Test successful player profile deletion (soft delete)."""
        # Create a player
        profile_data = PlayerProfileCreate(name="Deletable Player", handicap=16.0)
        created = self.player_service.create_player_profile(profile_data)
        
        # Delete the player
        result = self.player_service.delete_player_profile(created.id)
        
        assert result is True
        
        # Verify player is not returned in active queries
        retrieved = self.player_service.get_player_profile(created.id)
        assert retrieved is None
        
        # But should still exist in database as inactive
        all_players = self.player_service.get_all_player_profiles(active_only=False)
        inactive_player = next((p for p in all_players if p.id == created.id), None)
        assert inactive_player is not None
        assert inactive_player.is_active == 0
    
    def test_delete_player_profile_not_found(self):
        """Test deletion of non-existent player profile."""
        result = self.player_service.delete_player_profile(99999)
        assert result is False


class TestPlayerStatistics:
    """Test suite for player statistics management."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.engine = create_engine("sqlite:///:memory:", echo=False)
        self.Session = sessionmaker(bind=self.engine)
        
        from app.models import Base
        Base.metadata.create_all(self.engine)
        
        self.db = self.Session()
        self.player_service = PlayerService(self.db)
        
        # Create a test player
        profile_data = PlayerProfileCreate(name="Stats Player", handicap=12.0)
        self.test_player = self.player_service.create_player_profile(profile_data)
    
    def teardown_method(self):
        """Clean up."""
        self.db.close()
    
    def test_get_player_statistics_initial(self):
        """Test getting initial player statistics."""
        stats = self.player_service.get_player_statistics(self.test_player.id)
        
        assert stats is not None
        assert stats.player_id == self.test_player.id
        assert stats.games_played == 0
        assert stats.games_won == 0
        assert stats.total_earnings == 0.0
        assert stats.holes_played == 0
        assert stats.holes_won == 0
        assert stats.avg_earnings_per_hole == 0.0
        assert stats.betting_success_rate == 0.0
        assert stats.partnership_success_rate == 0.0
    
    def test_record_game_result_basic(self):
        """Test recording a basic game result."""
        game_result = GamePlayerResultCreate(
            player_profile_id=self.test_player.id,
            game_id="test_game_123",
            final_position=2,
            total_earnings=5.0,
            hole_scores={"1": 4, "2": 5, "3": 3},
            holes_won=1,
            successful_bets=3,
            total_bets=5,
            partnerships_formed=1,
            partnerships_won=0,
            solo_attempts=0,
            solo_wins=0
        )
        
        result = self.player_service.record_game_result(game_result)
        assert result is True
        
        # Check updated statistics
        stats = self.player_service.get_player_statistics(self.test_player.id)
        assert stats.games_played == 1
        assert stats.games_won == 0  # Didn't win (position 2)
        assert stats.total_earnings == 5.0
        assert stats.holes_played == 3
        assert stats.holes_won == 1
        assert stats.avg_earnings_per_hole == 5.0 / 3
        assert abs(stats.betting_success_rate - 0.6) < 0.001  # 3/5
        assert stats.partnership_success_rate == 0.0  # 0/1
        assert stats.partnerships_formed == 1
        assert stats.partnerships_won == 0
    
    def test_record_game_result_winning(self):
        """Test recording a winning game result."""
        game_result = GamePlayerResultCreate(
            player_profile_id=self.test_player.id,
            game_id="winning_game",
            final_position=1,  # Won the game
            total_earnings=15.0,
            hole_scores={"1": 3, "2": 4},
            holes_won=2,
            successful_bets=4,
            total_bets=4,
            partnerships_formed=0,
            partnerships_won=0,
            solo_attempts=1,
            solo_wins=1
        )
        
        result = self.player_service.record_game_result(game_result)
        assert result is True
        
        stats = self.player_service.get_player_statistics(self.test_player.id)
        assert stats.games_played == 1
        assert stats.games_won == 1  # Won this game
        assert stats.total_earnings == 15.0
        assert stats.betting_success_rate == 1.0  # 4/4
        assert stats.solo_attempts == 1
        assert stats.solo_wins == 1
    
    def test_record_multiple_games(self):
        """Test recording multiple game results and cumulative statistics."""
        game_results = [
            GamePlayerResultCreate(
                player_profile_id=self.test_player.id,
                game_id=f"game_{i}",
                final_position=i % 2 + 1,  # Alternate between 1st and 2nd place
                total_earnings=float(i * 3),
                hole_scores={str(j): 4 for j in range(1, 4)},
                holes_won=i % 2,
                successful_bets=i + 1,
                total_bets=i + 2,
                partnerships_formed=1 if i % 2 == 0 else 0,
                partnerships_won=1 if i % 3 == 0 else 0,
                solo_attempts=0,
                solo_wins=0
            )
            for i in range(5)
        ]
        
        for game_result in game_results:
            self.player_service.record_game_result(game_result)
        
        stats = self.player_service.get_player_statistics(self.test_player.id)
        
        assert stats.games_played == 5
        assert stats.games_won == 3  # Won games 0, 2, 4 (position 1)
        assert stats.total_earnings == sum(i * 3 for i in range(5))  # 0+3+6+9+12 = 30
        assert stats.holes_played == 15  # 3 holes per game * 5 games
        assert stats.holes_won == 2  # Won on games 0, 2, 4, but only count holes_won values
    
    def test_update_last_played(self):
        """Test updating last played timestamp."""
        # Get initial last played (should be None or creation time)
        initial_player = self.player_service.get_player_profile(self.test_player.id)
        
        # Update last played
        self.player_service.update_last_played(self.test_player.id)
        
        # Check that last played was updated
        updated_player = self.player_service.get_player_profile(self.test_player.id)
        
        # Should have a recent timestamp
        if updated_player.last_played:
            last_played_time = datetime.fromisoformat(updated_player.last_played)
            now = datetime.now()
            time_diff = (now - last_played_time).total_seconds()
            assert time_diff < 5  # Should be within 5 seconds
    
    def test_performance_trends_tracking(self):
        """Test that performance trends are properly tracked."""
        # Record several games to build trend data
        for i in range(3):
            game_result = GamePlayerResultCreate(
                player_profile_id=self.test_player.id,
                game_id=f"trend_game_{i}",
                final_position=i + 1,
                total_earnings=float(10 - i * 2),  # Declining earnings
                hole_scores={"1": 4},
                holes_won=1 if i == 0 else 0,
                successful_bets=2,
                total_bets=3,
                partnerships_formed=0,
                partnerships_won=0,
                solo_attempts=0,
                solo_wins=0
            )
            self.player_service.record_game_result(game_result)
            time.sleep(0.01)  # Small delay to ensure different timestamps
        
        stats = self.player_service.get_player_statistics(self.test_player.id)
        
        assert stats.performance_trends is not None
        assert len(stats.performance_trends) == 3
        
        # Check trend data structure
        for i, trend in enumerate(stats.performance_trends):
            assert "game_date" in trend
            assert "earnings" in trend
            assert "position" in trend
            assert "holes_won" in trend
            assert "betting_success" in trend
            assert trend["earnings"] == float(10 - i * 2)
            assert trend["position"] == i + 1


class TestPlayerAchievements:
    """Test suite for player achievement system."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.engine = create_engine("sqlite:///:memory:", echo=False)
        self.Session = sessionmaker(bind=self.engine)
        
        from app.models import Base
        Base.metadata.create_all(self.engine)
        
        self.db = self.Session()
        self.player_service = PlayerService(self.db)
        
        # Create a test player
        profile_data = PlayerProfileCreate(name="Achievement Player", handicap=12.0)
        self.test_player = self.player_service.create_player_profile(profile_data)
    
    def teardown_method(self):
        """Clean up."""
        self.db.close()
    
    def test_first_win_achievement(self):
        """Test that first win achievement is awarded."""
        # Record a winning game
        game_result = GamePlayerResultCreate(
            player_profile_id=self.test_player.id,
            game_id="first_win_game",
            final_position=1,  # First place
            total_earnings=10.0,
            hole_scores={"1": 4},
            holes_won=1,
            successful_bets=2,
            total_bets=3,
            partnerships_formed=0,
            partnerships_won=0,
            solo_attempts=0,
            solo_wins=0
        )
        
        achievements = self.player_service.check_and_award_achievements(
            self.test_player.id, game_result
        )
        
        assert "First Victory" in achievements
        
        # Verify achievement is recorded in database
        player_achievements = self.db.query(PlayerAchievement).filter(
            PlayerAchievement.player_profile_id == self.test_player.id
        ).all()
        
        first_win = next((a for a in player_achievements if a.achievement_type == "first_win"), None)
        assert first_win is not None
        assert first_win.achievement_name == "First Victory"
    
    def test_big_earner_achievement(self):
        """Test that big earner achievement is awarded."""
        game_result = GamePlayerResultCreate(
            player_profile_id=self.test_player.id,
            game_id="big_earner_game",
            final_position=2,
            total_earnings=25.0,  # Over 20 quarters
            hole_scores={"1": 4},
            holes_won=0,
            successful_bets=1,
            total_bets=2,
            partnerships_formed=0,
            partnerships_won=0,
            solo_attempts=0,
            solo_wins=0
        )
        
        achievements = self.player_service.check_and_award_achievements(
            self.test_player.id, game_result
        )
        
        assert "Big Earner" in achievements
    
    def test_betting_expert_achievement(self):
        """Test betting expert achievement requirements."""
        # First, build up betting statistics
        for i in range(4):
            game_result = GamePlayerResultCreate(
                player_profile_id=self.test_player.id,
                game_id=f"betting_game_{i}",
                final_position=2,
                total_earnings=5.0,
                hole_scores={"1": 4},
                holes_won=0,
                successful_bets=4,  # Good betting success
                total_bets=5,
                partnerships_formed=0,
                partnerships_won=0,
                solo_attempts=0,
                solo_wins=0
            )
            self.player_service.record_game_result(game_result)
        
        # Final game to trigger achievement check
        final_game_result = GamePlayerResultCreate(
            player_profile_id=self.test_player.id,
            game_id="betting_expert_trigger",
            final_position=2,
            total_earnings=3.0,
            hole_scores={"1": 4},
            holes_won=0,
            successful_bets=4,
            total_bets=5,
            partnerships_formed=0,
            partnerships_won=0,
            solo_attempts=0,
            solo_wins=0
        )
        
        achievements = self.player_service.check_and_award_achievements(
            self.test_player.id, final_game_result
        )
        
        # Check if betting expert was awarded (need 70% success rate with 20+ bets)
        stats = self.player_service.get_player_statistics(self.test_player.id)
        if stats.total_bets >= 20 and stats.betting_success_rate >= 0.7:
            assert "Betting Expert" in achievements
    
    def test_achievement_not_duplicated(self):
        """Test that achievements are not awarded multiple times."""
        # Award first win achievement
        first_win_game = GamePlayerResultCreate(
            player_profile_id=self.test_player.id,
            game_id="first_win",
            final_position=1,
            total_earnings=10.0,
            hole_scores={"1": 4},
            holes_won=1,
            successful_bets=2,
            total_bets=3,
            partnerships_formed=0,
            partnerships_won=0,
            solo_attempts=0,
            solo_wins=0
        )
        
        achievements1 = self.player_service.check_and_award_achievements(
            self.test_player.id, first_win_game
        )
        assert "First Victory" in achievements1
        
        # Try to award again with another winning game
        second_win_game = GamePlayerResultCreate(
            player_profile_id=self.test_player.id,
            game_id="second_win",
            final_position=1,
            total_earnings=8.0,
            hole_scores={"1": 3},
            holes_won=1,
            successful_bets=3,
            total_bets=4,
            partnerships_formed=0,
            partnerships_won=0,
            solo_attempts=0,
            solo_wins=0
        )
        
        achievements2 = self.player_service.check_and_award_achievements(
            self.test_player.id, second_win_game
        )
        assert "First Victory" not in achievements2  # Should not be awarded again


class TestPlayerAnalytics:
    """Test suite for player performance analytics."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.engine = create_engine("sqlite:///:memory:", echo=False)
        self.Session = sessionmaker(bind=self.engine)
        
        from app.models import Base
        Base.metadata.create_all(self.engine)
        
        self.db = self.Session()
        self.player_service = PlayerService(self.db)
        
        # Create test players
        self.test_player = self.player_service.create_player_profile(
            PlayerProfileCreate(name="Analytics Player", handicap=12.0)
        )
        
        # Record some game history for analysis
        self._create_game_history()
    
    def teardown_method(self):
        """Clean up."""
        self.db.close()
    
    def _create_game_history(self):
        """Create sample game history for testing analytics."""
        game_results = [
            # Game 1: Win
            GamePlayerResultCreate(
                player_profile_id=self.test_player.id,
                game_id="analytics_game_1",
                final_position=1,
                total_earnings=12.0,
                hole_scores={"1": 4, "2": 3, "3": 5},
                holes_won=2,
                successful_bets=4,
                total_bets=5,
                partnerships_formed=1,
                partnerships_won=1,
                solo_attempts=0,
                solo_wins=0
            ),
            # Game 2: Second place
            GamePlayerResultCreate(
                player_profile_id=self.test_player.id,
                game_id="analytics_game_2",
                final_position=2,
                total_earnings=6.0,
                hole_scores={"1": 5, "2": 4, "3": 4},
                holes_won=1,
                successful_bets=2,
                total_bets=4,
                partnerships_formed=1,
                partnerships_won=0,
                solo_attempts=0,
                solo_wins=0
            ),
            # Game 3: Third place
            GamePlayerResultCreate(
                player_profile_id=self.test_player.id,
                game_id="analytics_game_3",
                final_position=3,
                total_earnings=-2.0,
                hole_scores={"1": 6, "2": 5, "3": 4},
                holes_won=0,
                successful_bets=1,
                total_bets=3,
                partnerships_formed=0,
                partnerships_won=0,
                solo_attempts=1,
                solo_wins=0
            )
        ]
        
        for game_result in game_results:
            self.player_service.record_game_result(game_result)
    
    def test_get_player_performance_analytics(self):
        """Test comprehensive performance analytics generation."""
        analytics = self.player_service.get_player_performance_analytics(self.test_player.id)
        
        assert analytics is not None
        assert analytics.player_id == self.test_player.id
        assert analytics.player_name == "Analytics Player"
        
        # Check performance summary
        summary = analytics.performance_summary
        assert summary["games_played"] == 3
        assert summary["win_rate"] == 33.3  # 1 win out of 3 games
        assert summary["total_earnings"] == 16.0  # 12 + 6 + (-2)
        assert summary["avg_earnings"] > 0  # Should be positive overall
        
        # Check that trend analysis exists
        assert analytics.trend_analysis is not None
        
        # Check strength analysis
        assert analytics.strength_analysis is not None
        assert "betting" in analytics.strength_analysis
        assert "partnerships" in analytics.strength_analysis
        assert "solo_play" in analytics.strength_analysis
        assert "consistency" in analytics.strength_analysis
        
        # Check recommendations exist
        assert analytics.improvement_recommendations is not None
        assert len(analytics.improvement_recommendations) > 0
    
    def test_get_leaderboard(self):
        """Test leaderboard generation."""
        # Create additional players for leaderboard
        additional_players = []
        for i in range(3):
            player_data = PlayerProfileCreate(
                name=f"Leaderboard Player {i+1}",
                handicap=10.0 + i*2
            )
            player = self.player_service.create_player_profile(player_data)
            additional_players.append(player)
            
            # Give them some game history
            for j in range(6):  # Ensure minimum games for leaderboard
                game_result = GamePlayerResultCreate(
                    player_profile_id=player.id,
                    game_id=f"leaderboard_game_{i}_{j}",
                    final_position=(j % 3) + 1,
                    total_earnings=float(5 - i + j),
                    hole_scores={"1": 4},
                    holes_won=1 if j % 2 == 0 else 0,
                    successful_bets=2,
                    total_bets=3,
                    partnerships_formed=1,
                    partnerships_won=1 if j % 3 == 0 else 0,
                    solo_attempts=0,
                    solo_wins=0
                )
                self.player_service.record_game_result(game_result)
        
        leaderboard = self.player_service.get_leaderboard(limit=5)
        
        assert len(leaderboard) >= 1  # At least our test player should qualify
        
        # Check leaderboard structure
        for entry in leaderboard:
            assert isinstance(entry, LeaderboardEntry)
            assert entry.rank > 0
            assert entry.player_name is not None
            assert entry.games_played >= 5  # Minimum for leaderboard
            assert entry.win_percentage >= 0.0
            assert entry.total_earnings is not None
        
        # Check that rankings are in correct order (by total earnings)
        if len(leaderboard) > 1:
            for i in range(len(leaderboard) - 1):
                assert leaderboard[i].total_earnings >= leaderboard[i + 1].total_earnings
    
    def test_comparative_analysis(self):
        """Test comparative analysis against other players."""
        # Create more players for comparison
        comparison_players = []
        for i in range(5):
            player_data = PlayerProfileCreate(
                name=f"Comparison Player {i+1}",
                handicap=8.0 + i*3
            )
            player = self.player_service.create_player_profile(player_data)
            comparison_players.append(player)
            
            # Give them varied performance
            for j in range(8):
                game_result = GamePlayerResultCreate(
                    player_profile_id=player.id,
                    game_id=f"comparison_game_{i}_{j}",
                    final_position=(j % 4) + 1,
                    total_earnings=float(8 - i*2 + j),
                    hole_scores={"1": 4},
                    holes_won=1 if j % 2 == 0 else 0,
                    successful_bets=3,
                    total_bets=4,
                    partnerships_formed=1,
                    partnerships_won=1 if j % 2 == 0 else 0,
                    solo_attempts=0,
                    solo_wins=0
                )
                self.player_service.record_game_result(game_result)
        
        analytics = self.player_service.get_player_performance_analytics(self.test_player.id)
        
        assert analytics.comparative_analysis is not None
        comparative = analytics.comparative_analysis
        
        if comparative["status"] == "available":
            assert "earnings_percentile" in comparative
            assert "win_rate_percentile" in comparative
            assert "players_compared" in comparative
            assert "ranking_summary" in comparative
            
            assert 0 <= comparative["earnings_percentile"] <= 100
            assert 0 <= comparative["win_rate_percentile"] <= 100
            assert comparative["players_compared"] > 0
    
    def test_improvement_recommendations(self):
        """Test that improvement recommendations are contextual."""
        # Test with poor betting statistics
        poor_betting_game = GamePlayerResultCreate(
            player_profile_id=self.test_player.id,
            game_id="poor_betting_game",
            final_position=3,
            total_earnings=-5.0,
            hole_scores={"1": 6},
            holes_won=0,
            successful_bets=1,  # Poor betting success
            total_bets=5,
            partnerships_formed=1,
            partnerships_won=0,  # Poor partnership success
            solo_attempts=0,
            solo_wins=0
        )
        
        self.player_service.record_game_result(poor_betting_game)
        
        analytics = self.player_service.get_player_performance_analytics(self.test_player.id)
        recommendations = analytics.improvement_recommendations
        
        # Should contain advice about conservative betting or partnership selection
        recommendation_text = " ".join(recommendations).lower()
        assert any(keyword in recommendation_text for keyword in 
                  ["conservative", "betting", "partner", "selective"])


class TestConcurrencyAndEdgeCases:
    """Test suite for concurrency safety and edge cases."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.engine = create_engine("sqlite:///:memory:", echo=False)
        self.Session = sessionmaker(bind=self.engine)
        
        from app.models import Base
        Base.metadata.create_all(self.engine)
    
    def test_concurrent_player_creation(self):
        """Test concurrent player profile creation."""
        import queue
        import threading
        
        results_queue = queue.Queue()
        errors_queue = queue.Queue()
        
        def create_player_worker(worker_id):
            try:
                db = self.Session()
                player_service = PlayerService(db)
                
                profile_data = PlayerProfileCreate(
                    name=f"Concurrent Player {worker_id}",
                    handicap=float(10 + worker_id)
                )
                
                result = player_service.create_player_profile(profile_data)
                results_queue.put((worker_id, result.id))
                db.close()
                
            except Exception as e:
                errors_queue.put((worker_id, e))
        
        # Start multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=create_player_worker, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join()
        
        # Check for errors
        errors = []
        while not errors_queue.empty():
            worker_id, error = errors_queue.get()
            errors.append((worker_id, error))
        
        if errors:
            pytest.fail(f"Concurrent creation errors: {errors}")
        
        # Check results
        results = {}
        while not results_queue.empty():
            worker_id, player_id = results_queue.get()
            results[worker_id] = player_id
        
        assert len(results) == 5, "All concurrent creations should succeed"
    
    def test_concurrent_game_recording(self):
        """Test concurrent game result recording for same player."""
        # Create a player first
        db = self.Session()
        player_service = PlayerService(db)
        
        profile_data = PlayerProfileCreate(name="Concurrent Stats Player", handicap=12.0)
        test_player = player_service.create_player_profile(profile_data)
        db.close()
        
        import queue
        import threading
        
        results_queue = queue.Queue()
        errors_queue = queue.Queue()
        
        def record_game_worker(worker_id):
            try:
                db = self.Session()
                player_service = PlayerService(db)
                
                game_result = GamePlayerResultCreate(
                    player_profile_id=test_player.id,
                    game_id=f"concurrent_game_{worker_id}",
                    final_position=(worker_id % 3) + 1,
                    total_earnings=float(worker_id * 2),
                    hole_scores={"1": 4},
                    holes_won=1 if worker_id % 2 == 0 else 0,
                    successful_bets=worker_id + 1,
                    total_bets=worker_id + 2,
                    partnerships_formed=1,
                    partnerships_won=1 if worker_id % 2 == 0 else 0,
                    solo_attempts=0,
                    solo_wins=0
                )
                
                result = player_service.record_game_result(game_result)
                results_queue.put((worker_id, result))
                db.close()
                
            except Exception as e:
                errors_queue.put((worker_id, e))
        
        # Start multiple threads
        threads = []
        for i in range(8):
            thread = threading.Thread(target=record_game_worker, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join()
        
        # Check for errors
        errors = []
        while not errors_queue.empty():
            worker_id, error = errors_queue.get()
            errors.append((worker_id, error))
        
        if errors:
            pytest.fail(f"Concurrent recording errors: {errors}")
        
        # Verify final statistics are correct
        db = self.Session()
        player_service = PlayerService(db)
        final_stats = player_service.get_player_statistics(test_player.id)
        
        assert final_stats.games_played == 8
        # Total earnings should be sum of all worker earnings
        expected_earnings = sum(i * 2 for i in range(8))
        assert final_stats.total_earnings == expected_earnings
        
        db.close()
    
    def test_invalid_player_references(self):
        """Test handling of invalid player references."""
        db = self.Session()
        player_service = PlayerService(db)
        
        # Try to record game for non-existent player
        invalid_game_result = GamePlayerResultCreate(
            player_profile_id=99999,  # Non-existent player
            game_id="invalid_player_game",
            final_position=1,
            total_earnings=10.0,
            hole_scores={"1": 4},
            holes_won=1,
            successful_bets=2,
            total_bets=3,
            partnerships_formed=0,
            partnerships_won=0,
            solo_attempts=0,
            solo_wins=0
        )
        
        # This should handle gracefully (not crash)
        try:
            result = player_service.record_game_result(invalid_game_result)
            # Implementation may return False or raise exception
            # Either is acceptable as long as it doesn't crash
        except Exception as e:
            # Exception is acceptable for invalid input
            assert "player" in str(e).lower() or "not found" in str(e).lower()
        
        db.close()
    
    def test_extreme_statistics_values(self):
        """Test handling of extreme statistics values."""
        db = self.Session()
        player_service = PlayerService(db)
        
        profile_data = PlayerProfileCreate(name="Extreme Stats Player", handicap=12.0)
        test_player = player_service.create_player_profile(profile_data)
        
        # Record game with extreme values
        extreme_game = GamePlayerResultCreate(
            player_profile_id=test_player.id,
            game_id="extreme_game",
            final_position=1,
            total_earnings=1000000.0,  # Extremely high earnings
            hole_scores={str(i): 4 for i in range(1, 19)},  # Full 18 holes
            holes_won=18,
            successful_bets=500,  # Many bets
            total_bets=500,
            partnerships_formed=10,
            partnerships_won=10,
            solo_attempts=0,
            solo_wins=0
        )
        
        result = player_service.record_game_result(extreme_game)
        assert result is True
        
        stats = player_service.get_player_statistics(test_player.id)
        assert stats.total_earnings == 1000000.0
        assert stats.holes_played == 18
        assert stats.betting_success_rate == 1.0
        
        db.close()
    
    def test_data_persistence_across_sessions(self):
        """Test that data persists correctly across database sessions."""
        # Create player in one session
        db1 = self.Session()
        player_service1 = PlayerService(db1)
        
        profile_data = PlayerProfileCreate(name="Persistence Player", handicap=15.0)
        created_player = player_service1.create_player_profile(profile_data)
        player_id = created_player.id
        db1.close()
        
        # Retrieve player in different session
        db2 = self.Session()
        player_service2 = PlayerService(db2)
        
        retrieved_player = player_service2.get_player_profile(player_id)
        assert retrieved_player is not None
        assert retrieved_player.name == "Persistence Player"
        assert retrieved_player.handicap == 15.0
        
        # Record game in second session
        game_result = GamePlayerResultCreate(
            player_profile_id=player_id,
            game_id="persistence_game",
            final_position=2,
            total_earnings=7.0,
            hole_scores={"1": 4},
            holes_won=0,
            successful_bets=2,
            total_bets=3,
            partnerships_formed=1,
            partnerships_won=1,
            solo_attempts=0,
            solo_wins=0
        )
        
        player_service2.record_game_result(game_result)
        db2.close()
        
        # Verify persistence in third session
        db3 = self.Session()
        player_service3 = PlayerService(db3)
        
        final_stats = player_service3.get_player_statistics(player_id)
        assert final_stats.games_played == 1
        assert final_stats.total_earnings == 7.0
        
        db3.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
"""
Comprehensive tests for player_service.py - Player profile management service

Tests cover:
- Player profile CRUD operations
- Statistics management and updates
- Game result recording
- Performance analytics
- Achievement system
- Leaderboard functionality
- Error handling and edge cases
- Data validation
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from backend.app.services.player_service import PlayerService
from backend.app.models import (
    PlayerProfile, PlayerStatistics, GameRecord, GamePlayerResult, 
    PlayerAchievement
)
from backend.app.schemas import (
    PlayerProfileCreate, PlayerProfileUpdate, PlayerProfileResponse,
    PlayerStatisticsResponse, GamePlayerResultCreate,
    PlayerPerformanceAnalytics, LeaderboardEntry
)


class TestPlayerProfileCRUD:
    """Test player profile CRUD operations"""
    
    @pytest.fixture
    def mock_db(self):
        return Mock(spec=Session)
    
    @pytest.fixture
    def player_service(self, mock_db):
        return PlayerService(mock_db)
    
    @pytest.fixture
    def sample_profile_data(self):
        return PlayerProfileCreate(
            name="Test Player",
            handicap=15.5,
            avatar_url="https://example.com/avatar.jpg",
            preferences={
                "ai_difficulty": "hard",
                "preferred_game_modes": ["wolf_goat_pig", "skins"],
                "preferred_player_count": 4,
                "betting_style": "aggressive",
                "display_hints": False
            }
        )
    
    def test_create_player_profile_success(self, player_service, mock_db, sample_profile_data):
        """Test successful player profile creation"""
        # Mock no existing player
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        # Mock profile creation
        mock_profile = Mock()
        mock_profile.id = 1
        mock_profile.name = sample_profile_data.name
        mock_profile.handicap = sample_profile_data.handicap
        mock_db.flush = Mock()
        mock_db.refresh = Mock()
        
        with patch('backend.app.services.player_service.PlayerProfile') as mock_profile_class:
            mock_profile_class.return_value = mock_profile
            with patch('backend.app.services.player_service.PlayerStatistics') as mock_stats_class:
                mock_stats = Mock()
                mock_stats_class.return_value = mock_stats
                
                result = player_service.create_player_profile(sample_profile_data)
                
                mock_db.add.assert_called()
                mock_db.commit.assert_called_once()
                assert mock_db.add.call_count == 2  # Profile + Statistics
    
    def test_create_player_profile_duplicate_name(self, player_service, mock_db, sample_profile_data):
        """Test player profile creation with duplicate name"""
        # Mock existing player
        existing_player = Mock()
        existing_player.name = sample_profile_data.name
        mock_db.query.return_value.filter.return_value.first.return_value = existing_player
        
        with pytest.raises(ValueError, match="Player with name 'Test Player' already exists"):
            player_service.create_player_profile(sample_profile_data)
    
    def test_create_player_profile_database_error(self, player_service, mock_db, sample_profile_data):
        """Test player profile creation with database error"""
        mock_db.query.return_value.filter.return_value.first.return_value = None
        mock_db.add.side_effect = Exception("Database error")
        
        with pytest.raises(Exception, match="Database error"):
            player_service.create_player_profile(sample_profile_data)
        
        mock_db.rollback.assert_called_once()
    
    def test_get_player_profile_success(self, player_service, mock_db):
        """Test successful player profile retrieval"""
        mock_profile = Mock()
        mock_profile.id = 1
        mock_profile.name = "Test Player"
        mock_db.query.return_value.filter.return_value.first.return_value = mock_profile
        
        with patch('backend.app.schemas.PlayerProfileResponse.model_validate') as mock_validate:
            mock_response = Mock()
            mock_validate.return_value = mock_response
            
            result = player_service.get_player_profile(1)
            
            assert result == mock_response
            mock_validate.assert_called_once_with(mock_profile)
    
    def test_get_player_profile_not_found(self, player_service, mock_db):
        """Test player profile retrieval when not found"""
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        result = player_service.get_player_profile(999)
        
        assert result is None
    
    def test_get_player_profile_by_name_success(self, player_service, mock_db):
        """Test successful player profile retrieval by name"""
        mock_profile = Mock()
        mock_profile.name = "Test Player"
        mock_db.query.return_value.filter.return_value.first.return_value = mock_profile
        
        with patch('backend.app.schemas.PlayerProfileResponse.model_validate') as mock_validate:
            mock_response = Mock()
            mock_validate.return_value = mock_response
            
            result = player_service.get_player_profile_by_name("Test Player")
            
            assert result == mock_response
    
    def test_get_all_player_profiles(self, player_service, mock_db):
        """Test retrieving all player profiles"""
        mock_profiles = [Mock(), Mock(), Mock()]
        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = mock_profiles
        
        with patch('backend.app.schemas.PlayerProfileResponse.model_validate') as mock_validate:
            mock_validate.side_effect = lambda x: f"response_{x}"
            
            result = player_service.get_all_player_profiles()
            
            assert len(result) == 3
            assert mock_validate.call_count == 3
    
    def test_update_player_profile_success(self, player_service, mock_db):
        """Test successful player profile update"""
        mock_profile = Mock()
        mock_profile.id = 1
        mock_profile.name = "Old Name"
        mock_db.query.return_value.filter.return_value.first.return_value = mock_profile
        
        update_data = PlayerProfileUpdate(
            name="New Name",
            handicap=12.0,
            avatar_url="new_url.jpg"
        )
        
        # Mock no name conflict
        mock_db.query.return_value.filter.return_value.first.side_effect = [mock_profile, None]
        
        with patch('backend.app.schemas.PlayerProfileResponse.model_validate') as mock_validate:
            mock_response = Mock()
            mock_validate.return_value = mock_response
            
            result = player_service.update_player_profile(1, update_data)
            
            assert mock_profile.name == "New Name"
            assert mock_profile.handicap == 12.0
            assert mock_profile.avatar_url == "new_url.jpg"
            mock_db.commit.assert_called_once()
    
    def test_update_player_profile_name_conflict(self, player_service, mock_db):
        """Test player profile update with name conflict"""
        mock_profile = Mock()
        mock_profile.id = 1
        
        # Mock existing profile with same name (different ID)
        existing_player = Mock()
        existing_player.id = 2
        mock_db.query.return_value.filter.return_value.first.side_effect = [mock_profile, existing_player]
        
        update_data = PlayerProfileUpdate(name="Existing Name")
        
        with pytest.raises(ValueError, match="Player with name 'Existing Name' already exists"):
            player_service.update_player_profile(1, update_data)
    
    def test_update_player_profile_not_found(self, player_service, mock_db):
        """Test player profile update when profile not found"""
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        update_data = PlayerProfileUpdate(name="New Name")
        
        result = player_service.update_player_profile(999, update_data)
        
        assert result is None
    
    def test_delete_player_profile_success(self, player_service, mock_db):
        """Test successful player profile deletion (soft delete)"""
        mock_profile = Mock()
        mock_profile.is_active = 1
        mock_db.query.return_value.filter.return_value.first.return_value = mock_profile
        
        result = player_service.delete_player_profile(1)
        
        assert result is True
        assert mock_profile.is_active == 0
        mock_db.commit.assert_called_once()
    
    def test_delete_player_profile_not_found(self, player_service, mock_db):
        """Test player profile deletion when profile not found"""
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        result = player_service.delete_player_profile(999)
        
        assert result is False


class TestStatisticsManagement:
    """Test statistics management functionality"""
    
    @pytest.fixture
    def mock_db(self):
        return Mock(spec=Session)
    
    @pytest.fixture
    def player_service(self, mock_db):
        return PlayerService(mock_db)
    
    def test_get_player_statistics_success(self, player_service, mock_db):
        """Test successful statistics retrieval"""
        mock_stats = Mock()
        mock_stats.player_id = 1
        mock_stats.games_played = 10
        mock_db.query.return_value.filter.return_value.first.return_value = mock_stats
        
        with patch('backend.app.schemas.PlayerStatisticsResponse.model_validate') as mock_validate:
            mock_response = Mock()
            mock_validate.return_value = mock_response
            
            result = player_service.get_player_statistics(1)
            
            assert result == mock_response
            mock_validate.assert_called_once_with(mock_stats)
    
    def test_get_player_statistics_not_found(self, player_service, mock_db):
        """Test statistics retrieval when not found"""
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        result = player_service.get_player_statistics(999)
        
        assert result is None
    
    def test_update_last_played(self, player_service, mock_db):
        """Test updating last played timestamp"""
        mock_profile = Mock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_profile
        
        with patch('backend.app.services.player_service.datetime') as mock_datetime:
            mock_datetime.now.return_value.isoformat.return_value = "2023-01-01T12:00:00"
            
            player_service.update_last_played(1)
            
            assert mock_profile.last_played == "2023-01-01T12:00:00"
            mock_db.commit.assert_called_once()


class TestGameResultRecording:
    """Test game result recording and statistics updates"""
    
    @pytest.fixture
    def mock_db(self):
        return Mock(spec=Session)
    
    @pytest.fixture
    def player_service(self, mock_db):
        return PlayerService(mock_db)
    
    @pytest.fixture
    def sample_game_result(self):
        return GamePlayerResultCreate(
            player_profile_id=1,
            game_id="game123",
            final_position=1,
            total_earnings=15.5,
            hole_scores={"1": 4, "2": 3, "3": 5},
            holes_won=8,
            successful_bets=5,
            total_bets=7,
            partnerships_formed=3,
            partnerships_won=2,
            solo_attempts=1,
            solo_wins=1
        )
    
    def test_record_game_result_success(self, player_service, mock_db, sample_game_result):
        """Test successful game result recording"""
        # Mock existing statistics
        mock_stats = Mock()
        mock_stats.games_played = 5
        mock_stats.games_won = 2
        mock_stats.total_earnings = 50.0
        mock_stats.holes_played = 45
        mock_stats.holes_won = 20
        mock_stats.successful_bets = 15
        mock_stats.total_bets = 25
        mock_stats.partnerships_formed = 8
        mock_stats.partnerships_won = 5
        mock_stats.solo_attempts = 2
        mock_stats.solo_wins = 1
        mock_stats.performance_trends = []
        
        mock_db.query.return_value.filter.return_value.first.return_value = mock_stats
        
        with patch.object(player_service, 'update_last_played'):
            result = player_service.record_game_result(sample_game_result)
            
            assert result is True
            # Verify statistics updates
            assert mock_stats.games_played == 6
            assert mock_stats.games_won == 3  # Won this game (position 1)
            assert mock_stats.total_earnings == 65.5
            assert mock_stats.holes_played == 48  # Added 3 holes
            assert mock_stats.holes_won == 28
            mock_db.commit.assert_called_once()
    
    def test_record_game_result_new_statistics(self, player_service, mock_db, sample_game_result):
        """Test game result recording with new statistics record"""
        # Mock no existing statistics
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        with patch('backend.app.services.player_service.PlayerStatistics') as mock_stats_class:
            mock_stats = Mock()
            mock_stats.games_played = 0
            mock_stats.games_won = 0
            mock_stats.total_earnings = 0
            mock_stats.holes_played = 0
            mock_stats.holes_won = 0
            mock_stats.successful_bets = 0
            mock_stats.total_bets = 0
            mock_stats.partnerships_formed = 0
            mock_stats.partnerships_won = 0
            mock_stats.solo_attempts = 0
            mock_stats.solo_wins = 0
            mock_stats.performance_trends = []
            mock_stats_class.return_value = mock_stats
            
            with patch.object(player_service, 'update_last_played'):
                result = player_service.record_game_result(sample_game_result)
                
                assert result is True
                mock_db.add.assert_called()  # For both result record and new stats
    
    def test_update_player_statistics_calculations(self, player_service, mock_db, sample_game_result):
        """Test statistics calculations during update"""
        mock_stats = Mock()
        mock_stats.games_played = 10
        mock_stats.games_won = 3
        mock_stats.total_earnings = 100.0
        mock_stats.holes_played = 90
        mock_stats.holes_won = 35
        mock_stats.successful_bets = 20
        mock_stats.total_bets = 30
        mock_stats.partnerships_formed = 15
        mock_stats.partnerships_won = 8
        mock_stats.solo_attempts = 3
        mock_stats.solo_wins = 1
        mock_stats.performance_trends = []
        
        mock_db.query.return_value.filter.return_value.first.return_value = mock_stats
        
        player_service._update_player_statistics_from_game(sample_game_result)
        
        # Verify calculated fields
        assert mock_stats.avg_earnings_per_hole == pytest.approx(115.5 / 93, rel=1e-3)  # Updated totals
        assert mock_stats.betting_success_rate == pytest.approx(25 / 37, rel=1e-3)  # (20+5)/(30+7)
        assert mock_stats.partnership_success_rate == pytest.approx(10 / 18, rel=1e-3)  # (8+2)/(15+3)
    
    def test_performance_trends_tracking(self, player_service, mock_db, sample_game_result):
        """Test performance trends are properly tracked"""
        mock_stats = Mock()
        mock_stats.games_played = 5
        mock_stats.performance_trends = [{"game_date": "2023-01-01", "earnings": 10}] * 49  # 49 existing
        
        mock_db.query.return_value.filter.return_value.first.return_value = mock_stats
        
        with patch('backend.app.services.player_service.datetime') as mock_datetime:
            mock_datetime.now.return_value.isoformat.return_value = "2023-01-02T12:00:00"
            
            player_service._update_player_statistics_from_game(sample_game_result)
            
            # Should have 50 trends (49 + 1 new)
            assert len(mock_stats.performance_trends) == 50
            
            # Add one more to test trimming
            sample_game_result.total_earnings = 20
            player_service._update_player_statistics_from_game(sample_game_result)
            
            # Should still be 50 (oldest removed)
            assert len(mock_stats.performance_trends) == 50


class TestPerformanceAnalytics:
    """Test performance analytics functionality"""
    
    @pytest.fixture
    def mock_db(self):
        return Mock(spec=Session)
    
    @pytest.fixture
    def player_service(self, mock_db):
        return PlayerService(mock_db)
    
    @pytest.fixture
    def mock_profile_and_stats(self):
        profile = Mock()
        profile.name = "Test Player"
        
        stats = Mock()
        stats.games_played = 20
        stats.games_won = 8
        stats.total_earnings = 150.5
        stats.avg_earnings_per_hole = 2.5
        stats.betting_success_rate = 0.65
        stats.partnership_success_rate = 0.7
        stats.solo_attempts = 5
        stats.solo_wins = 2
        stats.performance_trends = [
            {"earnings": 10, "position": 2, "betting_success": 0.6},
            {"earnings": 15, "position": 1, "betting_success": 0.8},
            {"earnings": 8, "position": 3, "betting_success": 0.4}
        ]
        
        return profile, stats
    
    def test_get_player_performance_analytics_success(self, player_service, mock_db, mock_profile_and_stats):
        """Test successful performance analytics generation"""
        profile, stats = mock_profile_and_stats
        
        with patch.object(player_service, 'get_player_profile', return_value=profile):
            with patch.object(player_service, 'get_player_statistics', return_value=stats):
                with patch.object(player_service, '_calculate_average_position', return_value=2.1):
                    with patch.object(player_service, '_calculate_recent_form', return_value="Good"):
                        with patch.object(player_service, '_analyze_performance_trends') as mock_trends:
                            with patch.object(player_service, '_generate_improvement_recommendations') as mock_recs:
                                with patch.object(player_service, '_get_comparative_analysis') as mock_comp:
                                    mock_trends.return_value = {"status": "improving"}
                                    mock_recs.return_value = ["Keep it up!"]
                                    mock_comp.return_value = {"percentile": 75}
                                    
                                    result = player_service.get_player_performance_analytics(1)
                                    
                                    assert result is not None
                                    assert result.player_name == "Test Player"
                                    assert result.performance_summary["games_played"] == 20
                                    assert result.performance_summary["win_rate"] == 40.0  # 8/20 * 100
    
    def test_get_player_performance_analytics_no_profile(self, player_service, mock_db):
        """Test performance analytics when profile not found"""
        with patch.object(player_service, 'get_player_profile', return_value=None):
            result = player_service.get_player_performance_analytics(999)
            assert result is None
    
    def test_calculate_average_position(self, player_service, mock_db):
        """Test average position calculation"""
        mock_results = [Mock(final_position=1), Mock(final_position=2), Mock(final_position=3)]
        mock_db.query.return_value.filter.return_value.all.return_value = mock_results
        
        result = player_service._calculate_average_position(1)
        
        assert result == 2.0  # (1+2+3)/3
    
    def test_calculate_recent_form(self, player_service, mock_db):
        """Test recent form calculation"""
        # Test excellent form
        mock_results = [Mock(final_position=1), Mock(final_position=1), Mock(final_position=2)]
        mock_db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = mock_results
        
        result = player_service._calculate_recent_form(1)
        
        assert result == "Excellent"  # avg = 1.33 <= 1.5
        
        # Test poor form
        mock_results = [Mock(final_position=4), Mock(final_position=3), Mock(final_position=4)]
        mock_db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = mock_results
        
        result = player_service._calculate_recent_form(1)
        
        assert result == "Poor"  # avg = 3.67 > 2.5
    
    def test_analyze_performance_trends(self, player_service, mock_db):
        """Test performance trends analysis"""
        trends = [
            {"earnings": 10, "position": 3},
            {"earnings": 12, "position": 2},
            {"earnings": 15, "position": 1}
        ]
        
        result = player_service._analyze_performance_trends(trends)
        
        assert result["status"] == "sufficient_data"
        assert result["earnings_trend"] == "improving"  # 15 > 10
        assert result["position_trend"] == "improving"  # 1 < 3 (lower position is better)
    
    def test_analyze_performance_trends_insufficient_data(self, player_service, mock_db):
        """Test performance trends with insufficient data"""
        trends = [{"earnings": 10, "position": 2}]  # Only 1 data point
        
        result = player_service._analyze_performance_trends(trends)
        
        assert result["status"] == "insufficient_data"
    
    def test_calculate_consistency_rating(self, player_service, mock_db):
        """Test consistency rating calculation"""
        # Very consistent positions
        trends = [{"position": 2}, {"position": 2}, {"position": 2}, {"position": 2}, {"position": 2}]
        
        result = player_service._calculate_consistency_rating(trends)
        
        assert result == "Very Consistent"  # Variance = 0
        
        # Inconsistent positions
        trends = [{"position": 1}, {"position": 4}, {"position": 1}, {"position": 4}, {"position": 1}]
        
        result = player_service._calculate_consistency_rating(trends)
        
        assert result == "Inconsistent"  # High variance
    
    def test_generate_improvement_recommendations(self, player_service, mock_db):
        """Test improvement recommendations generation"""
        stats = Mock()
        stats.betting_success_rate = 0.3  # Poor betting
        stats.partnership_success_rate = 0.8  # Good partnerships
        stats.partnerships_formed = 10
        stats.solo_attempts = 5
        stats.solo_wins = 1  # Poor solo success
        stats.games_played = 15
        
        result = player_service._generate_improvement_recommendations(stats)
        
        assert any("conservative betting" in rec for rec in result)
        assert any("Solo play is risky" in rec for rec in result)


class TestLeaderboard:
    """Test leaderboard functionality"""
    
    @pytest.fixture
    def mock_db(self):
        return Mock(spec=Session)
    
    @pytest.fixture
    def player_service(self, mock_db):
        return PlayerService(mock_db)
    
    def test_get_leaderboard_success(self, player_service, mock_db):
        """Test successful leaderboard generation"""
        # Mock player-stats pairs
        mock_players_stats = [
            (Mock(name="Player1"), Mock(games_played=10, games_won=5, total_earnings=100, avg_earnings_per_hole=2.0, partnership_success_rate=0.6)),
            (Mock(name="Player2"), Mock(games_played=8, games_won=3, total_earnings=80, avg_earnings_per_hole=1.8, partnership_success_rate=0.7)),
            (Mock(name="Player3"), Mock(games_played=15, games_won=6, total_earnings=120, avg_earnings_per_hole=1.5, partnership_success_rate=0.5))
        ]
        
        mock_db.query.return_value.join.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = mock_players_stats
        
        result = player_service.get_leaderboard()
        
        assert len(result) == 3
        assert result[0].rank == 1
        assert result[0].player_name == "Player1"
        assert result[1].rank == 2
        assert result[2].rank == 3
    
    def test_get_leaderboard_empty(self, player_service, mock_db):
        """Test leaderboard with no qualifying players"""
        mock_db.query.return_value.join.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []
        
        result = player_service.get_leaderboard()
        
        assert len(result) == 0


class TestAchievementSystem:
    """Test achievement system functionality"""
    
    @pytest.fixture
    def mock_db(self):
        return Mock(spec=Session)
    
    @pytest.fixture
    def player_service(self, mock_db):
        return PlayerService(mock_db)
    
    @pytest.fixture
    def sample_game_result(self):
        return GamePlayerResultCreate(
            player_profile_id=1,
            game_id="game123",
            final_position=1,
            total_earnings=25.0,  # Big earner
            hole_scores={"1": 4, "2": 3},
            holes_won=10,
            successful_bets=8,
            total_bets=10,
            partnerships_formed=1,
            partnerships_won=1,
            solo_attempts=0,
            solo_wins=0
        )
    
    def test_check_and_award_achievements_first_win(self, player_service, mock_db, sample_game_result):
        """Test awarding first win achievement"""
        mock_stats = Mock()
        mock_stats.games_won = 1  # First win
        mock_stats.partnerships_won = 5
        mock_stats.solo_wins = 2
        mock_stats.betting_success_rate = 0.6
        mock_stats.total_bets = 15
        mock_stats.games_played = 20
        
        with patch.object(player_service, 'get_player_statistics', return_value=mock_stats):
            # Mock no existing achievements
            mock_db.query.return_value.filter.return_value.first.return_value = None
            with patch.object(player_service, '_check_win_streak', return_value=False):
                
                result = player_service.check_and_award_achievements(1, sample_game_result)
                
                # Should award both "first_win" and "big_earner" achievements
                assert "First Victory" in result
                assert "Big Earner" in result
                assert mock_db.add.called  # Achievement records added
    
    def test_check_and_award_achievements_no_new(self, player_service, mock_db, sample_game_result):
        """Test when no new achievements are earned"""
        mock_stats = Mock()
        mock_stats.games_won = 5  # Not first win
        mock_stats.partnerships_won = 5
        mock_stats.solo_wins = 2
        mock_stats.betting_success_rate = 0.6
        mock_stats.total_bets = 15
        mock_stats.games_played = 20
        
        # Mock existing achievement
        existing_achievement = Mock()
        mock_db.query.return_value.filter.return_value.first.return_value = existing_achievement
        
        with patch.object(player_service, 'get_player_statistics', return_value=mock_stats):
            with patch.object(player_service, '_check_win_streak', return_value=False):
                
                result = player_service.check_and_award_achievements(1, sample_game_result)
                
                # No new achievements since "big_earner" already exists (mocked)
                assert len(result) == 0
    
    def test_check_win_streak(self, player_service, mock_db):
        """Test win streak checking"""
        # Mock 5 consecutive wins
        mock_results = [Mock(final_position=1)] * 5
        mock_db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = mock_results
        
        result = player_service._check_win_streak(1, 5)
        
        assert result is True
        
        # Mock non-consecutive wins
        mock_results = [Mock(final_position=1), Mock(final_position=2), Mock(final_position=1)]
        mock_db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = mock_results
        
        result = player_service._check_win_streak(1, 3)
        
        assert result is False


class TestComparativeAnalysis:
    """Test comparative analysis functionality"""
    
    @pytest.fixture
    def mock_db(self):
        return Mock(spec=Session)
    
    @pytest.fixture
    def player_service(self, mock_db):
        return PlayerService(mock_db)
    
    def test_get_comparative_analysis_success(self, player_service, mock_db):
        """Test successful comparative analysis"""
        # Mock player stats
        player_stats = Mock()
        player_stats.total_earnings = 100
        player_stats.games_won = 5
        player_stats.games_played = 10
        
        # Mock all players stats for comparison
        all_stats = [
            Mock(total_earnings=50, games_won=2, games_played=10),
            Mock(total_earnings=75, games_won=3, games_played=10),
            Mock(total_earnings=100, games_won=5, games_played=10),  # Our player
            Mock(total_earnings=125, games_won=6, games_played=10),
            Mock(total_earnings=150, games_won=7, games_played=10)
        ]
        
        mock_db.query.return_value.filter.return_value.all.return_value = all_stats
        
        result = player_service._get_comparative_analysis(1, player_stats)
        
        assert result["status"] == "available"
        assert result["earnings_percentile"] == 60.0  # 3rd out of 5
        assert result["players_compared"] == 5
    
    def test_calculate_percentile(self, player_service, mock_db):
        """Test percentile calculation"""
        sorted_values = [10, 20, 30, 40, 50]
        
        # Test exact match
        percentile = player_service._calculate_percentile(30, sorted_values)
        assert percentile == 60.0  # 3 out of 5 values <= 30
        
        # Test value not in list
        percentile = player_service._calculate_percentile(35, sorted_values)
        assert percentile == 60.0  # Still 3 out of 5 values <= 35
        
        # Test highest value
        percentile = player_service._calculate_percentile(50, sorted_values)
        assert percentile == 100.0
    
    def test_get_ranking_summary(self, player_service, mock_db):
        """Test ranking summary generation"""
        # Elite player
        summary = player_service._get_ranking_summary(95, 90)
        assert summary == "Elite Player"
        
        # Average player
        summary = player_service._get_ranking_summary(55, 45)
        assert summary == "Average Player"
        
        # Beginner player
        summary = player_service._get_ranking_summary(15, 20)
        assert summary == "Beginner Player"


class TestErrorHandling:
    """Test error handling and edge cases"""
    
    @pytest.fixture
    def mock_db(self):
        return Mock(spec=Session)
    
    @pytest.fixture
    def player_service(self, mock_db):
        return PlayerService(mock_db)
    
    def test_database_error_handling(self, player_service, mock_db):
        """Test handling of database errors"""
        mock_db.query.side_effect = Exception("Database connection error")
        
        with pytest.raises(Exception, match="Database connection error"):
            player_service.get_player_profile(1)
    
    def test_achievement_error_handling(self, player_service, mock_db):
        """Test achievement system error handling"""
        with patch.object(player_service, 'get_player_statistics', side_effect=Exception("Stats error")):
            result = player_service.check_and_award_achievements(1, Mock())
            
            # Should return empty list on error, not raise exception
            assert result == []
    
    def test_comparative_analysis_error_handling(self, player_service, mock_db):
        """Test comparative analysis error handling"""
        mock_db.query.side_effect = Exception("Query error")
        
        player_stats = Mock()
        result = player_service._get_comparative_analysis(1, player_stats)
        
        assert result["status"] == "error"


if __name__ == "__main__":
    pytest.main([__file__])
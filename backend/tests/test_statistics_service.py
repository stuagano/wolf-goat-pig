"""
Unit tests for StatisticsService

Tests advanced statistical analysis including:
- Performance metrics calculation
- Trend analysis
- Player insights and recommendations
- Skill rating calculations
- Head-to-head comparisons
- Special event analytics
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock, patch
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.services.statistics_service import (
    StatisticsService,
    TrendPoint,
    PerformanceMetric,
    InsightRecommendation,
)
from app.models import Base, PlayerProfile, PlayerStatistics, GamePlayerResult, GameRecord


# Test database setup
TEST_DATABASE_URL = "sqlite:///./test_statistics.db"
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
def test_player_with_stats(db):
    """Create a test player with comprehensive statistics."""
    player = PlayerProfile(
        name="Test Player",
        email="test@example.com",
        handicap=15.0,
        is_active=1,
        is_ai=0,
        created_at=datetime.now().isoformat()
    )
    db.add(player)
    db.flush()

    stats = PlayerStatistics(
        player_id=player.id,
        games_played=25,
        games_won=10,
        total_earnings=500.0,
        avg_earnings_per_hole=2.5,
        betting_success_rate=0.65,
        total_bets=100,
        successful_bets=65,
        partnership_success_rate=0.6,
        partnerships_formed=20,
        partnerships_won=12,
        solo_attempts=10,
        solo_wins=3,
        holes_played=450,
        holes_won=100,
        ping_pong_count=5,
        ping_pong_wins=3,
        invisible_aardvark_appearances=2,
        invisible_aardvark_wins=1,
        duncan_attempts=3,
        duncan_wins=1,
        tunkarri_attempts=2,
        tunkarri_wins=1,
        big_dick_attempts=4,
        big_dick_wins=2,
        eagles=2,
        birdies=30,
        pars=180,
        bogeys=150,
        double_bogeys=60,
        worse_than_double=28,
        last_updated=datetime.now().isoformat()
    )
    db.add(stats)
    db.commit()

    return player, stats


@pytest.fixture
def test_game_results(db, test_player_with_stats):
    """Create test game results for trend analysis."""
    player, _ = test_player_with_stats
    results = []

    for i in range(10):
        game_record = GameRecord(
            game_id=f"test-game-{i}",
            game_mode="wolf_goat_pig",
            player_count=4,
            total_holes_played=18,
            course_name="Test Course",
            created_at=(datetime.now() - timedelta(days=10 - i)).isoformat(),
            completed_at=datetime.now().isoformat()
        )
        db.add(game_record)
        db.flush()

        result = GamePlayerResult(
            game_record_id=game_record.id,
            player_profile_id=player.id,
            player_name=player.name,
            final_position=((i % 4) + 1),  # Positions 1-4
            total_earnings=5.0 + i * 2,  # Increasing earnings
            holes_won=3 + (i % 3),
            successful_bets=3 + (i % 2),
            total_bets=5,
            partnerships_formed=1,
            partnerships_won=1 if i % 2 == 0 else 0,
            solo_attempts=1 if i % 3 == 0 else 0,
            solo_wins=1 if i % 6 == 0 else 0,
            created_at=(datetime.now() - timedelta(days=10 - i)).isoformat()
        )
        db.add(result)
        results.append(result)

    db.commit()
    return results


@pytest.fixture
def multiple_players(db):
    """Create multiple players for comparative analysis."""
    players = []
    for i in range(5):
        player = PlayerProfile(
            name=f"Player {i+1}",
            email=f"player{i+1}@example.com",
            handicap=10.0 + i * 2,
            is_active=1,
            is_ai=0,
            created_at=datetime.now().isoformat()
        )
        db.add(player)
        db.flush()

        stats = PlayerStatistics(
            player_id=player.id,
            games_played=20 + i * 5,
            games_won=5 + i * 2,
            total_earnings=200.0 + i * 100,
            avg_earnings_per_hole=2.0 + i * 0.5,
            betting_success_rate=0.4 + i * 0.1,
            total_bets=50 + i * 10,
            successful_bets=20 + i * 5,
            partnership_success_rate=0.3 + i * 0.1,
            partnerships_formed=10 + i,
            partnerships_won=3 + i,
            solo_attempts=5,
            solo_wins=1,
            last_updated=datetime.now().isoformat()
        )
        db.add(stats)
        players.append(player)

    db.commit()
    return players


class TestPerformanceMetrics:
    """Test advanced performance metrics calculation."""

    def test_get_advanced_metrics_returns_expected_keys(self, db, test_player_with_stats):
        """Test that advanced metrics returns expected metric types."""
        player, _ = test_player_with_stats
        service = StatisticsService(db)

        metrics = service.get_advanced_player_metrics(player.id)

        expected_keys = [
            "win_rate",
            "earnings_efficiency",
            "betting_accuracy",
            "partnership_synergy",
            "consistency"
        ]

        for key in expected_keys:
            assert key in metrics

    def test_metrics_have_correct_structure(self, db, test_player_with_stats):
        """Test that metrics have correct PerformanceMetric structure."""
        player, _ = test_player_with_stats
        service = StatisticsService(db)

        metrics = service.get_advanced_player_metrics(player.id)

        for key, metric in metrics.items():
            assert hasattr(metric, 'name')
            assert hasattr(metric, 'value')
            assert hasattr(metric, 'percentile')
            assert hasattr(metric, 'trend')
            assert hasattr(metric, 'confidence')
            assert hasattr(metric, 'description')

    def test_win_rate_calculation(self, db, test_player_with_stats):
        """Test win rate metric calculation."""
        player, stats = test_player_with_stats
        service = StatisticsService(db)

        metrics = service.get_advanced_player_metrics(player.id)

        expected_win_rate = (10 / 25) * 100  # 40%
        assert metrics["win_rate"].value == expected_win_rate

    def test_metrics_for_nonexistent_player(self, db):
        """Test metrics for non-existent player returns empty dict."""
        service = StatisticsService(db)

        metrics = service.get_advanced_player_metrics(99999)

        assert metrics == {}


class TestPerformanceTrends:
    """Test performance trend analysis."""

    def test_get_performance_trends(self, db, test_player_with_stats, test_game_results):
        """Test getting performance trends over time."""
        player, _ = test_player_with_stats
        service = StatisticsService(db)

        trends = service.get_performance_trends(player.id, days=30)

        assert "earnings" in trends
        assert "position" in trends
        assert "betting_success" in trends
        assert "holes_won" in trends

    def test_trend_points_have_correct_structure(self, db, test_player_with_stats, test_game_results):
        """Test that trend points have correct structure."""
        player, _ = test_player_with_stats
        service = StatisticsService(db)

        trends = service.get_performance_trends(player.id, days=30)

        if trends["earnings"]:
            point = trends["earnings"][0]
            assert hasattr(point, 'timestamp') or 'timestamp' in dir(point)
            assert hasattr(point, 'value') or 'value' in dir(point)

    def test_trends_with_no_data(self, db):
        """Test trends returns empty lists when no data."""
        # Create player without game results
        player = PlayerProfile(
            name="New Player",
            email="new@example.com",
            handicap=18.0,
            created_at=datetime.now().isoformat()
        )
        db.add(player)
        db.commit()

        service = StatisticsService(db)
        trends = service.get_performance_trends(player.id, days=30)

        assert trends.get("earnings", []) == []


class TestPlayerInsights:
    """Test player insights and recommendations."""

    def test_get_insights_structure(self, db, test_player_with_stats):
        """Test that insights have correct structure."""
        player, _ = test_player_with_stats
        service = StatisticsService(db)

        insights = service.get_player_insights(player.id)

        for insight in insights:
            assert hasattr(insight, 'category')
            assert hasattr(insight, 'priority')
            assert hasattr(insight, 'title')
            assert hasattr(insight, 'description')
            assert hasattr(insight, 'suggested_actions')

    def test_insights_for_low_betting_accuracy(self, db):
        """Test insights generated for poor betting performance."""
        player = PlayerProfile(
            name="Poor Bettor",
            email="poor@example.com",
            handicap=18.0,
            created_at=datetime.now().isoformat()
        )
        db.add(player)
        db.flush()

        stats = PlayerStatistics(
            player_id=player.id,
            games_played=30,
            games_won=5,
            betting_success_rate=0.2,  # Very low
            total_bets=100,
            successful_bets=20,
            partnership_success_rate=0.5,
            partnerships_formed=10,
            solo_attempts=5,
            solo_wins=0,
            last_updated=datetime.now().isoformat()
        )
        db.add(stats)
        db.commit()

        service = StatisticsService(db)
        insights = service.get_player_insights(player.id)

        # Should have betting improvement insight
        betting_insights = [i for i in insights if i.category == "betting"]
        assert len(betting_insights) >= 1

    def test_insights_for_new_player(self, db):
        """Test insights for player with few games."""
        player = PlayerProfile(
            name="New Player",
            email="newbie@example.com",
            handicap=18.0,
            created_at=datetime.now().isoformat()
        )
        db.add(player)
        db.flush()

        stats = PlayerStatistics(
            player_id=player.id,
            games_played=3,  # Very few games
            games_won=1,
            last_updated=datetime.now().isoformat()
        )
        db.add(stats)
        db.commit()

        service = StatisticsService(db)
        insights = service.get_player_insights(player.id)

        # Should suggest playing more games
        experience_insights = [i for i in insights if i.category == "experience"]
        assert len(experience_insights) >= 1


class TestSkillRating:
    """Test skill rating calculations."""

    def test_calculate_skill_rating(self, db, test_player_with_stats):
        """Test basic skill rating calculation."""
        player, _ = test_player_with_stats
        service = StatisticsService(db)

        rating = service.calculate_skill_rating(player.id)

        assert "overall" in rating
        assert "confidence" in rating
        assert "win_component" in rating
        assert "earnings_component" in rating
        assert "betting_component" in rating
        assert "partnership_component" in rating

    def test_skill_rating_default_for_new_player(self, db):
        """Test default skill rating for player without stats."""
        service = StatisticsService(db)

        rating = service.calculate_skill_rating(99999)

        assert rating["overall"] == 1200.0
        assert rating["confidence"] == 0.0

    def test_skill_rating_confidence_increases_with_games(self, db, multiple_players):
        """Test that confidence increases with more games played."""
        service = StatisticsService(db)

        ratings = []
        for player in multiple_players:
            rating = service.calculate_skill_rating(player.id)
            ratings.append(rating)

        # Players with more games should have higher confidence
        # (Players are created with increasing games_played)
        for i in range(len(ratings) - 1):
            if ratings[i]["games_played"] < ratings[i + 1]["games_played"]:
                assert ratings[i]["confidence"] <= ratings[i + 1]["confidence"]


class TestHeadToHead:
    """Test head-to-head comparison functionality."""

    def test_head_to_head_no_games(self, db, multiple_players):
        """Test head-to-head when players haven't played together."""
        service = StatisticsService(db)

        result = service.get_head_to_head(
            multiple_players[0].id,
            multiple_players[1].id
        )

        assert result["status"] == "no_games"
        assert result["games_together"] == 0

    def test_head_to_head_with_games(self, db, test_player_with_stats, test_game_results):
        """Test head-to-head with shared games."""
        player, _ = test_player_with_stats

        # Create an opponent who played same games
        opponent = PlayerProfile(
            name="Opponent",
            email="opponent@example.com",
            handicap=18.0,
            created_at=datetime.now().isoformat()
        )
        db.add(opponent)
        db.flush()

        # Add opponent to same games
        for result in test_game_results:
            opponent_result = GamePlayerResult(
                game_record_id=result.game_record_id,
                player_profile_id=opponent.id,
                player_name=opponent.name,
                final_position=2,  # Always second
                total_earnings=5.0,
                holes_won=2,
                successful_bets=2,
                total_bets=4,
                created_at=result.created_at
            )
            db.add(opponent_result)

        db.commit()

        service = StatisticsService(db)
        h2h = service.get_head_to_head(player.id, opponent.id)

        assert h2h["status"] == "available"
        assert h2h["games_together"] == 10
        assert "wins" in h2h
        assert "losses" in h2h
        assert "win_rate" in h2h

    def test_get_all_head_to_head(self, db, test_player_with_stats, test_game_results):
        """Test getting all head-to-head records."""
        player, _ = test_player_with_stats
        service = StatisticsService(db)

        all_h2h = service.get_all_head_to_head(player.id)

        assert isinstance(all_h2h, dict)


class TestStreakAnalysis:
    """Test streak analysis functionality."""

    def test_streak_analysis_structure(self, db, test_player_with_stats, test_game_results):
        """Test streak analysis returns correct structure."""
        player, _ = test_player_with_stats
        service = StatisticsService(db)

        analysis = service.get_streak_analysis(player.id)

        assert analysis["status"] == "available"
        assert "current_streak" in analysis
        assert "best_win_streak" in analysis
        assert "worst_loss_streak" in analysis
        assert "recent_form" in analysis

    def test_streak_analysis_no_games(self, db):
        """Test streak analysis with no games."""
        player = PlayerProfile(
            name="No Games Player",
            email="nogames@example.com",
            handicap=18.0,
            created_at=datetime.now().isoformat()
        )
        db.add(player)
        db.commit()

        service = StatisticsService(db)
        analysis = service.get_streak_analysis(player.id)

        assert analysis["status"] == "no_games"


class TestSpecialEventAnalytics:
    """Test special event analytics (ping pong, aardvark, etc.)."""

    def test_special_event_analytics(self, db, test_player_with_stats):
        """Test special event analytics returns all event types."""
        player, _ = test_player_with_stats
        service = StatisticsService(db)

        analytics = service.get_special_event_analytics(player.id)

        assert analytics["status"] == "available"
        assert "ping_pong" in analytics
        assert "invisible_aardvark" in analytics
        assert "duncan" in analytics
        assert "tunkarri" in analytics
        assert "big_dick" in analytics
        assert "totals" in analytics

    def test_special_event_success_rates(self, db, test_player_with_stats):
        """Test success rate calculations for special events."""
        player, _ = test_player_with_stats
        service = StatisticsService(db)

        analytics = service.get_special_event_analytics(player.id)

        # Ping pong: 3/5 = 60%
        assert analytics["ping_pong"]["success_rate"] == 60.0
        # Duncan: 1/3 ≈ 33.3%
        assert analytics["duncan"]["success_rate"] == pytest.approx(33.3, rel=0.1)


class TestScorePerformanceAnalytics:
    """Test score performance analytics."""

    def test_score_performance_structure(self, db, test_player_with_stats):
        """Test score performance analytics structure."""
        player, _ = test_player_with_stats
        service = StatisticsService(db)

        analytics = service.get_score_performance_analytics(player.id)

        assert analytics["status"] == "available"
        assert "raw_counts" in analytics
        assert "rates" in analytics
        assert "summary" in analytics

    def test_score_performance_raw_counts(self, db, test_player_with_stats):
        """Test raw score counts are correct."""
        player, stats = test_player_with_stats
        service = StatisticsService(db)

        analytics = service.get_score_performance_analytics(player.id)

        assert analytics["raw_counts"]["eagles"] == 2
        assert analytics["raw_counts"]["birdies"] == 30
        assert analytics["raw_counts"]["pars"] == 180
        assert analytics["raw_counts"]["bogeys"] == 150

    def test_score_performance_rates(self, db, test_player_with_stats):
        """Test score performance rates calculation."""
        player, stats = test_player_with_stats
        service = StatisticsService(db)

        analytics = service.get_score_performance_analytics(player.id)

        # Par rate: 180/450 = 40%
        assert analytics["rates"]["par_rate"] == 40.0


class TestComparativeLeaderboard:
    """Test comparative leaderboard functionality."""

    def test_comparative_leaderboard(self, db, multiple_players):
        """Test getting comparative leaderboard."""
        service = StatisticsService(db)

        leaderboard = service.get_comparative_leaderboard(
            metric="total_earnings",
            limit=10
        )

        assert isinstance(leaderboard, list)
        assert len(leaderboard) <= 10

        for entry in leaderboard:
            assert "rank" in entry
            assert "player_id" in entry
            assert "total_earnings" in entry
            assert "win_rate" in entry

    def test_comparative_leaderboard_excludes_ai(self, db, multiple_players):
        """Test that AI players are excluded from comparative leaderboard."""
        # Add AI player with high stats
        ai_player = PlayerProfile(
            name="AI Player",
            is_ai=1,
            is_active=1,
            created_at=datetime.now().isoformat()
        )
        db.add(ai_player)
        db.flush()

        stats = PlayerStatistics(
            player_id=ai_player.id,
            games_played=100,
            total_earnings=10000.0,
            last_updated=datetime.now().isoformat()
        )
        db.add(stats)
        db.commit()

        service = StatisticsService(db)
        leaderboard = service.get_comparative_leaderboard()

        ai_in_board = any(
            entry["player_id"] == ai_player.id for entry in leaderboard
        )
        assert not ai_in_board


class TestGameModeAnalytics:
    """Test game mode analytics."""

    def test_game_mode_analytics(self, db, test_player_with_stats, test_game_results):
        """Test getting game mode analytics."""
        player, _ = test_player_with_stats
        service = StatisticsService(db)

        analytics = service.get_game_mode_analytics(player.id)

        assert isinstance(analytics, dict)

    def test_game_mode_analytics_all_players(self, db, test_game_results):
        """Test game mode analytics for all players."""
        service = StatisticsService(db)

        analytics = service.get_game_mode_analytics(player_id=None)

        assert isinstance(analytics, dict)


class TestHelperMethods:
    """Test internal helper methods."""

    def test_calculate_percentile(self, db):
        """Test percentile calculation."""
        service = StatisticsService(db)

        # Test median
        percentile = service._calculate_percentile(50, [0, 25, 50, 75, 100])
        assert percentile == 60.0  # 3 values <= 50, 3/5 = 60%

    def test_calculate_percentile_empty(self, db):
        """Test percentile with empty list."""
        service = StatisticsService(db)

        percentile = service._calculate_percentile(50, [])
        assert percentile == 50.0  # Default

    def test_analyze_win_rate_trend_insufficient_data(self, db):
        """Test trend analysis with insufficient data."""
        service = StatisticsService(db)

        trend = service._analyze_win_rate_trend(99999)  # Non-existent player
        assert trend == "stable"

    def test_calculate_consistency_score_insufficient_data(self, db):
        """Test consistency score with insufficient data."""
        service = StatisticsService(db)

        score = service._calculate_consistency_score(99999)
        assert score == 50.0  # Default for insufficient data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

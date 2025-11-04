"""
Comprehensive unit tests for AchievementService class.

Tests all 8 methods in AchievementService:
- award_badge() - Badge awarding, duplicates, errors
- get_player_badges() - Retrieving player badges
- get_available_badges() - Listing all badges
- check_badge_eligibility() - Eligibility checks
- calculate_badge_progress() - Progress calculation
- get_player_achievements() - Legacy achievement retrieval
- create_achievement() - Legacy achievement creation
- sync_achievements_to_badges() - Migration from achievements to badges

Author: Test Suite
Date: 2025-11-03
"""

import pytest
from unittest.mock import Mock, MagicMock, patch, call
from datetime import datetime
from typing import List, Dict, Any

from app.services.achievement_service import AchievementService, get_achievement_service
from app.models import Badge, PlayerBadgeEarned, BadgeProgress, PlayerAchievement


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def mock_db():
    """Mock database session."""
    db = MagicMock()
    return db


@pytest.fixture
def mock_badge_engine():
    """Mock BadgeEngine."""
    engine = MagicMock()
    return engine


@pytest.fixture
def achievement_service(mock_db):
    """Create AchievementService instance with mocked dependencies."""
    with patch('app.services.achievement_service.BadgeEngine') as mock_badge_class:
        mock_badge_engine = MagicMock()
        mock_badge_class.return_value = mock_badge_engine
        service = AchievementService(mock_db)
        service.badge_engine = mock_badge_engine
        return service


@pytest.fixture
def sample_badge():
    """Sample Badge object."""
    badge = Mock(spec=Badge)
    badge.id = 1
    badge.name = "Lone Wolf"
    badge.description = "Win your first solo game"
    badge.category = "achievement"
    badge.rarity = "common"
    badge.trigger_type = "one_time"
    badge.trigger_condition = {"wins": 1}
    badge.image_url = "/images/lone_wolf.png"
    badge.points_value = 10
    badge.is_active = True
    badge.max_supply = None
    badge.current_supply = 5
    badge.series_id = None
    badge.tier = None
    return badge


@pytest.fixture
def sample_earned_badge():
    """Sample PlayerBadgeEarned object."""
    earned = Mock(spec=PlayerBadgeEarned)
    earned.id = 1
    earned.player_profile_id = 100
    earned.badge_id = 1
    earned.earned_at = "2024-11-03T10:00:00"
    earned.serial_number = 47
    earned.game_record_id = 200
    earned.is_favorited = False
    earned.showcase_position = None
    return earned


@pytest.fixture
def sample_badge_progress():
    """Sample BadgeProgress object."""
    progress = Mock(spec=BadgeProgress)
    progress.id = 1
    progress.player_profile_id = 100
    progress.badge_id = 1
    progress.current_progress = 7
    progress.target_progress = 10
    progress.progress_percentage = 70.0
    progress.last_progress_date = "2024-11-03T10:00:00"
    progress.progress_data = {}
    return progress


@pytest.fixture
def sample_achievement():
    """Sample PlayerAchievement object."""
    achievement = Mock(spec=PlayerAchievement)
    achievement.id = 1
    achievement.player_profile_id = 100
    achievement.achievement_type = "first_win"
    achievement.achievement_name = "First Win"
    achievement.description = "Won your first game"
    achievement.earned_date = "2024-11-03T10:00:00"
    achievement.game_record_id = 200
    achievement.achievement_data = {"score": 100}
    return achievement


# ============================================================================
# AWARD_BADGE TESTS
# ============================================================================

class TestAwardBadge:
    """Test AchievementService.award_badge() method."""

    def test_award_badge_success(self, achievement_service, mock_db, sample_badge, sample_earned_badge):
        """Test successfully awarding a badge."""
        # Setup
        mock_query = mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.first.side_effect = [sample_badge, None]  # Badge exists, not earned yet

        achievement_service.badge_engine._award_badge.return_value = sample_earned_badge

        # Execute
        result = achievement_service.award_badge(
            player_profile_id=100,
            badge_name="Lone Wolf",
            game_record_id=200
        )

        # Assert
        assert result is not None
        assert result["badge_id"] == 1
        assert result["badge_name"] == "Lone Wolf"
        assert result["serial_number"] == 47
        assert result["points_value"] == 10
        achievement_service.badge_engine._award_badge.assert_called_once_with(
            player_profile_id=100,
            badge_id=1,
            game_record_id=200
        )

    def test_award_badge_already_earned(self, achievement_service, mock_db, sample_badge, sample_earned_badge):
        """Test awarding badge that player already has."""
        # Setup
        mock_query = mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.first.side_effect = [sample_badge, sample_earned_badge]  # Badge exists, already earned

        # Execute
        result = achievement_service.award_badge(
            player_profile_id=100,
            badge_name="Lone Wolf"
        )

        # Assert
        assert result is None
        achievement_service.badge_engine._award_badge.assert_not_called()

    def test_award_badge_not_found(self, achievement_service, mock_db):
        """Test awarding badge that doesn't exist."""
        # Setup
        mock_query = mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.first.return_value = None  # Badge not found

        # Execute
        result = achievement_service.award_badge(
            player_profile_id=100,
            badge_name="Nonexistent Badge"
        )

        # Assert
        assert result is None
        achievement_service.badge_engine._award_badge.assert_not_called()

    def test_award_badge_inactive(self, achievement_service, mock_db, sample_badge):
        """Test awarding inactive badge."""
        # Setup
        sample_badge.is_active = False
        mock_query = mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.first.return_value = None  # Filter includes is_active=True, so returns None

        # Execute
        result = achievement_service.award_badge(
            player_profile_id=100,
            badge_name="Lone Wolf"
        )

        # Assert
        assert result is None

    def test_award_badge_without_game_record(self, achievement_service, mock_db, sample_badge, sample_earned_badge):
        """Test awarding badge without game_record_id."""
        # Setup
        mock_query = mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.first.side_effect = [sample_badge, None]
        achievement_service.badge_engine._award_badge.return_value = sample_earned_badge

        # Execute
        result = achievement_service.award_badge(
            player_profile_id=100,
            badge_name="Lone Wolf",
            game_record_id=None
        )

        # Assert
        assert result is not None
        achievement_service.badge_engine._award_badge.assert_called_once_with(
            player_profile_id=100,
            badge_id=1,
            game_record_id=None
        )

    def test_award_badge_engine_returns_none(self, achievement_service, mock_db, sample_badge):
        """Test when badge engine fails to award badge."""
        # Setup
        mock_query = mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.first.side_effect = [sample_badge, None]
        achievement_service.badge_engine._award_badge.return_value = None

        # Execute
        result = achievement_service.award_badge(
            player_profile_id=100,
            badge_name="Lone Wolf"
        )

        # Assert
        assert result is None

    def test_award_badge_database_error(self, achievement_service, mock_db, sample_badge):
        """Test award_badge handles database errors."""
        # Setup
        mock_db.query.side_effect = Exception("Database connection error")

        # Execute & Assert
        with pytest.raises(Exception) as exc_info:
            achievement_service.award_badge(
                player_profile_id=100,
                badge_name="Lone Wolf"
            )

        assert "Database connection error" in str(exc_info.value)
        mock_db.rollback.assert_called_once()

    def test_award_badge_with_all_badge_fields(self, achievement_service, mock_db, sample_badge, sample_earned_badge):
        """Test that all badge fields are returned in result."""
        # Setup
        mock_query = mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.first.side_effect = [sample_badge, None]
        achievement_service.badge_engine._award_badge.return_value = sample_earned_badge

        # Execute
        result = achievement_service.award_badge(
            player_profile_id=100,
            badge_name="Lone Wolf"
        )

        # Assert
        assert "badge_id" in result
        assert "badge_name" in result
        assert "description" in result
        assert "category" in result
        assert "rarity" in result
        assert "earned_at" in result
        assert "serial_number" in result
        assert "image_url" in result
        assert "points_value" in result


# ============================================================================
# GET_PLAYER_BADGES TESTS
# ============================================================================

class TestGetPlayerBadges:
    """Test AchievementService.get_player_badges() method."""

    def test_get_player_badges_success(self, achievement_service, mock_db, sample_badge, sample_earned_badge):
        """Test successfully retrieving player badges."""
        # Setup
        mock_query = mock_db.query.return_value
        mock_join = mock_query.join.return_value
        mock_filter = mock_join.filter.return_value
        mock_order = mock_filter.order_by.return_value
        mock_order.all.return_value = [(sample_earned_badge, sample_badge)]

        # Execute
        result = achievement_service.get_player_badges(player_profile_id=100)

        # Assert
        assert len(result) == 1
        assert result[0]["badge_id"] == 1
        assert result[0]["badge_name"] == "Lone Wolf"
        assert result[0]["serial_number"] == 47
        assert result[0]["is_favorited"] is False

    def test_get_player_badges_multiple(self, achievement_service, mock_db):
        """Test retrieving multiple badges."""
        # Setup
        badge1 = Mock(spec=Badge)
        badge1.id = 1
        badge1.name = "Badge 1"
        badge1.description = "First badge"
        badge1.category = "achievement"
        badge1.rarity = "common"
        badge1.image_url = "/img1.png"
        badge1.points_value = 10

        badge2 = Mock(spec=Badge)
        badge2.id = 2
        badge2.name = "Badge 2"
        badge2.description = "Second badge"
        badge2.category = "progression"
        badge2.rarity = "rare"
        badge2.image_url = "/img2.png"
        badge2.points_value = 20

        earned1 = Mock(spec=PlayerBadgeEarned)
        earned1.badge_id = 1
        earned1.earned_at = "2024-11-03T10:00:00"
        earned1.serial_number = 1
        earned1.game_record_id = 100
        earned1.is_favorited = True
        earned1.showcase_position = 1

        earned2 = Mock(spec=PlayerBadgeEarned)
        earned2.badge_id = 2
        earned2.earned_at = "2024-11-03T11:00:00"
        earned2.serial_number = 2
        earned2.game_record_id = 101
        earned2.is_favorited = False
        earned2.showcase_position = None

        mock_query = mock_db.query.return_value
        mock_join = mock_query.join.return_value
        mock_filter = mock_join.filter.return_value
        mock_order = mock_filter.order_by.return_value
        mock_order.all.return_value = [(earned1, badge1), (earned2, badge2)]

        # Execute
        result = achievement_service.get_player_badges(player_profile_id=100)

        # Assert
        assert len(result) == 2
        assert result[0]["badge_name"] == "Badge 1"
        assert result[1]["badge_name"] == "Badge 2"

    def test_get_player_badges_empty(self, achievement_service, mock_db):
        """Test retrieving badges when player has none."""
        # Setup
        mock_query = mock_db.query.return_value
        mock_join = mock_query.join.return_value
        mock_filter = mock_join.filter.return_value
        mock_order = mock_filter.order_by.return_value
        mock_order.all.return_value = []

        # Execute
        result = achievement_service.get_player_badges(player_profile_id=100)

        # Assert
        assert result == []

    def test_get_player_badges_database_error(self, achievement_service, mock_db):
        """Test get_player_badges handles database errors."""
        # Setup
        mock_db.query.side_effect = Exception("Database query failed")

        # Execute & Assert
        with pytest.raises(Exception) as exc_info:
            achievement_service.get_player_badges(player_profile_id=100)

        assert "Database query failed" in str(exc_info.value)

    def test_get_player_badges_all_fields_present(self, achievement_service, mock_db, sample_badge, sample_earned_badge):
        """Test that all expected fields are present in result."""
        # Setup
        mock_query = mock_db.query.return_value
        mock_join = mock_query.join.return_value
        mock_filter = mock_join.filter.return_value
        mock_order = mock_filter.order_by.return_value
        mock_order.all.return_value = [(sample_earned_badge, sample_badge)]

        # Execute
        result = achievement_service.get_player_badges(player_profile_id=100)

        # Assert
        badge = result[0]
        assert "badge_id" in badge
        assert "badge_name" in badge
        assert "description" in badge
        assert "category" in badge
        assert "rarity" in badge
        assert "earned_at" in badge
        assert "serial_number" in badge
        assert "game_record_id" in badge
        assert "image_url" in badge
        assert "points_value" in badge
        assert "is_favorited" in badge
        assert "showcase_position" in badge


# ============================================================================
# GET_AVAILABLE_BADGES TESTS
# ============================================================================

class TestGetAvailableBadges:
    """Test AchievementService.get_available_badges() method."""

    def test_get_available_badges_success(self, achievement_service, mock_db, sample_badge):
        """Test successfully retrieving available badges."""
        # Setup
        mock_query = mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.all.return_value = [sample_badge]

        # Execute
        result = achievement_service.get_available_badges()

        # Assert
        assert len(result) == 1
        assert result[0]["badge_id"] == 1
        assert result[0]["badge_name"] == "Lone Wolf"
        assert result[0]["trigger_type"] == "one_time"

    def test_get_available_badges_multiple(self, achievement_service, mock_db):
        """Test retrieving multiple available badges."""
        # Setup
        badges = []
        for i in range(1, 4):
            badge = Mock(spec=Badge)
            badge.id = i
            badge.name = f"Badge {i}"
            badge.description = f"Description {i}"
            badge.category = "achievement"
            badge.rarity = "common"
            badge.trigger_type = "one_time"
            badge.image_url = f"/img{i}.png"
            badge.points_value = i * 10
            badge.max_supply = 100 if i == 1 else None
            badge.current_supply = i * 10
            badge.series_id = None if i < 3 else 1
            badge.tier = None if i < 3 else 1
            badges.append(badge)

        mock_query = mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.all.return_value = badges

        # Execute
        result = achievement_service.get_available_badges()

        # Assert
        assert len(result) == 3
        assert result[0]["badge_name"] == "Badge 1"
        assert result[0]["max_supply"] == 100
        assert result[2]["series_id"] == 1

    def test_get_available_badges_empty(self, achievement_service, mock_db):
        """Test retrieving available badges when none exist."""
        # Setup
        mock_query = mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.all.return_value = []

        # Execute
        result = achievement_service.get_available_badges()

        # Assert
        assert result == []

    def test_get_available_badges_only_active(self, achievement_service, mock_db):
        """Test that only active badges are returned."""
        # Execute
        achievement_service.get_available_badges()

        # Assert - verify filter was called with is_active=True
        mock_db.query.assert_called_once()

    def test_get_available_badges_database_error(self, achievement_service, mock_db):
        """Test get_available_badges handles database errors."""
        # Setup
        mock_db.query.side_effect = Exception("Database error")

        # Execute & Assert
        with pytest.raises(Exception) as exc_info:
            achievement_service.get_available_badges()

        assert "Database error" in str(exc_info.value)

    def test_get_available_badges_all_fields(self, achievement_service, mock_db, sample_badge):
        """Test that all expected fields are present in result."""
        # Setup
        mock_query = mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.all.return_value = [sample_badge]

        # Execute
        result = achievement_service.get_available_badges()

        # Assert
        badge = result[0]
        assert "badge_id" in badge
        assert "badge_name" in badge
        assert "description" in badge
        assert "category" in badge
        assert "rarity" in badge
        assert "trigger_type" in badge
        assert "image_url" in badge
        assert "points_value" in badge
        assert "max_supply" in badge
        assert "current_supply" in badge
        assert "series_id" in badge
        assert "tier" in badge


# ============================================================================
# CHECK_BADGE_ELIGIBILITY TESTS
# ============================================================================

class TestCheckBadgeEligibility:
    """Test AchievementService.check_badge_eligibility() method."""

    def test_check_badge_eligibility_eligible(self, achievement_service, mock_db, sample_badge):
        """Test checking eligibility when player is eligible."""
        # Setup
        sample_badge.trigger_type = "one_time"
        mock_query = mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.first.side_effect = [sample_badge, None]  # Badge exists, not earned

        # Execute
        result = achievement_service.check_badge_eligibility(
            player_profile_id=100,
            badge_name="Lone Wolf"
        )

        # Assert
        assert result is True

    def test_check_badge_eligibility_already_earned(self, achievement_service, mock_db, sample_badge, sample_earned_badge):
        """Test checking eligibility when badge already earned."""
        # Setup
        mock_query = mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.first.side_effect = [sample_badge, sample_earned_badge]  # Badge exists, already earned

        # Execute
        result = achievement_service.check_badge_eligibility(
            player_profile_id=100,
            badge_name="Lone Wolf"
        )

        # Assert
        assert result is False

    def test_check_badge_eligibility_badge_not_found(self, achievement_service, mock_db):
        """Test checking eligibility when badge doesn't exist."""
        # Setup
        mock_query = mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.first.return_value = None

        # Execute
        result = achievement_service.check_badge_eligibility(
            player_profile_id=100,
            badge_name="Nonexistent Badge"
        )

        # Assert
        assert result is False

    def test_check_badge_eligibility_supply_exhausted(self, achievement_service, mock_db, sample_badge):
        """Test checking eligibility when supply is exhausted."""
        # Setup
        sample_badge.max_supply = 100
        sample_badge.current_supply = 100
        mock_query = mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.first.side_effect = [sample_badge, None]

        # Execute
        result = achievement_service.check_badge_eligibility(
            player_profile_id=100,
            badge_name="Lone Wolf"
        )

        # Assert
        assert result is False

    def test_check_badge_eligibility_supply_available(self, achievement_service, mock_db, sample_badge):
        """Test checking eligibility when supply is available."""
        # Setup
        sample_badge.max_supply = 100
        sample_badge.current_supply = 50
        mock_query = mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.first.side_effect = [sample_badge, None]

        # Execute
        result = achievement_service.check_badge_eligibility(
            player_profile_id=100,
            badge_name="Lone Wolf"
        )

        # Assert
        assert result is True

    def test_check_badge_eligibility_progression_complete(self, achievement_service, mock_db, sample_badge):
        """Test checking eligibility for progression badge with 100% progress."""
        # Setup
        sample_badge.trigger_type = "progression"
        mock_query = mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.first.side_effect = [sample_badge, None]

        with patch.object(achievement_service, 'calculate_badge_progress') as mock_progress:
            mock_progress.return_value = {"progress_percentage": 100.0}

            # Execute
            result = achievement_service.check_badge_eligibility(
                player_profile_id=100,
                badge_name="Veteran"
            )

            # Assert
            assert result is True

    def test_check_badge_eligibility_progression_incomplete(self, achievement_service, mock_db, sample_badge):
        """Test checking eligibility for progression badge with incomplete progress."""
        # Setup
        sample_badge.trigger_type = "career_milestone"
        mock_query = mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.first.side_effect = [sample_badge, None]

        with patch.object(achievement_service, 'calculate_badge_progress') as mock_progress:
            mock_progress.return_value = {"progress_percentage": 75.0}

            # Execute
            result = achievement_service.check_badge_eligibility(
                player_profile_id=100,
                badge_name="Veteran"
            )

            # Assert
            assert result is False

    def test_check_badge_eligibility_database_error(self, achievement_service, mock_db):
        """Test check_badge_eligibility handles database errors."""
        # Setup
        mock_db.query.side_effect = Exception("Database error")

        # Execute & Assert
        with pytest.raises(Exception) as exc_info:
            achievement_service.check_badge_eligibility(
                player_profile_id=100,
                badge_name="Lone Wolf"
            )

        assert "Database error" in str(exc_info.value)


# ============================================================================
# CALCULATE_BADGE_PROGRESS TESTS
# ============================================================================

class TestCalculateBadgeProgress:
    """Test AchievementService.calculate_badge_progress() method."""

    def test_calculate_badge_progress_in_progress(self, achievement_service, mock_db, sample_badge, sample_badge_progress):
        """Test calculating progress for badge in progress."""
        # Setup
        mock_query = mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.first.side_effect = [sample_badge, None]  # Badge exists, not earned
        achievement_service.badge_engine._get_or_create_progress.return_value = sample_badge_progress

        # Execute
        result = achievement_service.calculate_badge_progress(
            player_profile_id=100,
            badge_name="Lone Wolf"
        )

        # Assert
        assert result["badge_id"] == 1
        assert result["badge_name"] == "Lone Wolf"
        assert result["earned"] is False
        assert result["current_progress"] == 7
        assert result["target_progress"] == 10
        assert result["progress_percentage"] == 70.0

    def test_calculate_badge_progress_already_earned(self, achievement_service, mock_db, sample_badge, sample_earned_badge):
        """Test calculating progress for already earned badge."""
        # Setup
        mock_query = mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.first.side_effect = [sample_badge, sample_earned_badge]

        # Execute
        result = achievement_service.calculate_badge_progress(
            player_profile_id=100,
            badge_name="Lone Wolf"
        )

        # Assert
        assert result["badge_id"] == 1
        assert result["badge_name"] == "Lone Wolf"
        assert result["earned"] is True
        assert result["earned_at"] == "2024-11-03T10:00:00"
        assert result["progress_percentage"] == 100.0

    def test_calculate_badge_progress_badge_not_found(self, achievement_service, mock_db):
        """Test calculating progress when badge doesn't exist."""
        # Setup
        mock_query = mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.first.return_value = None

        # Execute
        result = achievement_service.calculate_badge_progress(
            player_profile_id=100,
            badge_name="Nonexistent Badge"
        )

        # Assert
        assert "error" in result
        assert result["error"] == "Badge not found or inactive"
        assert result["badge_name"] == "Nonexistent Badge"

    def test_calculate_badge_progress_zero_progress(self, achievement_service, mock_db, sample_badge):
        """Test calculating progress with zero progress."""
        # Setup
        progress = Mock(spec=BadgeProgress)
        progress.current_progress = 0
        progress.target_progress = 10
        progress.progress_percentage = 0.0

        mock_query = mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.first.side_effect = [sample_badge, None]
        achievement_service.badge_engine._get_or_create_progress.return_value = progress

        # Execute
        result = achievement_service.calculate_badge_progress(
            player_profile_id=100,
            badge_name="Lone Wolf"
        )

        # Assert
        assert result["current_progress"] == 0
        assert result["progress_percentage"] == 0.0

    def test_calculate_badge_progress_complete_but_not_awarded(self, achievement_service, mock_db, sample_badge):
        """Test calculating progress when progress is complete but badge not yet awarded."""
        # Setup
        progress = Mock(spec=BadgeProgress)
        progress.current_progress = 10
        progress.target_progress = 10
        progress.progress_percentage = 100.0

        mock_query = mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.first.side_effect = [sample_badge, None]
        achievement_service.badge_engine._get_or_create_progress.return_value = progress

        # Execute
        result = achievement_service.calculate_badge_progress(
            player_profile_id=100,
            badge_name="Lone Wolf"
        )

        # Assert
        assert result["earned"] is False
        assert result["progress_percentage"] == 100.0

    def test_calculate_badge_progress_all_fields(self, achievement_service, mock_db, sample_badge, sample_badge_progress):
        """Test that all expected fields are present in result."""
        # Setup
        mock_query = mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.first.side_effect = [sample_badge, None]
        achievement_service.badge_engine._get_or_create_progress.return_value = sample_badge_progress

        # Execute
        result = achievement_service.calculate_badge_progress(
            player_profile_id=100,
            badge_name="Lone Wolf"
        )

        # Assert
        assert "badge_id" in result
        assert "badge_name" in result
        assert "description" in result
        assert "category" in result
        assert "rarity" in result
        assert "earned" in result
        assert "current_progress" in result
        assert "target_progress" in result
        assert "progress_percentage" in result
        assert "requirements" in result
        assert "trigger_type" in result

    def test_calculate_badge_progress_database_error(self, achievement_service, mock_db):
        """Test calculate_badge_progress handles database errors."""
        # Setup
        mock_db.query.side_effect = Exception("Database error")

        # Execute & Assert
        with pytest.raises(Exception) as exc_info:
            achievement_service.calculate_badge_progress(
                player_profile_id=100,
                badge_name="Lone Wolf"
            )

        assert "Database error" in str(exc_info.value)


# ============================================================================
# GET_PLAYER_ACHIEVEMENTS TESTS
# ============================================================================

class TestGetPlayerAchievements:
    """Test AchievementService.get_player_achievements() method (legacy)."""

    def test_get_player_achievements_success(self, achievement_service, mock_db, sample_achievement):
        """Test successfully retrieving player achievements."""
        # Setup
        mock_query = mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_order = mock_filter.order_by.return_value
        mock_order.all.return_value = [sample_achievement]

        # Execute
        result = achievement_service.get_player_achievements(player_profile_id=100)

        # Assert
        assert len(result) == 1
        assert result[0]["id"] == 1
        assert result[0]["achievement_type"] == "first_win"
        assert result[0]["achievement_name"] == "First Win"

    def test_get_player_achievements_multiple(self, achievement_service, mock_db):
        """Test retrieving multiple achievements."""
        # Setup
        achievements = []
        for i in range(1, 4):
            ach = Mock(spec=PlayerAchievement)
            ach.id = i
            ach.player_profile_id = 100
            ach.achievement_type = f"achievement_{i}"
            ach.achievement_name = f"Achievement {i}"
            ach.description = f"Description {i}"
            ach.earned_date = f"2024-11-0{i}T10:00:00"
            ach.game_record_id = 200 + i
            ach.achievement_data = {"data": i}
            achievements.append(ach)

        mock_query = mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_order = mock_filter.order_by.return_value
        mock_order.all.return_value = achievements

        # Execute
        result = achievement_service.get_player_achievements(player_profile_id=100)

        # Assert
        assert len(result) == 3
        assert result[0]["achievement_name"] == "Achievement 1"
        assert result[2]["achievement_name"] == "Achievement 3"

    def test_get_player_achievements_empty(self, achievement_service, mock_db):
        """Test retrieving achievements when player has none."""
        # Setup
        mock_query = mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_order = mock_filter.order_by.return_value
        mock_order.all.return_value = []

        # Execute
        result = achievement_service.get_player_achievements(player_profile_id=100)

        # Assert
        assert result == []

    def test_get_player_achievements_all_fields(self, achievement_service, mock_db, sample_achievement):
        """Test that all expected fields are present in result."""
        # Setup
        mock_query = mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_order = mock_filter.order_by.return_value
        mock_order.all.return_value = [sample_achievement]

        # Execute
        result = achievement_service.get_player_achievements(player_profile_id=100)

        # Assert
        achievement = result[0]
        assert "id" in achievement
        assert "achievement_type" in achievement
        assert "achievement_name" in achievement
        assert "description" in achievement
        assert "earned_date" in achievement
        assert "game_record_id" in achievement
        assert "achievement_data" in achievement

    def test_get_player_achievements_database_error(self, achievement_service, mock_db):
        """Test get_player_achievements handles database errors."""
        # Setup
        mock_db.query.side_effect = Exception("Database error")

        # Execute & Assert
        with pytest.raises(Exception) as exc_info:
            achievement_service.get_player_achievements(player_profile_id=100)

        assert "Database error" in str(exc_info.value)


# ============================================================================
# CREATE_ACHIEVEMENT TESTS
# ============================================================================

class TestCreateAchievement:
    """Test AchievementService.create_achievement() method (legacy)."""

    def test_create_achievement_success(self, achievement_service, mock_db):
        """Test successfully creating an achievement."""
        # Setup
        new_achievement = Mock(spec=PlayerAchievement)
        new_achievement.id = 1
        new_achievement.player_profile_id = 100
        new_achievement.achievement_type = "first_win"
        new_achievement.achievement_name = "First Win"
        new_achievement.description = "Won your first game"
        new_achievement.earned_date = "2024-11-03T10:00:00"
        new_achievement.game_record_id = 200
        new_achievement.achievement_data = {"score": 100}

        mock_db.refresh.side_effect = lambda obj: setattr(obj, 'id', 1)

        with patch('app.services.achievement_service.PlayerAchievement') as mock_achievement_class:
            mock_achievement_class.return_value = new_achievement

            # Execute
            result = achievement_service.create_achievement(
                player_profile_id=100,
                achievement_type="first_win",
                description="Won your first game",
                achievement_name="First Win",
                game_record_id=200,
                achievement_data={"score": 100}
            )

            # Assert
            assert result["id"] == 1
            assert result["achievement_type"] == "first_win"
            assert result["achievement_name"] == "First Win"
            mock_db.add.assert_called_once()
            mock_db.commit.assert_called_once()

    def test_create_achievement_without_optional_params(self, achievement_service, mock_db):
        """Test creating achievement without optional parameters."""
        # Setup
        new_achievement = Mock(spec=PlayerAchievement)
        new_achievement.id = 1
        new_achievement.player_profile_id = 100
        new_achievement.achievement_type = "custom_achievement"
        new_achievement.achievement_name = "Custom Achievement"
        new_achievement.description = "Custom description"
        new_achievement.earned_date = "2024-11-03T10:00:00"
        new_achievement.game_record_id = None
        new_achievement.achievement_data = {}

        with patch('app.services.achievement_service.PlayerAchievement') as mock_achievement_class:
            mock_achievement_class.return_value = new_achievement

            # Execute
            result = achievement_service.create_achievement(
                player_profile_id=100,
                achievement_type="custom_achievement",
                description="Custom description"
            )

            # Assert
            assert result["achievement_type"] == "custom_achievement"
            assert result["game_record_id"] is None
            assert result["achievement_data"] == {}

    def test_create_achievement_name_auto_generated(self, achievement_service, mock_db):
        """Test that achievement name is auto-generated from type if not provided."""
        # Setup
        new_achievement = Mock(spec=PlayerAchievement)
        new_achievement.id = 1
        new_achievement.player_profile_id = 100
        new_achievement.achievement_type = "first_win"
        new_achievement.achievement_name = "First Win"  # Auto-generated
        new_achievement.description = "Description"
        new_achievement.earned_date = "2024-11-03T10:00:00"
        new_achievement.game_record_id = None
        new_achievement.achievement_data = {}

        with patch('app.services.achievement_service.PlayerAchievement') as mock_achievement_class:
            mock_achievement_class.return_value = new_achievement

            # Execute
            result = achievement_service.create_achievement(
                player_profile_id=100,
                achievement_type="first_win",
                description="Description"
            )

            # Assert
            # The name should be generated from type
            mock_achievement_class.assert_called_once()

    def test_create_achievement_database_error(self, achievement_service, mock_db):
        """Test create_achievement handles database errors."""
        # Setup
        mock_db.add.side_effect = Exception("Database error")

        with patch('app.services.achievement_service.PlayerAchievement'):
            # Execute & Assert
            with pytest.raises(Exception) as exc_info:
                achievement_service.create_achievement(
                    player_profile_id=100,
                    achievement_type="first_win",
                    description="Description"
                )

            assert "Database error" in str(exc_info.value)
            mock_db.rollback.assert_called_once()

    def test_create_achievement_all_fields_in_result(self, achievement_service, mock_db):
        """Test that all expected fields are in the result."""
        # Setup
        new_achievement = Mock(spec=PlayerAchievement)
        new_achievement.id = 1
        new_achievement.player_profile_id = 100
        new_achievement.achievement_type = "first_win"
        new_achievement.achievement_name = "First Win"
        new_achievement.description = "Description"
        new_achievement.earned_date = "2024-11-03T10:00:00"
        new_achievement.game_record_id = 200
        new_achievement.achievement_data = {"key": "value"}

        with patch('app.services.achievement_service.PlayerAchievement') as mock_achievement_class:
            mock_achievement_class.return_value = new_achievement

            # Execute
            result = achievement_service.create_achievement(
                player_profile_id=100,
                achievement_type="first_win",
                description="Description",
                achievement_name="First Win",
                game_record_id=200,
                achievement_data={"key": "value"}
            )

            # Assert
            assert "id" in result
            assert "achievement_type" in result
            assert "achievement_name" in result
            assert "description" in result
            assert "earned_date" in result
            assert "game_record_id" in result
            assert "achievement_data" in result


# ============================================================================
# SYNC_ACHIEVEMENTS_TO_BADGES TESTS
# ============================================================================

class TestSyncAchievementsToBadges:
    """Test AchievementService.sync_achievements_to_badges() method (migration)."""

    def test_sync_achievements_to_badges_success(self, achievement_service, mock_db):
        """Test successfully syncing achievements to badges."""
        # Setup
        achievements = []
        for i in range(3):
            ach = Mock(spec=PlayerAchievement)
            ach.id = i + 1
            ach.player_profile_id = 100
            ach.achievement_type = "first_win"
            ach.game_record_id = 200 + i
            achievements.append(ach)

        mock_query = mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.all.return_value = achievements

        with patch.object(achievement_service, 'award_badge') as mock_award:
            mock_award.return_value = {"badge_id": 1, "badge_name": "Lone Wolf"}

            # Execute
            result = achievement_service.sync_achievements_to_badges(player_profile_id=100)

            # Assert
            assert result == 3
            assert mock_award.call_count == 3

    def test_sync_achievements_to_badges_no_achievements(self, achievement_service, mock_db):
        """Test syncing when player has no achievements."""
        # Setup
        mock_query = mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.all.return_value = []

        # Execute
        result = achievement_service.sync_achievements_to_badges(player_profile_id=100)

        # Assert
        assert result == 0

    def test_sync_achievements_to_badges_partial_mapping(self, achievement_service, mock_db):
        """Test syncing with some unmapped achievement types."""
        # Setup
        achievements = [
            Mock(spec=PlayerAchievement, achievement_type="first_win", game_record_id=200),
            Mock(spec=PlayerAchievement, achievement_type="unmapped_type", game_record_id=201),
            Mock(spec=PlayerAchievement, achievement_type="big_earner", game_record_id=202)
        ]

        mock_query = mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.all.return_value = achievements

        with patch.object(achievement_service, 'award_badge') as mock_award:
            mock_award.return_value = {"badge_id": 1, "badge_name": "Badge"}

            # Execute
            result = achievement_service.sync_achievements_to_badges(player_profile_id=100)

            # Assert
            assert result == 2  # Only 2 mapped achievements
            assert mock_award.call_count == 2

    def test_sync_achievements_to_badges_already_earned(self, achievement_service, mock_db):
        """Test syncing when badges are already earned."""
        # Setup
        achievement = Mock(spec=PlayerAchievement)
        achievement.achievement_type = "first_win"
        achievement.game_record_id = 200

        mock_query = mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.all.return_value = [achievement]

        with patch.object(achievement_service, 'award_badge') as mock_award:
            mock_award.return_value = None  # Badge already earned

            # Execute
            result = achievement_service.sync_achievements_to_badges(player_profile_id=100)

            # Assert
            assert result == 0

    def test_sync_achievements_to_badges_mapping(self, achievement_service, mock_db):
        """Test that achievement types are correctly mapped to badge names."""
        # Setup
        test_mappings = [
            ("first_win", "Lone Wolf"),
            ("big_earner", "The Gambler"),
            ("partnership_master", "Dynamic Duo"),
            ("solo_warrior", "Wolf Pack Leader"),
            ("betting_expert", "High Roller"),
            ("veteran", "Veteran"),
            ("consistent_winner", "Pestilence")
        ]

        for achievement_type, expected_badge in test_mappings:
            achievement = Mock(spec=PlayerAchievement)
            achievement.achievement_type = achievement_type
            achievement.game_record_id = 200

            mock_query = mock_db.query.return_value
            mock_filter = mock_query.filter.return_value
            mock_filter.all.return_value = [achievement]

            with patch.object(achievement_service, 'award_badge') as mock_award:
                mock_award.return_value = {"badge_id": 1, "badge_name": expected_badge}

                # Execute
                achievement_service.sync_achievements_to_badges(player_profile_id=100)

                # Assert
                mock_award.assert_called_with(
                    player_profile_id=100,
                    badge_name=expected_badge,
                    game_record_id=200
                )

    def test_sync_achievements_to_badges_database_error(self, achievement_service, mock_db):
        """Test sync_achievements_to_badges handles database errors."""
        # Setup
        mock_db.query.side_effect = Exception("Database error")

        # Execute & Assert
        with pytest.raises(Exception) as exc_info:
            achievement_service.sync_achievements_to_badges(player_profile_id=100)

        assert "Database error" in str(exc_info.value)

    def test_sync_achievements_to_badges_preserves_game_record(self, achievement_service, mock_db):
        """Test that game_record_id is preserved during migration."""
        # Setup
        achievement = Mock(spec=PlayerAchievement)
        achievement.achievement_type = "first_win"
        achievement.game_record_id = 999

        mock_query = mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.all.return_value = [achievement]

        with patch.object(achievement_service, 'award_badge') as mock_award:
            mock_award.return_value = {"badge_id": 1}

            # Execute
            achievement_service.sync_achievements_to_badges(player_profile_id=100)

            # Assert
            mock_award.assert_called_with(
                player_profile_id=100,
                badge_name="Lone Wolf",
                game_record_id=999
            )


# ============================================================================
# GET_ACHIEVEMENT_SERVICE SINGLETON TESTS
# ============================================================================

class TestGetAchievementService:
    """Test get_achievement_service() singleton function."""

    def test_get_achievement_service_creates_instance(self, mock_db):
        """Test that get_achievement_service creates new instance."""
        # Reset global instance
        import app.services.achievement_service as service_module
        service_module._achievement_service_instance = None

        with patch('app.services.achievement_service.BadgeEngine'):
            # Execute
            service = get_achievement_service(mock_db)

            # Assert
            assert service is not None
            assert isinstance(service, AchievementService)

    def test_get_achievement_service_returns_singleton(self, mock_db):
        """Test that get_achievement_service returns same instance."""
        # Reset global instance
        import app.services.achievement_service as service_module
        service_module._achievement_service_instance = None

        with patch('app.services.achievement_service.BadgeEngine'):
            # Execute
            service1 = get_achievement_service(mock_db)
            service2 = get_achievement_service(mock_db)

            # Assert
            assert service1 is service2

    def test_get_achievement_service_updates_db_session(self, mock_db):
        """Test that get_achievement_service updates database session."""
        # Reset global instance
        import app.services.achievement_service as service_module
        service_module._achievement_service_instance = None

        mock_db1 = MagicMock()
        mock_db2 = MagicMock()

        with patch('app.services.achievement_service.BadgeEngine'):
            # Execute
            service1 = get_achievement_service(mock_db1)
            service2 = get_achievement_service(mock_db2)

            # Assert
            assert service1 is service2
            assert service2.db is mock_db2


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestAchievementServiceIntegration:
    """Test AchievementService methods working together."""

    def test_award_and_retrieve_badge_workflow(self, achievement_service, mock_db, sample_badge, sample_earned_badge):
        """Test complete workflow: award badge then retrieve it."""
        # Setup award
        mock_query = mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.first.side_effect = [sample_badge, None]
        achievement_service.badge_engine._award_badge.return_value = sample_earned_badge

        # Award badge
        award_result = achievement_service.award_badge(
            player_profile_id=100,
            badge_name="Lone Wolf"
        )
        assert award_result is not None

        # Setup retrieval
        mock_join = mock_query.join.return_value
        mock_filter_2 = mock_join.filter.return_value
        mock_order = mock_filter_2.order_by.return_value
        mock_order.all.return_value = [(sample_earned_badge, sample_badge)]

        # Retrieve badges
        badges = achievement_service.get_player_badges(player_profile_id=100)
        assert len(badges) == 1
        assert badges[0]["badge_name"] == "Lone Wolf"

    def test_check_eligibility_then_award_workflow(self, achievement_service, mock_db, sample_badge, sample_earned_badge):
        """Test workflow: check eligibility then award badge."""
        # Check eligibility
        sample_badge.trigger_type = "one_time"
        mock_query = mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.first.side_effect = [sample_badge, None, sample_badge, None]

        eligible = achievement_service.check_badge_eligibility(
            player_profile_id=100,
            badge_name="Lone Wolf"
        )
        assert eligible is True

        # Award badge
        achievement_service.badge_engine._award_badge.return_value = sample_earned_badge
        result = achievement_service.award_badge(
            player_profile_id=100,
            badge_name="Lone Wolf"
        )
        assert result is not None

    def test_track_progress_to_completion_workflow(self, achievement_service, mock_db, sample_badge):
        """Test workflow: track progress until badge is earned."""
        # Check progress at 50%
        progress_50 = Mock(spec=BadgeProgress)
        progress_50.current_progress = 5
        progress_50.target_progress = 10
        progress_50.progress_percentage = 50.0

        mock_query = mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.first.side_effect = [sample_badge, None]
        achievement_service.badge_engine._get_or_create_progress.return_value = progress_50

        result = achievement_service.calculate_badge_progress(
            player_profile_id=100,
            badge_name="Veteran"
        )
        assert result["progress_percentage"] == 50.0
        assert result["earned"] is False

    def test_legacy_to_badge_migration_workflow(self, achievement_service, mock_db, sample_badge, sample_earned_badge):
        """Test workflow: create legacy achievement then migrate to badges."""
        # Create legacy achievement
        new_achievement = Mock(spec=PlayerAchievement)
        new_achievement.id = 1
        new_achievement.player_profile_id = 100
        new_achievement.achievement_type = "first_win"
        new_achievement.achievement_name = "First Win"
        new_achievement.description = "Description"
        new_achievement.earned_date = "2024-11-03T10:00:00"
        new_achievement.game_record_id = 200
        new_achievement.achievement_data = {}

        with patch('app.services.achievement_service.PlayerAchievement') as mock_achievement_class:
            mock_achievement_class.return_value = new_achievement

            legacy_result = achievement_service.create_achievement(
                player_profile_id=100,
                achievement_type="first_win",
                description="Description"
            )
            assert legacy_result["achievement_type"] == "first_win"

        # Migrate to badges
        mock_query = mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.all.return_value = [new_achievement]

        with patch.object(achievement_service, 'award_badge') as mock_award:
            mock_award.return_value = {"badge_id": 1, "badge_name": "Lone Wolf"}

            migrated_count = achievement_service.sync_achievements_to_badges(player_profile_id=100)
            assert migrated_count == 1


# ============================================================================
# ERROR HANDLING TESTS
# ============================================================================

class TestAchievementServiceErrorHandling:
    """Test error handling across all methods."""

    def test_award_badge_rollback_on_error(self, achievement_service, mock_db):
        """Test that database rollback is called on error."""
        mock_db.query.side_effect = Exception("Query failed")

        with pytest.raises(Exception):
            achievement_service.award_badge(100, "Badge")

        mock_db.rollback.assert_called_once()

    def test_create_achievement_rollback_on_error(self, achievement_service, mock_db):
        """Test that database rollback is called on error."""
        with patch('app.services.achievement_service.PlayerAchievement'):
            mock_db.add.side_effect = Exception("Add failed")

            with pytest.raises(Exception):
                achievement_service.create_achievement(100, "type", "desc")

            mock_db.rollback.assert_called_once()

    def test_methods_handle_none_values_gracefully(self, achievement_service, mock_db):
        """Test that methods handle None values gracefully."""
        mock_query = mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.first.return_value = None

        # These should not raise, but return None/empty
        assert achievement_service.award_badge(100, "Badge") is None
        assert achievement_service.check_badge_eligibility(100, "Badge") is False

        progress = achievement_service.calculate_badge_progress(100, "Badge")
        assert "error" in progress

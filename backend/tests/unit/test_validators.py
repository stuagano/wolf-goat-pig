"""
Comprehensive unit tests for Wolf Goat Pig validators.

Tests all three validator classes:
- HandicapValidator: USGA handicap calculations and stroke allocation
- BettingValidator: Betting rules and wager validation
- GameStateValidator: Game state transitions and phase validation

Author: Test Suite
Date: 2024-11-03
"""

import pytest
from typing import List, Dict
from app.validators import (
    HandicapValidator,
    BettingValidator,
    GameStateValidator,
    HandicapValidationError,
    BettingValidationError,
    GameStateValidationError,
    ValidationError
)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def valid_handicaps():
    """Valid handicap values for testing."""
    return [0.0, 5.5, 10.0, 18.0, 25.5, 36.0, 54.0]


@pytest.fixture
def invalid_handicaps():
    """Invalid handicap values for testing."""
    return [-1.0, -10.0, 55.0, 60.0, 100.0]


@pytest.fixture
def stroke_indexes():
    """Valid stroke index list (1-18)."""
    return list(range(1, 19))


@pytest.fixture
def valid_course_data():
    """Valid course rating data."""
    return {
        "course_rating": 72.5,
        "slope_rating": 113,
        "par": 72
    }


@pytest.fixture
def sample_players():
    """Sample player data for team validation."""
    return [
        {"id": "p1", "name": "Alice", "handicap": 10.0},
        {"id": "p2", "name": "Bob", "handicap": 15.0},
        {"id": "p3", "name": "Charlie", "handicap": 20.0},
        {"id": "p4", "name": "Dave", "handicap": 12.0}
    ]


# ============================================================================
# HANDICAP VALIDATOR TESTS
# ============================================================================

class TestHandicapValidator:
    """Test HandicapValidator methods."""

    # ========================================================================
    # validate_handicap tests
    # ========================================================================

    def test_validate_handicap_valid_zero(self):
        """Test handicap validation with zero (scratch golfer)."""
        # Should not raise
        HandicapValidator.validate_handicap(0.0)

    def test_validate_handicap_valid_mid_range(self, valid_handicaps):
        """Test handicap validation with valid mid-range values."""
        for handicap in valid_handicaps:
            HandicapValidator.validate_handicap(handicap)

    def test_validate_handicap_valid_max(self):
        """Test handicap validation at maximum (54.0)."""
        HandicapValidator.validate_handicap(54.0)

    def test_validate_handicap_negative(self):
        """Test handicap validation rejects negative values."""
        with pytest.raises(HandicapValidationError) as exc_info:
            HandicapValidator.validate_handicap(-5.0)

        assert "cannot be less than 0" in str(exc_info.value)
        assert exc_info.value.field == "handicap"
        assert exc_info.value.details["value"] == -5.0
        assert exc_info.value.details["min"] == 0.0

    def test_validate_handicap_too_high(self):
        """Test handicap validation rejects values above 54."""
        with pytest.raises(HandicapValidationError) as exc_info:
            HandicapValidator.validate_handicap(60.0)

        assert "cannot exceed 54" in str(exc_info.value)
        assert exc_info.value.field == "handicap"
        assert exc_info.value.details["value"] == 60.0
        assert exc_info.value.details["max"] == 54.0

    def test_validate_handicap_not_number(self):
        """Test handicap validation rejects non-numeric values."""
        with pytest.raises(HandicapValidationError) as exc_info:
            HandicapValidator.validate_handicap("10.5")

        assert "must be a number" in str(exc_info.value)
        assert exc_info.value.details["type"] == "str"

    def test_validate_handicap_custom_field_name(self):
        """Test handicap validation with custom field name."""
        with pytest.raises(HandicapValidationError) as exc_info:
            HandicapValidator.validate_handicap(60.0, field_name="player_handicap")

        assert "player_handicap" in str(exc_info.value)
        assert exc_info.value.field == "player_handicap"

    def test_validate_handicap_edge_cases(self):
        """Test handicap validation at boundary values."""
        # Just inside bounds - should pass
        HandicapValidator.validate_handicap(0.1)
        HandicapValidator.validate_handicap(53.9)

        # Just outside bounds - should fail
        with pytest.raises(HandicapValidationError):
            HandicapValidator.validate_handicap(-0.1)

        with pytest.raises(HandicapValidationError):
            HandicapValidator.validate_handicap(54.1)

    # ========================================================================
    # validate_stroke_index tests
    # ========================================================================

    def test_validate_stroke_index_valid_range(self, stroke_indexes):
        """Test stroke index validation for all valid values (1-18)."""
        for index in stroke_indexes:
            HandicapValidator.validate_stroke_index(index)

    def test_validate_stroke_index_below_range(self):
        """Test stroke index validation rejects values below 1."""
        with pytest.raises(HandicapValidationError) as exc_info:
            HandicapValidator.validate_stroke_index(0)

        assert "must be between 1 and 18" in str(exc_info.value)
        assert exc_info.value.details["value"] == 0
        assert exc_info.value.details["min"] == 1
        assert exc_info.value.details["max"] == 18

    def test_validate_stroke_index_above_range(self):
        """Test stroke index validation rejects values above 18."""
        with pytest.raises(HandicapValidationError) as exc_info:
            HandicapValidator.validate_stroke_index(19)

        assert "must be between 1 and 18" in str(exc_info.value)

    def test_validate_stroke_index_not_integer(self):
        """Test stroke index validation rejects non-integer values."""
        with pytest.raises(HandicapValidationError) as exc_info:
            HandicapValidator.validate_stroke_index(5.5)

        assert "must be an integer" in str(exc_info.value)


    # ========================================================================
    # calculate_net_score tests
    # ========================================================================

    def test_calculate_net_score_no_strokes(self):
        """Test net score calculation with no strokes received."""
        net = HandicapValidator.calculate_net_score(
            gross_score=4,
            strokes_received=0
        )
        assert net == 4

    def test_calculate_net_score_one_stroke(self):
        """Test net score calculation with one stroke received."""
        net = HandicapValidator.calculate_net_score(
            gross_score=5,
            strokes_received=1
        )
        assert net == 4

    def test_calculate_net_score_multiple_strokes(self):
        """Test net score calculation with multiple strokes received."""
        net = HandicapValidator.calculate_net_score(
            gross_score=7,
            strokes_received=2
        )
        assert net == 5

    def test_calculate_net_score_invalid_gross(self):
        """Test net score validation rejects invalid gross score."""
        with pytest.raises(HandicapValidationError) as exc_info:
            HandicapValidator.calculate_net_score(0, 1)

        assert "Gross score must be a positive number" in str(exc_info.value)

    def test_calculate_net_score_negative_strokes(self):
        """Test net score validation rejects negative strokes received."""
        with pytest.raises(HandicapValidationError) as exc_info:
            HandicapValidator.calculate_net_score(5, -1)

        assert "Strokes received must be a non-negative number" in str(exc_info.value)

    def test_calculate_net_score_without_validation(self):
        """Test net score calculation can skip validation."""
        net = HandicapValidator.calculate_net_score(
            gross_score=5,
            strokes_received=1,
            validate=False
        )
        assert net == 4

    # ========================================================================
    # validate_course_rating tests
    # ========================================================================

    def test_validate_course_rating_valid(self, valid_course_data):
        """Test course rating validation with valid data."""
        HandicapValidator.validate_course_rating(
            valid_course_data["course_rating"],
            valid_course_data["slope_rating"]
        )

    def test_validate_course_rating_below_range(self):
        """Test course rating validation rejects values below 60."""
        with pytest.raises(HandicapValidationError) as exc_info:
            HandicapValidator.validate_course_rating(55.0, 113)

        assert "Course rating must be between 60.0 and 85.0" in str(exc_info.value)
        assert exc_info.value.details["min"] == 60.0

    def test_validate_course_rating_above_range(self):
        """Test course rating validation rejects values above 85."""
        with pytest.raises(HandicapValidationError) as exc_info:
            HandicapValidator.validate_course_rating(90.0, 113)

        assert "Course rating must be between 60.0 and 85.0" in str(exc_info.value)

    def test_validate_course_rating_not_number(self):
        """Test course rating validation rejects non-numeric values."""
        with pytest.raises(HandicapValidationError) as exc_info:
            HandicapValidator.validate_course_rating("72.5", 113)

        assert "Course rating must be a number" in str(exc_info.value)

    def test_validate_slope_rating_below_range(self):
        """Test slope rating validation rejects values below 55."""
        with pytest.raises(HandicapValidationError) as exc_info:
            HandicapValidator.validate_course_rating(72.5, 50)

        assert "Slope rating must be between 55 and 155" in str(exc_info.value)

    def test_validate_slope_rating_above_range(self):
        """Test slope rating validation rejects values above 155."""
        with pytest.raises(HandicapValidationError) as exc_info:
            HandicapValidator.validate_course_rating(72.5, 160)

        assert "Slope rating must be between 55 and 155" in str(exc_info.value)

    def test_validate_slope_rating_not_integer(self):
        """Test slope rating validation rejects non-integer values."""
        with pytest.raises(HandicapValidationError) as exc_info:
            HandicapValidator.validate_course_rating(72.5, 113.5)

        assert "Slope rating must be an integer" in str(exc_info.value)

    # ========================================================================
    # calculate_course_handicap tests
    # ========================================================================

    def test_calculate_course_handicap_average_conditions(self):
        """Test course handicap calculation with average slope (113)."""
        course_handicap = HandicapValidator.calculate_course_handicap(
            handicap_index=10.0,
            slope_rating=113,
            course_rating=72.0,
            par=72
        )
        # (10.0 * 113 / 113) + (72.0 - 72) = 10.0
        assert course_handicap == 10

    def test_calculate_course_handicap_difficult_course(self):
        """Test course handicap calculation with high slope."""
        course_handicap = HandicapValidator.calculate_course_handicap(
            handicap_index=10.0,
            slope_rating=140,
            course_rating=74.0,
            par=72
        )
        # (10.0 * 140 / 113) + (74.0 - 72) = 12.39 + 2 = 14.39 -> rounds to 14
        assert course_handicap == 14

    def test_calculate_course_handicap_easy_course(self):
        """Test course handicap calculation with low slope."""
        course_handicap = HandicapValidator.calculate_course_handicap(
            handicap_index=10.0,
            slope_rating=90,
            course_rating=70.0,
            par=72
        )
        # (10.0 * 90 / 113) + (70.0 - 72) = 7.96 - 2 = 5.96 -> rounds to 6
        assert course_handicap == 6

    def test_calculate_course_handicap_scratch_golfer(self):
        """Test course handicap for scratch golfer."""
        course_handicap = HandicapValidator.calculate_course_handicap(
            handicap_index=0.0,
            slope_rating=113,
            course_rating=72.0,
            par=72
        )
        assert course_handicap == 0

    def test_calculate_course_handicap_invalid_par(self):
        """Test course handicap validation rejects invalid par."""
        with pytest.raises(HandicapValidationError) as exc_info:
            HandicapValidator.calculate_course_handicap(
                handicap_index=10.0,
                slope_rating=113,
                course_rating=72.0,
                par=50  # Too low
            )

        assert "Par must be between 54 and 90" in str(exc_info.value)

    # ========================================================================
    # validate_stroke_allocation tests
    # ========================================================================

    def test_validate_stroke_allocation_valid(self, valid_handicaps, stroke_indexes):
        """Test stroke allocation validation with valid data."""
        HandicapValidator.validate_stroke_allocation(
            players_handicaps=valid_handicaps[:4],
            hole_stroke_indexes=stroke_indexes
        )

    def test_validate_stroke_allocation_wrong_hole_count(self):
        """Test stroke allocation rejects incorrect number of holes."""
        with pytest.raises(HandicapValidationError) as exc_info:
            HandicapValidator.validate_stroke_allocation(
                players_handicaps=[10.0, 15.0],
                hole_stroke_indexes=list(range(1, 10))  # Only 9 holes
            )

        assert "Must have stroke indexes for all 18 holes" in str(exc_info.value)
        assert exc_info.value.details["count"] == 9
        assert exc_info.value.details["expected"] == 18

    def test_validate_stroke_allocation_duplicate_indexes(self):
        """Test stroke allocation rejects duplicate stroke indexes."""
        duplicate_indexes = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 17]  # 17 twice

        with pytest.raises(HandicapValidationError) as exc_info:
            HandicapValidator.validate_stroke_allocation(
                players_handicaps=[10.0],
                hole_stroke_indexes=duplicate_indexes
            )

        assert "Stroke indexes must be unique values 1-18" in str(exc_info.value)
        assert 17 in exc_info.value.details["duplicates"]

    def test_validate_stroke_allocation_missing_indexes(self):
        """Test stroke allocation rejects missing stroke indexes."""
        missing_indexes = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 19]  # Missing 18

        with pytest.raises(HandicapValidationError) as exc_info:
            HandicapValidator.validate_stroke_allocation(
                players_handicaps=[10.0],
                hole_stroke_indexes=missing_indexes
            )

        assert "Stroke indexes must be unique values 1-18" in str(exc_info.value)
        assert 18 in exc_info.value.details["missing"]

    def test_validate_stroke_allocation_invalid_player_handicap(self):
        """Test stroke allocation rejects invalid player handicap."""
        with pytest.raises(HandicapValidationError) as exc_info:
            HandicapValidator.validate_stroke_allocation(
                players_handicaps=[10.0, 60.0],  # 60.0 is invalid
                hole_stroke_indexes=list(range(1, 19))
            )

        assert "Invalid handicap for player 1" in str(exc_info.value)

    # ========================================================================
    # get_handicap_category tests
    # ========================================================================

    def test_get_handicap_category_scratch(self):
        """Test handicap category for scratch golfers."""
        assert HandicapValidator.get_handicap_category(0.0) == "SCRATCH"
        assert HandicapValidator.get_handicap_category(3.5) == "SCRATCH"
        assert HandicapValidator.get_handicap_category(5.0) == "SCRATCH"

    def test_get_handicap_category_low(self):
        """Test handicap category for low handicap golfers."""
        assert HandicapValidator.get_handicap_category(6.0) == "LOW"
        assert HandicapValidator.get_handicap_category(9.5) == "LOW"
        assert HandicapValidator.get_handicap_category(12.0) == "LOW"

    def test_get_handicap_category_mid(self):
        """Test handicap category for mid handicap golfers."""
        assert HandicapValidator.get_handicap_category(13.0) == "MID"
        assert HandicapValidator.get_handicap_category(16.5) == "MID"
        assert HandicapValidator.get_handicap_category(20.0) == "MID"

    def test_get_handicap_category_high(self):
        """Test handicap category for high handicap golfers."""
        assert HandicapValidator.get_handicap_category(21.0) == "HIGH"
        assert HandicapValidator.get_handicap_category(25.5) == "HIGH"
        assert HandicapValidator.get_handicap_category(30.0) == "HIGH"

    def test_get_handicap_category_beginner(self):
        """Test handicap category for beginner golfers."""
        assert HandicapValidator.get_handicap_category(31.0) == "BEGINNER"
        assert HandicapValidator.get_handicap_category(40.0) == "BEGINNER"
        assert HandicapValidator.get_handicap_category(54.0) == "BEGINNER"

    def test_get_handicap_category_invalid(self):
        """Test handicap category rejects invalid handicap."""
        with pytest.raises(HandicapValidationError):
            HandicapValidator.get_handicap_category(60.0)

    # ========================================================================
    # validate_team_handicaps tests
    # ========================================================================

    def test_validate_team_handicaps_balanced(self):
        """Test team handicap validation with balanced teams."""
        result = HandicapValidator.validate_team_handicaps(
            team1_handicaps=[10.0, 15.0],
            team2_handicaps=[12.0, 13.0]
        )

        assert result["valid"] is True
        assert result["team1_average"] == 12.5
        assert result["team2_average"] == 12.5
        assert result["difference"] == 0.0
        assert result["balanced"] is True

    def test_validate_team_handicaps_acceptable_difference(self):
        """Test team handicap validation with acceptable difference."""
        result = HandicapValidator.validate_team_handicaps(
            team1_handicaps=[8.0, 12.0],  # avg 10.0
            team2_handicaps=[14.0, 18.0],  # avg 16.0
            max_difference=10.0
        )

        assert result["valid"] is True
        assert result["difference"] == 6.0
        assert result["balanced"] is False  # difference > max_difference/2

    def test_validate_team_handicaps_too_unbalanced(self):
        """Test team handicap validation rejects unbalanced teams."""
        with pytest.raises(HandicapValidationError) as exc_info:
            HandicapValidator.validate_team_handicaps(
                team1_handicaps=[5.0, 8.0],  # avg 6.5
                team2_handicaps=[20.0, 25.0],  # avg 22.5
                max_difference=10.0
            )

        assert "Team handicaps too unbalanced" in str(exc_info.value)
        assert exc_info.value.details["difference"] == 16.0
        assert exc_info.value.details["max_allowed"] == 10.0

    def test_validate_team_handicaps_invalid_player(self):
        """Test team handicap validation rejects invalid handicaps."""
        with pytest.raises(HandicapValidationError):
            HandicapValidator.validate_team_handicaps(
                team1_handicaps=[10.0, 60.0],  # 60.0 is invalid
                team2_handicaps=[12.0, 13.0]
            )

    def test_validate_team_handicaps_empty_team(self):
        """Test team handicap validation with empty team (unbalanced)."""
        # Empty team vs team with players is unbalanced
        with pytest.raises(HandicapValidationError) as exc_info:
            HandicapValidator.validate_team_handicaps(
                team1_handicaps=[],
                team2_handicaps=[12.0, 13.0]
            )

        assert "Team handicaps too unbalanced" in str(exc_info.value)


# ============================================================================
# BETTING VALIDATOR TESTS
# ============================================================================

class TestBettingValidator:
    """Test BettingValidator methods."""

    # ========================================================================
    # validate_base_wager tests
    # ========================================================================

    def test_validate_base_wager_valid(self):
        """Test base wager validation with valid values."""
        BettingValidator.validate_base_wager(1)
        BettingValidator.validate_base_wager(2)
        BettingValidator.validate_base_wager(5)

    def test_validate_base_wager_zero(self):
        """Test base wager validation rejects zero."""
        with pytest.raises(BettingValidationError) as exc_info:
            BettingValidator.validate_base_wager(0)

        assert "Base wager must be positive" in str(exc_info.value)

    def test_validate_base_wager_negative(self):
        """Test base wager validation rejects negative values."""
        with pytest.raises(BettingValidationError) as exc_info:
            BettingValidator.validate_base_wager(-1)

        assert "Base wager must be positive" in str(exc_info.value)

    def test_validate_base_wager_not_integer(self):
        """Test base wager validation rejects non-integer values."""
        with pytest.raises(BettingValidationError) as exc_info:
            BettingValidator.validate_base_wager(1.5)

        assert "Base wager must be an integer" in str(exc_info.value)

    # ========================================================================
    # validate_double tests
    # ========================================================================

    def test_validate_double_allowed(self):
        """Test double validation when allowed."""
        BettingValidator.validate_double(
            already_doubled=False,
            wagering_closed=False,
            partnership_formed=True
        )

    def test_validate_double_already_doubled(self):
        """Test double validation rejects when already doubled."""
        with pytest.raises(BettingValidationError) as exc_info:
            BettingValidator.validate_double(
                already_doubled=True,
                wagering_closed=False,
                partnership_formed=True
            )

        assert "already been doubled" in str(exc_info.value)

    def test_validate_double_wagering_closed(self):
        """Test double validation rejects when wagering closed."""
        with pytest.raises(BettingValidationError) as exc_info:
            BettingValidator.validate_double(
                already_doubled=False,
                wagering_closed=True,
                partnership_formed=True
            )

        assert "Wagering is closed" in str(exc_info.value)

    def test_validate_double_no_partnership(self):
        """Test double validation rejects when no partnership formed."""
        with pytest.raises(BettingValidationError) as exc_info:
            BettingValidator.validate_double(
                already_doubled=False,
                wagering_closed=False,
                partnership_formed=False
            )

        assert "Partnership must be formed" in str(exc_info.value)

    # ========================================================================
    # validate_duncan tests
    # ========================================================================

    def test_validate_duncan_allowed(self):
        """Test Duncan validation when allowed."""
        BettingValidator.validate_duncan(
            is_captain=True,
            partnership_formed=False,
            tee_shots_complete=False
        )

    def test_validate_duncan_not_captain(self):
        """Test Duncan validation rejects non-captain."""
        with pytest.raises(BettingValidationError) as exc_info:
            BettingValidator.validate_duncan(
                is_captain=False,
                partnership_formed=False,
                tee_shots_complete=False
            )

        assert "Only the captain can invoke The Duncan" in str(exc_info.value)

    def test_validate_duncan_partnership_formed(self):
        """Test Duncan validation rejects after partnership formed."""
        with pytest.raises(BettingValidationError) as exc_info:
            BettingValidator.validate_duncan(
                is_captain=True,
                partnership_formed=True,
                tee_shots_complete=False
            )

        assert "Cannot invoke The Duncan after partnership formed" in str(exc_info.value)

    def test_validate_duncan_after_tee_shots(self):
        """Test Duncan validation rejects after tee shots complete."""
        with pytest.raises(BettingValidationError) as exc_info:
            BettingValidator.validate_duncan(
                is_captain=True,
                partnership_formed=False,
                tee_shots_complete=True
            )

        assert "Cannot invoke The Duncan after tee shots complete" in str(exc_info.value)

    # ========================================================================
    # validate_carry_over tests
    # ========================================================================

    def test_validate_carry_over_allowed(self):
        """Test carry over validation when allowed."""
        BettingValidator.validate_carry_over(
            hole_number=5,
            previous_hole_tied=True
        )

    def test_validate_carry_over_first_hole(self):
        """Test carry over validation rejects on first hole."""
        with pytest.raises(BettingValidationError) as exc_info:
            BettingValidator.validate_carry_over(
                hole_number=1,
                previous_hole_tied=True
            )

        assert "Cannot carry over on first hole" in str(exc_info.value)

    def test_validate_carry_over_not_tied(self):
        """Test carry over validation rejects when previous hole not tied."""
        with pytest.raises(BettingValidationError) as exc_info:
            BettingValidator.validate_carry_over(
                hole_number=5,
                previous_hole_tied=False
            )

        assert "Previous hole must have been tied" in str(exc_info.value)

    # ========================================================================
    # calculate_wager_multiplier tests
    # ========================================================================

    def test_calculate_wager_multiplier_base(self):
        """Test wager multiplier calculation with no modifiers."""
        multiplier = BettingValidator.calculate_wager_multiplier(
            doubled=False,
            carry_over=False,
            duncan=False
        )
        assert multiplier == 1

    def test_calculate_wager_multiplier_doubled(self):
        """Test wager multiplier calculation with double."""
        multiplier = BettingValidator.calculate_wager_multiplier(
            doubled=True,
            carry_over=False,
            duncan=False
        )
        assert multiplier == 2

    def test_calculate_wager_multiplier_carry_over(self):
        """Test wager multiplier calculation with carry over."""
        multiplier = BettingValidator.calculate_wager_multiplier(
            doubled=False,
            carry_over=True,
            duncan=False
        )
        assert multiplier == 2

    def test_calculate_wager_multiplier_duncan(self):
        """Test wager multiplier calculation with Duncan."""
        multiplier = BettingValidator.calculate_wager_multiplier(
            doubled=False,
            carry_over=False,
            duncan=True
        )
        assert multiplier == 2

    def test_calculate_wager_multiplier_all_modifiers(self):
        """Test wager multiplier calculation with all modifiers."""
        multiplier = BettingValidator.calculate_wager_multiplier(
            doubled=True,
            carry_over=True,
            duncan=True
        )
        # 2 (double) * 2 (carry) * 2 (duncan) = 8
        assert multiplier == 8

    # ========================================================================
    # calculate_total_wager tests
    # ========================================================================

    def test_calculate_total_wager_base(self):
        """Test total wager calculation with base wager."""
        total = BettingValidator.calculate_total_wager(
            base_wager=1,
            multiplier=1
        )
        assert total == 1

    def test_calculate_total_wager_doubled(self):
        """Test total wager calculation with double."""
        total = BettingValidator.calculate_total_wager(
            base_wager=1,
            multiplier=2
        )
        assert total == 2

    def test_calculate_total_wager_high_stakes(self):
        """Test total wager calculation with high stakes."""
        total = BettingValidator.calculate_total_wager(
            base_wager=5,
            multiplier=8
        )
        assert total == 40


# ============================================================================
# GAME STATE VALIDATOR TESTS
# ============================================================================

class TestGameStateValidator:
    """Test GameStateValidator methods."""

    # ========================================================================
    # validate_game_phase tests
    # ========================================================================

    def test_validate_game_phase_valid(self):
        """Test game phase validation with valid phases."""
        GameStateValidator.validate_game_phase("SETUP")
        GameStateValidator.validate_game_phase("PRE_TEE")
        GameStateValidator.validate_game_phase("PLAYING")
        GameStateValidator.validate_game_phase("COMPLETED")

    def test_validate_game_phase_invalid(self):
        """Test game phase validation rejects invalid phase."""
        with pytest.raises(GameStateValidationError) as exc_info:
            GameStateValidator.validate_game_phase("INVALID_PHASE")

        assert "Invalid game phase" in str(exc_info.value)

    # ========================================================================
    # validate_player_count tests
    # ========================================================================

    def test_validate_player_count_valid(self):
        """Test player count validation with valid counts."""
        # Wolf-Goat-Pig requires 4, 5, or 6 players
        GameStateValidator.validate_player_count(4)
        GameStateValidator.validate_player_count(5)
        GameStateValidator.validate_player_count(6)

    def test_validate_player_count_too_few(self):
        """Test player count validation rejects too few players."""
        with pytest.raises(GameStateValidationError) as exc_info:
            GameStateValidator.validate_player_count(1)

        assert "4, 5, or 6 players required" in str(exc_info.value)

    def test_validate_player_count_too_many(self):
        """Test player count validation rejects too many players."""
        with pytest.raises(GameStateValidationError) as exc_info:
            GameStateValidator.validate_player_count(7)

        assert "4, 5, or 6 players required" in str(exc_info.value)

    # ========================================================================
    # validate_hole_number tests
    # ========================================================================

    def test_validate_hole_number_valid(self):
        """Test hole number validation with valid holes."""
        for hole in range(1, 19):
            GameStateValidator.validate_hole_number(hole)

    def test_validate_hole_number_zero(self):
        """Test hole number validation rejects zero."""
        with pytest.raises(GameStateValidationError) as exc_info:
            GameStateValidator.validate_hole_number(0)

        assert "Hole number must be between 1 and 18" in str(exc_info.value)

    def test_validate_hole_number_too_high(self):
        """Test hole number validation rejects numbers above 18."""
        with pytest.raises(GameStateValidationError) as exc_info:
            GameStateValidator.validate_hole_number(19)

        assert "Hole number must be between 1 and 18" in str(exc_info.value)

    # ========================================================================
    # validate_player_action tests
    # ========================================================================

    def test_validate_player_action_valid(self):
        """Test player action validation when allowed."""
        GameStateValidator.validate_player_action(
            player_id="p1",
            action="shoot",
            current_player="p1",
            game_phase="PLAYING"
        )

    def test_validate_player_action_wrong_player(self):
        """Test player action validation rejects wrong player."""
        with pytest.raises(GameStateValidationError) as exc_info:
            GameStateValidator.validate_player_action(
                player_id="p2",
                action="shoot",
                current_player="p1",
                game_phase="PLAYING"
            )

        assert "Not your turn" in str(exc_info.value)

    def test_validate_player_action_wrong_phase(self):
        """Test player action validation rejects action in wrong phase."""
        with pytest.raises(GameStateValidationError) as exc_info:
            GameStateValidator.validate_player_action(
                player_id="p1",
                action="shoot",
                current_player="p1",
                game_phase="SETUP"
            )

        assert "Cannot perform action in current game phase" in str(exc_info.value)

    # ========================================================================
    # validate_partnership_formation tests
    # ========================================================================

    def test_validate_partnership_formation_valid(self):
        """Test partnership formation validation when allowed."""
        GameStateValidator.validate_partnership_formation(
            captain_id="p1",
            partner_id="p2",
            tee_shots_complete=False
        )

    def test_validate_partnership_formation_self(self):
        """Test partnership formation validation rejects self-partnership."""
        with pytest.raises(GameStateValidationError) as exc_info:
            GameStateValidator.validate_partnership_formation(
                captain_id="p1",
                partner_id="p1",
                tee_shots_complete=False
            )

        assert "Cannot partner with yourself" in str(exc_info.value)

    def test_validate_partnership_formation_after_deadline(self):
        """Test partnership formation validation rejects after deadline."""
        with pytest.raises(GameStateValidationError) as exc_info:
            GameStateValidator.validate_partnership_formation(
                captain_id="p1",
                partner_id="p2",
                tee_shots_complete=True
            )

        assert "Partnership deadline has passed" in str(exc_info.value)

    # ========================================================================
    # validate_shot_execution tests
    # ========================================================================

    def test_validate_shot_execution_valid(self):
        """Test shot execution validation when allowed."""
        GameStateValidator.validate_shot_execution(
            player_id="p1",
            hole_complete=False,
            player_holed=False
        )

    def test_validate_shot_execution_hole_complete(self):
        """Test shot execution validation rejects when hole complete."""
        with pytest.raises(GameStateValidationError) as exc_info:
            GameStateValidator.validate_shot_execution(
                player_id="p1",
                hole_complete=True,
                player_holed=False
            )

        assert "Hole is already complete" in str(exc_info.value)

    def test_validate_shot_execution_player_holed(self):
        """Test shot execution validation rejects when player already holed."""
        with pytest.raises(GameStateValidationError) as exc_info:
            GameStateValidator.validate_shot_execution(
                player_id="p1",
                hole_complete=False,
                player_holed=True
            )

        assert "Player has already holed out" in str(exc_info.value)

    # ========================================================================
    # validate_game_start tests
    # ========================================================================

    def test_validate_game_start_valid(self):
        """Test game start validation with valid conditions."""
        GameStateValidator.validate_game_start(
            player_count=4,
            course_selected=True,
            all_players_ready=True
        )

    def test_validate_game_start_no_course(self):
        """Test game start validation rejects without course."""
        with pytest.raises(GameStateValidationError) as exc_info:
            GameStateValidator.validate_game_start(
                player_count=4,
                course_selected=False,
                all_players_ready=True
            )

        assert "Course must be selected" in str(exc_info.value)

    def test_validate_game_start_players_not_ready(self):
        """Test game start validation rejects when players not ready."""
        with pytest.raises(GameStateValidationError) as exc_info:
            GameStateValidator.validate_game_start(
                player_count=4,
                course_selected=True,
                all_players_ready=False
            )

        assert "All players must be ready" in str(exc_info.value)

    def test_validate_game_start_invalid_player_count(self):
        """Test game start validation rejects invalid player count."""
        with pytest.raises(GameStateValidationError) as exc_info:
            GameStateValidator.validate_game_start(
                player_count=1,
                course_selected=True,
                all_players_ready=True
            )

        assert "4, 5, or 6 players required" in str(exc_info.value)

    # ========================================================================
    # validate_hole_completion tests
    # ========================================================================

    def test_validate_hole_completion_valid(self):
        """Test hole completion validation with all players finished."""
        GameStateValidator.validate_hole_completion(
            players_holed=["p1", "p2", "p3", "p4"],
            total_players=4
        )

    def test_validate_hole_completion_incomplete(self):
        """Test hole completion validation rejects when players remain."""
        with pytest.raises(GameStateValidationError) as exc_info:
            GameStateValidator.validate_hole_completion(
                players_holed=["p1", "p2"],
                total_players=4
            )

        assert "Not all players have completed the hole" in str(exc_info.value)
        assert exc_info.value.details["completed"] == 2
        assert exc_info.value.details["total"] == 4


# ============================================================================
# EXCEPTION TESTS
# ============================================================================

class TestValidationExceptions:
    """Test validation exception behavior."""

    def test_validation_error_basic(self):
        """Test basic ValidationError creation."""
        error = ValidationError("Test error")
        assert str(error) == "Test error"
        assert error.message == "Test error"
        assert error.field is None
        assert error.details == {}

    def test_validation_error_with_field(self):
        """Test ValidationError with field."""
        error = ValidationError("Test error", field="test_field")
        assert error.field == "test_field"

    def test_validation_error_with_details(self):
        """Test ValidationError with details."""
        details = {"value": 60.0, "max": 54.0}
        error = ValidationError("Test error", details=details)
        assert error.details == details

    def test_validation_error_to_dict(self):
        """Test ValidationError to_dict method."""
        error = ValidationError(
            "Test error",
            field="test_field",
            details={"value": 60.0}
        )

        error_dict = error.to_dict()
        assert error_dict["error"] == "Test error"
        assert error_dict["field"] == "test_field"
        assert error_dict["details"]["value"] == 60.0

    def test_handicap_validation_error_inheritance(self):
        """Test HandicapValidationError inherits from ValidationError."""
        error = HandicapValidationError("Handicap error")
        assert isinstance(error, ValidationError)
        assert isinstance(error, HandicapValidationError)

    def test_betting_validation_error_inheritance(self):
        """Test BettingValidationError inherits from ValidationError."""
        error = BettingValidationError("Betting error")
        assert isinstance(error, ValidationError)
        assert isinstance(error, BettingValidationError)

    def test_game_state_validation_error_inheritance(self):
        """Test GameStateValidationError inherits from ValidationError."""
        error = GameStateValidationError("Game state error")
        assert isinstance(error, ValidationError)
        assert isinstance(error, GameStateValidationError)


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestValidatorIntegration:
    """Test validators working together."""

    def test_full_handicap_workflow(self):
        """Test complete handicap calculation workflow."""
        # 1. Validate player handicap
        handicap_index = 15.0
        HandicapValidator.validate_handicap(handicap_index)

        # 2. Validate course ratings
        course_rating = 72.5
        slope_rating = 130
        HandicapValidator.validate_course_rating(course_rating, slope_rating)

        # 3. Calculate course handicap
        course_handicap = HandicapValidator.calculate_course_handicap(
            handicap_index=handicap_index,
            slope_rating=slope_rating,
            course_rating=course_rating,
            par=72
        )

        # 4. Calculate strokes received on a hole
        stroke_index = 5
        strokes = HandicapValidator.calculate_strokes_received_with_creecher(
            course_handicap=course_handicap,
            stroke_index=stroke_index
        )

        # 5. Calculate net score
        gross_score = 5
        net_score = HandicapValidator.calculate_net_score(
            gross_score=gross_score,
            strokes_received=strokes
        )

        assert net_score < gross_score  # Net should be better than gross

    def test_full_betting_workflow(self):
        """Test complete betting workflow."""
        # 1. Validate base wager
        base_wager = 1
        BettingValidator.validate_base_wager(base_wager)

        # 2. Validate double
        BettingValidator.validate_double(
            already_doubled=False,
            wagering_closed=False,
            partnership_formed=True
        )

        # 3. Calculate multiplier
        multiplier = BettingValidator.calculate_wager_multiplier(
            doubled=True,
            carry_over=False,
            duncan=False
        )

        # 4. Calculate total wager
        total = BettingValidator.calculate_total_wager(
            base_wager=base_wager,
            multiplier=multiplier
        )

        assert total == 2  # Base wager doubled

    def test_full_game_state_workflow(self):
        """Test complete game state workflow."""
        # 1. Validate game start
        GameStateValidator.validate_game_start(
            player_count=4,
            course_selected=True,
            all_players_ready=True
        )

        # 2. Validate hole number
        hole_number = 1
        GameStateValidator.validate_hole_number(hole_number)

        # 3. Validate player action
        GameStateValidator.validate_player_action(
            player_id="p1",
            action="shoot",
            current_player="p1",
            game_phase="PLAYING"
        )

        # 4. Validate shot execution
        GameStateValidator.validate_shot_execution(
            player_id="p1",
            hole_complete=False,
            player_holed=False
        )

        # Workflow should complete without errors

    def test_cross_validator_scenario(self):
        """Test scenario involving multiple validators."""
        # Setup: 4 players starting a game
        players = [
            {"id": "p1", "handicap": 10.0},
            {"id": "p2", "handicap": 15.0},
            {"id": "p3", "handicap": 20.0},
            {"id": "p4", "handicap": 12.0}
        ]

        # 1. Game state: validate start
        GameStateValidator.validate_game_start(
            player_count=len(players),
            course_selected=True,
            all_players_ready=True
        )

        # 2. Handicap: validate all player handicaps
        for player in players:
            HandicapValidator.validate_handicap(player["handicap"])

        # 3. Game state: validate hole
        hole_number = 1
        GameStateValidator.validate_hole_number(hole_number)

        # 4. Betting: validate base wager
        base_wager = 1
        BettingValidator.validate_base_wager(base_wager)

        # 5. Game state: validate partnership
        GameStateValidator.validate_partnership_formation(
            captain_id="p1",
            partner_id="p2",
            tee_shots_complete=False
        )

        # 6. Betting: validate double
        BettingValidator.validate_double(
            already_doubled=False,
            wagering_closed=False,
            partnership_formed=True
        )

        # All validations should pass

"""
Handicap Validator for Wolf Goat Pig.

Validates all handicap-related calculations and ensures USGA compliance.
Centralizes handicap validation logic that was previously scattered across
Player, StrokeAdvantage, and various service classes.
"""

import logging
import warnings
from typing import List, Dict, Any, Optional, Union
from .exceptions import HandicapValidationError

logger = logging.getLogger(__name__)


class HandicapValidator:
    """
    Validates handicap calculations and USGA compliance.

    Ensures:
    - Handicaps are within valid range (0-54)
    - Stroke allocation follows USGA rules
    - Net scores are calculated correctly
    - Course handicaps are properly derived from handicap index
    """

    # USGA Handicap Limits
    MIN_HANDICAP = 0.0
    MAX_HANDICAP = 54.0

    # Stroke index range (handicap per hole)
    MIN_STROKE_INDEX = 1
    MAX_STROKE_INDEX = 18

    @staticmethod
    def validate_and_normalize_handicap(
        handicap: Optional[Union[int, float, str]],
        player_name: Optional[str] = None
    ) -> float:
        """
        Validate and normalize handicap value with fallback to default.

        Handles missing, invalid, or out-of-range handicap values by falling back
        to the default handicap of 18.0 with appropriate logging.

        Args:
            handicap: Handicap value (any type)
            player_name: Optional player name for logging

        Returns:
            Valid handicap as float (defaults to 18.0 if invalid)
        """
        DEFAULT_HANDICAP = 18.0

        # Handle missing handicap
        if handicap is None:
            if player_name:
                logger.warning(f"Player {player_name} missing handicap, using default {DEFAULT_HANDICAP}")
            else:
                logger.warning(f"Missing handicap, using default {DEFAULT_HANDICAP}")
            return DEFAULT_HANDICAP

        # Attempt to convert to float and validate
        try:
            handicap_float = float(handicap)
            # Validate handicap range using existing validator
            HandicapValidator.validate_handicap(handicap_float)
            return handicap_float
        except (ValueError, TypeError) as e:
            if player_name:
                logger.warning(f"Invalid handicap for {player_name}, using {DEFAULT_HANDICAP}")
            else:
                logger.warning(f"Invalid handicap value, using {DEFAULT_HANDICAP}")
            return DEFAULT_HANDICAP
        except HandicapValidationError as e:
            if player_name:
                logger.warning(f"Handicap validation failed for {player_name}: {e}, using {DEFAULT_HANDICAP}")
            else:
                logger.warning(f"Handicap validation failed: {e}, using {DEFAULT_HANDICAP}")
            return DEFAULT_HANDICAP

    @staticmethod
    def calculate_strength_from_handicap(handicap: float) -> int:
        """
        Calculate player strength from handicap.

        Lower handicap = higher strength.
        Formula: max(1, 10 - int(handicap))

        This provides a simple strength metric where:
        - Handicap 0 = strength 10 (best)
        - Handicap 9 = strength 1
        - Handicap 10+ = strength 1 (minimum)

        Args:
            handicap: Player's handicap index

        Returns:
            Integer strength value (minimum 1)
        """
        return max(1, 10 - int(handicap))

    @classmethod
    def validate_handicap(cls, handicap: float, field_name: str = "handicap") -> None:
        """
        Validate handicap is within USGA range (0-54).

        Args:
            handicap: Player's handicap index
            field_name: Name of field being validated (for error messages)

        Raises:
            HandicapValidationError: If handicap is invalid
        """
        if not isinstance(handicap, (int, float)):
            raise HandicapValidationError(
                f"{field_name} must be a number",
                field=field_name,
                details={"value": handicap, "type": type(handicap).__name__}
            )

        if handicap < cls.MIN_HANDICAP:
            raise HandicapValidationError(
                f"{field_name} cannot be less than {cls.MIN_HANDICAP}",
                field=field_name,
                details={"value": handicap, "min": cls.MIN_HANDICAP}
            )

        if handicap > cls.MAX_HANDICAP:
            raise HandicapValidationError(
                f"{field_name} cannot exceed {cls.MAX_HANDICAP}",
                field=field_name,
                details={"value": handicap, "max": cls.MAX_HANDICAP}
            )

    @classmethod
    def validate_stroke_index(cls, stroke_index: int, field_name: str = "stroke_index") -> None:
        """
        Validate stroke index (handicap allocation per hole).

        Args:
            stroke_index: Hole's stroke index (1-18)
            field_name: Name of field being validated

        Raises:
            HandicapValidationError: If stroke index is invalid
        """
        if not isinstance(stroke_index, int):
            raise HandicapValidationError(
                f"{field_name} must be an integer",
                field=field_name,
                details={"value": stroke_index, "type": type(stroke_index).__name__}
            )

        if stroke_index < cls.MIN_STROKE_INDEX or stroke_index > cls.MAX_STROKE_INDEX:
            raise HandicapValidationError(
                f"{field_name} must be between {cls.MIN_STROKE_INDEX} and {cls.MAX_STROKE_INDEX}",
                field=field_name,
                details={
                    "value": stroke_index,
                    "min": cls.MIN_STROKE_INDEX,
                    "max": cls.MAX_STROKE_INDEX
                }
            )


    @classmethod
    def calculate_strokes_received_with_creecher(
        cls,
        course_handicap: float,
        stroke_index: int,
        validate: bool = True
    ) -> float:
        """
        Calculate strokes received with Creecher Feature (half strokes).

        The Creecher Feature is a Wolf-Goat-Pig house rule that awards half strokes
        on certain holes to provide more granular handicapping.

        Creecher Feature Rules:
        1. Players receive full strokes on holes where stroke_index <= min(handicap, 18)
        2. Players with fractional handicaps (e.g., 10.5) get a half stroke on the
           next hardest hole (stroke_index == full_handicap + 1)
        3. For handicaps >18, the extra strokes beyond 18 are distributed as
           additional half strokes on the easiest holes (preventing 2 full strokes
           per hole). Each extra stroke = 0.5 on two easiest holes.

        Examples:
            handicap=10.5, stroke_index=10 → 1.0 (full stroke)
            handicap=10.5, stroke_index=11 → 0.5 (half stroke from fractional)
            handicap=10.5, stroke_index=12 → 0.0 (no stroke)
            handicap=20.0, stroke_index=18 → 1.5 (1.0 base + 0.5 Creecher)
            handicap=20.0, stroke_index=15 → 1.5 (1.0 base + 0.5 Creecher)
            handicap=20.0, stroke_index=14 → 1.0 (1.0 base only)

        Args:
            course_handicap: Player's course handicap (can be fractional)
            stroke_index: Hole's stroke index (1-18, where 1 is hardest)
            validate: Whether to validate inputs first

        Returns:
            Float strokes: 0.0, 0.5, 1.0, 1.5, 2.0, etc.

        Raises:
            HandicapValidationError: If validation fails
        """
        if validate:
            cls.validate_handicap(course_handicap, "course_handicap")
            cls.validate_stroke_index(stroke_index)

        # Separate full and fractional parts of handicap
        full_strokes = int(course_handicap)
        fractional_part = course_handicap - full_strokes
        has_half_stroke = fractional_part >= 0.5

        total_strokes = 0.0

        # Rule 1: Base strokes - full stroke on holes up to min(handicap, 18)
        if stroke_index <= min(full_strokes, 18):
            total_strokes += 1.0

        # Rule 3: Creecher Feature for high handicaps (>18)
        # Extra strokes beyond 18 are distributed as additional 0.5 strokes
        # on the easiest holes to avoid giving 2 full strokes per hole
        if full_strokes > 18:
            extra_strokes = full_strokes - 18

            # Distribute extra strokes as 0.5 increments using multiple passes
            # Each pass gives 0.5 to a set of easiest holes
            # Continue passes until all extra strokes are distributed
            remaining_extra = extra_strokes
            pass_sizes = [18, 18, 12, 6, 6, 6]  # Number of holes in each pass (supports up to handicap 45)

            for pass_size in pass_sizes:
                if remaining_extra <= 0:
                    break

                # How many strokes does this pass use? (Each hole gets 0.5)
                strokes_in_pass = min(remaining_extra, pass_size / 2.0)
                holes_in_pass = int(strokes_in_pass * 2)

                # Threshold: easiest holes_in_pass holes get the bonus
                threshold = 18 - holes_in_pass + 1

                if stroke_index >= threshold:
                    total_strokes += 0.5

                remaining_extra -= strokes_in_pass

            # If still have remaining extra strokes (for handicaps >45),
            # give additional full strokes on hardest holes (USGA fallback)
            if remaining_extra > 0:
                # How many holes get an additional full stroke?
                extra_full_strokes = int(remaining_extra)
                # Give to the hardest holes (lowest stroke indexes)
                if stroke_index <= extra_full_strokes:
                    total_strokes += 1.0

        # Rule 2: Fractional handicap gives half stroke on next hardest hole
        # For handicaps >18, the fractional applies differently
        if has_half_stroke:
            if full_strokes < 18:
                # Normal case: half stroke on next hole after full handicap
                if stroke_index == full_strokes + 1:
                    total_strokes += 0.5
            else:
                # For handicaps >18, fractional adds to the Creecher distribution
                # Add 0.5 to one more hole (the next easiest after current Creecher holes)
                extra_strokes = full_strokes - 18
                # Calculate how many holes already get Creecher bonuses
                num_creecher_holes = min(int(extra_strokes * 2), 18)
                threshold = 18 - num_creecher_holes

                # The fractional adds 0.5 to one more hole
                if stroke_index == threshold:
                    total_strokes += 0.5

        return total_strokes

    @classmethod
    def calculate_net_score(
        cls,
        gross_score: Union[int, float],
        strokes_received: Union[int, float],
        validate: bool = True
    ) -> float:
        """
        Calculate net score from gross score and strokes received.

        Supports both integer and float values to accommodate the Creecher Feature
        which awards half strokes (0.5). Net scores can be fractional values like
        4.5, 3.5, etc.

        Examples:
            gross=5, strokes=1 → net=4.0
            gross=5, strokes=0.5 → net=4.5
            gross=4, strokes=1.5 → net=2.5

        Args:
            gross_score: Player's actual strokes on hole (int or float)
            strokes_received: Handicap strokes for this hole (can be 0.5)
            validate: Whether to validate inputs

        Returns:
            Net score as float (gross - strokes)

        Raises:
            HandicapValidationError: If validation fails
        """
        if validate:
            if not isinstance(gross_score, (int, float)) or gross_score < 1:
                raise HandicapValidationError(
                    "Gross score must be a positive number",
                    field="gross_score",
                    details={"value": gross_score, "type": type(gross_score).__name__}
                )

            if not isinstance(strokes_received, (int, float)) or strokes_received < 0:
                raise HandicapValidationError(
                    "Strokes received must be a non-negative number",
                    field="strokes_received",
                    details={"value": strokes_received, "type": type(strokes_received).__name__}
                )

        return float(gross_score) - float(strokes_received)

    @classmethod
    def validate_course_rating(cls, course_rating: float, slope_rating: int) -> None:
        """
        Validate course rating and slope rating.

        USGA standards:
        - Course rating: typically 67-77 (can vary)
        - Slope rating: 55-155 (113 is average)

        Args:
            course_rating: Course rating from tees being played
            slope_rating: Slope rating from tees being played

        Raises:
            HandicapValidationError: If ratings are invalid
        """
        if not isinstance(course_rating, (int, float)):
            raise HandicapValidationError(
                "Course rating must be a number",
                field="course_rating",
                details={"value": course_rating}
            )

        if course_rating < 60.0 or course_rating > 85.0:
            raise HandicapValidationError(
                "Course rating must be between 60.0 and 85.0",
                field="course_rating",
                details={"value": course_rating, "min": 60.0, "max": 85.0}
            )

        if not isinstance(slope_rating, int):
            raise HandicapValidationError(
                "Slope rating must be an integer",
                field="slope_rating",
                details={"value": slope_rating}
            )

        if slope_rating < 55 or slope_rating > 155:
            raise HandicapValidationError(
                "Slope rating must be between 55 and 155",
                field="slope_rating",
                details={"value": slope_rating, "min": 55, "max": 155}
            )

    @classmethod
    def calculate_course_handicap(
        cls,
        handicap_index: float,
        slope_rating: int,
        course_rating: float,
        par: int,
        validate: bool = True
    ) -> int:
        """
        Calculate course handicap from handicap index using USGA formula.

        Formula: (Handicap Index × Slope Rating / 113) + (Course Rating - Par)

        Args:
            handicap_index: Player's handicap index
            slope_rating: Course slope rating from tees
            course_rating: Course rating from tees
            par: Par for the course
            validate: Whether to validate inputs

        Returns:
            Course handicap (rounded)

        Raises:
            HandicapValidationError: If validation fails
        """
        if validate:
            cls.validate_handicap(handicap_index, "handicap_index")
            cls.validate_course_rating(course_rating, slope_rating)

            if not isinstance(par, int) or par < 54 or par > 90:
                raise HandicapValidationError(
                    "Par must be between 54 and 90",
                    field="par",
                    details={"value": par}
                )

        # USGA Course Handicap Formula
        course_handicap = (
            (handicap_index * slope_rating / 113.0) +
            (course_rating - par)
        )

        return round(course_handicap)

    @classmethod
    def validate_stroke_allocation(
        cls,
        players_handicaps: List[float],
        hole_stroke_indexes: List[int]
    ) -> None:
        """
        Validate stroke allocation for all players on all holes.

        Args:
            players_handicaps: List of player handicaps
            hole_stroke_indexes: List of stroke indexes for all 18 holes

        Raises:
            HandicapValidationError: If stroke allocation is invalid
        """
        # Validate each player's handicap
        for i, handicap in enumerate(players_handicaps):
            try:
                cls.validate_handicap(handicap, f"player_{i}_handicap")
            except HandicapValidationError as e:
                raise HandicapValidationError(
                    f"Invalid handicap for player {i}: {e.message}",
                    field=f"player_{i}_handicap",
                    details=e.details
                )

        # Validate each hole's stroke index
        if len(hole_stroke_indexes) != 18:
            raise HandicapValidationError(
                "Must have stroke indexes for all 18 holes",
                field="hole_stroke_indexes",
                details={"count": len(hole_stroke_indexes), "expected": 18}
            )

        # Check for unique stroke indexes 1-18
        sorted_indexes = sorted(hole_stroke_indexes)
        expected_indexes = list(range(1, 19))

        if sorted_indexes != expected_indexes:
            missing = set(expected_indexes) - set(hole_stroke_indexes)
            duplicates = [
                idx for idx in hole_stroke_indexes
                if hole_stroke_indexes.count(idx) > 1
            ]

            raise HandicapValidationError(
                "Stroke indexes must be unique values 1-18",
                field="hole_stroke_indexes",
                details={
                    "missing": list(missing),
                    "duplicates": list(set(duplicates))
                }
            )

    @classmethod
    def get_handicap_category(cls, handicap: float) -> str:
        """
        Categorize handicap into skill level.

        Categories:
        - SCRATCH: 0-5
        - LOW: 6-12
        - MID: 13-20
        - HIGH: 21-30
        - BEGINNER: 31+

        Args:
            handicap: Player's handicap

        Returns:
            Category string

        Raises:
            HandicapValidationError: If handicap is invalid
        """
        cls.validate_handicap(handicap)

        if handicap <= 5:
            return "SCRATCH"
        elif handicap <= 12:
            return "LOW"
        elif handicap <= 20:
            return "MID"
        elif handicap <= 30:
            return "HIGH"
        else:
            return "BEGINNER"

    @classmethod
    def validate_team_handicaps(
        cls,
        team1_handicaps: List[float],
        team2_handicaps: List[float],
        max_difference: float = 10.0
    ) -> Dict[str, Any]:
        """
        Validate team handicaps are balanced and fair.

        Args:
            team1_handicaps: Handicaps of team 1 players
            team2_handicaps: Handicaps of team 2 players
            max_difference: Maximum allowed average handicap difference

        Returns:
            Dictionary with validation results and team stats

        Raises:
            HandicapValidationError: If teams are too unbalanced
        """
        # Validate all handicaps
        for handicap in team1_handicaps + team2_handicaps:
            cls.validate_handicap(handicap)

        # Calculate team averages
        team1_avg = sum(team1_handicaps) / len(team1_handicaps) if team1_handicaps else 0
        team2_avg = sum(team2_handicaps) / len(team2_handicaps) if team2_handicaps else 0

        difference = abs(team1_avg - team2_avg)

        if difference > max_difference:
            raise HandicapValidationError(
                f"Team handicaps too unbalanced (difference: {difference:.1f})",
                field="team_handicaps",
                details={
                    "team1_average": round(team1_avg, 1),
                    "team2_average": round(team2_avg, 1),
                    "difference": round(difference, 1),
                    "max_allowed": max_difference
                }
            )

        return {
            "valid": True,
            "team1_average": round(team1_avg, 1),
            "team2_average": round(team2_avg, 1),
            "difference": round(difference, 1),
            "balanced": difference <= (max_difference / 2)
        }

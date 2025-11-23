"""
Handicap Validator for Wolf Goat Pig.

Validates all handicap-related calculations and ensures USGA compliance.
Centralizes handicap validation logic that was previously scattered across
Player, StrokeAdvantage, and various service classes.
"""

import logging
from typing import Any, Dict, List, Optional, Union

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
        except (ValueError, TypeError):
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

        Official Rules:
        1. Players with net handicap <= 6: Play all their handicap holes at half strokes.
        2. Players with net handicap > 6 and <= 18: Play their easiest 6 handicap holes
           at half strokes, and the rest at full strokes.
        3. Players with net handicap > 18:
           - Play holes 13-18 at half stroke (easiest 6 of base 18).
           - Play holes 1-12 at full stroke.
           - Receive an additional 1/2 stroke on two holes for every 1 stroke > 18.
             (These extra half strokes wrap around starting from the hardest holes).

        Args:
            course_handicap: Player's course handicap (can be fractional)
            stroke_index: Hole's stroke index (1-18, where 1 is hardest)
            validate: Whether to validate inputs first

        Returns:
            Float strokes: 0.0, 0.5, 1.0, 1.5, 2.0, etc.
        """
        if validate:
            cls.validate_handicap(course_handicap, "course_handicap")
            cls.validate_stroke_index(stroke_index)

        full_handicap = int(course_handicap)
        fractional_part = course_handicap - full_handicap

        total_strokes = 0.0

        # --- Base Allocation (First 18 strokes) ---
        if full_handicap <= 6:
            # Rule 1: All allocated holes get 0.5
            if stroke_index <= full_handicap:
                total_strokes += 0.5
        elif full_handicap <= 18:
            # Rule 2: Easiest 6 allocated holes get 0.5, rest get 1.0 (Creecher)
            # Allocated holes are stroke indexes 1 to full_handicap
            # Remember: stroke index 1 = hardest hole, stroke index 18 = easiest hole
            if stroke_index <= full_handicap:
                # The easiest 6 holes you get strokes on are the highest stroke indexes
                # For H=13: easiest 6 are indexes 8-13, rest (1-7) are full strokes
                # For H=10: easiest 6 are indexes 5-10, rest (1-4) are full strokes
                creecher_threshold = full_handicap - 6
                if stroke_index > creecher_threshold:
                    total_strokes += 0.5  # Easiest 6 get half strokes
                else:
                    total_strokes += 1.0  # Rest get full strokes
        else:
            # Rule 3 (Base part): H > 18
            # Holes 13-18 get 0.5, Holes 1-12 get 1.0
            if stroke_index >= 13:
                total_strokes += 0.5
            else:
                total_strokes += 1.0

        # --- Extra Allocation (Handicap > 18) ---
        if full_handicap > 18:
            extra_full_strokes = full_handicap - 18
            # Convert to half strokes: 1 extra stroke = 2 half strokes
            extra_half_strokes = extra_full_strokes * 2

            # Distribute extra half strokes wrapping around from 1
            # Each pass through 1-18 consumes 18 half strokes

            # Full passes (0.5 added to all holes)
            full_passes = extra_half_strokes // 18
            total_strokes += full_passes * 0.5

            # Remaining half strokes
            remainder = extra_half_strokes % 18
            if stroke_index <= remainder:
                total_strokes += 0.5

        # --- Fractional Handling ---
        # If there is a fractional part (e.g. .5), add 0.5 to the next hole
        # "Next hole" is the one after the full_handicap allocation
        # For H > 18, this continues the wrap around sequence?
        # Or does it just apply to hole (full_handicap + 1)?
        # Given the wrap-around logic for >18, "next hole" is complex.
        # Simple interpretation: Treat fractional as one more "half stroke" in the sequence.

        if fractional_part >= 0.5:
            # Determine which hole gets the fractional half stroke
            # For H <= 18, it's hole (full_handicap + 1)
            # For H > 18, it's the next hole in the extra_half_strokes sequence

            target_hole = 0
            if full_handicap < 18:
                target_hole = full_handicap + 1
            else:
                # H=19 (1 extra) -> 2 halves (Holes 1, 2). Next is 3.
                # H=18 (0 extra) -> 0 halves. Next is 1.
                extra_full = full_handicap - 18
                extra_halves = extra_full * 2
                # The fractional half stroke goes to the hole at position (extra_halves + 1)
                # wrapped around 1-18
                target_hole = (extra_halves % 18) + 1

            if stroke_index == target_hole:
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

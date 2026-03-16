"""
Validator Layer Contracts

Protocol definitions for validation classes.
"""

from typing import Protocol, Dict, Any, List


class HandicapValidatorProtocol(Protocol):
    """Contract for HandicapValidator.

    Defines the interface for USGA-compliant handicap validation.
    """

    @staticmethod
    def validate_handicap_index(handicap_index: float) -> None:
        """Validate handicap index is within USGA rules.

        Args:
            handicap_index: Player's handicap index

        Raises:
            HandicapValidationError: If invalid
        """
        ...

    @staticmethod
    def validate_course_ratings(
        course_rating: float,
        slope_rating: float,
        par: int
    ) -> None:
        """Validate course ratings are within USGA guidelines."""
        ...

    @staticmethod
    def calculate_course_handicap(
        handicap_index: float,
        slope_rating: float,
        course_rating: float,
        par: int
    ) -> int:
        """Calculate USGA course handicap.

        Args:
            handicap_index: Player's handicap index
            slope_rating: Course slope rating
            course_rating: Course rating
            par: Course par

        Returns:
            Course handicap (integer)
        """
        ...

    @staticmethod
    def allocate_strokes(
        course_handicap: int,
        hole_handicaps: List[int]
    ) -> Dict[int, int]:
        """Allocate handicap strokes across holes.

        Args:
            course_handicap: Player's course handicap
            hole_handicaps: List of hole handicap ratings (1-18)

        Returns:
            Dict mapping hole_number to strokes
        """
        ...

    @staticmethod
    def calculate_net_score(
        gross_score: int,
        strokes_received: int
    ) -> int:
        """Calculate net score after applying handicap strokes.

        Args:
            gross_score: Actual strokes taken
            strokes_received: Handicap strokes to apply

        Returns:
            Net score
        """
        ...


class BettingValidatorProtocol(Protocol):
    """Contract for BettingValidator.

    Defines the interface for Wolf Goat Pig betting validation.
    """

    @staticmethod
    def validate_double(
        already_doubled: bool,
        wagering_closed: bool,
        partnership_formed: bool
    ) -> None:
        """Validate double is allowed.

        Args:
            already_doubled: Whether wager already doubled
            wagering_closed: Whether betting phase is closed
            partnership_formed: Whether partnership formed

        Raises:
            BettingValidationError: If double not allowed
        """
        ...

    @staticmethod
    def validate_redouble(
        already_redoubled: bool,
        already_doubled: bool,
        wagering_closed: bool
    ) -> None:
        """Validate redouble is allowed."""
        ...

    @staticmethod
    def validate_duncan(
        is_duncan_hole: bool,
        partnership_formed: bool
    ) -> None:
        """Validate Duncan special rule."""
        ...

    @staticmethod
    def calculate_wager_multiplier(
        base_wager: float,
        doubled: bool,
        redoubled: bool
    ) -> float:
        """Calculate final wager multiplier.

        Args:
            base_wager: Base wager amount
            doubled: Whether wager doubled
            redoubled: Whether wager redoubled

        Returns:
            Final multiplier
        """
        ...


class GameStateValidatorProtocol(Protocol):
    """Contract for GameStateValidator.

    Defines the interface for game state validation.
    """

    @staticmethod
    def validate_game_phase(
        current_phase: str,
        valid_phases: List[str]
    ) -> None:
        """Validate game is in an allowed phase.

        Args:
            current_phase: Current game phase
            valid_phases: List of allowed phases

        Raises:
            GameStateValidationError: If invalid phase
        """
        ...

    @staticmethod
    def validate_partnership_formation(
        captain_id: str,
        partner_id: str,
        tee_shots_complete: bool
    ) -> None:
        """Validate partnership can be formed.

        Args:
            captain_id: Captain player ID
            partner_id: Partner player ID
            tee_shots_complete: Whether tee shots completed

        Raises:
            GameStateValidationError: If invalid
        """
        ...

    @staticmethod
    def validate_hole_number(
        hole_number: int,
        total_holes: int
    ) -> None:
        """Validate hole number is valid.

        Args:
            hole_number: Current hole (1-18)
            total_holes: Total holes in round

        Raises:
            GameStateValidationError: If invalid
        """
        ...

    @staticmethod
    def validate_player_turn(
        player_id: str,
        current_player: str,
        game_phase: str
    ) -> None:
        """Validate it's the correct player's turn."""
        ...

    @staticmethod
    def validate_shot_execution(
        player_id: str,
        game_phase: str,
        shot_type: str
    ) -> None:
        """Validate player can execute this shot type now."""
        ...

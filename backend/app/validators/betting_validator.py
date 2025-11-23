"""
Betting Validator for Wolf Goat Pig.

Validates all betting-related rules including doubles, Duncan, carry-overs,
and wager calculations.
"""

from .exceptions import BettingValidationError


class BettingValidator:
    """
    Validates betting actions and wager calculations.

    Ensures:
    - Base wagers are valid
    - Doubles follow game rules
    - Special betting actions (Duncan, carry-over) are allowed
    - Wager multipliers calculated correctly
    """

    @classmethod
    def validate_base_wager(cls, base_wager: int) -> None:
        """
        Validate base wager amount.

        Args:
            base_wager: Base wager in quarters

        Raises:
            BettingValidationError: If wager is invalid
        """
        if not isinstance(base_wager, int):
            raise BettingValidationError(
                "Base wager must be an integer",
                field="base_wager",
                details={"value": base_wager, "type": type(base_wager).__name__}
            )

        if base_wager <= 0:
            raise BettingValidationError(
                "Base wager must be positive",
                field="base_wager",
                details={"value": base_wager}
            )

    @classmethod
    def validate_double(
        cls,
        already_doubled: bool,
        wagering_closed: bool,
        partnership_formed: bool
    ) -> None:
        """
        Validate double action is allowed.

        Args:
            already_doubled: Whether hole has already been doubled
            wagering_closed: Whether wagering window is closed
            partnership_formed: Whether partnership has been formed

        Raises:
            BettingValidationError: If double is not allowed
        """
        if already_doubled:
            raise BettingValidationError(
                "Hole has already been doubled",
                field="double",
                details={"already_doubled": True}
            )

        if wagering_closed:
            raise BettingValidationError(
                "Wagering is closed for this hole",
                field="double",
                details={"wagering_closed": True}
            )

        if not partnership_formed:
            raise BettingValidationError(
                "Partnership must be formed before doubling",
                field="double",
                details={"partnership_formed": False}
            )

    @classmethod
    def validate_duncan(
        cls,
        is_captain: bool,
        partnership_formed: bool,
        tee_shots_complete: bool
    ) -> None:
        """
        Validate The Duncan (captain goes solo) is allowed.

        Args:
            is_captain: Whether player is the captain
            partnership_formed: Whether partnership has been formed
            tee_shots_complete: Whether tee shots are complete

        Raises:
            BettingValidationError: If Duncan is not allowed
        """
        if not is_captain:
            raise BettingValidationError(
                "Only the captain can invoke The Duncan",
                field="duncan",
                details={"is_captain": False}
            )

        if partnership_formed:
            raise BettingValidationError(
                "Cannot invoke The Duncan after partnership formed",
                field="duncan",
                details={"partnership_formed": True}
            )

        if tee_shots_complete:
            raise BettingValidationError(
                "Cannot invoke The Duncan after tee shots complete",
                field="duncan",
                details={"tee_shots_complete": True}
            )

    @classmethod
    def validate_carry_over(
        cls,
        hole_number: int,
        previous_hole_tied: bool
    ) -> None:
        """
        Validate carry over is allowed.

        Args:
            hole_number: Current hole number
            previous_hole_tied: Whether previous hole was tied

        Raises:
            BettingValidationError: If carry over is not allowed
        """
        if hole_number == 1:
            raise BettingValidationError(
                "Cannot carry over on first hole",
                field="carry_over",
                details={"hole_number": hole_number}
            )

        if not previous_hole_tied:
            raise BettingValidationError(
                "Previous hole must have been tied to carry over",
                field="carry_over",
                details={"previous_hole_tied": False}
            )

    @classmethod
    def calculate_wager_multiplier(
        cls,
        doubled: bool = False,
        carry_over: bool = False,
        duncan: bool = False
    ) -> int:
        """
        Calculate wager multiplier based on betting modifiers.

        Args:
            doubled: Whether hole has been doubled
            carry_over: Whether carry over is in effect
            duncan: Whether Duncan is in effect

        Returns:
            Wager multiplier
        """
        multiplier = 1

        if doubled:
            multiplier *= 2

        if carry_over:
            multiplier *= 2

        if duncan:
            multiplier *= 2

        return multiplier

    @classmethod
    def calculate_total_wager(
        cls,
        base_wager: int,
        multiplier: int
    ) -> int:
        """
        Calculate total wager amount.

        Args:
            base_wager: Base wager in quarters
            multiplier: Wager multiplier

        Returns:
            Total wager amount
        """
        return base_wager * multiplier

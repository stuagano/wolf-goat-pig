"""
Centralized Validation Utilities

Provides a base validator class and common validation methods
to eliminate duplicate validation logic across the codebase.
"""

from typing import Any, Callable, Dict, List, Optional, Type, TypeVar, Union, cast

T = TypeVar("T")


class ValidationError(Exception):
    """
    Standard validation error with field and details support.

    Attributes:
        message: Human-readable error message
        field: Name of the field that failed validation
        details: Additional context about the validation failure
    """

    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.field = field
        self.details = details or {}
        super().__init__(message)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "message": self.message,
            "field": self.field,
            "details": self.details
        }


class BaseValidator:
    """
    Base class providing common validation methods.

    All validation methods are static and can be used independently
    or combined in custom validators.

    Example:
        class PlayerValidator(BaseValidator):
            @classmethod
            def validate_player(cls, data: dict) -> None:
                cls.validate_type(data.get('name'), str, 'name')
                cls.validate_not_empty(data.get('name'), 'name')
                cls.validate_range(data.get('handicap'), 0, 54, 'handicap')
    """

    # Default error class - can be overridden in subclasses
    error_class: Type[ValidationError] = ValidationError

    @classmethod
    def _raise_error(
        cls,
        message: str,
        field: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Raise a validation error using the configured error class.

        This helper method avoids mypy issues with keyword arguments.
        """
        raise ValidationError(message, field=field, details=details)

    @classmethod
    def validate_type(
        cls,
        value: Any,
        expected_type: Union[type, tuple],
        field: str,
        allow_none: bool = False
    ) -> None:
        """
        Validate that a value is of the expected type.

        Args:
            value: Value to validate
            expected_type: Expected type or tuple of types
            field: Field name for error message
            allow_none: Whether None is acceptable

        Raises:
            ValidationError: If type doesn't match
        """
        if value is None:
            if allow_none:
                return
            raise ValidationError(
                f"{field} is required",
                field=field,
                details={"value": value}
            )

        if not isinstance(value, expected_type):
            type_name = (
                expected_type.__name__
                if isinstance(expected_type, type)
                else str(expected_type)
            )
            raise ValidationError(
                f"{field} must be {type_name}",
                field=field,
                details={"value": value, "type": type(value).__name__}
            )

    @classmethod
    def validate_range(
        cls,
        value: Optional[Union[int, float]],
        min_val: Optional[Union[int, float]] = None,
        max_val: Optional[Union[int, float]] = None,
        field: str = "value",
        inclusive: bool = True
    ) -> None:
        """
        Validate that a numeric value is within a range.

        Args:
            value: Value to validate
            min_val: Minimum allowed value (None for no minimum)
            max_val: Maximum allowed value (None for no maximum)
            field: Field name for error message
            inclusive: Whether bounds are inclusive

        Raises:
            ValidationError: If value is out of range
        """
        if value is None:
            return

        if min_val is not None:
            if inclusive and value < min_val:
                raise ValidationError(
                    f"{field} must be >= {min_val}",
                    field=field,
                    details={"value": value, "min": min_val}
                )
            elif not inclusive and value <= min_val:
                raise ValidationError(
                    f"{field} must be > {min_val}",
                    field=field,
                    details={"value": value, "min": min_val}
                )

        if max_val is not None:
            if inclusive and value > max_val:
                raise ValidationError(
                    f"{field} must be <= {max_val}",
                    field=field,
                    details={"value": value, "max": max_val}
                )
            elif not inclusive and value >= max_val:
                raise ValidationError(
                    f"{field} must be < {max_val}",
                    field=field,
                    details={"value": value, "max": max_val}
                )

    @classmethod
    def validate_enum(
        cls,
        value: Any,
        allowed_values: List[Any],
        field: str = "value"
    ) -> None:
        """
        Validate that a value is one of the allowed values.

        Args:
            value: Value to validate
            allowed_values: List of acceptable values
            field: Field name for error message

        Raises:
            ValidationError: If value not in allowed list
        """
        if value is None:
            return

        if value not in allowed_values:
            raise ValidationError(
                f"{field} must be one of {allowed_values}",
                field=field,
                details={"value": value, "allowed": allowed_values}
            )

    @classmethod
    def validate_not_empty(
        cls,
        value: Any,
        field: str = "value"
    ) -> None:
        """
        Validate that a value is not empty (None, empty string, empty list).

        Args:
            value: Value to validate
            field: Field name for error message

        Raises:
            ValidationError: If value is empty
        """
        if value is None or value == "" or value == [] or value == {}:
            raise ValidationError(
                f"{field} cannot be empty",
                field=field,
                details={"value": value}
            )

    @classmethod
    def validate_length(
        cls,
        value: Optional[Union[str, list, dict]],
        min_length: Optional[int] = None,
        max_length: Optional[int] = None,
        field: str = "value"
    ) -> None:
        """
        Validate the length of a string, list, or dict.

        Args:
            value: Value to validate
            min_length: Minimum length (None for no minimum)
            max_length: Maximum length (None for no maximum)
            field: Field name for error message

        Raises:
            ValidationError: If length is out of bounds
        """
        if value is None:
            return

        length = len(value)

        if min_length is not None and length < min_length:
            raise ValidationError(
                f"{field} must be at least {min_length} characters/items",
                field=field,
                details={"value": value, "length": length, "min_length": min_length}
            )

        if max_length is not None and length > max_length:
            raise ValidationError(
                f"{field} must be at most {max_length} characters/items",
                field=field,
                details={"value": value, "length": length, "max_length": max_length}
            )

    @classmethod
    def validate_positive(
        cls,
        value: Optional[Union[int, float]],
        field: str = "value",
        allow_zero: bool = False
    ) -> None:
        """
        Validate that a number is positive.

        Args:
            value: Value to validate
            field: Field name for error message
            allow_zero: Whether zero is acceptable

        Raises:
            ValidationError: If value is not positive
        """
        if value is None:
            return

        if allow_zero:
            if value < 0:
                raise ValidationError(
                    f"{field} must be non-negative",
                    field=field,
                    details={"value": value}
                )
        else:
            if value <= 0:
                raise ValidationError(
                    f"{field} must be positive",
                    field=field,
                    details={"value": value}
                )

    @classmethod
    def validate_pattern(
        cls,
        value: Optional[str],
        pattern: str,
        field: str = "value",
        pattern_description: Optional[str] = None
    ) -> None:
        """
        Validate that a string matches a regex pattern.

        Args:
            value: Value to validate
            pattern: Regex pattern to match
            field: Field name for error message
            pattern_description: Human-readable pattern description

        Raises:
            ValidationError: If value doesn't match pattern
        """
        import re

        if value is None:
            return

        if not re.match(pattern, value):
            description = pattern_description or f"pattern {pattern}"
            raise ValidationError(
                f"{field} must match {description}",
                field=field,
                details={"value": value, "pattern": pattern}
            )

    @classmethod
    def validate_all(
        cls,
        validations: List[Callable[[], None]]
    ) -> List[ValidationError]:
        """
        Run multiple validations and collect all errors.

        Args:
            validations: List of validation functions to run

        Returns:
            List of ValidationError instances (empty if all pass)
        """
        errors = []
        for validation in validations:
            try:
                validation()
            except ValidationError as e:
                errors.append(e)
        return errors


# Pre-built validators for common game-specific validations

class GameValidator(BaseValidator):
    """Validators specific to Wolf Goat Pig game rules."""

    VALID_PLAYER_COUNTS = [4, 5, 6]
    VALID_HOLE_NUMBERS = list(range(1, 19))
    MIN_HANDICAP = 0.0
    MAX_HANDICAP = 54.0
    MIN_PAR = 3
    MAX_PAR = 6

    @classmethod
    def validate_player_count(cls, count: int) -> None:
        """Validate player count is 4, 5, or 6."""
        cls.validate_type(count, int, "player_count")
        cls.validate_enum(count, cls.VALID_PLAYER_COUNTS, "player_count")

    @classmethod
    def validate_hole_number(cls, hole: int) -> None:
        """Validate hole number is 1-18."""
        cls.validate_type(hole, int, "hole_number")
        cls.validate_range(hole, 1, 18, "hole_number")

    @classmethod
    def validate_handicap(cls, handicap: Union[int, float]) -> None:
        """Validate handicap is 0-54."""
        cls.validate_type(handicap, (int, float), "handicap")
        cls.validate_range(handicap, cls.MIN_HANDICAP, cls.MAX_HANDICAP, "handicap")

    @classmethod
    def validate_par(cls, par: int) -> None:
        """Validate par is 3-6."""
        cls.validate_type(par, int, "par")
        cls.validate_range(par, cls.MIN_PAR, cls.MAX_PAR, "par")

    @classmethod
    def validate_score(cls, score: int, par: int = 4) -> None:
        """Validate a golf score is reasonable (1 to par+10)."""
        cls.validate_type(score, int, "score")
        cls.validate_range(score, 1, par + 10, "score")

    @classmethod
    def validate_wager(cls, wager: int) -> None:
        """Validate wager is positive integer."""
        cls.validate_type(wager, int, "wager")
        cls.validate_positive(wager, "wager")


class BettingValidator(BaseValidator):
    """Validators for betting-related operations."""

    VALID_BET_TYPES = ["standard", "press", "double", "auto_press"]
    MAX_PRESS_MULTIPLIER = 8

    @classmethod
    def validate_bet_type(cls, bet_type: str) -> None:
        """Validate bet type is valid."""
        cls.validate_type(bet_type, str, "bet_type")
        cls.validate_enum(bet_type, cls.VALID_BET_TYPES, "bet_type")

    @classmethod
    def validate_press_multiplier(cls, multiplier: int) -> None:
        """Validate press multiplier is reasonable."""
        cls.validate_type(multiplier, int, "press_multiplier")
        cls.validate_range(multiplier, 1, cls.MAX_PRESS_MULTIPLIER, "press_multiplier")

"""
Custom exceptions for Wolf Goat Pig validation errors.

Provides specific exception types for different validation failures,
making error handling more precise and informative.
"""

from typing import Optional, Dict, Any


class ValidationError(Exception):
    """
    Base class for all validation errors.

    Attributes:
        message: Human-readable error message
        field: Optional field name that failed validation
        details: Optional dictionary with additional context
    """

    message: str
    field: Optional[str]
    details: Dict[str, Any]

    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.field = field
        self.details = details or {}
        super().__init__(self.message)

    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for API responses."""
        result: Dict[str, Any] = {"error": self.message}
        if self.field:
            result["field"] = self.field
        if self.details:
            result["details"] = self.details
        return result


class GameStateValidationError(ValidationError):
    """
    Raised when game state is invalid for requested operation.

    Examples:
    - Trying to execute shot when no active hole
    - Trying to form partnership after deadline
    - Invalid player action for current game phase
    """
    pass


class BettingValidationError(ValidationError):
    """
    Raised when betting action violates game rules.

    Examples:
    - Applying double when not allowed
    - Using Duncan after partnership formed
    - Invalid wager amount
    """
    pass


class HandicapValidationError(ValidationError):
    """
    Raised when handicap-related validation fails.

    Examples:
    - Handicap out of valid range (0-54)
    - Invalid stroke allocation
    - Incorrect net score calculation
    """
    pass


class PartnershipValidationError(ValidationError):
    """
    Raised when partnership formation violates rules.

    Examples:
    - Captain trying to partner with themselves
    - Partnership offer after tee shots complete
    - Invalid player ID in partnership
    """
    pass


class RuleViolationError(ValidationError):
    """
    Raised when a game rule is violated.

    This is a high-level exception used by the RuleManager to indicate
    that a requested action violates the game rules. It extends ValidationError
    to provide consistent error handling across the application.

    Examples:
    - Attempting to form partnership after deadline
    - Trying to double when not allowed
    - Invalid player attempting to take action out of turn
    - Invoking Duncan after partnership formed
    """
    pass

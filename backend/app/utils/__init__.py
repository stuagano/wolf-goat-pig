"""
Utility modules for Wolf Goat Pig backend.

This package contains reusable utilities:
- api_helpers: Error handling decorators and response utilities
- validators: Centralized validation logic
- response_types: TypedDict models for API responses

Related services:
- services.score_calculation_service: Centralized scoring logic
"""

from .api_helpers import handle_api_errors, with_db_session, ApiResponse, require_not_none
from .validators import BaseValidator, ValidationError, GameValidator, BettingValidator

__all__ = [
    # API helpers
    "handle_api_errors",
    "with_db_session",
    "ApiResponse",
    "require_not_none",
    # Validators
    "BaseValidator",
    "ValidationError",
    "GameValidator",
    "BettingValidator",
]

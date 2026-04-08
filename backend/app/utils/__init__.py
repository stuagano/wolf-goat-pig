"""
Utility modules for Wolf Goat Pig backend.

This package contains reusable utilities:
- api_helpers: Error handling decorators and response utilities
- validators: Centralized validation logic
- response_types: TypedDict models for API responses

Related services:
- (deprecated) scoring logic lives in domain/managers; legacy modules quarantined under `backend/_unused/`
"""

from .api_helpers import ApiResponse, handle_api_errors, require_not_none, with_db_session
from .validators import BaseValidator, BettingValidator, GameValidator, ValidationError

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

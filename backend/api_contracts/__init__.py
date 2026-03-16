"""
API Contracts - Interface Definitions for Wolf Goat Pig Services

This module defines Protocol-based contracts that ensure class compatibility
through structural typing rather than traditional unit tests.

Using Python's typing.Protocol, we define the expected interface contracts
for all service classes, managers, and validators. These contracts are:

1. Checked at runtime via contract validation tests
2. Verified by type checkers (mypy, pyright)
3. Self-documenting through type hints
4. Enforced by the Python type system

Benefits:
- Type safety without inheritance
- Compile-time contract checking
- Runtime contract validation
- Self-documenting interfaces
- No test maintenance overhead
"""

from .service_contracts import (
    GameLifecycleServiceProtocol,
    NotificationServiceProtocol,
    LeaderboardServiceProtocol,
    AchievementServiceProtocol
)

from .manager_contracts import (
    RuleManagerProtocol,
    ScoringManagerProtocol
)

from .validator_contracts import (
    HandicapValidatorProtocol,
    BettingValidatorProtocol,
    GameStateValidatorProtocol
)

__all__ = [
    # Services
    "GameLifecycleServiceProtocol",
    "NotificationServiceProtocol",
    "LeaderboardServiceProtocol",
    "AchievementServiceProtocol",
    # Managers
    "RuleManagerProtocol",
    "ScoringManagerProtocol",
    # Validators
    "HandicapValidatorProtocol",
    "BettingValidatorProtocol",
    "GameStateValidatorProtocol",
]

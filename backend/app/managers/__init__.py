"""
Managers package for Wolf Goat Pig application.

This package contains manager classes that centralize business logic
for various aspects of the game.
"""

from .scoring_manager import ScoringManager, get_scoring_manager
from .rule_manager import RuleManager, RuleViolationError

__all__ = [
    "ScoringManager",
    "get_scoring_manager",
    "RuleManager",
    "RuleViolationError",
]

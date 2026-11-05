"""
RuleManager for Wolf Goat Pig.

Centralizes all game rules and provides a single source of truth for rule enforcement.
Implements the singleton pattern to ensure consistent rule application across the application.

The rule methods are split across mixin modules by concern:

- ``core``: the ``RuleManager`` singleton, constants, helpers, and ``PlayerAction``
- ``partnership``: partnership formation and lone wolf rules
- ``betting``: double, redouble, Duncan, turn order, and valid actions
- ``scoring``: hole winner, handicap strokes, and Joe's Special
- ``opportunities``: betting opportunity detection and The Option

Everything previously importable from ``app.managers.rule_manager`` is re-exported here.
"""

from ...validators import (
    BettingValidationError,
    BettingValidator,
    GameStateValidationError,
    GameStateValidator,
    HandicapValidationError,
    HandicapValidator,
    RuleViolationError,
)
from .core import PlayerAction, RuleManager, logger

__all__ = [
    "BettingValidationError",
    "BettingValidator",
    "GameStateValidationError",
    "GameStateValidator",
    "HandicapValidationError",
    "HandicapValidator",
    "PlayerAction",
    "RuleManager",
    "RuleViolationError",
    "logger",
]

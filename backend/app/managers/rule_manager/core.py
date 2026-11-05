"""
RuleManager for Wolf Goat Pig.

Centralizes all game rules and provides a single source of truth for rule enforcement.
Implements the singleton pattern to ensure consistent rule application across the application.

The RuleManager integrates with existing validators and provides high-level rule checking
methods that encapsulate complex game logic.
"""

import logging
from dataclasses import dataclass
from typing import Any, Optional

from ...validators import RuleViolationError
from .betting import BettingRulesMixin
from .opportunities import BettingOpportunityRulesMixin
from .partnership import PartnershipRulesMixin
from .scoring import ScoringRulesMixin

# Same logger name as the original single-module rule_manager.
logger = logging.getLogger(__package__)


@dataclass
class PlayerAction:
    """Represents a valid action that a player can take."""

    action_type: str
    description: str
    requires_input: bool = False
    input_type: str | None = None  # "player_id", "wager_amount", etc.


class RuleManager(
    PartnershipRulesMixin,
    BettingRulesMixin,
    ScoringRulesMixin,
    BettingOpportunityRulesMixin,
):
    """
    Singleton manager for Wolf Goat Pig game rules.

    Provides centralized rule enforcement and validation for all game actions.
    Integrates with existing validators while adding higher-level game logic.

    The RuleManager follows the singleton pattern to ensure consistent rule
    application across all game instances.

    Key Responsibilities:
        - Partnership formation rules
        - Betting action validation (double, redouble, Duncan)
        - Turn order enforcement
        - Action availability checking
        - Scoring and handicap rules

    Usage:
        manager = RuleManager.get_instance()
        can_form = manager.can_form_partnership(captain_id, partner_id, game_state)
    """

    _instance: Optional["RuleManager"] = None
    _initialized: bool = False

    # Game constants
    MIN_PLAYERS = 2
    MAX_PLAYERS = 6
    HOLES_PER_ROUND = 18

    # Partnership timing constants
    TEE_SHOTS_PARTNERSHIP_DEADLINE = True  # Partnership must be formed before tee shots complete

    # Betting constants
    BASE_WAGER_QUARTERS = 1
    MIN_WAGER = 1
    MAX_DOUBLE_MULTIPLIER = 8  # Base * 2 (double) * 2 (redouble) * 2 (re-redouble) = 8x

    def __new__(cls) -> "RuleManager":
        """Singleton pattern implementation."""
        if cls._instance is None:
            cls._instance = super(RuleManager, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize the RuleManager (only once due to singleton pattern)."""
        if not RuleManager._initialized:
            logger.info("Initializing RuleManager singleton")
            RuleManager._initialized = True

    @classmethod
    def get_instance(cls) -> "RuleManager":
        """
        Get the singleton instance of RuleManager.

        Returns:
            The singleton RuleManager instance
        """
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        """
        Reset the singleton instance (primarily for testing).

        Warning: This should only be used in test scenarios to ensure
        a clean state between tests.
        """
        cls._instance = None
        cls._initialized = False
        logger.warning("RuleManager instance reset")

    # Helper Methods

    def _get_current_hole_state(self, game_state: dict[str, Any]) -> dict[str, Any]:
        """
        Extract current hole state from game state.

        Args:
            game_state: Complete game state dictionary

        Returns:
            Current hole state dictionary

        Raises:
            RuleViolationError: If no active hole found
        """
        # Try to get current hole from game state
        current_hole = game_state.get("current_hole")

        if current_hole is not None:
            return dict(current_hole) if not isinstance(current_hole, dict) else current_hole

        # Alternative: get from holes array
        holes = game_state.get("holes", [])
        current_hole_number = game_state.get("current_hole_number", 1)

        if holes and 0 < current_hole_number <= len(holes):
            hole = holes[current_hole_number - 1]
            return dict(hole) if not isinstance(hole, dict) else hole

        # No active hole found
        raise RuleViolationError(
            "No active hole found in game state",
            field="game_state",
            details={"current_hole_number": current_hole_number},
        )

    def get_rule_summary(self) -> dict[str, Any]:
        """
        Get a summary of all game rules.

        Returns:
            Dictionary containing rule categories and descriptions

        Example:
            >>> manager = RuleManager.get_instance()
            >>> summary = manager.get_rule_summary()
            >>> print(summary["partnership"]["formation"])
        """
        return {
            "partnership": {
                "formation": "Captain can form partnership before all tee shots complete",
                "deadline": "Partnership must be formed before tee shots complete",
                "restrictions": "Cannot partner with yourself",
            },
            "betting": {
                "double": "Can double wager after partnership formed, before ball holed",
                "redouble": "Can redouble after initial double, before ball holed",
                "duncan": "Captain can go solo (2x wager) before partnership/tee shots complete",
                "carry_over": "Tied holes carry over to next hole (2x wager)",
                "max_multiplier": f"{self.MAX_DOUBLE_MULTIPLIER}x base wager",
            },
            "turn_order": {
                "tee_shot": "Follow hitting order (captain first)",
                "after_tee": "Farthest from hole plays first",
                "enforcement": "Players must wait their turn",
            },
            "scoring": {
                "winner": "Lowest net score wins hole",
                "ties": "Tied holes carry over wager to next hole",
                "handicap": "USGA stroke allocation by hole stroke index",
            },
            "game": {
                "players": f"{self.MIN_PLAYERS}-{self.MAX_PLAYERS} players",
                "holes": f"{self.HOLES_PER_ROUND} holes per round",
                "base_wager": f"{self.BASE_WAGER_QUARTERS} quarter(s)",
            },
        }

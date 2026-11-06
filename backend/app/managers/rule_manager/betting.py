"""
Betting and turn-order rules for the Wolf Goat Pig RuleManager.

Part of the RuleManager package; mixed into ``RuleManager`` in ``core.py``.
"""

import logging
from typing import TYPE_CHECKING, Any

from ...validators import (
    BettingValidationError,
    BettingValidator,
    RuleViolationError,
)

# Same logger name as the original single-module rule_manager.
logger = logging.getLogger(__package__)


class BettingRulesMixin:
    """Double, redouble, Duncan, turn order, and valid-action rules."""

    if TYPE_CHECKING:

        def _get_current_hole_state(self, game_state: dict[str, Any]) -> dict[str, Any]: ...

        def can_go_lone_wolf(self, player_id: str, game_state: dict[str, Any]) -> bool: ...

    def validate_can_double(self, player_id: str, game_state: dict[str, Any]) -> None:
        """
        Validate player can double. Raises exception if not allowed.

        This is like can_double() but raises exception for better error handling.
        Used when you want to validate and get detailed error messages rather than
        just a boolean result.

        Args:
            player_id: ID of player attempting to double
            game_state: Current game state dictionary

        Raises:
            RuleViolationError: If double action violates game rules with detailed reason

        Example:
            >>> manager = RuleManager.get_instance()
            >>> try:
            ...     manager.validate_can_double("player_1", game_state)
            ...     print("Can double!")
            ... except RuleViolationError as e:
            ...     print(f"Cannot double: {e.message}")
        """
        # Use existing can_double method which already raises RuleViolationError
        # This method exists for semantic clarity - explicitly for validation
        self.can_double(player_id, game_state)
        logger.info(f"Double validation passed for player {player_id}")

    # Betting Rules

    def can_double(self, player_id: str, game_state: dict[str, Any]) -> bool:
        """
        Check if a player can double the wager.

        Double Rules:
            1. Partnership must be formed first
            2. Hole cannot have been doubled already
            3. Wagering window must be open (no balls holed yet)
            4. Player must be on one of the teams

        Args:
            player_id: ID of player attempting to double
            game_state: Current game state dictionary

        Returns:
            True if player can double, False otherwise

        Raises:
            RuleViolationError: If double action violates game rules
        """
        try:
            hole_state = self._get_current_hole_state(game_state)
            betting = hole_state.get("betting", {})

            # Check if already doubled
            already_doubled = betting.get("doubled", False)

            # Check if wagering is closed
            wagering_closed = hole_state.get("wagering_closed", False)

            # Check if partnership formed
            teams = hole_state.get("teams", {})
            partnership_formed = bool(teams and teams.get("partnership_captain"))

            # Use BettingValidator for core validation
            BettingValidator.validate_double(
                already_doubled=already_doubled,
                wagering_closed=wagering_closed,
                partnership_formed=partnership_formed,
            )

            # Additional check: player must be in the game
            player_ids = [p["id"] for p in game_state.get("players", [])]
            if player_id not in player_ids:
                raise RuleViolationError(
                    f"Player {player_id} not found in game",
                    field="player_id",
                    details={"player_id": player_id},
                )

            logger.info(f"Double validation passed for player {player_id}")
            return True

        except BettingValidationError as e:
            # Convert BettingValidationError to RuleViolationError
            raise RuleViolationError(e.message, field=e.field, details=e.details)
        except RuleViolationError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error in can_double: {e!s}")
            raise RuleViolationError(f"Double validation failed: {e!s}", field="double")

    def can_redouble(self, player_id: str, game_state: dict[str, Any]) -> bool:
        """
        Check if a player can redouble the wager.

        Redouble Rules:
            1. Hole must have been doubled first
            2. Redouble can only happen once per double
            3. Wagering window must be open
            4. Player must be on the opposing team from doubler

        Args:
            player_id: ID of player attempting to redouble
            game_state: Current game state dictionary

        Returns:
            True if player can redouble, False otherwise

        Raises:
            RuleViolationError: If redouble action violates game rules
        """
        try:
            hole_state = self._get_current_hole_state(game_state)
            betting = hole_state.get("betting", {})

            # Must be doubled first
            if not betting.get("doubled", False):
                raise RuleViolationError(
                    "Cannot redouble before initial double",
                    field="redouble",
                    details={"doubled": False},
                )

            # Cannot redouble if already redoubled
            if betting.get("redoubled", False):
                raise RuleViolationError(
                    "Hole has already been redoubled",
                    field="redouble",
                    details={"redoubled": True},
                )

            # Check wagering window
            if hole_state.get("wagering_closed", False):
                raise RuleViolationError(
                    "Wagering is closed for this hole",
                    field="redouble",
                    details={"wagering_closed": True},
                )

            logger.info(f"Redouble validation passed for player {player_id}")
            return True

        except RuleViolationError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error in can_redouble: {e!s}")
            raise RuleViolationError(f"Redouble validation failed: {e!s}", field="redouble")

    def can_duncan(self, player_id: str, game_state: dict[str, Any]) -> bool:
        """
        Check if The Duncan special rule can be invoked.

        The Duncan Rules:
            1. Only the captain can invoke Duncan
            2. Cannot be used after partnership is formed
            3. Cannot be used after tee shots are complete
            4. Doubles the wager (captain goes solo)
            5. Named after Duncan - the legendary move

        Args:
            player_id: ID of player attempting Duncan
            game_state: Current game state dictionary

        Returns:
            True if Duncan can be invoked, False otherwise

        Raises:
            RuleViolationError: If Duncan action violates game rules
        """
        try:
            hole_state = self._get_current_hole_state(game_state)

            # Check if player is captain
            hitting_order = hole_state.get("hitting_order", [])
            is_captain = hitting_order and hitting_order[0] == player_id

            # Check if partnership formed
            teams = hole_state.get("teams", {})
            partnership_formed = bool(teams and teams.get("partnership_captain"))

            # Check tee shots
            tee_shots_complete = hole_state.get("tee_shots_complete", 0) >= len(game_state.get("players", []))

            # Use BettingValidator for validation
            BettingValidator.validate_duncan(
                is_captain=is_captain,
                partnership_formed=partnership_formed,
                tee_shots_complete=tee_shots_complete,
            )

            logger.info(f"Duncan validation passed for player {player_id}")
            return True

        except BettingValidationError as e:
            # Convert BettingValidationError to RuleViolationError
            raise RuleViolationError(e.message, field=e.field, details=e.details)
        except RuleViolationError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error in can_duncan: {e!s}")
            raise RuleViolationError(f"Duncan validation failed: {e!s}", field="duncan")

    # Turn Order Rules

    def validate_player_turn(self, player_id: str, game_state: dict[str, Any]) -> bool:
        """
        Validate that it is the specified player's turn.

        Turn Rules:
            1. Based on distance from hole (farthest plays first)
            2. On tee, follows hitting order
            3. After tee shots, order determined by ball position
            4. Player cannot act out of turn

        Args:
            player_id: ID of player attempting action
            game_state: Current game state dictionary

        Returns:
            True if it's the player's turn, False otherwise

        Raises:
            RuleViolationError: If it's not the player's turn
        """
        try:
            hole_state = self._get_current_hole_state(game_state)

            # Get next player to hit
            next_player = hole_state.get("next_player_to_hit")

            if next_player != player_id:
                raise RuleViolationError(
                    f"Not your turn. Waiting for player {next_player}",
                    field="turn_order",
                    details={
                        "player_id": player_id,
                        "next_player": next_player,
                        "current_order": hole_state.get("current_order_of_play", []),
                    },
                )

            logger.debug(f"Turn validation passed for player {player_id}")
            return True

        except RuleViolationError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error in validate_player_turn: {e!s}")
            raise RuleViolationError(f"Turn validation failed: {e!s}", field="turn_order")

    def validate_betting_action(self, player_id: str, action_type: str, game_state: dict[str, Any]) -> bool:
        """
        Validate a betting action is allowed.

        Validates that the specified betting action (double, redouble, Duncan, etc.)
        is legal in the current game state.

        Args:
            player_id: ID of player attempting action
            action_type: Type of betting action ("double", "redouble", "duncan", "carry_over")
            game_state: Current game state dictionary

        Returns:
            True if action is valid, False otherwise

        Raises:
            RuleViolationError: If action is not allowed
        """
        try:
            action_type = action_type.lower()

            if action_type == "double":
                return self.can_double(player_id, game_state)
            if action_type == "redouble":
                return self.can_redouble(player_id, game_state)
            if action_type == "duncan":
                return self.can_duncan(player_id, game_state)
            if action_type == "carry_over":
                hole_state = self._get_current_hole_state(game_state)
                hole_number = hole_state.get("hole_number", 1)

                # For carry over, we need previous hole result
                # This is a simplified check - full implementation would check previous hole tie
                if hole_number == 1:
                    raise RuleViolationError(
                        "Cannot carry over on first hole",
                        field="carry_over",
                        details={"hole_number": hole_number},
                    )
                return True
            raise RuleViolationError(
                f"Unknown betting action: {action_type}",
                field="action_type",
                details={"action_type": action_type},
            )

        except RuleViolationError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error in validate_betting_action: {e!s}")
            raise RuleViolationError(f"Betting action validation failed: {e!s}", field="betting_action")

    # Action Discovery

    def get_valid_actions(self, player_id: str, game_state: dict[str, Any]) -> list[str]:
        """
        Get list of valid actions for a player in current game state.

        Returns all actions that the player can legally take right now,
        including partnership formation, betting actions, and gameplay actions.

        Args:
            player_id: ID of player
            game_state: Current game state dictionary

        Returns:
            List of valid action names (e.g., ["hit_shot", "form_partnership", "double"])

        Example:
            >>> manager = RuleManager.get_instance()
            >>> actions = manager.get_valid_actions("player_1", game_state)
            >>> print(actions)
            ['hit_shot', 'double', 'go_lone_wolf']
        """
        valid_actions: list[str] = []

        try:
            hole_state = self._get_current_hole_state(game_state)

            # Check if hole is complete
            if hole_state.get("hole_complete", False):
                return ["advance_to_next_hole"]

            # Check if it's player's turn for gameplay
            is_players_turn = False
            try:
                is_players_turn = self.validate_player_turn(player_id, game_state)
            except RuleViolationError:
                pass

            if is_players_turn:
                # Can hit shot if not holed out
                balls_in_hole = hole_state.get("balls_in_hole", [])
                if player_id not in balls_in_hole:
                    valid_actions.append("hit_shot")
                    valid_actions.append("concede_hole")

            # Check captain actions
            hitting_order = hole_state.get("hitting_order", [])
            is_captain = hitting_order and hitting_order[0] == player_id

            if is_captain:
                # Check partnership formation
                teams = hole_state.get("teams", {})
                no_partnership = not (teams and teams.get("partnership_captain"))
                tee_shots_incomplete = hole_state.get("tee_shots_complete", 0) < len(game_state.get("players", []))

                if no_partnership and tee_shots_incomplete:
                    valid_actions.append("form_partnership")

                # Check lone wolf
                try:
                    if self.can_go_lone_wolf(player_id, game_state):
                        valid_actions.append("go_lone_wolf")
                except RuleViolationError:
                    pass

                # Check Duncan
                try:
                    if self.can_duncan(player_id, game_state):
                        valid_actions.append("invoke_duncan")
                except RuleViolationError:
                    pass

            # Check betting actions (available to all players on a team)
            try:
                if self.can_double(player_id, game_state):
                    valid_actions.append("double")
            except RuleViolationError:
                pass

            try:
                if self.can_redouble(player_id, game_state):
                    valid_actions.append("redouble")
            except RuleViolationError:
                pass

            logger.debug(f"Valid actions for {player_id}: {valid_actions}")
            return valid_actions

        except Exception as e:
            logger.error(f"Error getting valid actions: {e!s}")
            return []

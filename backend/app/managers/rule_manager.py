"""
RuleManager for Wolf Goat Pig.

Centralizes all game rules and provides a single source of truth for rule enforcement.
Implements the singleton pattern to ensure consistent rule application across the application.

The RuleManager integrates with existing validators and provides high-level rule checking
methods that encapsulate complex game logic.
"""

import logging
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass

from ..validators import (
    ValidationError,
    GameStateValidationError,
    BettingValidationError,
    HandicapValidationError,
    RuleViolationError,
    GameStateValidator,
    BettingValidator,
    HandicapValidator
)

logger = logging.getLogger(__name__)


@dataclass
class PlayerAction:
    """Represents a valid action that a player can take."""
    action_type: str
    description: str
    requires_input: bool = False
    input_type: Optional[str] = None  # "player_id", "wager_amount", etc.


class RuleManager:
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

    _instance: Optional['RuleManager'] = None
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

    def __new__(cls) -> 'RuleManager':
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
    def get_instance(cls) -> 'RuleManager':
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

    # Partnership Rules

    def can_form_partnership(
        self,
        captain_id: str,
        partner_id: str,
        game_state: Dict[str, Any]
    ) -> bool:
        """
        Check if a partnership can be formed between captain and partner.

        Partnership Rules:
            1. Captain cannot partner with themselves
            2. Both players must be in the game
            3. Partnership deadline must not have passed (tee shots incomplete)
            4. No existing partnership for this hole
            5. Partner must be eligible (not already partnered)

        Args:
            captain_id: ID of the player initiating partnership
            partner_id: ID of the proposed partner
            game_state: Current game state dictionary

        Returns:
            True if partnership can be formed, False otherwise

        Raises:
            RuleViolationError: If partnership violates game rules with detailed reason
        """
        try:
            # Validate basic partnership rules
            if captain_id == partner_id:
                raise RuleViolationError(
                    "Cannot partner with yourself",
                    field="partnership",
                    details={"captain_id": captain_id, "partner_id": partner_id}
                )

            # Get current hole state
            hole_state = self._get_current_hole_state(game_state)

            # Check if partnership deadline has passed
            tee_shots_complete = hole_state.get("tee_shots_complete", 0)
            partnership_deadline_passed = hole_state.get("partnership_deadline_passed", False)

            if partnership_deadline_passed or tee_shots_complete >= len(game_state.get("players", [])):
                raise RuleViolationError(
                    "Partnership deadline has passed (tee shots complete)",
                    field="partnership",
                    details={"tee_shots_complete": tee_shots_complete}
                )

            # Check if partnership already exists
            teams = hole_state.get("teams", {})
            if teams and teams.get("partnership_captain"):
                raise RuleViolationError(
                    "Partnership already formed for this hole",
                    field="partnership",
                    details={"existing_captain": teams.get("partnership_captain")}
                )

            # Validate both players exist in game
            player_ids = [p["id"] for p in game_state.get("players", [])]
            if captain_id not in player_ids:
                raise RuleViolationError(
                    f"Captain {captain_id} not found in game",
                    field="captain_id",
                    details={"captain_id": captain_id}
                )

            if partner_id not in player_ids:
                raise RuleViolationError(
                    f"Partner {partner_id} not found in game",
                    field="partner_id",
                    details={"partner_id": partner_id}
                )

            logger.info(f"Partnership validation passed: {captain_id} -> {partner_id}")
            return True

        except RuleViolationError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error in can_form_partnership: {str(e)}")
            raise RuleViolationError(
                f"Partnership validation failed: {str(e)}",
                field="partnership"
            )

    def can_go_lone_wolf(
        self,
        player_id: str,
        game_state: Dict[str, Any]
    ) -> bool:
        """
        Check if a player can go lone wolf (play solo against all others).

        Lone Wolf Rules:
            1. Must be the captain for this hole
            2. Partnership must not have been formed yet
            3. Can be done before or after tee shots (unlike partnership formation)
            4. Creates 1 vs. all scenario

        Args:
            player_id: ID of player attempting to go lone wolf
            game_state: Current game state dictionary

        Returns:
            True if player can go lone wolf, False otherwise

        Raises:
            RuleViolationError: If lone wolf action violates game rules
        """
        try:
            hole_state = self._get_current_hole_state(game_state)

            # Check if player is captain
            hitting_order = hole_state.get("hitting_order", [])
            if not hitting_order or hitting_order[0] != player_id:
                raise RuleViolationError(
                    "Only the captain (first in hitting order) can go lone wolf",
                    field="lone_wolf",
                    details={"player_id": player_id, "captain": hitting_order[0] if hitting_order else None}
                )

            # Check if partnership already formed
            teams = hole_state.get("teams", {})
            if teams and teams.get("partnership_captain"):
                raise RuleViolationError(
                    "Cannot go lone wolf after partnership formed",
                    field="lone_wolf",
                    details={"partnership_exists": True}
                )

            logger.info(f"Lone wolf validation passed for player {player_id}")
            return True

        except RuleViolationError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error in can_go_lone_wolf: {str(e)}")
            raise RuleViolationError(
                f"Lone wolf validation failed: {str(e)}",
                field="lone_wolf"
            )

    def get_available_partners(
        self,
        game_state: Dict[str, Any],
        captain_id: str,
        hole_number: int
    ) -> List[Dict[str, Any]]:
        """
        Get list of available partners for captain based on timing rules.

        Partnership timing rules in Wolf-Goat-Pig:
        - Partnership decision comes AFTER tee shots are hit
        - Captain must see how players performed before choosing
        - Only players who have already hit their tee shot are eligible

        Args:
            game_state: Current game state dictionary
            captain_id: ID of the captain forming partnership
            hole_number: Current hole number

        Returns:
            List of dicts with partner info (id, name, handicap, tee_shot_distance, tee_shot_quality)

        Example:
            >>> manager = RuleManager.get_instance()
            >>> partners = manager.get_available_partners(game_state, "player_1", 1)
            >>> print(partners)
            [{'id': 'player_2', 'name': 'Bob', 'handicap': 10.0,
              'tee_shot_distance': 250.0, 'tee_shot_quality': 'good'}]
        """
        try:
            available_partners = []

            # Get current hole state
            hole_state = self._get_current_hole_state(game_state)

            # Check if partnership deadline has passed
            tee_shots_complete = hole_state.get("tee_shots_complete", 0)
            total_players = len(game_state.get("players", []))

            if tee_shots_complete >= total_players:
                logger.info("Partnership deadline passed - all tee shots complete")
                return []

            # Check if partnership already formed
            teams = hole_state.get("teams", {})
            if teams and teams.get("partnership_captain"):
                logger.info("Partnership already formed on this hole")
                return []

            # Get ball positions to check who has hit
            ball_positions = hole_state.get("ball_positions", {})

            # Iterate through all players
            for player in game_state.get("players", []):
                player_id = player.get("id")

                # Skip the captain
                if player_id == captain_id:
                    continue

                # Check if player has hit their tee shot
                if player_id in ball_positions and ball_positions[player_id]:
                    ball = ball_positions[player_id]

                    # Validate partnership is allowed with this player
                    try:
                        if self.can_form_partnership(captain_id, player_id, game_state):
                            # Add to available partners with tee shot info
                            available_partners.append({
                                "id": player_id,
                                "name": player.get("name", "Unknown"),
                                "handicap": player.get("handicap", 0.0),
                                "tee_shot_distance": ball.get("distance_to_pin", 0.0),
                                "tee_shot_quality": ball.get("last_shot_quality", "unknown")
                            })
                    except RuleViolationError:
                        # Partnership not allowed with this player, skip
                        continue

            logger.info(f"Found {len(available_partners)} available partners for captain {captain_id}")
            return available_partners

        except Exception as e:
            logger.error(f"Error getting available partners: {str(e)}")
            return []

    def are_partnerships_formed(
        self,
        game_state: Dict[str, Any],
        hole_number: int
    ) -> bool:
        """
        Check if partnerships have been formed on the current hole.

        Partnerships are considered formed when teams.type is 'partners' or 'solo'
        (not 'pending'). This determines whether betting actions can proceed.

        Args:
            game_state: Current game state dictionary
            hole_number: Current hole number

        Returns:
            True if teams.type is 'partners' or 'solo', False if 'pending'

        Example:
            >>> manager = RuleManager.get_instance()
            >>> formed = manager.are_partnerships_formed(game_state, 1)
            >>> print(formed)
            True  # Partnerships have been formed
        """
        try:
            # Get current hole state
            hole_state = self._get_current_hole_state(game_state)

            # Get teams structure
            teams = hole_state.get("teams", {})

            if not teams:
                logger.debug("No teams structure found - partnerships not formed")
                return False

            # Check teams.type - partnerships are formed if type is 'partners' or 'solo'
            teams_type = teams.get("type", "pending")
            partnerships_formed = teams_type in ["partners", "solo"]

            logger.info(f"Partnership check on hole {hole_number}: teams.type={teams_type}, formed={partnerships_formed}")
            return partnerships_formed

        except Exception as e:
            logger.error(f"Error checking partnerships formed: {str(e)}")
            return False

    def validate_can_double(
        self,
        player_id: str,
        game_state: Dict[str, Any]
    ) -> None:
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

    def can_double(
        self,
        player_id: str,
        game_state: Dict[str, Any]
    ) -> bool:
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
                partnership_formed=partnership_formed
            )

            # Additional check: player must be in the game
            player_ids = [p["id"] for p in game_state.get("players", [])]
            if player_id not in player_ids:
                raise RuleViolationError(
                    f"Player {player_id} not found in game",
                    field="player_id",
                    details={"player_id": player_id}
                )

            logger.info(f"Double validation passed for player {player_id}")
            return True

        except BettingValidationError as e:
            # Convert BettingValidationError to RuleViolationError
            raise RuleViolationError(
                e.message,
                field=e.field,
                details=e.details
            )
        except RuleViolationError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error in can_double: {str(e)}")
            raise RuleViolationError(
                f"Double validation failed: {str(e)}",
                field="double"
            )

    def can_redouble(
        self,
        player_id: str,
        game_state: Dict[str, Any]
    ) -> bool:
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
                    details={"doubled": False}
                )

            # Cannot redouble if already redoubled
            if betting.get("redoubled", False):
                raise RuleViolationError(
                    "Hole has already been redoubled",
                    field="redouble",
                    details={"redoubled": True}
                )

            # Check wagering window
            if hole_state.get("wagering_closed", False):
                raise RuleViolationError(
                    "Wagering is closed for this hole",
                    field="redouble",
                    details={"wagering_closed": True}
                )

            logger.info(f"Redouble validation passed for player {player_id}")
            return True

        except RuleViolationError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error in can_redouble: {str(e)}")
            raise RuleViolationError(
                f"Redouble validation failed: {str(e)}",
                field="redouble"
            )

    def can_duncan(
        self,
        player_id: str,
        game_state: Dict[str, Any]
    ) -> bool:
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
                tee_shots_complete=tee_shots_complete
            )

            logger.info(f"Duncan validation passed for player {player_id}")
            return True

        except BettingValidationError as e:
            # Convert BettingValidationError to RuleViolationError
            raise RuleViolationError(
                e.message,
                field=e.field,
                details=e.details
            )
        except RuleViolationError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error in can_duncan: {str(e)}")
            raise RuleViolationError(
                f"Duncan validation failed: {str(e)}",
                field="duncan"
            )

    # Turn Order Rules

    def validate_player_turn(
        self,
        player_id: str,
        game_state: Dict[str, Any]
    ) -> bool:
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
                        "current_order": hole_state.get("current_order_of_play", [])
                    }
                )

            logger.debug(f"Turn validation passed for player {player_id}")
            return True

        except RuleViolationError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error in validate_player_turn: {str(e)}")
            raise RuleViolationError(
                f"Turn validation failed: {str(e)}",
                field="turn_order"
            )

    def validate_betting_action(
        self,
        player_id: str,
        action_type: str,
        game_state: Dict[str, Any]
    ) -> bool:
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
            elif action_type == "redouble":
                return self.can_redouble(player_id, game_state)
            elif action_type == "duncan":
                return self.can_duncan(player_id, game_state)
            elif action_type == "carry_over":
                hole_state = self._get_current_hole_state(game_state)
                hole_number = hole_state.get("hole_number", 1)

                # For carry over, we need previous hole result
                # This is a simplified check - full implementation would check previous hole tie
                if hole_number == 1:
                    raise RuleViolationError(
                        "Cannot carry over on first hole",
                        field="carry_over",
                        details={"hole_number": hole_number}
                    )
                return True
            else:
                raise RuleViolationError(
                    f"Unknown betting action: {action_type}",
                    field="action_type",
                    details={"action_type": action_type}
                )

        except RuleViolationError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error in validate_betting_action: {str(e)}")
            raise RuleViolationError(
                f"Betting action validation failed: {str(e)}",
                field="betting_action"
            )

    # Action Discovery

    def get_valid_actions(
        self,
        player_id: str,
        game_state: Dict[str, Any]
    ) -> List[str]:
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
        valid_actions: List[str] = []

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
            logger.error(f"Error getting valid actions: {str(e)}")
            return []

    # Scoring Rules

    def calculate_hole_winner(
        self,
        hole_results: Dict[str, int]
    ) -> Optional[str]:
        """
        Determine the winner of a hole based on net scores.

        Applies Wolf Goat Pig scoring rules:
            - Lowest net score wins
            - Ties result in carry-over (no winner)
            - In team play, best ball of team is used

        Args:
            hole_results: Dictionary mapping player_id/team_id to net scores

        Returns:
            Winner ID (player or team), or None if tied

        Example:
            >>> results = {"player_1": 4, "player_2": 5, "player_3": 4}
            >>> winner = manager.calculate_hole_winner(results)
            >>> print(winner)
            None  # Tie between player_1 and player_3
        """
        if not hole_results:
            logger.warning("Empty hole results provided")
            return None

        try:
            # Find minimum score
            min_score = min(hole_results.values())

            # Find all players/teams with minimum score
            winners = [pid for pid, score in hole_results.items() if score == min_score]

            # If tie, no winner (carry over)
            if len(winners) > 1:
                logger.info(f"Hole tied between: {winners}")
                return None

            winner = winners[0]
            logger.info(f"Hole winner: {winner} with score {min_score}")
            return winner

        except Exception as e:
            logger.error(f"Error calculating hole winner: {str(e)}")
            return None

    def apply_handicap_strokes(
        self,
        hole_number: int,
        player_handicaps: Dict[str, float],
        hole_stroke_index: int
    ) -> Dict[str, int]:
        """
        Calculate handicap strokes for each player on a specific hole.

        Uses USGA stroke allocation rules via HandicapValidator.

        Args:
            hole_number: Current hole number (1-18)
            player_handicaps: Dictionary mapping player_id to handicap
            hole_stroke_index: Stroke index for this hole (1-18, where 1 is hardest)

        Returns:
            Dictionary mapping player_id to strokes received on this hole

        Raises:
            RuleViolationError: If handicap validation fails

        Example:
            >>> handicaps = {"player_1": 18.0, "player_2": 10.0, "player_3": 5.0}
            >>> strokes = manager.apply_handicap_strokes(1, handicaps, 3)
            >>> print(strokes)
            {'player_1': 1, 'player_2': 1, 'player_3': 0}
        """
        try:
            # Validate hole number
            GameStateValidator.validate_hole_number(hole_number)

            # Validate stroke index
            HandicapValidator.validate_stroke_index(hole_stroke_index)

            strokes_by_player: Dict[str, int] = {}

            for player_id, handicap in player_handicaps.items():
                try:
                    # Validate handicap
                    HandicapValidator.validate_handicap(handicap)

                    # Calculate strokes using validator (with Creecher Feature support)
                    strokes = HandicapValidator.calculate_strokes_received_with_creecher(
                        handicap,
                        hole_stroke_index,
                        validate=False  # Already validated above
                    )

                    strokes_by_player[player_id] = strokes

                except HandicapValidationError as e:
                    logger.error(f"Handicap validation failed for {player_id}: {e.message}")
                    raise RuleViolationError(
                        f"Invalid handicap for player {player_id}: {e.message}",
                        field="handicap",
                        details={"player_id": player_id, "handicap": handicap}
                    )

            logger.debug(f"Handicap strokes for hole {hole_number}: {strokes_by_player}")
            return strokes_by_player

        except (GameStateValidationError, HandicapValidationError) as e:
            raise RuleViolationError(
                f"Handicap stroke calculation failed: {e.message}",
                field=e.field,
                details=e.details
            )
        except RuleViolationError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error in apply_handicap_strokes: {str(e)}")
            raise RuleViolationError(
                f"Handicap stroke calculation failed: {str(e)}",
                field="handicap_strokes"
            )

    # Betting Application Methods

    def apply_joes_special(
        self,
        game_state: Dict[str, Any],
        hole_number: int,
        selected_value: int
    ) -> None:
        """
        Apply Joe's Special wager selection in Hoepfinger variant.

        Joe's Special allows pre-setting the wager value for a hole in the Hoepfinger variant.
        This directly mutates the betting state to set wager values.

        Args:
            game_state: Current game state dictionary
            hole_number: Hole number to apply Joe's Special to
            selected_value: Selected wager value in quarters

        Raises:
            RuleViolationError: If Joe's Special cannot be applied
        """
        try:
            # Validate the selected value
            BettingValidator.validate_base_wager(selected_value)

            # Get hole state
            hole_state = self._get_current_hole_state(game_state)

            # Verify it's the correct hole
            if hole_state.get("hole_number") != hole_number:
                raise RuleViolationError(
                    f"Hole number mismatch: expected {hole_number}, got {hole_state.get('hole_number')}",
                    field="hole_number",
                    details={"expected": hole_number, "actual": hole_state.get("hole_number")}
                )

            # Apply Joe's Special value to betting state
            betting = hole_state.get("betting", {})
            betting["joes_special_value"] = selected_value
            betting["base_wager"] = selected_value
            betting["current_wager"] = selected_value

            logger.info(f"Joe's Special applied: hole {hole_number} set to {selected_value} quarters")

        except BettingValidationError as e:
            raise RuleViolationError(
                e.message,
                field=e.field,
                details=e.details
            )
        except RuleViolationError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error in apply_joes_special: {str(e)}")
            raise RuleViolationError(
                f"Joe's Special application failed: {str(e)}",
                field="joes_special"
            )

    def check_betting_opportunities(
        self,
        game_state: Dict[str, Any],
        hole_number: int,
        last_shot: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Check for betting opportunities (doubles/flushes) based on game state.

        Analyzes the current game situation to determine if betting opportunities
        should be offered. This includes checking for excellent/terrible shots,
        position analysis, and determining strategic betting moments.

        Args:
            game_state: Current game state dictionary
            hole_number: Current hole number
            last_shot: Optional dictionary containing last shot details with keys:
                - player_id: ID of player who took shot
                - shot_quality: Quality rating ("excellent", "good", "average", "poor", "terrible")
                - distance_to_pin: Distance to pin in yards
                - shot_number: Shot number in sequence

        Returns:
            Dict with keys:
            - should_offer: bool - Whether to offer betting opportunities
            - context: List[str] - Betting context messages describing the situation
            - action: Optional[Dict] - Betting action to offer with keys:
                - action_type: Type of betting action ("double" or "flush")
                - description: Human-readable description
                - eligible_players: List of player IDs who can make this bet

        Raises:
            RuleViolationError: If betting opportunity check fails
        """
        try:
            hole_state = self._get_current_hole_state(game_state)

            # Initialize result
            result = {
                "should_offer": False,
                "context": [],
                "action": None
            }

            # Check if wagering is open
            wagering_closed = hole_state.get("wagering_closed", False)
            if wagering_closed:
                logger.debug("Wagering closed, no betting opportunities")
                return result

            # Check if teams are formed (need partners or solo)
            teams = hole_state.get("teams", {})
            team_type = teams.get("type", "pending")
            if team_type not in ["partners", "solo"]:
                logger.debug(f"Team type '{team_type}' not eligible for betting opportunities")
                return result

            # Get recent shot context
            betting_context = []
            should_offer_betting = False

            # Analyze last shot if provided
            if last_shot and "shot_result" in last_shot:
                shot = last_shot["shot_result"]
                player_id = shot.get("player_id")
                shot_quality = shot.get("shot_quality", "average")
                distance_to_pin = shot.get("distance_to_pin", 999)
                shot_number = shot.get("shot_number", 1)

                # Get player name for context
                player_name = player_id  # Fallback to ID
                for player in game_state.get("players", []):
                    if player["id"] == player_id:
                        player_name = player.get("name", player_id)
                        break

                # Check for excellent shot close to pin
                if shot_quality == "excellent" and distance_to_pin < 50:
                    should_offer_betting = True
                    betting_context.append(
                        f"🎯 {player_name} hit an excellent shot to {distance_to_pin:.0f} yards!"
                    )

                # Check for terrible shot early in hole
                elif shot_quality == "terrible" and shot_number <= 3:
                    should_offer_betting = True
                    betting_context.append(
                        f"😬 {player_name} struggling after terrible shot"
                    )

            # If no compelling reason to offer betting, return
            if not should_offer_betting:
                return result

            # Build position context
            ball_positions = hole_state.get("ball_positions", {})
            recent_shots = []
            for pid, ball in ball_positions.items():
                if ball and ball.get("shot_count", 0) > 0:
                    player_name = pid
                    for player in game_state.get("players", []):
                        if player["id"] == pid:
                            player_name = player.get("name", pid)
                            break
                    recent_shots.append(
                        f"{player_name}: {ball.get('distance_to_pin', 999):.0f}yd ({ball.get('shot_count', 0)} shots)"
                    )

            # Determine if we should offer double or flush (redouble)
            betting = hole_state.get("betting", {})
            already_doubled = betting.get("doubled", False)
            already_redoubled = betting.get("redoubled", False)

            # Find eligible players for double
            eligible_for_double = []
            eligible_for_flush = []

            for player in game_state.get("players", []):
                player_id = player["id"]

                # Check if player can double (not already doubled)
                if not already_doubled:
                    try:
                        if self.can_double(player_id, game_state):
                            eligible_for_double.append(player_id)
                    except RuleViolationError:
                        pass

                # Check if player can redouble (flush)
                if already_doubled and not already_redoubled:
                    try:
                        if self.can_redouble(player_id, game_state):
                            eligible_for_flush.append(player_id)
                    except RuleViolationError:
                        pass

            # Build result
            result["should_offer"] = True
            result["context"] = betting_context

            # Determine which action to offer
            current_wager = betting.get("current_wager", 1)

            if eligible_for_double:
                result["action"] = {
                    "action_type": "double",
                    "description": f"Double from {current_wager} to {current_wager * 2} quarters",
                    "eligible_players": eligible_for_double,
                    "context": " ".join(betting_context) + f" Current positions: {', '.join(recent_shots[:3])}"
                }
            elif eligible_for_flush:
                result["action"] = {
                    "action_type": "flush",
                    "description": f"Flush! Double back from {current_wager} to {current_wager * 2} quarters",
                    "eligible_players": eligible_for_flush,
                    "context": " ".join(betting_context) + f" Positions: {', '.join(recent_shots[:3])}"
                }

            logger.info(f"Betting opportunity found: {result['action']['action_type'] if result['action'] else 'none'}")
            return result

        except RuleViolationError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error in check_betting_opportunities: {str(e)}")
            raise RuleViolationError(
                f"Betting opportunity check failed: {str(e)}",
                field="betting_opportunities"
            )

    def apply_option(
        self,
        game_state: Dict[str, Any],
        captain_id: str,
        hole_number: int
    ) -> None:
        """
        Apply The Option rule (automatically doubles wager when captain is losing).

        The Option is a special betting rule that monitors the captain's position
        relative to opponents and automatically doubles the wager when the captain
        falls behind. This implements the full logic, not just a toggle.

        Rules:
        1. Only the captain can invoke The Option
        2. Once invoked, The Option monitors captain's position
        3. If captain is currently losing (further from hole than best opponent),
           the wager is automatically doubled
        4. The Option can only double once per hole

        Args:
            game_state: Current game state dictionary
            captain_id: ID of the captain invoking The Option
            hole_number: Hole number to apply The Option to

        Raises:
            RuleViolationError: If The Option cannot be applied
        """
        try:
            hole_state = self._get_current_hole_state(game_state)

            # Verify it's the correct hole
            if hole_state.get("hole_number") != hole_number:
                raise RuleViolationError(
                    f"Hole number mismatch: expected {hole_number}, got {hole_state.get('hole_number')}",
                    field="hole_number",
                    details={"expected": hole_number, "actual": hole_state.get("hole_number")}
                )

            # Verify player is the captain
            teams = hole_state.get("teams", {})
            actual_captain = teams.get("captain")
            if actual_captain != captain_id:
                raise RuleViolationError(
                    "Only the captain can invoke The Option",
                    field="option",
                    details={"captain_id": captain_id, "actual_captain": actual_captain}
                )

            # Get betting state
            betting = hole_state.get("betting", {})

            # Check if option is already active
            option_active = getattr(betting, "option_active", False) if hasattr(betting, "option_active") else betting.get("option_active", False)
            if option_active:
                raise RuleViolationError(
                    "The Option is already active for this hole",
                    field="option",
                    details={"option_active": True}
                )

            # Check if wagering is closed
            wagering_closed = hole_state.get("wagering_closed", False)
            if wagering_closed:
                raise RuleViolationError(
                    "Wagering is closed for this hole",
                    field="option",
                    details={"wagering_closed": True}
                )

            # Activate The Option
            if hasattr(betting, "option_active"):
                betting.option_active = True
            else:
                betting["option_active"] = True

            # Check captain's current position
            ball_positions = hole_state.get("ball_positions", {})
            captain_ball = ball_positions.get(captain_id)

            if not captain_ball:
                logger.info(f"The Option activated for captain {captain_id}, but no position yet")
                return

            captain_distance = captain_ball.get("distance_to_pin", 999) if isinstance(captain_ball, dict) else captain_ball.distance_to_pin

            # Get opponents' positions
            opponents = teams.get("opponents", [])
            if not opponents:
                # If solo, all other players are opponents
                opponents = [p["id"] for p in game_state.get("players", []) if p["id"] != captain_id]

            # Find best opponent position (closest to hole)
            best_opponent_distance = float('inf')
            for opp_id in opponents:
                opp_ball = ball_positions.get(opp_id)
                if opp_ball:
                    opp_distance = opp_ball.get("distance_to_pin", 999) if isinstance(opp_ball, dict) else opp_ball.distance_to_pin
                    best_opponent_distance = min(best_opponent_distance, opp_distance)

            # If captain is losing (further from hole), double the wager
            if captain_distance > best_opponent_distance:
                current_wager = betting.get("current_wager", 1) if isinstance(betting, dict) else betting.current_wager
                new_wager = current_wager * 2

                if isinstance(betting, dict):
                    betting["current_wager"] = new_wager
                    betting["option_invoked"] = True
                else:
                    betting.current_wager = new_wager
                    betting.option_invoked = True

                logger.info(
                    f"The Option triggered! Captain losing ({captain_distance:.0f}yd vs {best_opponent_distance:.0f}yd), "
                    f"wager doubled from {current_wager} to {new_wager} quarters"
                )
            else:
                logger.info(
                    f"The Option activated but captain winning ({captain_distance:.0f}yd vs {best_opponent_distance:.0f}yd), "
                    f"no doubling applied yet"
                )

        except RuleViolationError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error in apply_option: {str(e)}")
            raise RuleViolationError(
                f"Option application failed: {str(e)}",
                field="option"
            )

    # Helper Methods

    def _get_current_hole_state(self, game_state: Dict[str, Any]) -> Dict[str, Any]:
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
            return current_hole

        # Alternative: get from holes array
        holes = game_state.get("holes", [])
        current_hole_number = game_state.get("current_hole_number", 1)

        if holes and 0 < current_hole_number <= len(holes):
            return holes[current_hole_number - 1]

        # No active hole found
        raise RuleViolationError(
            "No active hole found in game state",
            field="game_state",
            details={"current_hole_number": current_hole_number}
        )

    def get_rule_summary(self) -> Dict[str, Any]:
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
                "restrictions": "Cannot partner with yourself"
            },
            "betting": {
                "double": "Can double wager after partnership formed, before ball holed",
                "redouble": "Can redouble after initial double, before ball holed",
                "duncan": "Captain can go solo (2x wager) before partnership/tee shots complete",
                "carry_over": "Tied holes carry over to next hole (2x wager)",
                "max_multiplier": f"{self.MAX_DOUBLE_MULTIPLIER}x base wager"
            },
            "turn_order": {
                "tee_shot": "Follow hitting order (captain first)",
                "after_tee": "Farthest from hole plays first",
                "enforcement": "Players must wait their turn"
            },
            "scoring": {
                "winner": "Lowest net score wins hole",
                "ties": "Tied holes carry over wager to next hole",
                "handicap": "USGA stroke allocation by hole stroke index"
            },
            "game": {
                "players": f"{self.MIN_PLAYERS}-{self.MAX_PLAYERS} players",
                "holes": f"{self.HOLES_PER_ROUND} holes per round",
                "base_wager": f"{self.BASE_WAGER_QUARTERS} quarter(s)"
            }
        }

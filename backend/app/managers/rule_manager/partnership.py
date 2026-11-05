"""
Partnership rules for the Wolf Goat Pig RuleManager.

Part of the RuleManager package; mixed into ``RuleManager`` in ``core.py``.
"""

import logging
from typing import TYPE_CHECKING, Any

from ...validators import RuleViolationError

# Same logger name as the original single-module rule_manager.
logger = logging.getLogger(__package__)


class PartnershipRulesMixin:
    """Partnership formation, lone wolf, and partner availability rules."""

    if TYPE_CHECKING:

        def _get_current_hole_state(self, game_state: dict[str, Any]) -> dict[str, Any]: ...

    # Partnership Rules

    def can_form_partnership(self, captain_id: str, partner_id: str, game_state: dict[str, Any]) -> bool:
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
                    details={"captain_id": captain_id, "partner_id": partner_id},
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
                    details={"tee_shots_complete": tee_shots_complete},
                )

            # Check if partnership already exists
            teams = hole_state.get("teams", {})
            if teams and teams.get("partnership_captain"):
                raise RuleViolationError(
                    "Partnership already formed for this hole",
                    field="partnership",
                    details={"existing_captain": teams.get("partnership_captain")},
                )

            # Validate both players exist in game
            player_ids = [p["id"] for p in game_state.get("players", [])]
            if captain_id not in player_ids:
                raise RuleViolationError(
                    f"Captain {captain_id} not found in game",
                    field="captain_id",
                    details={"captain_id": captain_id},
                )

            if partner_id not in player_ids:
                raise RuleViolationError(
                    f"Partner {partner_id} not found in game",
                    field="partner_id",
                    details={"partner_id": partner_id},
                )

            logger.info(f"Partnership validation passed: {captain_id} -> {partner_id}")
            return True

        except RuleViolationError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error in can_form_partnership: {e!s}")
            raise RuleViolationError(f"Partnership validation failed: {e!s}", field="partnership")

    def can_go_lone_wolf(self, player_id: str, game_state: dict[str, Any]) -> bool:
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
                    details={
                        "player_id": player_id,
                        "captain": hitting_order[0] if hitting_order else None,
                    },
                )

            # Check if partnership already formed
            teams = hole_state.get("teams", {})
            if teams and teams.get("partnership_captain"):
                raise RuleViolationError(
                    "Cannot go lone wolf after partnership formed",
                    field="lone_wolf",
                    details={"partnership_exists": True},
                )

            logger.info(f"Lone wolf validation passed for player {player_id}")
            return True

        except RuleViolationError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error in can_go_lone_wolf: {e!s}")
            raise RuleViolationError(f"Lone wolf validation failed: {e!s}", field="lone_wolf")

    def get_available_partners(
        self, game_state: dict[str, Any], captain_id: str, hole_number: int
    ) -> list[dict[str, Any]]:
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
                if ball_positions.get(player_id):
                    ball = ball_positions[player_id]

                    # Validate partnership is allowed with this player
                    try:
                        if self.can_form_partnership(captain_id, player_id, game_state):
                            # Add to available partners with tee shot info
                            available_partners.append(
                                {
                                    "id": player_id,
                                    "name": player.get("name", "Unknown"),
                                    "handicap": player.get("handicap", 0.0),
                                    "tee_shot_distance": ball.get("distance_to_pin", 0.0),
                                    "tee_shot_quality": ball.get("last_shot_quality", "unknown"),
                                }
                            )
                    except RuleViolationError:
                        # Partnership not allowed with this player, skip
                        continue

            logger.info(f"Found {len(available_partners)} available partners for captain {captain_id}")
            return available_partners

        except Exception as e:
            logger.error(f"Error getting available partners: {e!s}")
            return []

    def are_partnerships_formed(self, game_state: dict[str, Any], hole_number: int) -> bool:
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

            logger.info(
                f"Partnership check on hole {hole_number}: teams.type={teams_type}, formed={partnerships_formed}"
            )
            return partnerships_formed

        except Exception as e:
            logger.error(f"Error checking partnerships formed: {e!s}")
            return False

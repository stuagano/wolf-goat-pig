"""
Betting opportunity and The Option rules for the Wolf Goat Pig RuleManager.

Part of the RuleManager package; mixed into ``RuleManager`` in ``core.py``.
"""

import logging
from typing import TYPE_CHECKING, Any

from ...validators import RuleViolationError

# Same logger name as the original single-module rule_manager.
logger = logging.getLogger(__package__)


class BettingOpportunityRulesMixin:
    """Betting opportunity detection and The Option rule."""

    if TYPE_CHECKING:

        def _get_current_hole_state(self, game_state: dict[str, Any]) -> dict[str, Any]: ...

        def can_double(self, player_id: str, game_state: dict[str, Any]) -> bool: ...

        def can_redouble(self, player_id: str, game_state: dict[str, Any]) -> bool: ...

    def check_betting_opportunities(
        self,
        game_state: dict[str, Any],
        hole_number: int,
        last_shot: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
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
            result: dict[str, Any] = {
                "should_offer": False,
                "context": [],
                "action": None,
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
                    betting_context.append(f"🎯 {player_name} hit an excellent shot to {distance_to_pin:.0f} yards!")

                # Check for terrible shot early in hole
                elif shot_quality == "terrible" and shot_number <= 3:
                    should_offer_betting = True
                    betting_context.append(f"😬 {player_name} struggling after terrible shot")

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
                    "context": " ".join(betting_context) + f" Current positions: {', '.join(recent_shots[:3])}",
                }
            elif eligible_for_flush:
                result["action"] = {
                    "action_type": "flush",
                    "description": f"Flush! Double back from {current_wager} to {current_wager * 2} quarters",
                    "eligible_players": eligible_for_flush,
                    "context": " ".join(betting_context) + f" Positions: {', '.join(recent_shots[:3])}",
                }

            logger.info(f"Betting opportunity found: {result['action']['action_type'] if result['action'] else 'none'}")
            return result

        except RuleViolationError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error in check_betting_opportunities: {e!s}")
            raise RuleViolationError(
                f"Betting opportunity check failed: {e!s}",
                field="betting_opportunities",
            )

    def apply_option(self, game_state: dict[str, Any], captain_id: str, hole_number: int) -> None:
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
                    details={
                        "expected": hole_number,
                        "actual": hole_state.get("hole_number"),
                    },
                )

            # Verify player is the captain
            teams = hole_state.get("teams", {})
            actual_captain = teams.get("captain")
            if actual_captain != captain_id:
                raise RuleViolationError(
                    "Only the captain can invoke The Option",
                    field="option",
                    details={
                        "captain_id": captain_id,
                        "actual_captain": actual_captain,
                    },
                )

            # Get betting state
            betting = hole_state.get("betting", {})

            # Check if option is already active
            option_active = (
                getattr(betting, "option_active", False)
                if hasattr(betting, "option_active")
                else betting.get("option_active", False)
            )
            if option_active:
                raise RuleViolationError(
                    "The Option is already active for this hole",
                    field="option",
                    details={"option_active": True},
                )

            # Check if wagering is closed
            wagering_closed = hole_state.get("wagering_closed", False)
            if wagering_closed:
                raise RuleViolationError(
                    "Wagering is closed for this hole",
                    field="option",
                    details={"wagering_closed": True},
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

            captain_distance = (
                captain_ball.get("distance_to_pin", 999)
                if isinstance(captain_ball, dict)
                else captain_ball.distance_to_pin
            )

            # Get opponents' positions
            opponents = teams.get("opponents", [])
            if not opponents:
                # If solo, all other players are opponents
                opponents = [p["id"] for p in game_state.get("players", []) if p["id"] != captain_id]

            # Find best opponent position (closest to hole)
            best_opponent_distance = float("inf")
            for opp_id in opponents:
                opp_ball = ball_positions.get(opp_id)
                if opp_ball:
                    opp_distance = (
                        opp_ball.get("distance_to_pin", 999) if isinstance(opp_ball, dict) else opp_ball.distance_to_pin
                    )
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
            logger.error(f"Unexpected error in apply_option: {e!s}")
            raise RuleViolationError(f"Option application failed: {e!s}", field="option")

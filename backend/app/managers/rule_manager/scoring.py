"""
Scoring and handicap rules for the Wolf Goat Pig RuleManager.

Part of the RuleManager package; mixed into ``RuleManager`` in ``core.py``.
"""

import logging
from typing import TYPE_CHECKING, Any

from ...validators import (
    BettingValidationError,
    BettingValidator,
    GameStateValidationError,
    GameStateValidator,
    HandicapValidationError,
    HandicapValidator,
    RuleViolationError,
)

# Same logger name as the original single-module rule_manager.
logger = logging.getLogger(__package__)


class ScoringRulesMixin:
    """Hole winner, handicap stroke, and Joe's Special rules."""

    if TYPE_CHECKING:

        def _get_current_hole_state(self, game_state: dict[str, Any]) -> dict[str, Any]: ...

    # Scoring Rules

    def calculate_hole_winner(self, hole_results: dict[str, int]) -> str | None:
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
            logger.error(f"Error calculating hole winner: {e!s}")
            return None

    def apply_handicap_strokes(
        self,
        hole_number: int,
        player_handicaps: dict[str, float],
        hole_stroke_index: int,
    ) -> dict[str, float]:
        """
        Calculate handicap strokes for each player on a specific hole.

        Uses match play format where strokes are calculated relative to
        the player with the lowest handicap in the group.

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
            {'player_1': 1, 'player_2': 0.5, 'player_3': 0}
        """
        try:
            # Validate hole number
            GameStateValidator.validate_hole_number(hole_number)

            # Validate stroke index
            HandicapValidator.validate_stroke_index(hole_stroke_index)

            # Calculate net handicaps relative to lowest handicap player
            net_handicaps = HandicapValidator.calculate_net_handicaps(player_handicaps)

            strokes_by_player: dict[str, float] = {}

            for player_id, original_handicap in player_handicaps.items():
                try:
                    # Validate handicap
                    HandicapValidator.validate_handicap(original_handicap)

                    # Get net handicap (relative to lowest player)
                    net_handicap = net_handicaps.get(player_id, 0.0)

                    # Calculate strokes using validator (with Creecher Feature support)
                    strokes = HandicapValidator.calculate_strokes_received_with_creecher(
                        net_handicap,
                        hole_stroke_index,
                        validate=False,  # Already validated above
                    )

                    strokes_by_player[player_id] = strokes

                except HandicapValidationError as e:
                    logger.error(f"Handicap validation failed for {player_id}: {e.message}")
                    raise RuleViolationError(
                        f"Invalid handicap for player {player_id}: {e.message}",
                        field="handicap",
                        details={"player_id": player_id, "handicap": original_handicap},
                    )

            logger.debug(f"Handicap strokes for hole {hole_number}: {strokes_by_player}")
            return strokes_by_player

        except (GameStateValidationError, HandicapValidationError) as e:
            raise RuleViolationError(
                f"Handicap stroke calculation failed: {e.message}",
                field=e.field,
                details=e.details,
            )
        except RuleViolationError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error in apply_handicap_strokes: {e!s}")
            raise RuleViolationError(
                f"Handicap stroke calculation failed: {e!s}",
                field="handicap_strokes",
            )

    # Betting Application Methods

    def apply_joes_special(self, game_state: dict[str, Any], hole_number: int, selected_value: int) -> None:
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
                    details={
                        "expected": hole_number,
                        "actual": hole_state.get("hole_number"),
                    },
                )

            # Apply Joe's Special value to betting state
            betting = hole_state.get("betting", {})
            betting["joes_special_value"] = selected_value
            betting["base_wager"] = selected_value
            betting["current_wager"] = selected_value

            logger.info(f"Joe's Special applied: hole {hole_number} set to {selected_value} quarters")

        except BettingValidationError as e:
            raise RuleViolationError(e.message, field=e.field, details=e.details)
        except RuleViolationError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error in apply_joes_special: {e!s}")
            raise RuleViolationError(f"Joe's Special application failed: {e!s}", field="joes_special")

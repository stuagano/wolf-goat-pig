"""Read-only state views for WolfGoatPigGame — API-facing game state and scorecard data."""

import logging
from typing import Any

from ..state.course_manager import get_course_manager
from ..validators import HandicapValidator

logger = logging.getLogger(__name__)


class StateViewsMixin:
    """API-facing views of game state: summaries, scorecard, stroke allocation."""

    def get_game_state(self) -> dict[str, Any]:
        """Get complete current game state"""
        hole_state = self.hole_states.get(self.current_hole)

        # Get hole info from course manager if available
        hole_info = {}
        if self.course_manager:
            if not hasattr(self.course_manager, "get_hole_info"):
                pass
            else:
                try:
                    current_hole_info = self.course_manager.get_hole_info(self.current_hole)
                    hole_info = {
                        "hole_par": current_hole_info.get("par", 4),
                        "hole_distance": current_hole_info.get("yards", 400),
                        "hole_yardage": current_hole_info.get("yards", 400),
                        "hole_stroke_index": current_hole_info.get("stroke_index", 10),
                        "hole_handicap": current_hole_info.get("stroke_index", 10),
                        "hole_description": current_hole_info.get("description", ""),
                    }
                except (KeyError, AttributeError, TypeError):
                    # Use hole state values if available
                    if hole_state:
                        hole_info = {
                            "hole_par": hole_state.hole_par,
                            "hole_distance": hole_state.hole_yardage,
                            "hole_yardage": hole_state.hole_yardage,
                            "hole_stroke_index": hole_state.stroke_index,
                            "hole_handicap": hole_state.stroke_index,
                            "hole_description": "",
                        }
        elif hole_state:
            # Fallback to hole state values
            hole_info = {
                "hole_par": hole_state.hole_par,
                "hole_distance": hole_state.hole_yardage,
                "hole_yardage": hole_state.hole_yardage,
                "hole_stroke_index": hole_state.stroke_index,
                "hole_handicap": hole_state.stroke_index,
                "hole_description": "",
            }

        state = {
            "current_hole": self.current_hole,
            "game_phase": self.game_phase.value,
            "player_count": self.player_count,
            **hole_info,  # Include hole info at top level
            "course_name": (
                self.course_manager.selected_course_name if self.course_manager else getattr(self, "course_name", None)
            ),
            "players": [
                {
                    "id": p.id,
                    "name": p.name,
                    "handicap": p.handicap,
                    "points": p.points,
                    "float_used": p.float_used,
                    "solo_count": p.solo_count,
                }
                for p in self.players
            ],
            "hole_state": self._get_hole_state_summary() if hole_state else None,
            "hole_history": getattr(self, "scorekeeper_hole_history", None) or self._get_hole_history(),
            "course_holes": self._get_course_scorecard_info(),
            "stroke_allocation": self._get_stroke_allocation_table(),
            "hoepfinger_start": self.hoepfinger_start_hole,
            "settings": {
                "double_points_round": self.double_points_round,
                "annual_banquet": self.annual_banquet,
            },
        }

        # Include tracking fields if they exist as simulation attributes
        tracking_fields = [
            "carry_over_wager",
            "carry_over_from_hole",
            "consecutive_push_block",
            "last_push_hole",
            "base_wager",
            "current_rotation_order",
        ]
        for field_name in tracking_fields:
            if hasattr(self, field_name):
                value = getattr(self, field_name)
                if value is not None:  # Only include if not None
                    state[field_name] = value

        return state

    def _get_hole_history(self) -> list[dict[str, Any]]:
        """Build hole history with scores and points for completed holes"""
        history = []

        for hole_num in sorted(self.hole_states.keys()):
            hole_state = self.hole_states[hole_num]

            # Only include holes that have been completed with scores
            if hole_state.hole_complete and hole_state.scores:
                hole_data = {
                    "hole": hole_num,
                    "gross_scores": hole_state.scores.copy(),
                    "points_delta": (hole_state.points_awarded.copy() if hole_state.points_awarded else {}),
                    "wager": hole_state.betting.current_wager,
                    "team_type": hole_state.teams.type,
                    "halved": not bool(hole_state.points_awarded)
                    or all(v == 0 for v in hole_state.points_awarded.values()),
                    "par": hole_state.hole_par,
                    "handicap": hole_state.stroke_index,
                }
                history.append(hole_data)

        return history

    def _get_hole_state_summary(self) -> dict[str, Any]:
        """Get summary of current hole state"""
        hole_state = self.hole_states.get(self.current_hole)
        if not hole_state:
            return {}

        return {
            "hole_number": hole_state.hole_number,
            "hitting_order": hole_state.hitting_order,
            "current_shot_number": hole_state.current_shot_number,
            "hole_complete": hole_state.hole_complete,
            "wagering_closed": hole_state.wagering_closed,
            # Ball positions and order of play
            "ball_positions": {
                player_id: (
                    {
                        "distance_to_pin": ball.distance_to_pin,
                        "lie_type": ball.lie_type,
                        "shot_count": ball.shot_count,
                        "holed": ball.holed,
                        "conceded": ball.conceded,
                        "penalty_strokes": ball.penalty_strokes,
                    }
                    if ball
                    else None
                )
                for player_id in [p.id for p in self.players]
                for ball in [hole_state.get_player_ball_position(player_id)]
            },
            "current_order_of_play": hole_state.current_order_of_play,
            "line_of_scrimmage": hole_state.line_of_scrimmage,
            "next_player_to_hit": hole_state.next_player_to_hit,
            # Stroke advantages
            "stroke_advantages": {
                player_id: (
                    {
                        "handicap": stroke_adv.handicap,
                        "strokes_received": stroke_adv.strokes_received,
                        "net_score": stroke_adv.net_score,
                        "stroke_index": stroke_adv.stroke_index,
                    }
                    if stroke_adv
                    else None
                )
                for player_id in [p.id for p in self.players]
                for stroke_adv in [hole_state.get_player_stroke_advantage(player_id)]
            },
            "hole_par": hole_state.hole_par,
            "stroke_index": hole_state.stroke_index,
            # Team information
            "teams": {
                "type": hole_state.teams.type,
                "captain": hole_state.teams.captain,
                "team1": hole_state.teams.team1,
                "team2": hole_state.teams.team2,
                "team3": hole_state.teams.team3,
                "solo_player": hole_state.teams.solo_player,
                "opponents": hole_state.teams.opponents,
                "pending_request": hole_state.teams.pending_request,
            },
            # Betting state
            "betting": {
                "base_wager": hole_state.betting.base_wager,
                "current_wager": hole_state.betting.current_wager,
                "doubled": hole_state.betting.doubled,
                "redoubled": hole_state.betting.redoubled,
                "carry_over": hole_state.betting.carry_over,
                "special_rules": {
                    "float_invoked": hole_state.betting.float_invoked,
                    "option_invoked": hole_state.betting.option_invoked,
                    "duncan_invoked": hole_state.betting.duncan_invoked,
                    "tunkarri_invoked": hole_state.betting.tunkarri_invoked,
                    "joes_special_value": hole_state.betting.joes_special_value,
                },
            },
            # Completion tracking
            "scores": hole_state.scores,
            "balls_in_hole": hole_state.balls_in_hole,
            "concessions": hole_state.concessions,
        }

    # Helper methods

    def _get_course_scorecard_info(self) -> list[dict[str, Any]]:
        """
        Get par and handicap (stroke index) for all 18 holes for scorecard display.
        This provides the course layout information that appears at the top of
        traditional scorecards.

        Returns:
            List of hole information dictionaries for holes 1-18
            Example: [
                {"hole": 1, "par": 4, "handicap": 5, "yards": 420},
                {"hole": 2, "par": 3, "handicap": 17, "yards": 165},
                ...
            ]
        """
        course_manager = get_course_manager()
        # Get Wing Point holes as fallback data
        course_details = course_manager.get_course_details("Wing Point Golf & Country Club")

        if not course_details:
            # Create a default Wing Point course if it doesn't exist
            # This is a fallback for a clean database
            from ..seed_courses import DEFAULT_COURSES

            wing_point_data = next(
                (c for c in DEFAULT_COURSES if c["name"] == "Wing Point Golf & Country Club"),
                None,
            )
            if wing_point_data:
                course_manager.create_course(wing_point_data)
                course_details = course_manager.get_course_details("Wing Point Golf & Country Club")

        wing_point_holes = course_details.get("holes", []) if course_details else []

        holes_info = []

        if not self.course_manager:
            # Use Wing Point as fallback if no course loaded
            for wp_hole in wing_point_holes:
                holes_info.append(
                    {
                        "hole": wp_hole["hole_number"],
                        "par": wp_hole["par"],
                        "handicap": wp_hole.get("handicap", wp_hole.get("stroke_index", 1)),
                        "yards": wp_hole["yards"],
                    }
                )
            return holes_info

        for hole_num in range(1, 19):
            try:
                if hasattr(self.course_manager, "get_hole_info"):
                    hole_info = self.course_manager.get_hole_info(hole_num)
                else:
                    raise AttributeError("course_manager does not have get_hole_info method")
                holes_info.append(
                    {
                        "hole": hole_num,
                        "par": hole_info.get("par", 4),
                        "handicap": hole_info.get("handicap") or hole_info.get("stroke_index", hole_num),
                        "yards": hole_info.get("yards", 400),
                    }
                )
            except Exception as e:
                logger.warning(f"Failed to get hole info for hole {hole_num}: {e}")
                # Use Wing Point hole as fallback for this specific hole
                wp_hole = wing_point_holes[hole_num - 1] if hole_num <= len(wing_point_holes) else None
                if wp_hole:
                    holes_info.append(
                        {
                            "hole": hole_num,
                            "par": wp_hole["par"],
                            "handicap": wp_hole.get("handicap", wp_hole.get("stroke_index", hole_num)),
                            "yards": wp_hole["yards"],
                        }
                    )
                else:
                    # Final fallback to generic defaults
                    holes_info.append({"hole": hole_num, "par": 4, "handicap": hole_num, "yards": 400})

        return holes_info

    def _get_stroke_allocation_table(self) -> dict[str, dict[int, float]]:
        """
        Calculate stroke allocation for all 18 holes for each player.
        This allows the scorecard to display which holes each player gets strokes on
        before those holes are played (traditional golf scorecard functionality).

        Strokes are calculated relative to the player with the lowest handicap,
        following match play format where the best player gives strokes to others.

        Returns:
            Dictionary mapping player_id -> {hole_number: strokes_received}
            Example: {
                "player1": {1: 1.0, 2: 0.5, 3: 0.0, ...},
                "player2": {1: 0.5, 2: 0.0, 3: 0.0, ...}
            }
        """
        stroke_allocation: dict[str, dict[int, float]] = {}

        if not self.course_manager:
            return stroke_allocation

        # Calculate net handicaps relative to lowest handicap player
        player_handicaps = {player.id: player.handicap for player in self.players}
        net_handicaps = HandicapValidator.calculate_net_handicaps(player_handicaps)

        # Get hole handicaps (stroke indexes) for the course - returns list indexed 0-17 for holes 1-18
        hole_handicaps = self.course_manager.get_hole_handicaps()
        if not hole_handicaps:
            # Fallback to default 1-18 if course data unavailable
            hole_handicaps = list(range(1, 19))

        for player in self.players:
            player_strokes: dict[int, float] = {}
            net_handicap = net_handicaps.get(player.id, 0.0)

            # Calculate strokes for all 18 holes
            for hole_num in range(1, 19):
                try:
                    # Get stroke index for this hole (0-indexed in the list)
                    stroke_index = hole_handicaps[hole_num - 1] if hole_num <= len(hole_handicaps) else hole_num

                    # Calculate strokes received using Creecher Feature with net handicap
                    strokes = HandicapValidator.calculate_strokes_received_with_creecher(
                        net_handicap, stroke_index, validate=True
                    )
                    player_strokes[hole_num] = strokes

                except Exception as e:
                    logger.warning(f"Failed to calculate strokes for player {player.id} hole {hole_num}: {e}")
                    player_strokes[hole_num] = 0.0

            stroke_allocation[player.id] = player_strokes

        return stroke_allocation

    def _get_player_name(self, player_id: str | None) -> str:
        """Get player name by ID"""
        if player_id is None:
            return "Unknown"
        player = next((p for p in self.players if p.id == player_id), None)
        return player.name if player else player_id

"""State serialization for WolfGoatPigGame — DB round-trip and completion records."""

import logging
from dataclasses import asdict
from datetime import datetime
from typing import Any

from ..domain.game_types import (
    BallPosition,
    BettingState,
    GamePhase,
    HoleState,
    Player,
    StrokeAdvantage,
    TeamFormation,
    TimelineEvent,
    WGPHoleProgression,
)

logger = logging.getLogger(__name__)


class SerializationMixin:
    """Serialize/deserialize game state for persistence (used by PersistenceMixin)."""

    def _serialize(self) -> dict[str, Any]:
        """
        Convert all game state to a JSON-serializable dictionary.
        This now includes the simulation-specific state.
        """
        try:
            # Serialize course_manager safely
            course_manager_state = None
            if self.course_manager:
                course_manager_state = {
                    "selected_course_name": self.course_manager.selected_course_name,
                    "selected_course_id": self.course_manager.selected_course_id,
                }

            # Serialize hole_progression safely
            hole_progression_state = None
            if hasattr(self, "hole_progression") and self.hole_progression:
                hole_progression_state = {
                    "hole_number": self.hole_progression.hole_number,
                    "timeline_events": [
                        {
                            "id": e.id,
                            "timestamp": (
                                e.timestamp.isoformat() if hasattr(e.timestamp, "isoformat") else str(e.timestamp)
                            ),
                            "type": e.type,
                            "description": e.description,
                            "details": e.details,
                            "player_id": e.player_id,
                            "player_name": e.player_name,
                        }
                        for e in self.hole_progression.timeline_events
                    ],
                    "betting_decisions": getattr(self.hole_progression, "betting_decisions", []),
                    "hole_complete": self.hole_progression.hole_complete,
                }

            state = {
                "game_id": self.game_id,
                "player_count": self.player_count,
                "players": [asdict(p) for p in self.players],
                "current_hole": self.current_hole,
                "game_phase": self.game_phase.value,
                "hole_states": {num: asdict(hs) for num, hs in self.hole_states.items()},
                "double_points_round": self.double_points_round,
                "annual_banquet": self.annual_banquet,
                "course_manager": course_manager_state,
                "computer_players": list(self.computer_players.keys()),
                "shot_simulation_mode": self.shot_simulation_mode,
                "hoepfinger_start_hole": self.hoepfinger_start_hole,
                "vinnie_variation_start": self.vinnie_variation_start,
                "betting_analysis_enabled": getattr(self, "betting_analysis_enabled", True),
                "hole_progression": hole_progression_state,
            }
            return state
        except Exception as e:
            logger.error(f"Error serializing WolfGoatPigGame: {e}")
            # Return a minimal state to avoid crashing
            return {"game_id": self.game_id, "error": str(e)}

    def _deserialize(self, data: dict[str, Any]) -> None:
        """
        Restore complete game state from dictionary.
        Required by PersistenceMixin for database persistence.
        """
        try:
            # Restore basic attributes
            self.player_count = data.get("player_count", 4)
            self.current_hole = data.get("current_hole", 1)
            self.double_points_round = data.get("double_points_round", False)
            self.annual_banquet = data.get("annual_banquet", False)
            self.hoepfinger_start_hole = data.get("hoepfinger_start_hole", 17)
            self.vinnie_variation_start = data.get("vinnie_variation_start")
            self.betting_analysis_enabled = data.get("betting_analysis_enabled", True)
            self.shot_simulation_mode = data.get("shot_simulation_mode", False)

            # Restore game phase
            phase_value = data.get("game_phase", "regular")
            if isinstance(phase_value, str):
                self.game_phase = GamePhase(phase_value)
            else:
                self.game_phase = phase_value

            # Restore players
            players_data = data.get("players", [])
            self.players = [
                Player(
                    id=p["id"],
                    name=p["name"],
                    handicap=p["handicap"],
                    points=p.get("points", 0),
                    float_used=p.get("float_used", 0),
                    solo_count=p.get("solo_count", 0),
                    goat_position_history=p.get("goat_position_history", []),
                )
                for p in players_data
            ]

            # Restore hole states
            self.hole_states = {}
            hole_states_data = data.get("hole_states", {})
            for hole_num_str, hs_data in hole_states_data.items():
                hole_num = int(hole_num_str)

                # Restore teams
                teams_data = hs_data.get("teams", {})
                teams = TeamFormation(
                    type=teams_data.get("type", "pending"),
                    captain=teams_data.get("captain"),
                    second_captain=teams_data.get("second_captain"),
                    team1=teams_data.get("team1", []),
                    team2=teams_data.get("team2", []),
                    team3=teams_data.get("team3", []),
                    solo_player=teams_data.get("solo_player"),
                    opponents=teams_data.get("opponents", []),
                    pending_request=teams_data.get("pending_request"),
                )

                # Restore betting state
                betting_data = hs_data.get("betting", {})
                betting = BettingState(**betting_data)

                # Restore ball positions
                ball_positions_data = hs_data.get("ball_positions", {})
                ball_positions = {}
                for player_id, pos_data in ball_positions_data.items():
                    if pos_data:
                        ball_positions[player_id] = BallPosition(**pos_data)

                # Restore stroke advantages
                stroke_advantages_data = hs_data.get("stroke_advantages", {})
                stroke_advantages = {}
                for player_id, sa_data in stroke_advantages_data.items():
                    if sa_data:
                        stroke_advantages[player_id] = StrokeAdvantage(**sa_data)

                # Create hole state with all fields
                self.hole_states[hole_num] = HoleState(
                    hole_number=hole_num,
                    hitting_order=hs_data.get("hitting_order", []),
                    teams=teams,
                    betting=betting,
                    ball_positions=ball_positions,
                    current_order_of_play=hs_data.get("current_order_of_play", []),
                    line_of_scrimmage=hs_data.get("line_of_scrimmage"),
                    next_player_to_hit=hs_data.get("next_player_to_hit"),
                    stroke_advantages=stroke_advantages,
                    hole_par=hs_data.get("hole_par", 4),
                    stroke_index=hs_data.get("stroke_index", 10),
                    hole_yardage=hs_data.get("hole_yardage", 400),
                    hole_difficulty=hs_data.get("hole_difficulty", "Medium"),
                    scores=hs_data.get("scores", {}),
                    shots_completed=hs_data.get("shots_completed", {}),
                    balls_in_hole=hs_data.get("balls_in_hole", []),
                    concessions=hs_data.get("concessions", {}),
                    points_awarded=hs_data.get("points_awarded", {}),
                    current_shot_number=hs_data.get("current_shot_number", 1),
                    hole_complete=hs_data.get("hole_complete", False),
                    wagering_closed=hs_data.get("wagering_closed", False),
                    tee_shots_complete=hs_data.get("tee_shots_complete", 0),
                    partnership_deadline_passed=hs_data.get("partnership_deadline_passed", False),
                    invitation_windows=hs_data.get("invitation_windows", {}),
                )

            # Restore hole progression
            hole_prog_data = data.get("hole_progression")
            if hole_prog_data:
                # Reconstruct timeline events
                timeline_events = []
                for event_data in hole_prog_data.get("timeline_events", []):
                    timeline_events.append(
                        TimelineEvent(
                            id=event_data["id"],
                            timestamp=(
                                datetime.fromisoformat(event_data["timestamp"])
                                if isinstance(event_data["timestamp"], str)
                                else event_data["timestamp"]
                            ),
                            type=event_data["type"],
                            description=event_data["description"],
                            details=event_data.get("details", {}),
                            player_id=event_data.get("player_id"),
                            player_name=event_data.get("player_name"),
                        )
                    )

                self.hole_progression = WGPHoleProgression(hole_number=self.current_hole)
                self.hole_progression.timeline_events = timeline_events
                self.hole_progression.betting_opportunities = hole_prog_data.get("betting_decisions", [])

            # Initialize course manager if needed
            if hasattr(self, "course_manager") and self.course_manager:
                pass  # Already set
            else:
                from ..state.course_manager import CourseManager

                self.course_manager = CourseManager()
                # Check for course_manager state from serialization
                course_manager_data = data.get("course_manager")
                if course_manager_data:
                    course_name = course_manager_data.get("selected_course_name")
                    if course_name:
                        self.course_manager.load_course(course_name)
                else:
                    # Fallback for legacy data format
                    course_name = data.get("course_name")
                    if course_name:
                        self.course_manager.load_course(course_name)

            # Initialize empty computer players dict
            self.computer_players = {}

            # Mark as loaded from DB
            self._loaded_from_db = True

            logger.info(f"Successfully deserialized game {self.game_id}")

        except Exception as e:
            logger.error(f"Error deserializing WolfGoatPigGame: {e}")
            raise

    def _get_final_scores(self) -> dict[str, int]:
        """Get final scores for game completion. Used by PersistenceMixin."""
        return {player.id: player.points for player in self.players}

    def _get_game_metadata(self) -> dict[str, Any]:
        """Get game metadata for completion record. Used by PersistenceMixin."""
        course_name = "Unknown"
        if self.course_manager and hasattr(self.course_manager, "selected_course"):
            course_name = self.course_manager.selected_course
        return {
            "course_name": course_name,
            "player_count": self.player_count,
            "total_holes_played": len(self.hole_states),
            "settings": {
                "double_points_round": self.double_points_round,
                "annual_banquet": self.annual_banquet,
                "game_phase": (
                    self.game_phase.value if isinstance(self.game_phase, GamePhase) else str(self.game_phase)
                ),
            },
        }

    def _get_player_results(self) -> list[dict[str, Any]]:
        """Get individual player results for completion record. Used by PersistenceMixin."""
        results = []
        for player in self.players:
            results.append(
                {
                    "player_name": player.name,
                    "total_earnings": float(player.points),
                    "final_position": (
                        1 if player.points == max(p.points for p in self.players) else 2
                    ),  # Simplified rank logic
                    "performance_metrics": {
                        "handicap": player.handicap,
                        "float_used": player.float_used,
                        "solo_count": player.solo_count,
                        "goat_positions": player.goat_position_history,
                        "holes_played": len(self.hole_states),
                    },
                }
            )
        return results

"""
Game State Validator for Wolf Goat Pig.

Validates game state transitions, player actions, and game flow.
"""

from typing import List, Optional
from .exceptions import GameStateValidationError


class GameStateValidator:
    """
    Validates game state transitions and player actions.

    Ensures:
    - Game phases are valid
    - Player counts are within bounds
    - Actions are valid for current game state
    - Partnerships follow rules
    """

    VALID_PHASES = ["SETUP", "PRE_TEE", "PLAYING", "COMPLETED"]
    MIN_PLAYERS = 2
    MAX_PLAYERS = 6
    MIN_HOLE = 1
    MAX_HOLE = 18

    @classmethod
    def validate_game_phase(cls, phase: str) -> None:
        """
        Validate game phase is valid.

        Args:
            phase: Game phase string

        Raises:
            GameStateValidationError: If phase is invalid
        """
        if phase not in cls.VALID_PHASES:
            raise GameStateValidationError(
                f"Invalid game phase: {phase}",
                field="game_phase",
                details={"value": phase, "valid_phases": cls.VALID_PHASES}
            )

    @classmethod
    def validate_player_count(cls, count: int) -> None:
        """
        Validate player count is within valid range.

        Args:
            count: Number of players

        Raises:
            GameStateValidationError: If count is invalid
        """
        if not isinstance(count, int):
            raise GameStateValidationError(
                "Player count must be an integer",
                field="player_count",
                details={"value": count, "type": type(count).__name__}
            )

        if count < cls.MIN_PLAYERS or count > cls.MAX_PLAYERS:
            raise GameStateValidationError(
                f"Player count must be between {cls.MIN_PLAYERS} and {cls.MAX_PLAYERS}",
                field="player_count",
                details={"value": count, "min": cls.MIN_PLAYERS, "max": cls.MAX_PLAYERS}
            )

    @classmethod
    def validate_hole_number(cls, hole_number: int) -> None:
        """
        Validate hole number is valid.

        Args:
            hole_number: Hole number (1-18)

        Raises:
            GameStateValidationError: If hole number is invalid
        """
        if not isinstance(hole_number, int):
            raise GameStateValidationError(
                "Hole number must be an integer",
                field="hole_number",
                details={"value": hole_number, "type": type(hole_number).__name__}
            )

        if hole_number < cls.MIN_HOLE or hole_number > cls.MAX_HOLE:
            raise GameStateValidationError(
                f"Hole number must be between {cls.MIN_HOLE} and {cls.MAX_HOLE}",
                field="hole_number",
                details={"value": hole_number, "min": cls.MIN_HOLE, "max": cls.MAX_HOLE}
            )

    @classmethod
    def validate_player_action(
        cls,
        player_id: str,
        action: str,
        current_player: str,
        game_phase: str
    ) -> None:
        """
        Validate player action is allowed.

        Args:
            player_id: ID of player attempting action
            action: Action being attempted
            current_player: ID of current active player
            game_phase: Current game phase

        Raises:
            GameStateValidationError: If action is not allowed
        """
        if player_id != current_player:
            raise GameStateValidationError(
                "Not your turn",
                field="player_action",
                details={"player_id": player_id, "current_player": current_player}
            )

        if game_phase not in ["PLAYING", "PRE_TEE"]:
            raise GameStateValidationError(
                "Cannot perform action in current game phase",
                field="player_action",
                details={"action": action, "game_phase": game_phase}
            )

    @classmethod
    def validate_partnership_formation(
        cls,
        captain_id: str,
        partner_id: str,
        tee_shots_complete: bool
    ) -> None:
        """
        Validate partnership formation is allowed.

        Args:
            captain_id: ID of captain forming partnership
            partner_id: ID of proposed partner
            tee_shots_complete: Whether tee shots are complete

        Raises:
            GameStateValidationError: If partnership is not allowed
        """
        if captain_id == partner_id:
            raise GameStateValidationError(
                "Cannot partner with yourself",
                field="partnership",
                details={"captain_id": captain_id, "partner_id": partner_id}
            )

        if tee_shots_complete:
            raise GameStateValidationError(
                "Partnership deadline has passed (tee shots complete)",
                field="partnership",
                details={"tee_shots_complete": True}
            )

    @classmethod
    def validate_shot_execution(
        cls,
        player_id: str,
        hole_complete: bool,
        player_holed: bool
    ) -> None:
        """
        Validate shot execution is allowed.

        Args:
            player_id: ID of player shooting
            hole_complete: Whether hole is complete
            player_holed: Whether player has already holed out

        Raises:
            GameStateValidationError: If shot is not allowed
        """
        if hole_complete:
            raise GameStateValidationError(
                "Hole is already complete",
                field="shot_execution",
                details={"player_id": player_id, "hole_complete": True}
            )

        if player_holed:
            raise GameStateValidationError(
                "Player has already holed out",
                field="shot_execution",
                details={"player_id": player_id, "player_holed": True}
            )

    @classmethod
    def validate_game_start(
        cls,
        player_count: int,
        course_selected: bool,
        all_players_ready: bool
    ) -> None:
        """
        Validate game can start.

        Args:
            player_count: Number of players
            course_selected: Whether course has been selected
            all_players_ready: Whether all players are ready

        Raises:
            GameStateValidationError: If game cannot start
        """
        cls.validate_player_count(player_count)

        if not course_selected:
            raise GameStateValidationError(
                "Course must be selected before starting game",
                field="game_start",
                details={"course_selected": False}
            )

        if not all_players_ready:
            raise GameStateValidationError(
                "All players must be ready before starting game",
                field="game_start",
                details={"all_players_ready": False}
            )

    @classmethod
    def validate_hole_completion(
        cls,
        players_holed: List[str],
        total_players: int
    ) -> None:
        """
        Validate hole can be completed.

        Args:
            players_holed: List of player IDs who have holed out
            total_players: Total number of players

        Raises:
            GameStateValidationError: If hole cannot be completed
        """
        completed_count = len(players_holed)

        if completed_count < total_players:
            raise GameStateValidationError(
                "Not all players have completed the hole",
                field="hole_completion",
                details={
                    "completed": completed_count,
                    "total": total_players,
                    "remaining": total_players - completed_count
                }
            )

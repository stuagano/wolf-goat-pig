import logging
import random
from typing import Any, cast

from .domain.game_types import (
    BettingState,
    GamePhase,
    HoleState,
    Player,
    TeamFormation,
    WGPHoleProgression,
)
from .engine import (
    AardvarkMixin,
    AnalyticsMixin,
    BettingActionsMixin,
    PartnershipMixin,
    ScoringMixin,
    SerializationMixin,
    ShotProgressionMixin,
    SimulationMixin,
    StateViewsMixin,
)
from .mixins import PersistenceMixin
from .state.course_manager import get_course_manager
from .validators import (
    GameStateValidationError,
    GameStateValidator,
    HandicapValidationError,
    HandicapValidator,
)

logger = logging.getLogger(__name__)

# Backwards compatibility alias
WGPPlayer = Player


class WolfGoatPigGame(
    AardvarkMixin,
    BettingActionsMixin,
    ScoringMixin,
    StateViewsMixin,
    PartnershipMixin,
    ShotProgressionMixin,
    SimulationMixin,
    AnalyticsMixin,
    SerializationMixin,
    PersistenceMixin,
):
    """
    Complete Wolf Goat Pig simulation implementing all rules from rules.txt.
    Now includes database persistence via PersistenceMixin.
    """

    def __init__(
        self,
        game_id: str | None = None,
        player_count: int = 4,
        players: list[Player] | None = None,
        course_manager: Any = None,
    ) -> None:
        # Initialize persistence FIRST (generates/loads game_id)
        self.__init_persistence__(game_id)

        # Check if we loaded from DB - if so, skip initialization
        if hasattr(self, "_loaded_from_db") and cast("bool", getattr(self, "_loaded_from_db", False)):
            return

        # New game initialization
        if player_count not in [4, 5, 6]:
            raise ValueError("Wolf Goat Pig supports 4, 5, or 6 players only")

        self.player_count = player_count
        self.players = players or self._create_default_players()

        # Validate all player handicaps using HandicapValidator
        try:
            for player in self.players:
                HandicapValidator.validate_handicap(player.handicap, f"{player.name}_handicap")
        except HandicapValidationError as e:
            logger.error(f"Handicap validation failed: {e.message}")
            raise ValueError(f"Invalid player handicap: {e.message}") from e
        self.current_hole = 1
        self.game_phase = GamePhase.REGULAR
        self.hole_states: dict[int, HoleState] = {}
        self.double_points_round = False  # Major championship days
        self.annual_banquet = False  # Annual banquet day
        self.course_manager = course_manager if course_manager else get_course_manager()
        if not self.course_manager.get_selected_course():
            courses = self.course_manager.get_courses()
            if courses:
                first_course_name = next(iter(courses.keys()))
                self.course_manager.load_course(first_course_name)

        logger.info(f"Course manager type: {type(self.course_manager)}")
        logger.info(f"Course manager attributes: {dir(self.course_manager)}")

        self.course_name = self.course_manager.selected_course_name

        # Computer players for AI decision making
        self.computer_players: dict[str, Any] = {}

        # Shot progression and betting analysis
        self.hole_progression: WGPHoleProgression | None = None
        self.betting_analysis_enabled = True
        self.shot_simulation_mode = False  # Enable for shot-by-shot play

        # Game progression tracking
        self.hoepfinger_start_hole = self._get_hoepfinger_start_hole()
        self.vinnie_variation_start = 13 if player_count == 4 else None

        # Initialize first hole
        self._initialize_hole(1)

        # Save initial state to DB
        self._save_to_db()

    def set_computer_players(self, computer_player_ids: list[str], personalities: list[str] | None = None) -> None:
        """Set which players are computer-controlled with their personalities"""
        if personalities is None:
            personalities = ["balanced"] * len(computer_player_ids)

        # Simple computer player class for compatibility
        class SimpleComputerPlayer:
            def __init__(self, player, personality):
                self.player = player
                self.personality = personality

        self.computer_players = {}
        for player_id, personality in zip(computer_player_ids, personalities):
            player = next((p for p in self.players if p.id == player_id), None)
            if player:
                self.computer_players[player_id] = SimpleComputerPlayer(player, personality)

    def _create_default_players(self) -> list[Player]:
        """Create default players based on the rules.txt character list"""
        names = ["Bob", "Scott", "Vince", "Mike", "Terry", "Bill"][: self.player_count]
        handicaps = [10.5, 15, 8, 20.5, 12, 18][: self.player_count]

        return [Player(id=f"p{i + 1}", name=names[i], handicap=handicaps[i]) for i in range(self.player_count)]

    def _get_hoepfinger_start_hole(self) -> int:
        """Get starting hole for Hoepfinger phase based on player count"""
        return {4: 17, 5: 16, 6: 13}[self.player_count]

    def _initialize_hole(self, hole_number: int) -> None:
        """Initialize a new hole with proper state"""
        # Validate hole number using GameStateValidator
        try:
            GameStateValidator.validate_hole_number(hole_number)
        except GameStateValidationError as e:
            logger.error(f"Hole initialization validation failed: {e.message}")
            raise ValueError(f"Cannot initialize hole: {e.message}") from e

        # Determine hitting order
        if hole_number == 1:
            hitting_order = self._random_hitting_order()
        else:
            hitting_order = self._rotate_hitting_order(hole_number)

        # Handle Hoepfinger phase
        if hole_number >= self.hoepfinger_start_hole:
            self.game_phase = GamePhase.HOEPFINGER
            goat = self._get_goat()
            hitting_order = self._goat_chooses_position(goat, hitting_order)
        elif self.vinnie_variation_start and hole_number >= self.vinnie_variation_start:
            self.game_phase = GamePhase.VINNIE_VARIATION

        # Initialize betting state
        betting_state = BettingState()
        betting_state.base_wager = self._calculate_base_wager(hole_number)
        betting_state.current_wager = betting_state.base_wager

        # Apply The Option if applicable
        if self._should_apply_option(hitting_order[0]):
            betting_state.option_invoked = True
            betting_state.current_wager *= 2

        # Apply Joe's Special in Hoepfinger phase
        if self.game_phase == GamePhase.HOEPFINGER:
            goat = self._get_goat()
            joes_value = self._prompt_joes_special(goat, betting_state.base_wager)
            if joes_value:
                betting_state.joes_special_value = joes_value
                betting_state.current_wager = joes_value

        # Create team formation
        teams = TeamFormation(type="pending", captain=hitting_order[0])

        # Get hole info from course manager if available
        hole_par = None
        hole_yardage = None
        stroke_index = min(hole_number, 18)  # Default

        if self.course_manager:
            if not hasattr(self.course_manager, "get_hole_info"):
                hole_info = {}

            else:
                try:
                    hole_info = self.course_manager.get_hole_info(hole_number)
                    hole_par = hole_info.get("par")
                    hole_yardage = hole_info.get("yards")
                    stroke_index = hole_info.get("stroke_index", stroke_index)
                except (KeyError, AttributeError, TypeError):
                    # Fall back to defaults if course info unavailable
                    pass

        # Initialize hole state
        hole_state = HoleState(
            hole_number=hole_number,
            hitting_order=hitting_order,
            teams=teams,
            betting=betting_state,
            stroke_index=stroke_index,
            scores={p.id: None for p in self.players},
            shots_completed={p.id: False for p in self.players},
        )

        # Initialize invitation windows - all players can be invited initially
        hole_state.invitation_windows = {p.id: True for p in self.players}
        hole_state.tee_shots_complete = 0
        hole_state.partnership_deadline_passed = False

        # Set hole information (par, yardage, difficulty) - uses course data if available
        if hole_par is not None and hole_yardage is not None:
            hole_state.set_hole_info(par=hole_par, yardage=hole_yardage, stroke_index=stroke_index)

        else:
            hole_state.set_hole_info()

        # Calculate stroke advantages for all players on this hole
        hole_state.calculate_stroke_advantages(self.players)

        # Initialize hole progression with timeline tracking
        self.hole_progression = WGPHoleProgression(hole_number=hole_number)

        # Add hole start event to timeline
        captain_name = self._get_player_name(hitting_order[0])
        if self.hole_progression is not None:
            self.hole_progression.add_timeline_event(
                event_type="hole_start",
                description=f"Hole {hole_number} begins - {captain_name} is captain",
                player_id=hitting_order[0],
                player_name=captain_name,
                details={
                    "hole_number": hole_number,
                    "hitting_order": hitting_order,
                    "captain": captain_name,
                    "base_wager": betting_state.base_wager,
                    "stroke_index": stroke_index,
                },
            )

        self.hole_states[hole_number] = hole_state

    def _random_hitting_order(self) -> list[str]:
        """Use hitting order from player list (determined by tee toss in frontend)"""
        # Players are already in tee order from the database (set via frontend tee toss)
        player_ids = [p.id for p in self.players]
        return player_ids

    def _rotate_hitting_order(self, hole_number: int) -> list[str]:
        """Rotate hitting order for subsequent holes"""
        if hole_number == 1:
            return self._random_hitting_order()

        # Check if previous hole exists, if not use random order
        if hole_number - 1 not in self.hole_states:
            return self._random_hitting_order()

        previous_order = self.hole_states[hole_number - 1].hitting_order
        # Rotate: second becomes first, third becomes second, etc.
        return previous_order[1:] + [previous_order[0]]

    def _get_goat(self) -> Player:
        """Get the player who is furthest down (the Goat)"""
        return min(self.players, key=lambda p: p.points)

    def _goat_chooses_position(self, goat: Player, current_order: list[str]) -> list[str]:
        """
        In Hoepfinger phase, the Goat chooses hitting position
        Note: In 6-man game, can't choose same spot more than twice in a row
        """
        # For simulation, Goat chooses randomly (in real game, this would be user input)
        available_positions = list(range(len(current_order)))

        if self.player_count == 6 and len(goat.goat_position_history) >= 2:
            # Check for 6-man restriction: can't choose same spot more than twice in a row
            if goat.goat_position_history[-1] == goat.goat_position_history[-2]:
                last_pos = goat.goat_position_history[-1]
                if last_pos in available_positions:
                    available_positions.remove(last_pos)

        chosen_position = random.choice(available_positions if available_positions else list(range(len(current_order))))

        # Update goat's position history
        goat.goat_position_history.append(chosen_position)
        if len(goat.goat_position_history) > 2:
            goat.goat_position_history.pop(0)

        # Rebuild order with Goat in chosen position
        new_order = [pid for pid in current_order if pid != goat.id]
        new_order.insert(chosen_position, goat.id)
        return new_order

    def _calculate_base_wager(self, hole_number: int) -> int:
        """Calculate base wager considering all multipliers"""
        base = 1

        # Double Points Rounds (Major championships, Annual Banquet)
        if self.double_points_round or self.annual_banquet:
            base *= 2

        # Vinnie's Variation (holes 13-16 in 4-man game)
        if (
            self.player_count == 4
            and self.vinnie_variation_start
            and hole_number >= self.vinnie_variation_start
            and hole_number < self.hoepfinger_start_hole
        ):
            base *= 2

        # Carry-over from previous hole
        if hole_number > 1:
            prev_hole = self.hole_states.get(hole_number - 1)
            if prev_hole and prev_hole.betting.carry_over:
                prev_wager = prev_hole.betting.current_wager
                base = max(base, prev_wager * 2)  # Double the carried-over amount

        return base

    def _should_apply_option(self, captain_id: str) -> bool:
        """Check if The Option should be applied (captain has lost most quarters)"""
        captain = next(p for p in self.players if p.id == captain_id)
        min_points = min(p.points for p in self.players)
        return captain.points == min_points and min_points < 0

    def _prompt_joes_special(self, goat: Player, natural_start: int) -> int | None:
        """
        Joe's Special: Goat chooses starting value in Hoepfinger phase
        Returns chosen value or None if not invoked
        """
        # Available options: 2, 4, 8 quarters, or natural start if > 8
        options = [2, 4, 8]
        if natural_start > 8:
            options.append(natural_start)

        # For simulation, choose randomly (in real game, this would be user input)
        if random.random() < 0.3:  # 30% chance to invoke
            return random.choice(options)
        return None

import logging
from typing import Any, cast

from .domain.game_types import (
    GamePhase,
    HoleState,
    Player,
    WGPHoleProgression,
)
from .engine import (
    AardvarkMixin,
    AnalyticsMixin,
    BettingActionsMixin,
    HoleSetupMixin,
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
    HandicapValidationError,
    HandicapValidator,
)

logger = logging.getLogger(__name__)

# Backwards compatibility alias
WGPPlayer = Player


class WolfGoatPigGame(
    HoleSetupMixin,
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

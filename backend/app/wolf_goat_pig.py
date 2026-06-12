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
    AnalyticsMixin,
    PartnershipMixin,
    SerializationMixin,
    ShotProgressionMixin,
    SimulationMixin,
)
from .mixins import PersistenceMixin
from .services.post_hole_analysis_service import (
    get_post_hole_analysis as _get_post_hole_analysis,
)
from .state.course_manager import get_course_manager
from .validators import (
    BettingValidationError,
    BettingValidator,
    GameStateValidationError,
    GameStateValidator,
    HandicapValidationError,
    HandicapValidator,
)

logger = logging.getLogger(__name__)

# Backwards compatibility alias
WGPPlayer = Player


class WolfGoatPigGame(
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

    def request_partner(self, captain_id: str, partner_id: str) -> dict[str, Any]:
        """Captain requests a specific player as partner"""
        hole_state = self.hole_states[self.current_hole]

        # Validate partnership formation using GameStateValidator
        try:
            GameStateValidator.validate_partnership_formation(
                captain_id=captain_id,
                partner_id=partner_id,
                tee_shots_complete=hole_state.partnership_deadline_passed,
            )
        except GameStateValidationError as e:
            logger.error(f"Partnership validation failed: {e.message}")
            raise ValueError(f"Cannot request partnership: {e.message}") from e

        # Validate request
        if hole_state.teams.captain != captain_id:
            raise ValueError("Only the captain can request a partner")

        if partner_id not in [p.id for p in self.players]:
            raise ValueError("Invalid partner ID")

        # Check eligibility based on hitting order and shots taken
        if not self._is_player_eligible_for_partnership(partner_id, hole_state):
            raise ValueError("Player is no longer eligible for partnership")

        # Set pending request
        hole_state.teams.pending_request = {
            "type": "partnership",
            "captain": captain_id,
            "requested": partner_id,
        }

        # Add partnership request event to timeline
        captain_name = self._get_player_name(captain_id)
        partner_name = self._get_player_name(partner_id)
        if self.hole_progression is not None:
            self.hole_progression.add_timeline_event(
                event_type="partnership_request",
                description=f"{captain_name} requests {partner_name} as partner",
                player_id=captain_id,
                player_name=captain_name,
                details={
                    "captain": captain_name,
                    "requested_partner": partner_name,
                    "captain_handicap": next(p.handicap for p in self.players if p.id == captain_id),
                    "partner_handicap": next(p.handicap for p in self.players if p.id == partner_id),
                    "hole_number": self.current_hole,
                },
            )

        return {
            "status": "pending",
            "message": f"Partnership request sent to {partner_name}",
            "awaiting_response": partner_id,
        }

    def respond_to_partnership(self, partner_id: str, accept: bool) -> dict[str, Any]:
        """Respond to partnership request"""
        hole_state = self.hole_states[self.current_hole]

        # Validate response
        pending = hole_state.teams.pending_request
        if not pending or pending.get("requested") != partner_id:
            raise ValueError("No pending partnership request for this player")

        captain_id = pending["captain"]

        if accept:
            return self._accept_partnership(captain_id, partner_id, hole_state)
        return self._decline_partnership(captain_id, partner_id, hole_state)

    def go_solo(self, captain_id: str, use_duncan: bool = False) -> dict[str, Any]:
        """Alias for captain_go_solo for backward compatibility"""
        return self.captain_go_solo(captain_id, use_duncan)

    def captain_go_solo(self, captain_id: str, use_duncan: bool = False) -> dict[str, Any]:
        """Captain decides to go solo (Pig)"""
        hole_state = self.hole_states[self.current_hole]

        if hole_state.teams.captain != captain_id:
            raise ValueError("Only the captain can go solo")

        # Validate Duncan using BettingValidator if requested
        if use_duncan:
            try:
                is_captain = hole_state.teams.captain == captain_id
                partnership_formed = hole_state.teams.type in ["partners", "solo"]
                BettingValidator.validate_duncan(
                    is_captain=is_captain,
                    partnership_formed=partnership_formed,
                    tee_shots_complete=hole_state.partnership_deadline_passed,
                )
            except BettingValidationError as e:
                logger.error(f"Duncan validation failed: {e.message}")
                raise ValueError(f"Cannot invoke The Duncan: {e.message}") from e

        captain = next(p for p in self.players if p.id == captain_id)

        # Track solo count for 4-man game requirement
        if self.player_count == 4:
            captain.solo_count += 1

        # Set up solo play
        opponents = [p.id for p in self.players if p.id != captain_id]
        hole_state.teams = TeamFormation(type="solo", captain=captain_id, solo_player=captain_id, opponents=opponents)

        # Apply wager multipliers
        multiplier = 2  # Base "On Your Own" multiplier

        if use_duncan:
            # The Duncan: 3 quarters for every 2 wagered
            hole_state.betting.duncan_invoked = True
            multiplier = 2  # Still doubles the base wager

        hole_state.betting.current_wager *= multiplier

        # Add solo decision event to timeline
        captain_name = self._get_player_name(captain_id)
        if self.hole_progression is not None:
            self.hole_progression.add_timeline_event(
                event_type="partnership_decision",
                description=f"{captain_name} decides to go solo",
                player_id=captain_id,
                player_name=captain_name,
                details={
                    "decision": "solo",
                    "captain": captain_name,
                    "duncan": use_duncan,
                    "new_wager": hole_state.betting.current_wager,
                    "opponents": [self._get_player_name(p) for p in opponents],
                },
            )

        return {
            "status": "solo",
            "message": f"Captain {captain_name} goes solo!",
            "duncan": use_duncan,
            "wager": hole_state.betting.current_wager,
        }

    def aardvark_request_team(self, aardvark_id: str, target_team: str) -> dict[str, Any]:
        """Aardvark requests to join a team (5-man and 6-man games)"""
        if self.player_count == 4:
            raise ValueError("No aardvark in 4-man game")

        hole_state = self.hole_states[self.current_hole]

        # Validate aardvark status
        if not self._is_aardvark(aardvark_id, hole_state):
            raise ValueError("Player is not an aardvark on this hole")

        # Set pending aardvark request
        hole_state.teams.pending_request = {
            "type": "aardvark",
            "aardvark": aardvark_id,
            "target_team": target_team,
        }

        return {
            "status": "pending",
            "message": f"Aardvark {self._get_player_name(aardvark_id)} requests to join {target_team}",
            "awaiting_response": target_team,
        }

    def respond_to_aardvark(self, team_id: str, accept: bool) -> dict[str, Any]:
        """Respond to aardvark request"""
        hole_state = self.hole_states[self.current_hole]

        pending = hole_state.teams.pending_request
        if not pending or pending.get("type") != "aardvark":
            raise ValueError("No pending aardvark request")

        aardvark_id = pending["aardvark"]

        if accept:
            return self._accept_aardvark(aardvark_id, team_id, hole_state)
        return self._toss_aardvark(aardvark_id, team_id, hole_state)

    def aardvark_go_solo(self, aardvark_id: str, use_tunkarri: bool = False) -> dict[str, Any]:
        """Aardvark decides to go solo (5-man and 6-man games)"""
        if self.player_count == 4:
            raise ValueError("No aardvark in 4-man game")

        hole_state = self.hole_states[self.current_hole]

        if not self._is_aardvark(aardvark_id, hole_state):
            raise ValueError("Player is not an aardvark on this hole")

        # Set up aardvark solo play
        others = [p.id for p in self.players if p.id != aardvark_id]
        hole_state.teams = TeamFormation(type="solo", solo_player=aardvark_id, opponents=others)

        # Apply wager multipliers
        multiplier = 2  # Base solo multiplier

        if use_tunkarri:
            # The Tunkarri: 3 quarters for every 2 wagered
            hole_state.betting.tunkarri_invoked = True
            multiplier = 2  # Still doubles the base wager

        hole_state.betting.current_wager *= multiplier

        return {
            "status": "solo",
            "message": f"Aardvark {self._get_player_name(aardvark_id)} goes solo!",
            "tunkarri": use_tunkarri,
            "wager": hole_state.betting.current_wager,
        }

    def offer_double(self, offering_player_id: str, target_team: str | None = None) -> dict[str, Any]:
        """Offer a double to the opposing team"""
        hole_state = self.hole_states[self.current_hole]

        # Validate double using BettingValidator
        try:
            partnership_formed = hole_state.teams.type in ["partners", "solo"]
            BettingValidator.validate_double(
                already_doubled=hole_state.betting.doubled,
                wagering_closed=hole_state.wagering_closed,
                partnership_formed=partnership_formed,
            )
        except BettingValidationError as e:
            logger.error(f"Double validation failed: {e.message}")
            raise ValueError(f"Cannot offer double: {e.message}") from e

        # Check Line of Scrimmage rule - use the proper can_offer_double method
        if not hole_state.can_offer_double(offering_player_id):
            raise ValueError("Cannot offer double - player has passed line of scrimmage or betting is closed")

        # Check if any ball is in the hole
        if hole_state.balls_in_hole:
            raise ValueError("Cannot offer double - ball is in the hole")

        # Record double offer
        hole_state.betting.doubles_history.append(
            {
                "offering_player": offering_player_id,
                "target_team": target_team,
                "wager_before": hole_state.betting.current_wager,
            }
        )

        hole_state.betting.doubled = True

        # Add double offer event to timeline
        offering_player_name = self._get_player_name(offering_player_id)
        if self.hole_progression is not None:
            self.hole_progression.add_timeline_event(
                event_type="double_offer",
                description=f"{offering_player_name} offers a double - wager increases from {hole_state.betting.current_wager} to {hole_state.betting.current_wager * 2} quarters",
                player_id=offering_player_id,
                player_name=offering_player_name,
                details={
                    "offering_player": offering_player_name,
                    "current_wager": hole_state.betting.current_wager,
                    "potential_wager": hole_state.betting.current_wager * 2,
                    "hole_number": self.current_hole,
                },
            )

        return {
            "status": "double_offered",
            "message": f"{offering_player_name} offers a double",
            "current_wager": hole_state.betting.current_wager,
            "potential_wager": hole_state.betting.current_wager * 2,
        }

    def respond_to_double(
        self,
        responding_team: str,
        accept: bool,
        gambit_players: list[str] | None = None,
    ) -> dict[str, Any]:
        """Respond to a double offer, with optional Ackerley's Gambit"""
        hole_state = self.hole_states[self.current_hole]

        if not hole_state.betting.doubled:
            raise ValueError("No double to respond to")

        if accept:
            if gambit_players:
                # Ackerley's Gambit: some players opt out, others stay in
                return self._handle_ackerley_gambit(responding_team, gambit_players, hole_state)
            # Standard double acceptance
            hole_state.betting.current_wager *= 2
            hole_state.betting.doubled = False

            # Add double acceptance event to timeline
            if self.hole_progression is not None:
                self.hole_progression.add_timeline_event(
                    event_type="double_response",
                    description=f"Double accepted - wager increases to {hole_state.betting.current_wager} quarters",
                    details={
                        "accepted": True,
                        "new_wager": hole_state.betting.current_wager,
                        "responding_team": responding_team,
                    },
                )

            return {
                "status": "double_accepted",
                "message": "Double accepted",
                "new_wager": hole_state.betting.current_wager,
            }
        # Double declined - offering team wins hole
        return self._resolve_double_decline(hole_state)

    def invoke_float(self, captain_id: str) -> dict[str, Any]:
        """Captain invokes The Float to increase base wager"""
        captain = next(p for p in self.players if p.id == captain_id)
        hole_state = self.hole_states[self.current_hole]

        if captain.float_used:
            raise ValueError("Player has already used their float this round")

        if hole_state.teams.captain != captain_id:
            raise ValueError("Only the captain can invoke the float")

        # Apply float
        captain.float_used = True
        hole_state.betting.float_invoked = True
        hole_state.betting.current_wager *= 2

        return {
            "status": "float_invoked",
            "message": f"{captain.name} invokes The Float",
            "new_wager": hole_state.betting.current_wager,
        }

    def enter_hole_scores(self, scores: dict[str, int]) -> dict[str, Any]:
        """Enter scores for the hole and calculate points"""
        hole_state = self.hole_states[self.current_hole]

        # Validate all scores are provided
        for player_id in [p.id for p in self.players]:
            if player_id not in scores:
                raise ValueError(f"Score missing for player {self._get_player_name(player_id)}")

        hole_state.scores = {k: cast("int | None", v) for k, v in scores.items()}

        # Calculate and distribute points
        points_result = self._calculate_hole_points(hole_state)

        # Store points awarded in hole state for hole_history
        hole_state.points_awarded = points_result["points_changes"].copy()

        # Update player points
        for player_id, points_change in points_result["points_changes"].items():
            player = next(p for p in self.players if p.id == player_id)
            player.points += points_change

        # Check for carry-over
        if points_result["halved"]:
            hole_state.betting.carry_over = True

        return points_result

    def apply_hole_events(self, events: list[dict[str, Any]]) -> None:
        """Recompute player points from the full hole-event log.

        Accepts a list of per-player-per-hole dicts with keys:
          hole_number, player_id, score (optional), quarters.
        Resets all player points to zero, then sums quarters from each event.
        Also restores hole_state.scores / .points_awarded for initialized holes.
        """
        from collections import defaultdict

        for player in self.players:
            player.points = 0

        by_hole: dict[int, list[dict[str, Any]]] = defaultdict(list)
        for event in events:
            by_hole[event["hole_number"]].append(event)

        for hole_number in sorted(by_hole.keys()):
            hole_events = by_hole[hole_number]
            hole_state = self.hole_states.get(hole_number)
            if hole_state:
                hole_state.scores = {e["player_id"]: e["score"] for e in hole_events if e.get("score") is not None}
                hole_state.points_awarded = {e["player_id"]: e["quarters"] for e in hole_events}

            for event in hole_events:
                player = next((p for p in self.players if p.id == event["player_id"]), None)
                if player:
                    player.points += event["quarters"]

    def get_post_hole_analysis(self, hole_number: int) -> dict[str, Any]:
        """Generate comprehensive post-hole analysis"""
        return _get_post_hole_analysis(
            hole_states=self.hole_states,
            game_phase=self.game_phase,
            players=self.players,
            get_player_name_fn=self._get_player_name,
            hole_number=hole_number,
            calculate_hole_points_fn=self._calculate_hole_points,
        )

    def advance_to_next_hole(self) -> dict[str, Any]:
        """Advance to the next hole"""
        if self.current_hole >= 18:
            return self._finish_game()

        self.current_hole += 1
        self._initialize_hole(self.current_hole)

        return {
            "status": "hole_advanced",
            "current_hole": self.current_hole,
            "game_phase": self.game_phase.value,
            "hole_state": self._get_hole_state_summary(),
        }

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
            from .seed_courses import DEFAULT_COURSES

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

    def _is_player_eligible_for_partnership(self, player_id: str, hole_state: HoleState) -> bool:
        """Check if player is still eligible to be requested as partner"""
        # Player becomes ineligible once next player has hit
        player_index = hole_state.hitting_order.index(player_id)

        # Check if next player has already hit
        if player_index < len(hole_state.hitting_order) - 1:
            next_player = hole_state.hitting_order[player_index + 1]
            return not hole_state.shots_completed.get(next_player, False)

        # Last player is eligible until first second shot
        return not any(hole_state.shots_completed.values())

    def _is_aardvark(self, player_id: str, hole_state: HoleState) -> bool:
        """Check if player is an aardvark on this hole"""
        if self.player_count == 4:
            return False  # No aardvark in 4-man game (only invisible)
        if self.player_count == 5:
            return hole_state.hitting_order.index(player_id) == 4  # 5th position
        # 6-man
        index = hole_state.hitting_order.index(player_id)
        return index in [4, 5]  # 5th or 6th position

    def _accept_partnership(self, captain_id: str, partner_id: str, hole_state: HoleState) -> dict[str, Any]:
        """Handle partnership acceptance"""
        others = [p.id for p in self.players if p.id not in [captain_id, partner_id]]

        hole_state.teams = TeamFormation(
            type="partners",
            captain=captain_id,
            team1=[captain_id, partner_id],
            team2=others,
        )

        hole_state.teams.pending_request = None

        # Add partnership acceptance event to timeline
        captain_name = self._get_player_name(captain_id)
        partner_name = self._get_player_name(partner_id)
        if self.hole_progression is not None:
            self.hole_progression.add_timeline_event(
                event_type="partnership_response",
                description=f"{partner_name} accepts partnership with {captain_name}",
                player_id=partner_id,
                player_name=partner_name,
                details={
                    "accepted": True,
                    "captain": captain_name,
                    "partner": partner_name,
                    "team1": [captain_name, partner_name],
                    "team2": [self._get_player_name(p) for p in others],
                },
            )

        return {
            "status": "partnership_formed",
            "message": f"Partnership formed: {captain_name} & {partner_name}",
            "team1": [captain_id, partner_id],
            "team2": others,
        }

    def _decline_partnership(self, captain_id: str, partner_id: str, hole_state: HoleState) -> dict[str, Any]:
        """Handle partnership decline - captain goes solo"""
        others = [p.id for p in self.players if p.id != captain_id]

        # Track solo count for 4-man requirement
        if self.player_count == 4:
            captain = next(p for p in self.players if p.id == captain_id)
            captain.solo_count += 1

        hole_state.teams = TeamFormation(type="solo", captain=captain_id, solo_player=captain_id, opponents=others)

        # Double the wager due to partnership decline
        hole_state.betting.current_wager *= 2
        hole_state.teams.pending_request = None

        # Add partnership decline event to timeline
        captain_name = self._get_player_name(captain_id)
        partner_name = self._get_player_name(partner_id)
        if self.hole_progression is not None:
            self.hole_progression.add_timeline_event(
                event_type="partnership_response",
                description=f"{partner_name} declines partnership - {captain_name} goes solo",
                player_id=partner_id,
                player_name=partner_name,
                details={
                    "accepted": False,
                    "captain": captain_name,
                    "partner": partner_name,
                    "new_wager": hole_state.betting.current_wager,
                    "solo_player": captain_name,
                    "opponents": [self._get_player_name(p) for p in others],
                },
            )

        return {
            "status": "partnership_declined",
            "message": f"{partner_name} declined. {captain_name} goes solo!",
            "new_wager": hole_state.betting.current_wager,
        }

    def _accept_aardvark(self, aardvark_id: str, team_id: str, hole_state: HoleState) -> dict[str, Any]:
        """Handle aardvark acceptance to team"""
        # Add aardvark to the specified team
        if team_id == "team1":
            hole_state.teams.team1.append(aardvark_id)
        elif team_id == "team2":
            hole_state.teams.team2.append(aardvark_id)
        else:
            raise ValueError("Invalid team ID")

        hole_state.teams.pending_request = None

        return {
            "status": "aardvark_accepted",
            "message": f"Aardvark {self._get_player_name(aardvark_id)} joins {team_id}",
            "teams": {"team1": hole_state.teams.team1, "team2": hole_state.teams.team2},
        }

    def _toss_aardvark(self, aardvark_id: str, rejecting_team: str, hole_state: HoleState) -> dict[str, Any]:
        """Handle aardvark being tossed to other team"""
        # Add to tossed list
        hole_state.betting.tossed_aardvarks.append(aardvark_id)

        # Double the wager
        hole_state.betting.current_wager *= 2

        # Add aardvark to the other team
        other_team = "team2" if rejecting_team == "team1" else "team1"
        if other_team == "team1":
            hole_state.teams.team1.append(aardvark_id)
        else:
            hole_state.teams.team2.append(aardvark_id)

        hole_state.teams.pending_request = None

        return {
            "status": "aardvark_tossed",
            "message": f"Aardvark {self._get_player_name(aardvark_id)} tossed to {other_team}",
            "new_wager": hole_state.betting.current_wager,
            "teams": {"team1": hole_state.teams.team1, "team2": hole_state.teams.team2},
        }

    def _handle_ackerley_gambit(
        self, responding_team: str, gambit_players: list[str], hole_state: HoleState
    ) -> dict[str, Any]:
        """Handle Ackerley's Gambit - some players opt out, others stay in"""
        opt_out_players = [p for p in gambit_players if p not in gambit_players]
        opt_in_players = gambit_players

        # Opt-out players forfeit their current quarters at risk
        hole_state.betting.ackerley_gambit = {
            "opt_out": opt_out_players,
            "opt_in": opt_in_players,
        }

        # Double the wager for opt-in players
        hole_state.betting.current_wager *= 2
        hole_state.betting.doubled = False

        return {
            "status": "ackerley_gambit",
            "message": "Ackerley's Gambit invoked",
            "opt_out_players": opt_out_players,
            "opt_in_players": opt_in_players,
            "new_wager": hole_state.betting.current_wager,
        }

    def _resolve_double_decline(self, hole_state: HoleState) -> dict[str, Any]:
        """Handle double decline - offering team wins hole"""
        hole_state.betting.doubled = False

        # Determine offering team from doubles history
        last_double = hole_state.betting.doubles_history[-1]
        offering_player = last_double["offering_player"]

        # Add double decline event to timeline
        offering_player_name = self._get_player_name(offering_player)
        if self.hole_progression is not None:
            self.hole_progression.add_timeline_event(
                event_type="double_response",
                description=f"Double declined - {offering_player_name}'s team wins the hole",
                player_id=offering_player,
                player_name=offering_player_name,
                details={
                    "accepted": False,
                    "offering_player": offering_player_name,
                    "wager": last_double["wager_before"],
                    "hole_winner": "offering_team",
                },
            )

        # Award points to offering team
        points_result = {
            "status": "double_declined",
            "message": "Double declined. Offering team wins hole.",
            "hole_winner": "offering_team",
            "points_changes": {},
        }

        # Calculate points based on team structure
        wager = last_double["wager_before"]

        if hole_state.teams.type == "partners":
            # Determine which team the offering player is on
            if offering_player in hole_state.teams.team1:
                winners = hole_state.teams.team1
                losers = hole_state.teams.team2
            else:
                winners = hole_state.teams.team2
                losers = hole_state.teams.team1

            # Distribute points using Karl Marx rule
            points_changes = self._apply_karl_marx_rule(winners, losers, wager)
            points_result["points_changes"] = points_changes

        elif hole_state.teams.type == "solo":
            if offering_player == hole_state.teams.solo_player:
                # Solo player wins
                points_changes_dict = cast("dict[str, int]", points_result["points_changes"])
                points_changes_dict[offering_player] = wager * len(hole_state.teams.opponents)
                for opp in hole_state.teams.opponents:
                    points_changes_dict[opp] = -wager
            else:
                # Opponents win
                points_changes_dict = cast("dict[str, int]", points_result["points_changes"])
                solo_player_id = hole_state.teams.solo_player
                if solo_player_id:
                    points_changes_dict[solo_player_id] = -wager * len(hole_state.teams.opponents)
                for opp in hole_state.teams.opponents:
                    points_changes_dict[opp] = wager

        return points_result

    def _calculate_hole_points(self, hole_state: HoleState) -> dict[str, Any]:
        """Calculate points for the hole based on scores and betting"""
        scores = hole_state.scores
        betting = hole_state.betting
        teams = hole_state.teams

        # Filter out None values from scores
        valid_scores: dict[str, int] = {pid: score for pid, score in scores.items() if score is not None}

        if teams.type == "partners":
            return self._calculate_partners_points(valid_scores, teams, betting)
        if teams.type == "solo":
            return self._calculate_solo_points(valid_scores, teams, betting)
        raise ValueError(f"Invalid team type for points calculation: {teams.type}")

    def _calculate_partners_points(
        self, scores: dict[str, int], teams: TeamFormation, betting: BettingState
    ) -> dict[str, Any]:
        """Calculate points for partners format"""
        team1_score = min(scores[pid] for pid in teams.team1)
        team2_score = min(scores[pid] for pid in teams.team2)

        wager = betting.current_wager

        if team1_score < team2_score:
            winners = teams.team1
            losers = teams.team2
        elif team2_score < team1_score:
            winners = teams.team2
            losers = teams.team1
        else:
            # Hole halved
            return {
                "halved": True,
                "message": "Hole halved. No points awarded.",
                "points_changes": {p.id: 0 for p in self.players},
            }

        points_changes = self._apply_karl_marx_rule(winners, losers, wager)

        # Apply special rule multipliers
        if betting.duncan_invoked or betting.tunkarri_invoked:
            # 3 for 2 rule - winner gets 3 quarters for every 2 wagered
            for winner in winners:
                if points_changes[winner] > 0:
                    points_changes[winner] = int(points_changes[winner] * 1.5)

        return {
            "halved": False,
            "winners": winners,
            "losers": losers,
            "points_changes": points_changes,
            "message": f"Team {winners} wins the hole",
        }

    def _calculate_solo_points(
        self, scores: dict[str, int], teams: TeamFormation, betting: BettingState
    ) -> dict[str, Any]:
        """Calculate points for solo format"""
        solo_player = teams.solo_player
        opponents = teams.opponents

        if solo_player is None:
            raise ValueError("Solo player cannot be None")
        solo_score = scores[solo_player]
        opponent_score = min(scores[pid] for pid in opponents)

        wager = betting.current_wager

        if solo_score < opponent_score:
            # Solo player wins
            points_changes = {solo_player: wager * len(opponents)}
            for opp in opponents:
                points_changes[opp] = -wager

            winners = [solo_player]
            message = f"{self._get_player_name(solo_player)} wins solo!"

        elif opponent_score < solo_score:
            # Opponents win
            points_changes = {solo_player: -wager * len(opponents)}
            for opp in opponents:
                points_changes[opp] = wager

            winners_list: list[str] = list(opponents)
            message = f"Opponents defeat {self._get_player_name(solo_player)}"

        else:
            # Hole halved
            return {
                "halved": True,
                "message": "Hole halved. No points awarded.",
                "points_changes": {p.id: 0 for p in self.players},
            }

        # Apply special rule multipliers
        if betting.duncan_invoked or betting.tunkarri_invoked:
            # 3 for 2 rule
            # Use winners_list if defined, otherwise use winners
            winner_ids = winners_list if "winners_list" in locals() else winners
            for winner in winner_ids:
                if points_changes[winner] > 0:
                    points_changes[winner] = int(points_changes[winner] * 1.5)

        # Return with correct winners variable
        final_winners = winners_list if "winners_list" in locals() else winners
        return {
            "halved": False,
            "winners": final_winners,
            "points_changes": points_changes,
            "message": message,
        }

    def _apply_karl_marx_rule(self, winners: list[str], losers: list[str], wager: int) -> dict[str, int]:
        """
        Apply Karl Marx rule: "from each according to his ability, to each according to his need"
        Player furthest down pays/receives less
        """
        points_changes = {}

        # Initialize all players to 0
        for p in self.players:
            points_changes[p.id] = 0

        total_owed = wager * len(winners)
        total_won = wager * len(losers)

        # Winners get points
        if len(winners) == 1:
            points_changes[winners[0]] = total_won
        else:
            points_per_winner = total_won // len(winners)
            remainder = total_won % len(winners)

            # Sort winners by current points (ascending - furthest down gets less)
            sorted_winners = sorted(
                winners,
                key=lambda pid: next(p.points for p in self.players if p.id == pid),
            )

            for i, winner in enumerate(sorted_winners):
                points_changes[winner] = points_per_winner
                if i >= len(sorted_winners) - remainder:  # Last few get extra
                    points_changes[winner] += 1

        # Losers lose points
        if len(losers) == 1:
            points_changes[losers[0]] = -total_owed
        else:
            points_per_loser = total_owed // len(losers)
            remainder = total_owed % len(losers)

            # Sort losers by current points (ascending - furthest down pays less)
            sorted_losers = sorted(
                losers,
                key=lambda pid: next(p.points for p in self.players if p.id == pid),
            )

            for i, loser in enumerate(sorted_losers):
                points_changes[loser] = -points_per_loser
                if i >= len(sorted_losers) - remainder:  # Last few pay extra
                    points_changes[loser] -= 1

        return points_changes

    def offer_big_dick(self, player_id: str) -> dict[str, Any]:
        """
        The Big Dick: Player with most points can risk all winnings on hole 18
        Others must unanimously accept or individual players can use Ackerley's Gambit
        """
        if self.current_hole != 18:
            raise ValueError("Big Dick can only be offered on hole 18")

        player = next(p for p in self.players if p.id == player_id)

        # Must be the player with the most points
        max_points = max(p.points for p in self.players)
        if player.points != max_points or max_points <= 0:
            raise ValueError("Big Dick can only be offered by player with most points (and positive points)")

        hole_state = self.hole_states[self.current_hole]
        hole_state.betting.big_dick_invoked = True

        # Set up the challenge
        big_dick_wager = abs(player.points)  # Risk all winnings

        return {
            "status": "big_dick_offered",
            "challenger": player_id,
            "challenger_name": player.name,
            "wager_amount": big_dick_wager,
            "message": f"{player.name} offers The Big Dick! Risking {big_dick_wager} quarters against the field.",
            "requires_unanimous_acceptance": True,
        }

    def accept_big_dick(self, accepting_players: list[str]) -> dict[str, Any]:
        """
        Accept or reject The Big Dick challenge
        If not unanimous, individual players can use Ackerley's Gambit
        """
        hole_state = self.hole_states[self.current_hole]
        if not hole_state.betting.big_dick_invoked:
            raise ValueError("No Big Dick challenge active")

        challenger_id = next(p.id for p in self.players if p.points == max(p.points for p in self.players))
        challenger = next(p for p in self.players if p.id == challenger_id)

        other_players = [p for p in self.players if p.id != challenger_id]

        if len(accepting_players) == len(other_players):
            # Unanimous acceptance - standard Big Dick rules
            hole_state.teams = TeamFormation(
                type="solo",
                solo_player=challenger_id,
                opponents=[p.id for p in other_players],
                captain=challenger_id,
            )
            hole_state.betting.current_wager = abs(challenger.points)

            return {
                "status": "big_dick_accepted",
                "message": f"Big Dick unanimously accepted! {challenger.name} vs the field for {abs(challenger.points)} quarters.",
                "teams_formed": True,
            }
        # Not unanimous - handle Ackerley's Gambit
        declining_players = [p.id for p in other_players if p.id not in accepting_players]

        # Accepting players split the challenge
        if accepting_players:
            wager_per_player = abs(challenger.points) // len(accepting_players)
            hole_state.betting.ackerley_gambit = {
                "accepting_players": accepting_players,
                "declining_players": declining_players,
                "wager_per_accepting_player": wager_per_player,
            }

            return {
                "status": "big_dick_gambit",
                "message": f"Ackerley's Gambit invoked! {len(accepting_players)} players accept the challenge.",
                "accepting_players": [self._get_player_name(pid) for pid in accepting_players],
                "declining_players": [self._get_player_name(pid) for pid in declining_players],
                "wager_per_player": wager_per_player,
            }
        # No one accepts
        return {
            "status": "big_dick_declined",
            "message": "Big Dick challenge declined by all players.",
            "teams_formed": False,
        }

    def ping_pong_aardvark(self, team_id: str, aardvark_id: str) -> dict[str, Any]:
        """
        Ping Pong the Aardvark: Team can re-toss an Aardvark, doubling the bet again
        A team cannot toss the same Aardvark twice on the same hole
        """
        hole_state = self.hole_states[self.current_hole]

        # Check if this aardvark was already tossed to this team
        if aardvark_id in hole_state.betting.tossed_aardvarks:
            raise ValueError("Cannot ping pong the same Aardvark twice on the same hole")

        # Add to tossed list
        hole_state.betting.tossed_aardvarks.append(aardvark_id)
        hole_state.betting.ping_pong_count += 1

        # Double the bet again
        hole_state.betting.current_wager *= 2

        # Determine where the aardvark goes next
        available_teams = [t for t in ["team1", "team2", "team3"] if t != team_id]
        if available_teams:
            next_team = random.choice(available_teams)

            return {
                "status": "aardvark_ping_ponged",
                "message": f"Aardvark {self._get_player_name(aardvark_id)} ping ponged to {next_team}! Wager doubled to {hole_state.betting.current_wager}.",
                "new_wager": hole_state.betting.current_wager,
                "ping_pong_count": hole_state.betting.ping_pong_count,
                "aardvark_destination": next_team,
            }
        return {
            "status": "aardvark_stuck",
            "message": f"No more teams available! Aardvark {self._get_player_name(aardvark_id)} must stay.",
            "new_wager": hole_state.betting.current_wager,
        }

    def _finish_game(self) -> dict[str, Any]:
        """Finish the game and determine final results"""
        final_scores = {p.id: p.points for p in self.players}

        # Determine winner(s)
        max_points = max(final_scores.values())
        winners = [pid for pid, points in final_scores.items() if points == max_points]

        # Persist completed game to database
        self.complete_game()

        return {
            "status": "game_finished",
            "final_scores": final_scores,
            "winners": winners,
            "winner_names": [self._get_player_name(pid) for pid in winners],
            "game_summary": {
                "total_holes": 18,
                "final_phase": self.game_phase.value,
                "player_performances": [
                    {
                        "id": p.id,
                        "name": p.name,
                        "final_points": p.points,
                        "solo_count": p.solo_count,
                        "float_used": p.float_used,
                    }
                    for p in self.players
                ],
            },
        }

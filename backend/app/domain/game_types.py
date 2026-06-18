"""Domain data types for the Wolf Goat Pig game engine."""

import random
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from ..utils.time import utc_now
from ..validators import HandicapValidator


class GamePhase(Enum):
    """Game phases according to Wolf Goat Pig rules"""

    REGULAR = "regular"
    VINNIE_VARIATION = "vinnie_variation"  # Holes 13-16 in 4-man game
    HOEPFINGER = "hoepfinger"  # Final holes with Goat choosing position


class PlayerRole(Enum):
    """Player roles in Wolf Goat Pig"""

    CAPTAIN = "captain"
    SECOND_CAPTAIN = "second_captain"  # 6-man game only
    AARDVARK = "aardvark"  # 5th or 6th in rotation
    INVISIBLE_AARDVARK = "invisible_aardvark"  # 4-man game only
    GOAT = "goat"  # Player furthest down


@dataclass
class TimelineEvent:
    """Represents a chronological event in the hole timeline"""

    id: str
    timestamp: datetime
    type: str  # "shot", "partnership_request", "partnership_response", "double_offer", "double_response", "hole_start", "hole_complete"
    description: str
    details: dict[str, Any] = field(default_factory=dict)
    player_id: str | None = None
    player_name: str | None = None


@dataclass
class Player:
    """Wolf Goat Pig Player with all game-specific attributes"""

    id: str
    name: str
    handicap: float
    points: int = 0  # Current points (quarters)
    float_used: int = 0  # Number of times float has been used
    solo_count: int = 0  # Number of times gone solo (4-man requirement)
    goat_position_history: list[int] = field(default_factory=list)  # Track Hoepfinger position choices

    def __post_init__(self):
        """Ensure all attributes are properly initialized"""
        self.points = self.points or 0
        self.float_used = self.float_used or 0
        self.solo_count = self.solo_count or 0


# Backwards compatibility alias (temporary during transition)
WGPPlayer = Player


@dataclass
class TeamFormation:
    """Represents team formations for a hole"""

    type: str  # "partners", "solo", "aardvark_choice", "pending"
    captain: str | None = None
    second_captain: str | None = None  # 6-man game
    team1: list[str] = field(default_factory=list)
    team2: list[str] = field(default_factory=list)
    team3: list[str] = field(default_factory=list)  # 6-man game
    solo_player: str | None = None
    opponents: list[str] = field(default_factory=list)
    pending_request: dict | None = None


@dataclass
class BettingState:
    """Complete betting state for Wolf Goat Pig"""

    base_wager: int = 1  # Base quarters
    current_wager: int = 1  # Current wager including multipliers
    doubled: bool = False
    redoubled: bool = False
    carry_over: bool = False
    float_invoked: bool = False
    option_invoked: bool = False
    duncan_invoked: bool = False  # The Duncan (captain goes solo)
    tunkarri_invoked: bool = False  # The Tunkarri (aardvark goes solo)
    big_dick_invoked: bool = False  # The Big Dick (18th hole special)
    joes_special_value: int | None = None  # Hoepfinger hole value
    ackerley_gambit: dict | None = None  # Player opt-in/out situations
    line_of_scrimmage: str | None = None  # Player furthest from hole
    doubles_history: list[dict] = field(default_factory=list)  # Track double offers
    tossed_aardvarks: list[str] = field(default_factory=list)  # Track tossed aardvarks
    ping_pong_count: int = 0  # Ping pong counter


@dataclass
class BallPosition:
    """Represents a ball's current position on the hole"""

    player_id: str
    distance_to_pin: float
    lie_type: str  # "tee", "fairway", "rough", "bunker", "green", "in_hole"
    shot_count: int  # Number of shots taken
    holed: bool = False
    conceded: bool = False  # "good but not in"
    penalty_strokes: int = 0


@dataclass
class StrokeAdvantage:
    """Represents stroke advantages for a player on a specific hole"""

    player_id: str
    handicap: float
    strokes_received: float  # Number of strokes received on this hole (can be 0.5 for half strokes)
    net_score: float | None = None  # Gross score minus strokes received
    stroke_index: int | None = None  # Hole's stroke index (1-18)


@dataclass
class HoleState:
    """Complete state for a single hole with comprehensive shot-by-shot tracking"""

    hole_number: int
    hitting_order: list[str]
    teams: TeamFormation
    betting: BettingState

    # Shot-by-shot state tracking
    ball_positions: dict[str, BallPosition] = field(default_factory=dict)
    current_order_of_play: list[str] = field(default_factory=list)  # Based on distance from hole
    line_of_scrimmage: str | None = None  # Player furthest from hole
    next_player_to_hit: str | None = None

    # Handicap stroke tracking
    stroke_advantages: dict[str, StrokeAdvantage] = field(default_factory=dict)
    hole_par: int = 4  # Default par, can be overridden
    stroke_index: int = 10  # Default stroke index, can be overridden
    hole_yardage: int = 400  # Default yardage
    hole_difficulty: str = "Medium"  # Easy, Medium, Hard, Very Hard

    # Hole completion tracking
    scores: dict[str, int | None] = field(default_factory=dict)
    shots_completed: dict[str, bool] = field(default_factory=dict)
    balls_in_hole: list[str] = field(default_factory=list)  # Players who holed out
    concessions: dict[str, str] = field(default_factory=dict)  # "good but not in"
    points_awarded: dict[str, int] = field(default_factory=dict)  # Quarters won/lost per player

    # Shot progression state
    current_shot_number: int = 1
    hole_complete: bool = False
    wagering_closed: bool = False  # No more betting once ball is holed
    tee_shots_complete: int = 0  # Count of completed tee shots
    partnership_deadline_passed: bool = False  # Can no longer request partnerships
    invitation_windows: dict[str, bool] = field(default_factory=dict)  # Track who can still be invited

    def set_hole_info(
        self,
        par: int | None = None,
        yardage: int | None = None,
        stroke_index: int | None = None,
    ) -> None:
        """Set hole information with realistic defaults"""

        # Set par with realistic distribution
        if par is None:
            par_weights = [0.15, 0.65, 0.18, 0.02]  # Par 3, 4, 5, 6 weights
            self.hole_par = random.choices([3, 4, 5, 6], weights=par_weights)[0]
        else:
            self.hole_par = par

        # Set yardage based on par
        if yardage is None:
            if self.hole_par == 3:
                self.hole_yardage = random.randint(120, 220)
            elif self.hole_par == 4:
                self.hole_yardage = random.randint(300, 450)
            elif self.hole_par == 5:
                self.hole_yardage = random.randint(480, 650)
            else:  # Par 6
                self.hole_yardage = random.randint(650, 800)
        else:
            self.hole_yardage = yardage

        # Set stroke index (1 = hardest, 18 = easiest)
        if stroke_index is None:
            self.stroke_index = random.randint(1, 18)
        else:
            self.stroke_index = stroke_index

        # Determine difficulty based on par, yardage, and stroke index
        if self.stroke_index <= 4:
            self.hole_difficulty = "Very Hard"
        elif self.stroke_index <= 8:
            self.hole_difficulty = "Hard"
        elif self.stroke_index <= 14:
            self.hole_difficulty = "Medium"
        else:
            self.hole_difficulty = "Easy"

    def calculate_stroke_advantages(self, players: list["Player"]) -> None:
        """
        Calculate stroke advantages for all players on this hole.

        Strokes are calculated relative to the player with the lowest handicap,
        following match play format where the best player gives strokes to others.
        """
        self.stroke_advantages = {}

        # Calculate net handicaps relative to lowest handicap player
        player_handicaps = {player.id: player.handicap for player in players}
        net_handicaps = HandicapValidator.calculate_net_handicaps(player_handicaps)

        for player in players:
            # Use net handicap (relative to lowest) for stroke calculation
            net_handicap = net_handicaps.get(player.id, 0.0)
            strokes_received = self._calculate_strokes_received(net_handicap, self.stroke_index)

            self.stroke_advantages[player.id] = StrokeAdvantage(
                player_id=player.id,
                handicap=player.handicap,  # Store original handicap for reference
                strokes_received=strokes_received,
                stroke_index=self.stroke_index,
            )

    def _calculate_strokes_received(self, net_handicap: float, stroke_index: int) -> float:
        """
        Calculate strokes received on this hole with Creecher Feature support.

        Uses HandicapValidator's Creecher-aware method which properly implements
        the Wolf-Goat-Pig house rule for half strokes.

        Args:
            net_handicap: Player's NET handicap relative to lowest handicap player
            stroke_index: Hole's stroke index (1-18)

        Returns:
            Float strokes: 0.0, 0.5, 1.0, 1.5, etc.
        """
        try:
            # Use HandicapValidator with Creecher Feature support
            strokes = HandicapValidator.calculate_strokes_received_with_creecher(
                net_handicap, stroke_index, validate=True
            )
            return strokes
        except HandicapValidationError as e:
            logger.error(f"Stroke calculation failed: {e.message}, defaulting to 0 strokes")
            # If validation fails, default to no strokes rather than incorrect calculation
            return 0.0

    def get_player_stroke_advantage(self, player_id: str) -> StrokeAdvantage | None:
        """Get stroke advantage for a specific player"""
        return self.stroke_advantages.get(player_id)

    def calculate_net_score(self, player_id: str, gross_score: int) -> float:
        """
        Calculate net score for a player.

        Now uses HandicapValidator for validated net score calculation.
        """
        stroke_adv = self.get_player_stroke_advantage(player_id)
        if stroke_adv:
            try:
                # Use HandicapValidator for validated net score calculation
                net_score = HandicapValidator.calculate_net_score(
                    gross_score, int(stroke_adv.strokes_received), validate=True
                )
                stroke_adv.net_score = float(net_score)
                return stroke_adv.net_score
            except HandicapValidationError as e:
                logger.warning(f"Net score calculation error: {e.message}, using fallback")
                # Fallback calculation
                stroke_adv.net_score = gross_score - stroke_adv.strokes_received
                return stroke_adv.net_score
        return float(gross_score)

    def get_team_stroke_advantages(self) -> dict[str, list[StrokeAdvantage | None]]:
        """Get stroke advantages grouped by team"""
        team_strokes = {}

        if self.teams.type == "partners":
            # Team 1 vs Team 2
            team_strokes["team1"] = [
                self.stroke_advantages.get(p) for p in self.teams.team1 if p in self.stroke_advantages
            ]
            team_strokes["team2"] = [
                self.stroke_advantages.get(p) for p in self.teams.team2 if p in self.stroke_advantages
            ]
        elif self.teams.type == "solo":
            # Solo player vs opponents
            if self.teams.solo_player:
                team_strokes["solo"] = (
                    [self.stroke_advantages.get(self.teams.solo_player)]
                    if self.teams.solo_player in self.stroke_advantages
                    else []
                )
                team_strokes["opponents"] = [
                    self.stroke_advantages.get(p) for p in self.teams.opponents if p in self.stroke_advantages
                ]

        return team_strokes

    def get_best_net_score_for_team(self, team_players: list[str]) -> float | None:
        """Get the best net score for a team (for best ball scoring)"""
        team_scores = []
        for player_id in team_players:
            if player_id in self.scores and self.scores[player_id] is not None:
                score = cast("int", self.scores[player_id])
                net_score = self.calculate_net_score(player_id, score)
                team_scores.append(net_score)

        return min(team_scores) if team_scores else None

    def update_order_of_play(self):
        """Update order of play based on current ball positions"""
        # Filter out holed balls and sort by distance
        active_balls = [
            (player_id, pos) for player_id, pos in self.ball_positions.items() if not pos.holed and not pos.conceded
        ]

        # Sort by distance (furthest first)
        active_balls.sort(key=lambda x: x[1].distance_to_pin, reverse=True)

        self.current_order_of_play = [player_id for player_id, _ in active_balls]

        # Update line of scrimmage (furthest from hole)
        if active_balls:
            self.line_of_scrimmage = active_balls[0][0]

        # Set next player to hit
        if self.current_order_of_play:
            self.next_player_to_hit = self.current_order_of_play[0]
        else:
            self.next_player_to_hit = None

    def add_shot(self, player_id: str, shot_result: "WGPShotResult") -> None:
        """Add a shot result and update hole state"""
        if player_id not in self.ball_positions:
            # First shot of the hole (tee shot)
            ball = BallPosition(
                player_id=player_id,
                distance_to_pin=shot_result.distance_to_pin,
                lie_type=shot_result.lie_type,
                shot_count=1,
                penalty_strokes=shot_result.penalty_strokes,
            )
            if shot_result.made_shot:
                ball.holed = True
                self.balls_in_hole.append(player_id)
                self.wagering_closed = True

            self.ball_positions[player_id] = ball
        else:
            # Update existing ball position
            ball = self.ball_positions[player_id]
            ball.distance_to_pin = shot_result.distance_to_pin
            ball.lie_type = shot_result.lie_type
            ball.shot_count += 1
            ball.penalty_strokes += shot_result.penalty_strokes

            if shot_result.made_shot:
                ball.holed = True
                self.balls_in_hole.append(player_id)
                self.wagering_closed = True  # No more betting once ball is holed

        self.current_shot_number += 1
        self.update_order_of_play()
        self._recalculate_hole_completion()

    def _recalculate_hole_completion(self) -> None:
        """Update `hole_complete` based on current player ball states."""

        active_players: list[str] = []

        for player_id in self.hitting_order:
            if player_id in self.balls_in_hole:
                continue

            ball_pos = self.ball_positions.get(player_id)

            # Players without a recorded shot are still active and keep the hole open.
            if ball_pos is None:
                active_players.append(player_id)
                continue

            if ball_pos.conceded:
                continue

            # Player is active if they haven't holed out and haven't reached shot limit (8 shots)
            if not ball_pos.holed and ball_pos.shot_count < 8:
                active_players.append(player_id)

        self.hole_complete = not active_players

    def get_player_ball_position(self, player_id: str) -> BallPosition | None:
        """Get current ball position for a player"""
        return self.ball_positions.get(player_id)

    def is_player_eligible_for_betting(self, player_id: str) -> bool:
        """Check if player can make betting decisions (not past line of scrimmage)"""
        if not self.line_of_scrimmage:
            return True

        player_pos = self.get_player_ball_position(player_id)
        if not player_pos:
            return True

        line_pos = self.get_player_ball_position(self.line_of_scrimmage)
        if not line_pos:
            return True

        # Player can bet if they're not further from hole than line of scrimmage
        return player_pos.distance_to_pin >= line_pos.distance_to_pin

    def can_request_partnership(self, captain_id: str, target_id: str) -> bool:
        """Check if captain can still request this player as partner based on timing rules"""
        if self.partnership_deadline_passed:
            return False

        # Check invitation window for specific player
        return self.invitation_windows.get(target_id, True)

    def can_offer_double(self, player_id: str) -> bool:
        """Check if a player can offer a double based on line of scrimmage rules"""
        # No betting allowed once ball is holed
        if self.wagering_closed:
            return False

        # No doubles if player has passed line of scrimmage
        if self.line_of_scrimmage and player_id != self.line_of_scrimmage:
            # Check if this player is closer to hole than line of scrimmage
            if player_id in self.ball_positions and self.line_of_scrimmage in self.ball_positions:
                player_distance = self.ball_positions[player_id].distance_to_pin
                scrimmage_distance = self.ball_positions[self.line_of_scrimmage].distance_to_pin
                if player_distance < scrimmage_distance:
                    return False

        return True

    def has_ball_been_holed(self) -> bool:
        """Check if any ball has been holed (closes betting)"""
        return len(self.balls_in_hole) > 0

    def close_betting_if_ball_holed(self):
        """Close betting if any ball has been holed"""
        if self.has_ball_been_holed():
            self.wagering_closed = True

    def get_approach_shot_betting_opportunities(self) -> list[dict[str, Any]]:
        """Identify betting opportunities during approach shots and around the green"""
        opportunities: list[dict[str, Any]] = []

        if self.wagering_closed:
            return opportunities

        # Count players on green vs still approaching
        players_on_green = []
        players_approaching = []

        for player_id, ball_pos in self.ball_positions.items():
            if ball_pos.holed or ball_pos.conceded:
                continue
            if ball_pos.lie_type == "green":
                players_on_green.append(player_id)
            else:
                players_approaching.append(player_id)

        # Strategic betting moments:

        # 1. When all players are on the green (putting duel)
        if len(players_approaching) == 0 and len(players_on_green) >= 2:
            opportunities.append(
                {
                    "type": "putting_duel",
                    "description": "All players on green - prime time for doubles",
                    "strategic_value": "high",
                }
            )

        # 2. When most players are on green but one is still approaching
        elif len(players_approaching) == 1 and len(players_on_green) >= 2:
            opportunities.append(
                {
                    "type": "pressure_approach",
                    "description": "One player still needs to get on green",
                    "strategic_value": "medium",
                    "approaching_player": players_approaching[0],
                }
            )

        # 3. When someone has a short approach shot (within 100 yards)
        for player_id, ball_pos in self.ball_positions.items():
            if (
                not ball_pos.holed
                and not ball_pos.conceded
                and ball_pos.lie_type in ["fairway", "rough"]
                and ball_pos.distance_to_pin <= 100
            ):
                opportunities.append(
                    {
                        "type": "short_approach",
                        "description": f"Player has short approach shot ({ball_pos.distance_to_pin:.0f} yards)",
                        "strategic_value": "medium",
                        "player": player_id,
                        "distance": ball_pos.distance_to_pin,
                    }
                )

        return opportunities

    def should_offer_betting_after_shot(self, player_id: str) -> bool:
        """Determine if betting opportunities should be offered after a shot"""
        if self.wagering_closed:
            return False

        # Don't offer betting after every shot - only at strategic moments
        opportunities = self.get_approach_shot_betting_opportunities()
        return len(opportunities) > 0

    def process_tee_shot(self, player_id: str, shot_result: "WGPShotResult") -> None:
        """Process a tee shot and update partnership invitation windows"""
        # Add the shot
        self.add_shot(player_id, shot_result)

        # Update tee shot count
        if self.tee_shots_complete < len(self.hitting_order):
            self.tee_shots_complete += 1

        # Update invitation windows based on the rule:
        # "No player may be invited after they have hit their tee shot AND the next shot has been played as well"

        # Close invitation window for this player once they've hit
        self.invitation_windows[player_id] = False

        # If this is the 4th tee shot, partnership deadline has passed completely
        if self.tee_shots_complete >= len(self.hitting_order):
            self.partnership_deadline_passed = True

        # If there's a next player in tee order, and current player + next player have both hit,
        # then partnership opportunities are closed for current player
        current_index = self.hitting_order.index(player_id)
        if current_index < len(self.hitting_order) - 1:
            self.hitting_order[current_index + 1]
            # Next player's window closes when they hit AND the shot after them is played
            # This will be handled when the subsequent shot is processed

    def get_available_partners_for_captain(self, captain_id: str) -> list[str]:
        """Get players that captain can still invite based on timing rules"""
        available: list[str] = []

        if self.partnership_deadline_passed:
            return available

        for player_id in self.hitting_order:
            if player_id != captain_id and self.can_request_partnership(captain_id, player_id):
                available.append(player_id)

        return available

    def get_team_positions(self) -> dict[str, list[BallPosition | None]]:
        """Get ball positions grouped by team"""
        team_positions = {}

        if self.teams.type == "partners":
            # Team 1 vs Team 2
            team_positions["team1"] = [self.ball_positions.get(p) for p in self.teams.team1 if p in self.ball_positions]
            team_positions["team2"] = [self.ball_positions.get(p) for p in self.teams.team2 if p in self.ball_positions]
        elif self.teams.type == "solo":
            # Solo player vs opponents
            if self.teams.solo_player:
                team_positions["solo"] = (
                    [self.ball_positions.get(self.teams.solo_player)]
                    if self.teams.solo_player in self.ball_positions
                    else []
                )
                team_positions["opponents"] = [
                    self.ball_positions.get(p) for p in self.teams.opponents if p in self.ball_positions
                ]

        return team_positions


@dataclass
class WGPShotResult:
    """Represents a shot result in Wolf Goat Pig with betting implications"""

    player_id: str
    shot_number: int
    lie_type: str  # "tee", "fairway", "rough", "bunker", "green"
    distance_to_pin: float
    shot_quality: str  # "excellent", "good", "average", "poor", "terrible"
    made_shot: bool = False
    penalty_strokes: int = 0
    betting_implications: dict | None = None


@dataclass
class WGPBettingOpportunity:
    """Represents a betting opportunity during hole play"""

    opportunity_type: str  # "double", "strategic", "partnership_change"
    message: str
    options: list[str]
    probability_analysis: dict[str, float]
    recommended_action: str
    risk_assessment: str  # "low", "medium", "high"


@dataclass
class WGPHoleProgression:
    """Tracks shot-by-shot progression through a hole"""

    hole_number: int
    shots_taken: dict[str, list[WGPShotResult]] = field(default_factory=dict)
    current_shot_order: list[str] = field(default_factory=list)
    betting_opportunities: list[WGPBettingOpportunity] = field(default_factory=list)
    hole_complete: bool = False
    timeline_events: list[TimelineEvent] = field(default_factory=list)  # Chronological timeline

    def add_timeline_event(
        self,
        event_type: str,
        description: str,
        player_id: str | None = None,
        player_name: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> TimelineEvent:
        """Add a new timeline event"""
        event = TimelineEvent(
            id=f"event_{len(self.timeline_events) + 1}",
            timestamp=utc_now(),
            type=event_type,
            description=description,
            details=details or {},
            player_id=player_id,
            player_name=player_name,
        )
        self.timeline_events.append(event)
        return event

    def get_timeline_events(self) -> list[dict[str, Any]]:
        """Get timeline events as serializable dictionaries"""
        return [
            {
                "id": event.id,
                "timestamp": event.timestamp.isoformat(),
                "type": event.type,
                "description": event.description,
                "details": event.details,
                "player_id": event.player_id,
                "player_name": event.player_name,
            }
            for event in self.timeline_events
        ]

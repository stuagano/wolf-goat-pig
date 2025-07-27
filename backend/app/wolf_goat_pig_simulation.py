import random
import math
from typing import Dict, List, Tuple, Optional, Any, Union
from dataclasses import dataclass, field
from enum import Enum
import logging
from copy import deepcopy
from datetime import datetime

logger = logging.getLogger(__name__)

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
    details: Dict[str, Any] = field(default_factory=dict)
    player_id: Optional[str] = None
    player_name: Optional[str] = None

@dataclass
class WGPPlayer:
    """Wolf Goat Pig Player with all game-specific attributes"""
    id: str
    name: str
    handicap: float
    points: int = 0  # Current points (quarters)
    float_used: bool = False  # Has used their float
    solo_count: int = 0  # Number of times gone solo (4-man requirement)
    
    def __post_init__(self):
        """Ensure all attributes are properly initialized"""
        self.points = self.points or 0
        self.float_used = self.float_used or False
        self.solo_count = self.solo_count or 0

@dataclass
class TeamFormation:
    """Represents team formations for a hole"""
    type: str  # "partners", "solo", "aardvark_choice", "pending"
    captain: Optional[str] = None
    second_captain: Optional[str] = None  # 6-man game
    team1: List[str] = field(default_factory=list)
    team2: List[str] = field(default_factory=list) 
    team3: List[str] = field(default_factory=list)  # 6-man game
    solo_player: Optional[str] = None
    opponents: List[str] = field(default_factory=list)
    pending_request: Optional[Dict] = None

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
    joes_special_value: Optional[int] = None  # Hoepfinger hole value
    ackerley_gambit: Optional[Dict] = None  # Player opt-in/out situations
    line_of_scrimmage: Optional[str] = None  # Player furthest from hole
    doubles_history: List[Dict] = field(default_factory=list)  # Track double offers
    tossed_aardvarks: List[str] = field(default_factory=list)  # Track tossed aardvarks
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
    net_score: Optional[float] = None  # Gross score minus strokes received
    stroke_index: Optional[int] = None  # Hole's stroke index (1-18)

@dataclass
class HoleState:
    """Complete state for a single hole with comprehensive shot-by-shot tracking"""
    hole_number: int
    hitting_order: List[str]
    teams: TeamFormation
    betting: BettingState
    
    # Shot-by-shot state tracking
    ball_positions: Dict[str, BallPosition] = field(default_factory=dict)
    current_order_of_play: List[str] = field(default_factory=list)  # Based on distance from hole
    line_of_scrimmage: Optional[str] = None  # Player furthest from hole
    next_player_to_hit: Optional[str] = None
    
    # Handicap stroke tracking
    stroke_advantages: Dict[str, StrokeAdvantage] = field(default_factory=dict)
    hole_par: int = 4  # Default par, can be overridden
    stroke_index: int = 10  # Default stroke index, can be overridden
    
    # Hole completion tracking
    scores: Dict[str, Optional[int]] = field(default_factory=dict)
    shots_completed: Dict[str, bool] = field(default_factory=dict)
    balls_in_hole: List[str] = field(default_factory=list)  # Players who holed out
    concessions: Dict[str, str] = field(default_factory=dict)  # "good but not in"
    
    # Shot progression state
    current_shot_number: int = 1
    hole_complete: bool = False
    wagering_closed: bool = False  # No more betting once ball is holed
    
    def calculate_stroke_advantages(self, players: List['WGPPlayer']):
        """Calculate stroke advantages for all players on this hole"""
        self.stroke_advantages = {}
        
        for player in players:
            # Calculate strokes received based on handicap and stroke index
            strokes_received = self._calculate_strokes_received(player.handicap, self.stroke_index)
            
            self.stroke_advantages[player.id] = StrokeAdvantage(
                player_id=player.id,
                handicap=player.handicap,
                strokes_received=strokes_received,
                stroke_index=self.stroke_index
            )
    
    def _calculate_strokes_received(self, handicap: float, stroke_index: int) -> float:
        """Calculate strokes received on this hole based on handicap and stroke index"""
        # Use the proper Creecher Feature implementation from game_state.py
        full_strokes = int(handicap)
        half_stroke = (handicap - full_strokes) >= 0.5
        
        # Full strokes: assign to holes with stroke index <= full_strokes
        if stroke_index <= full_strokes:
            return 1.0
        
        # Half stroke: assign to next hardest hole not already getting a stroke
        if half_stroke and stroke_index == full_strokes + 1:
            return 0.5
        
        # Creecher Feature: Half strokes on easiest 6 holes (stroke indexes 13-18)
        if stroke_index >= 13 and stroke_index <= 18:
            # For players with handicap > 18, additional half strokes
            if handicap > 18:
                extra_half_strokes = int((handicap - 18) / 1.0)  # One extra half stroke per full stroke over 18
                # Assign to easiest holes first
                easiest_holes = [18, 17, 16, 15, 14, 13]
                if stroke_index in easiest_holes[:extra_half_strokes]:
                    return 0.5
        
        # No strokes for this hole
        return 0.0
    
    def get_player_stroke_advantage(self, player_id: str) -> Optional[StrokeAdvantage]:
        """Get stroke advantage for a specific player"""
        return self.stroke_advantages.get(player_id)
    
    def calculate_net_score(self, player_id: str, gross_score: int) -> float:
        """Calculate net score for a player"""
        stroke_adv = self.get_player_stroke_advantage(player_id)
        if stroke_adv:
            stroke_adv.net_score = gross_score - stroke_adv.strokes_received
            return stroke_adv.net_score
        return float(gross_score)
    
    def get_team_stroke_advantages(self) -> Dict[str, List[StrokeAdvantage]]:
        """Get stroke advantages grouped by team"""
        team_strokes = {}
        
        if self.teams.type == "partners":
            # Team 1 vs Team 2
            team_strokes["team1"] = [
                self.stroke_advantages.get(p) for p in self.teams.team1
                if p in self.stroke_advantages
            ]
            team_strokes["team2"] = [
                self.stroke_advantages.get(p) for p in self.teams.team2
                if p in self.stroke_advantages
            ]
        elif self.teams.type == "solo":
            # Solo player vs opponents
            if self.teams.solo_player:
                team_strokes["solo"] = [
                    self.stroke_advantages.get(self.teams.solo_player)
                ] if self.teams.solo_player in self.stroke_advantages else []
                team_strokes["opponents"] = [
                    self.stroke_advantages.get(p) for p in self.teams.opponents
                    if p in self.stroke_advantages
                ]
        
        return team_strokes
    
    def get_best_net_score_for_team(self, team_players: List[str]) -> Optional[float]:
        """Get the best net score for a team (for best ball scoring)"""
        team_scores = []
        for player_id in team_players:
            if player_id in self.scores and self.scores[player_id] is not None:
                net_score = self.calculate_net_score(player_id, self.scores[player_id])
                team_scores.append(net_score)
        
        return min(team_scores) if team_scores else None
    
    def update_order_of_play(self):
        """Update order of play based on current ball positions"""
        # Filter out holed balls and sort by distance
        active_balls = [
            (player_id, pos) for player_id, pos in self.ball_positions.items()
            if not pos.holed and not pos.conceded
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
    
    def add_shot(self, player_id: str, shot_result: 'WGPShotResult'):
        """Add a shot result and update hole state"""
        if player_id not in self.ball_positions:
            # First shot of the hole (tee shot)
            self.ball_positions[player_id] = BallPosition(
                player_id=player_id,
                distance_to_pin=shot_result.distance_to_pin,
                lie_type=shot_result.lie_type,
                shot_count=1,
                penalty_strokes=shot_result.penalty_strokes
            )
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
        
        # Check if hole is complete (all players have holed out or conceded)
        active_players = [p for p in self.hitting_order if p not in self.balls_in_hole]
        if not active_players:
            self.hole_complete = True
    
    def get_player_ball_position(self, player_id: str) -> Optional[BallPosition]:
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
    
    def get_team_positions(self) -> Dict[str, List[BallPosition]]:
        """Get ball positions grouped by team"""
        team_positions = {}
        
        if self.teams.type == "partners":
            # Team 1 vs Team 2
            team_positions["team1"] = [
                self.ball_positions.get(p) for p in self.teams.team1
                if p in self.ball_positions
            ]
            team_positions["team2"] = [
                self.ball_positions.get(p) for p in self.teams.team2
                if p in self.ball_positions
            ]
        elif self.teams.type == "solo":
            # Solo player vs opponents
            if self.teams.solo_player:
                team_positions["solo"] = [
                    self.ball_positions.get(self.teams.solo_player)
                ] if self.teams.solo_player in self.ball_positions else []
                team_positions["opponents"] = [
                    self.ball_positions.get(p) for p in self.teams.opponents
                    if p in self.ball_positions
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
    betting_implications: Optional[Dict] = None

@dataclass
class WGPBettingOpportunity:
    """Represents a betting opportunity during hole play"""
    opportunity_type: str  # "double", "strategic", "partnership_change"
    message: str
    options: List[str]
    probability_analysis: Dict[str, float]
    recommended_action: str
    risk_assessment: str  # "low", "medium", "high"

@dataclass
class WGPHoleProgression:
    """Tracks shot-by-shot progression through a hole"""
    hole_number: int
    shots_taken: Dict[str, List[WGPShotResult]] = field(default_factory=dict)
    current_shot_order: List[str] = field(default_factory=list)
    betting_opportunities: List[WGPBettingOpportunity] = field(default_factory=list)
    hole_complete: bool = False
    timeline_events: List[TimelineEvent] = field(default_factory=list)  # Chronological timeline
    
    def add_timeline_event(self, event_type: str, description: str, player_id: Optional[str] = None, 
                          player_name: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        """Add a new timeline event"""
        event = TimelineEvent(
            id=f"event_{len(self.timeline_events) + 1}",
            timestamp=datetime.now(),
            type=event_type,
            description=description,
            details=details or {},
            player_id=player_id,
            player_name=player_name
        )
        self.timeline_events.append(event)
        return event
    
    def get_timeline_events(self) -> List[Dict[str, Any]]:
        """Get timeline events as serializable dictionaries"""
        return [
            {
                "id": event.id,
                "timestamp": event.timestamp.isoformat(),
                "type": event.type,
                "description": event.description,
                "details": event.details,
                "player_id": event.player_id,
                "player_name": event.player_name
            }
            for event in self.timeline_events
        ]

class WolfGoatPigSimulation:
    """
    Complete Wolf Goat Pig simulation implementing all rules from rules.txt
    """
    
    def __init__(self, player_count: int = 4, players: Optional[List[WGPPlayer]] = None):
        if player_count not in [4, 5, 6]:
            raise ValueError("Wolf Goat Pig supports 4, 5, or 6 players only")
            
        self.player_count = player_count
        self.players = players or self._create_default_players()
        self.current_hole = 1
        self.game_phase = GamePhase.REGULAR
        self.hole_states: Dict[int, HoleState] = {}
        self.double_points_round = False  # Major championship days
        self.annual_banquet = False  # Annual banquet day
        
        # Computer players for AI decision making
        self.computer_players: Dict[str, Any] = {}
        
        # Shot progression and betting analysis
        self.hole_progression: Optional[WGPHoleProgression] = None
        self.betting_analysis_enabled = True
        self.shot_simulation_mode = False  # Enable for shot-by-shot play
        
        # Game progression tracking
        self.hoepfinger_start_hole = self._get_hoepfinger_start_hole()
        self.vinnie_variation_start = 13 if player_count == 4 else None
        
        # Initialize first hole
        self._initialize_hole(1)
    
    def set_computer_players(self, computer_player_ids: List[str], personalities: Optional[List[str]] = None):
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
    
    def _create_default_players(self) -> List[WGPPlayer]:
        """Create default players based on the rules.txt character list"""
        names = ["Bob", "Scott", "Vince", "Mike", "Terry", "Bill"][:self.player_count]
        handicaps = [10.5, 15, 8, 20.5, 12, 18][:self.player_count]
        
        return [
            WGPPlayer(id=f"p{i+1}", name=names[i], handicap=handicaps[i])
            for i in range(self.player_count)
        ]
    
    def _get_hoepfinger_start_hole(self) -> int:
        """Get starting hole for Hoepfinger phase based on player count"""
        return {4: 17, 5: 16, 6: 13}[self.player_count]
    
    def _initialize_hole(self, hole_number: int):
        """Initialize a new hole with proper state"""
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
        
        # Calculate stroke index for this hole (simplified - could be enhanced with course data)
        stroke_index = min(hole_number, 18)  # Simple stroke index calculation
        
        # Initialize hole state
        hole_state = HoleState(
            hole_number=hole_number,
            hitting_order=hitting_order,
            teams=teams,
            betting=betting_state,
            stroke_index=stroke_index,
            scores={p.id: None for p in self.players},
            shots_completed={p.id: False for p in self.players}
        )
        
        # Calculate stroke advantages for all players on this hole
        hole_state.calculate_stroke_advantages(self.players)
        
        # Initialize hole progression with timeline tracking
        self.hole_progression = WGPHoleProgression(hole_number=hole_number)
        
        # Add hole start event to timeline
        captain_name = self._get_player_name(hitting_order[0])
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
                "stroke_index": stroke_index
            }
        )
        
        self.hole_states[hole_number] = hole_state
        
    def _random_hitting_order(self) -> List[str]:
        """Determine random hitting order for first hole (tossing tees)"""
        player_ids = [p.id for p in self.players]
        random.shuffle(player_ids)
        return player_ids
    
    def _rotate_hitting_order(self, hole_number: int) -> List[str]:
        """Rotate hitting order for subsequent holes"""
        if hole_number == 1:
            return self._random_hitting_order()
            
        previous_order = self.hole_states[hole_number - 1].hitting_order
        # Rotate: second becomes first, third becomes second, etc.
        return previous_order[1:] + [previous_order[0]]
    
    def _get_goat(self) -> WGPPlayer:
        """Get the player who is furthest down (the Goat)"""
        return min(self.players, key=lambda p: p.points)
    
    def _goat_chooses_position(self, goat: WGPPlayer, current_order: List[str]) -> List[str]:
        """
        In Hoepfinger phase, the Goat chooses hitting position
        Note: In 6-man game, can't choose same spot more than twice in a row
        """
        # For simulation, Goat chooses randomly (in real game, this would be user input)
        # TODO: Add logic to track previous choices for 6-man restriction
        available_positions = list(range(len(current_order)))
        chosen_position = random.choice(available_positions)
        
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
        if (self.player_count == 4 and 
            self.vinnie_variation_start and 
            hole_number >= self.vinnie_variation_start and 
            hole_number < self.hoepfinger_start_hole):
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
    
    def _prompt_joes_special(self, goat: WGPPlayer, natural_start: int) -> Optional[int]:
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
    
    def request_partner(self, captain_id: str, partner_id: str) -> Dict[str, Any]:
        """Captain requests a specific player as partner"""
        hole_state = self.hole_states[self.current_hole]
        
        # Validate request
        if hole_state.teams.captain != captain_id:
            raise ValueError("Only the captain can request a partner")
            
        if partner_id not in [p.id for p in self.players]:
            raise ValueError("Invalid partner ID")
            
        if partner_id == captain_id:
            raise ValueError("Captain cannot partner with themselves")
            
        # Check eligibility based on hitting order and shots taken
        if not self._is_player_eligible_for_partnership(partner_id, hole_state):
            raise ValueError("Player is no longer eligible for partnership")
            
        # Set pending request
        hole_state.teams.pending_request = {
            "type": "partnership",
            "captain": captain_id,
            "requested": partner_id
        }
        
        # Add partnership request event to timeline
        captain_name = self._get_player_name(captain_id)
        partner_name = self._get_player_name(partner_id)
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
                "hole_number": self.current_hole
            }
        )
        
        return {
            "status": "pending",
            "message": f"Partnership request sent to {partner_name}",
            "awaiting_response": partner_id
        }
    
    def respond_to_partnership(self, partner_id: str, accept: bool) -> Dict[str, Any]:
        """Respond to partnership request"""
        hole_state = self.hole_states[self.current_hole]
        
        # Validate response
        pending = hole_state.teams.pending_request
        if not pending or pending.get("requested") != partner_id:
            raise ValueError("No pending partnership request for this player")
            
        captain_id = pending["captain"]
        
        if accept:
            return self._accept_partnership(captain_id, partner_id, hole_state)
        else:
            return self._decline_partnership(captain_id, partner_id, hole_state)
    
    def captain_go_solo(self, captain_id: str, use_duncan: bool = False) -> Dict[str, Any]:
        """Captain decides to go solo (Pig)"""
        hole_state = self.hole_states[self.current_hole]
        
        if hole_state.teams.captain != captain_id:
            raise ValueError("Only the captain can go solo")
            
        captain = next(p for p in self.players if p.id == captain_id)
        
        # Track solo count for 4-man game requirement
        if self.player_count == 4:
            captain.solo_count += 1
            
        # Set up solo play
        opponents = [p.id for p in self.players if p.id != captain_id]
        hole_state.teams = TeamFormation(
            type="solo",
            captain=captain_id,
            solo_player=captain_id,
            opponents=opponents
        )
        
        # Apply wager multipliers
        multiplier = 2  # Base "On Your Own" multiplier
        
        if use_duncan:
            # The Duncan: 3 quarters for every 2 wagered
            hole_state.betting.duncan_invoked = True
            multiplier = 2  # Still doubles the base wager
            
        hole_state.betting.current_wager *= multiplier
        
        # Add solo decision event to timeline
        captain_name = self._get_player_name(captain_id)
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
                "opponents": [self._get_player_name(p) for p in opponents]
            }
        )
        
        return {
            "status": "solo",
            "message": f"Captain {captain_name} goes solo!",
            "duncan": use_duncan,
            "wager": hole_state.betting.current_wager
        }
    
    def aardvark_request_team(self, aardvark_id: str, target_team: str) -> Dict[str, Any]:
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
            "target_team": target_team
        }
        
        return {
            "status": "pending",
            "message": f"Aardvark {self._get_player_name(aardvark_id)} requests to join {target_team}",
            "awaiting_response": target_team
        }
    
    def respond_to_aardvark(self, team_id: str, accept: bool) -> Dict[str, Any]:
        """Respond to aardvark request"""
        hole_state = self.hole_states[self.current_hole]
        
        pending = hole_state.teams.pending_request
        if not pending or pending.get("type") != "aardvark":
            raise ValueError("No pending aardvark request")
            
        aardvark_id = pending["aardvark"]
        
        if accept:
            return self._accept_aardvark(aardvark_id, team_id, hole_state)
        else:
            return self._toss_aardvark(aardvark_id, team_id, hole_state)
    
    def aardvark_go_solo(self, aardvark_id: str, use_tunkarri: bool = False) -> Dict[str, Any]:
        """Aardvark decides to go solo (5-man and 6-man games)"""
        if self.player_count == 4:
            raise ValueError("No aardvark in 4-man game")
            
        hole_state = self.hole_states[self.current_hole]
        
        if not self._is_aardvark(aardvark_id, hole_state):
            raise ValueError("Player is not an aardvark on this hole")
            
        # Set up aardvark solo play
        others = [p.id for p in self.players if p.id != aardvark_id]
        hole_state.teams = TeamFormation(
            type="solo",
            solo_player=aardvark_id,
            opponents=others
        )
        
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
            "wager": hole_state.betting.current_wager
        }
    
    def offer_double(self, offering_player_id: str, target_team: Optional[str] = None) -> Dict[str, Any]:
        """Offer a double to the opposing team"""
        hole_state = self.hole_states[self.current_hole]
        
        # Check Line of Scrimmage rule
        if hole_state.betting.line_of_scrimmage == offering_player_id:
            raise ValueError("Cannot offer double - player is past line of scrimmage")
            
        # Check if double already offered
        if hole_state.betting.doubled:
            raise ValueError("Double already offered on this hole")
            
        # Check if any ball is in the hole
        if hole_state.balls_in_hole:
            raise ValueError("Cannot offer double - ball is in the hole")
            
        # Record double offer
        hole_state.betting.doubles_history.append({
            "offering_player": offering_player_id,
            "target_team": target_team,
            "wager_before": hole_state.betting.current_wager
        })
        
        hole_state.betting.doubled = True
        
        # Add double offer event to timeline
        offering_player_name = self._get_player_name(offering_player_id)
        self.hole_progression.add_timeline_event(
            event_type="double_offer",
            description=f"{offering_player_name} offers a double - wager increases from {hole_state.betting.current_wager} to {hole_state.betting.current_wager * 2} quarters",
            player_id=offering_player_id,
            player_name=offering_player_name,
            details={
                "offering_player": offering_player_name,
                "current_wager": hole_state.betting.current_wager,
                "potential_wager": hole_state.betting.current_wager * 2,
                "hole_number": self.current_hole
            }
        )
        
        return {
            "status": "double_offered",
            "message": f"{offering_player_name} offers a double",
            "current_wager": hole_state.betting.current_wager,
            "potential_wager": hole_state.betting.current_wager * 2
        }
    
    def respond_to_double(self, responding_team: str, accept: bool, 
                         gambit_players: Optional[List[str]] = None) -> Dict[str, Any]:
        """Respond to a double offer, with optional Ackerley's Gambit"""
        hole_state = self.hole_states[self.current_hole]
        
        if not hole_state.betting.doubled:
            raise ValueError("No double to respond to")
            
        if accept:
            if gambit_players:
                # Ackerley's Gambit: some players opt out, others stay in
                return self._handle_ackerley_gambit(responding_team, gambit_players, hole_state)
            else:
                # Standard double acceptance
                hole_state.betting.current_wager *= 2
                hole_state.betting.doubled = False
                
                # Add double acceptance event to timeline
                self.hole_progression.add_timeline_event(
                    event_type="double_response",
                    description=f"Double accepted - wager increases to {hole_state.betting.current_wager} quarters",
                    details={
                        "accepted": True,
                        "new_wager": hole_state.betting.current_wager,
                        "responding_team": responding_team
                    }
                )
                
                return {
                    "status": "double_accepted",
                    "message": "Double accepted",
                    "new_wager": hole_state.betting.current_wager
                }
        else:
            # Double declined - offering team wins hole
            return self._resolve_double_decline(hole_state)
    
    def invoke_float(self, captain_id: str) -> Dict[str, Any]:
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
            "new_wager": hole_state.betting.current_wager
        }
    
    def enter_hole_scores(self, scores: Dict[str, int]) -> Dict[str, Any]:
        """Enter scores for the hole and calculate points"""
        hole_state = self.hole_states[self.current_hole]
        
        # Validate all scores are provided
        for player_id in [p.id for p in self.players]:
            if player_id not in scores:
                raise ValueError(f"Score missing for player {self._get_player_name(player_id)}")
                
        hole_state.scores = scores
        
        # Calculate and distribute points
        points_result = self._calculate_hole_points(hole_state)
        
        # Update player points
        for player_id, points_change in points_result["points_changes"].items():
            player = next(p for p in self.players if p.id == player_id)
            player.points += points_change
            
        # Check for carry-over
        if points_result["halved"]:
            hole_state.betting.carry_over = True
            
        return points_result
    
    def advance_to_next_hole(self) -> Dict[str, Any]:
        """Advance to the next hole"""
        if self.current_hole >= 18:
            return self._finish_game()
            
        self.current_hole += 1
        self._initialize_hole(self.current_hole)
        
        return {
            "status": "hole_advanced",
            "current_hole": self.current_hole,
            "game_phase": self.game_phase.value,
            "hole_state": self._get_hole_state_summary()
        }
    
    def get_game_state(self) -> Dict[str, Any]:
        """Get complete current game state"""
        hole_state = self.hole_states.get(self.current_hole)
        
        return {
            "current_hole": self.current_hole,
            "game_phase": self.game_phase.value,
            "player_count": self.player_count,
            "players": [
                {
                    "id": p.id,
                    "name": p.name,
                    "handicap": p.handicap,
                    "points": p.points,
                    "float_used": p.float_used,
                    "solo_count": p.solo_count
                }
                for p in self.players
            ],
            "hole_state": self._get_hole_state_summary() if hole_state else None,
            "hoepfinger_start": self.hoepfinger_start_hole,
            "settings": {
                "double_points_round": self.double_points_round,
                "annual_banquet": self.annual_banquet
            }
        }
    
    def _get_hole_state_summary(self) -> Dict[str, Any]:
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
                player_id: {
                    "distance_to_pin": ball.distance_to_pin,
                    "lie_type": ball.lie_type,
                    "shot_count": ball.shot_count,
                    "holed": ball.holed,
                    "conceded": ball.conceded,
                    "penalty_strokes": ball.penalty_strokes
                } if ball else None
                for player_id in [p.id for p in self.players]
                for ball in [hole_state.get_player_ball_position(player_id)]
            },
            "current_order_of_play": hole_state.current_order_of_play,
            "line_of_scrimmage": hole_state.line_of_scrimmage,
            "next_player_to_hit": hole_state.next_player_to_hit,
            
            # Stroke advantages
            "stroke_advantages": {
                player_id: {
                    "handicap": stroke_adv.handicap,
                    "strokes_received": stroke_adv.strokes_received,
                    "net_score": stroke_adv.net_score,
                    "stroke_index": stroke_adv.stroke_index
                } if stroke_adv else None
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
                "pending_request": hole_state.teams.pending_request
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
                    "joes_special_value": hole_state.betting.joes_special_value
                }
            },
            
            # Completion tracking
            "scores": hole_state.scores,
            "balls_in_hole": hole_state.balls_in_hole,
            "concessions": hole_state.concessions
        }
    
    # Helper methods
    
    def _get_player_name(self, player_id: str) -> str:
        """Get player name by ID"""
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
        elif self.player_count == 5:
            return hole_state.hitting_order.index(player_id) == 4  # 5th position
        else:  # 6-man
            index = hole_state.hitting_order.index(player_id)
            return index in [4, 5]  # 5th or 6th position
    
    def _accept_partnership(self, captain_id: str, partner_id: str, hole_state: HoleState) -> Dict[str, Any]:
        """Handle partnership acceptance"""
        others = [p.id for p in self.players if p.id not in [captain_id, partner_id]]
        
        hole_state.teams = TeamFormation(
            type="partners",
            captain=captain_id,
            team1=[captain_id, partner_id],
            team2=others
        )
        
        hole_state.teams.pending_request = None
        
        # Add partnership acceptance event to timeline
        captain_name = self._get_player_name(captain_id)
        partner_name = self._get_player_name(partner_id)
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
                "team2": [self._get_player_name(p) for p in others]
            }
        )
        
        return {
            "status": "partnership_formed",
            "message": f"Partnership formed: {captain_name} & {partner_name}",
            "team1": [captain_id, partner_id],
            "team2": others
        }
    
    def _decline_partnership(self, captain_id: str, partner_id: str, hole_state: HoleState) -> Dict[str, Any]:
        """Handle partnership decline - captain goes solo"""
        others = [p.id for p in self.players if p.id != captain_id]
        
        # Track solo count for 4-man requirement
        if self.player_count == 4:
            captain = next(p for p in self.players if p.id == captain_id)
            captain.solo_count += 1
        
        hole_state.teams = TeamFormation(
            type="solo",
            captain=captain_id,
            solo_player=captain_id,
            opponents=others
        )
        
        # Double the wager due to partnership decline
        hole_state.betting.current_wager *= 2
        hole_state.teams.pending_request = None
        
        # Add partnership decline event to timeline
        captain_name = self._get_player_name(captain_id)
        partner_name = self._get_player_name(partner_id)
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
                "opponents": [self._get_player_name(p) for p in others]
            }
        )
        
        return {
            "status": "partnership_declined",
            "message": f"{partner_name} declined. {captain_name} goes solo!",
            "new_wager": hole_state.betting.current_wager
        }
    
    def _accept_aardvark(self, aardvark_id: str, team_id: str, hole_state: HoleState) -> Dict[str, Any]:
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
            "teams": {
                "team1": hole_state.teams.team1,
                "team2": hole_state.teams.team2
            }
        }
    
    def _toss_aardvark(self, aardvark_id: str, rejecting_team: str, hole_state: HoleState) -> Dict[str, Any]:
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
            "teams": {
                "team1": hole_state.teams.team1,
                "team2": hole_state.teams.team2
            }
        }
    
    def _handle_ackerley_gambit(self, responding_team: str, gambit_players: List[str], 
                               hole_state: HoleState) -> Dict[str, Any]:
        """Handle Ackerley's Gambit - some players opt out, others stay in"""
        opt_out_players = [p for p in gambit_players if p not in gambit_players]
        opt_in_players = gambit_players
        
        # Opt-out players forfeit their current quarters at risk
        hole_state.betting.ackerley_gambit = {
            "opt_out": opt_out_players,
            "opt_in": opt_in_players
        }
        
        # Double the wager for opt-in players
        hole_state.betting.current_wager *= 2
        hole_state.betting.doubled = False
        
        return {
            "status": "ackerley_gambit",
            "message": "Ackerley's Gambit invoked",
            "opt_out_players": opt_out_players,
            "opt_in_players": opt_in_players,
            "new_wager": hole_state.betting.current_wager
        }
    
    def _resolve_double_decline(self, hole_state: HoleState) -> Dict[str, Any]:
        """Handle double decline - offering team wins hole"""
        hole_state.betting.doubled = False
        
        # Determine offering team from doubles history
        last_double = hole_state.betting.doubles_history[-1]
        offering_player = last_double["offering_player"]
        
        # Add double decline event to timeline
        offering_player_name = self._get_player_name(offering_player)
        self.hole_progression.add_timeline_event(
            event_type="double_response",
            description=f"Double declined - {offering_player_name}'s team wins the hole",
            player_id=offering_player,
            player_name=offering_player_name,
            details={
                "accepted": False,
                "offering_player": offering_player_name,
                "wager": last_double["wager_before"],
                "hole_winner": "offering_team"
            }
        )
        
        # Award points to offering team
        points_result = {
            "status": "double_declined",
            "message": "Double declined. Offering team wins hole.",
            "hole_winner": "offering_team",
            "points_changes": {}
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
                points_result["points_changes"][offering_player] = wager * len(hole_state.teams.opponents)
                for opp in hole_state.teams.opponents:
                    points_result["points_changes"][opp] = -wager
            else:
                # Opponents win
                points_result["points_changes"][hole_state.teams.solo_player] = -wager * len(hole_state.teams.opponents)
                for opp in hole_state.teams.opponents:
                    points_result["points_changes"][opp] = wager
        
        return points_result
    
    def _calculate_hole_points(self, hole_state: HoleState) -> Dict[str, Any]:
        """Calculate points for the hole based on scores and betting"""
        scores = hole_state.scores
        betting = hole_state.betting
        teams = hole_state.teams
        
        if teams.type == "partners":
            return self._calculate_partners_points(scores, teams, betting)
        elif teams.type == "solo":
            return self._calculate_solo_points(scores, teams, betting)
        else:
            raise ValueError(f"Invalid team type for points calculation: {teams.type}")
    
    def _calculate_partners_points(self, scores: Dict[str, int], teams: TeamFormation, 
                                  betting: BettingState) -> Dict[str, Any]:
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
                "points_changes": {p.id: 0 for p in self.players}
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
            "message": f"Team {winners} wins the hole"
        }
    
    def _calculate_solo_points(self, scores: Dict[str, int], teams: TeamFormation, 
                              betting: BettingState) -> Dict[str, Any]:
        """Calculate points for solo format"""
        solo_player = teams.solo_player
        opponents = teams.opponents
        
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
                
            winners = opponents
            message = f"Opponents defeat {self._get_player_name(solo_player)}"
            
        else:
            # Hole halved
            return {
                "halved": True,
                "message": "Hole halved. No points awarded.",
                "points_changes": {p.id: 0 for p in self.players}
            }
        
        # Apply special rule multipliers
        if betting.duncan_invoked or betting.tunkarri_invoked:
            # 3 for 2 rule
            for winner in winners:
                if points_changes[winner] > 0:
                    points_changes[winner] = int(points_changes[winner] * 1.5)
        
        return {
            "halved": False,
            "winners": winners,
            "points_changes": points_changes,
            "message": message
        }
    
    def _apply_karl_marx_rule(self, winners: List[str], losers: List[str], wager: int) -> Dict[str, int]:
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
            sorted_winners = sorted(winners, key=lambda pid: next(p.points for p in self.players if p.id == pid))
            
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
            sorted_losers = sorted(losers, key=lambda pid: next(p.points for p in self.players if p.id == pid))
            
            for i, loser in enumerate(sorted_losers):
                points_changes[loser] = -points_per_loser
                if i >= len(sorted_losers) - remainder:  # Last few pay extra
                    points_changes[loser] -= 1
        
        return points_changes
    
    def _finish_game(self) -> Dict[str, Any]:
        """Finish the game and determine final results"""
        final_scores = {p.id: p.points for p in self.players}
        
        # Determine winner(s)
        max_points = max(final_scores.values())
        winners = [pid for pid, points in final_scores.items() if points == max_points]
        
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
                        "float_used": p.float_used
                    }
                    for p in self.players
                ]
            }
        }

    def enable_shot_progression(self) -> Dict[str, Any]:
        """Enable shot-by-shot progression mode for betting analysis"""
        self.shot_simulation_mode = True
        if not self.hole_progression:
            self.hole_progression = WGPHoleProgression(hole_number=self.current_hole)
            # Initialize shot tracking for all players
            for player in self.players:
                self.hole_progression.shots_taken[player.id] = []
        
        # Always determine shot order when enabling shot progression
        self._determine_shot_order()
        
        return {
            "status": "shot_progression_enabled",
            "message": "Shot-by-shot progression enabled with betting analysis",
            "current_hole": self.current_hole,
            "shot_order": self.hole_progression.current_shot_order
        }
    
    def simulate_shot(self, player_id: str) -> Dict[str, Any]:
        """Simulate a single shot with comprehensive hole state tracking"""
        if not self.shot_simulation_mode:
            raise ValueError("Shot progression mode not enabled")
        
        player = next(p for p in self.players if p.id == player_id)
        hole_state = self.hole_states[self.current_hole]
        
        # Determine shot number based on current ball position
        current_ball = hole_state.get_player_ball_position(player_id)
        shot_number = (current_ball.shot_count + 1) if current_ball else 1
        
        # Simulate shot result based on player skill and situation
        shot_result = self._simulate_player_shot(player, shot_number)
        
        # Update hole state with the shot result
        hole_state.add_shot(player_id, shot_result)
        
        # Add shot event to timeline
        player_name = self._get_player_name(player_id)
        shot_description = f"{player_name} hits a {shot_result.shot_quality} shot"
        if shot_result.made_shot:
            shot_description += " and holes out!"
        elif shot_result.lie_type == "tee":
            shot_description += f" from the tee - {shot_result.distance_to_pin:.0f} yards to pin"
        else:
            shot_description += f" - {shot_result.distance_to_pin:.0f} yards to pin"
        
        self.hole_progression.add_timeline_event(
            event_type="shot",
            description=shot_description,
            player_id=player_id,
            player_name=player_name,
            details={
                "shot_number": shot_result.shot_number,
                "lie_type": shot_result.lie_type,
                "distance_to_pin": shot_result.distance_to_pin,
                "shot_quality": shot_result.shot_quality,
                "made_shot": shot_result.made_shot,
                "penalty_strokes": shot_result.penalty_strokes,
                "hole_number": self.current_hole
            }
        )
        
        # Analyze betting opportunities after this shot
        betting_opportunity = self._analyze_betting_opportunity(shot_result)
        
        # Get comprehensive hole state information
        hole_state_info = self._get_comprehensive_hole_state()
        
        return {
            "status": "shot_completed",
            "shot_result": {
                "player_id": shot_result.player_id,
                "shot_number": shot_result.shot_number,
                "lie_type": shot_result.lie_type,
                "distance_to_pin": shot_result.distance_to_pin,
                "shot_quality": shot_result.shot_quality,
                "made_shot": shot_result.made_shot,
                "penalty_strokes": shot_result.penalty_strokes
            },
            "hole_state": hole_state_info,
            "betting_opportunity": betting_opportunity.__dict__ if betting_opportunity else None,
            "betting_analysis": self._generate_betting_analysis(shot_result),
            "next_player": hole_state.next_player_to_hit,
            "hole_complete": hole_state.hole_complete,
            "game_state": self.get_game_state()
        }
    
    def get_hole_progression_state(self) -> Dict[str, Any]:
        """Get current hole progression state"""
        if not self.hole_progression:
            return {"shot_mode_enabled": False}
        
        return {
            "shot_mode_enabled": True,
            "hole_number": self.hole_progression.hole_number,
            "shots_taken": {
                player_id: [
                    {
                        "shot_number": shot.shot_number,
                        "lie_type": shot.lie_type,
                        "distance_to_pin": shot.distance_to_pin,
                        "shot_quality": shot.shot_quality,
                        "made_shot": shot.made_shot
                    }
                    for shot in shots
                ]
                for player_id, shots in self.hole_progression.shots_taken.items()
            },
            "betting_opportunities": [
                {
                    "type": opp.opportunity_type,
                    "message": opp.message,
                    "options": opp.options,
                    "recommended_action": opp.recommended_action,
                    "risk_assessment": opp.risk_assessment
                }
                for opp in self.hole_progression.betting_opportunities
            ],
            "timeline_events": self.hole_progression.get_timeline_events(),
            "next_player": self._get_next_shot_player(),
            "hole_complete": self.hole_progression.hole_complete
        }

    # Helper methods for shot progression
    def _determine_shot_order(self):
        """Determine order for shot-by-shot play"""
        hole_state = self.hole_states[self.current_hole]
        self.hole_progression.current_shot_order = hole_state.hitting_order.copy()
        
        # Initialize shot tracking for all players in hitting order
        for player_id in hole_state.hitting_order:
            if player_id not in self.hole_progression.shots_taken:
                self.hole_progression.shots_taken[player_id] = []
        
        # Set the initial next player to hit (first player in hitting order)
        if hole_state.hitting_order:
            hole_state.next_player_to_hit = hole_state.hitting_order[0]
            hole_state.current_order_of_play = hole_state.hitting_order.copy()
    
    def _simulate_player_shot(self, player: WGPPlayer, shot_number: int) -> WGPShotResult:
        """Simulate a single shot for a player"""
        # Determine lie type based on shot number and previous results
        if shot_number == 1:
            lie_type = "tee"
            distance_to_pin = random.uniform(150, 450)  # Tee shot distance
        else:
            # Get previous shot
            prev_shots = self.hole_progression.shots_taken[player.id]
            if prev_shots:
                prev_distance = prev_shots[-1].distance_to_pin
                lie_type = self._determine_lie_type(prev_shots[-1])
                distance_to_pin = max(0, prev_distance - random.uniform(50, 200))
            else:
                lie_type = "fairway"
                distance_to_pin = random.uniform(50, 150)
        
        # Simulate shot quality based on player handicap and lie
        shot_quality = self._determine_shot_quality(player.handicap, lie_type)
        
        # Determine if shot was made (holed out)
        made_shot = distance_to_pin < 5 and random.random() > 0.7
        if made_shot:
            distance_to_pin = 0
        
        return WGPShotResult(
            player_id=player.id,
            shot_number=shot_number,
            lie_type=lie_type,
            distance_to_pin=distance_to_pin,
            shot_quality=shot_quality,
            made_shot=made_shot
        )
    
    def _determine_lie_type(self, prev_shot: WGPShotResult) -> str:
        """Determine lie type based on previous shot quality"""
        if prev_shot.shot_quality == "excellent":
            return random.choice(["fairway", "green"])
        elif prev_shot.shot_quality == "good":
            return random.choice(["fairway", "fairway", "green"])
        elif prev_shot.shot_quality == "average":
            return random.choice(["fairway", "rough"])
        elif prev_shot.shot_quality == "poor":
            return random.choice(["rough", "bunker"])
        else:  # terrible
            return random.choice(["rough", "bunker", "rough"])
    
    def _determine_shot_quality(self, handicap: float, lie_type: str) -> str:
        """Determine shot quality based on handicap and lie"""
        # Base probability on handicap (lower handicap = better shots)
        skill_factor = max(0, 1 - (handicap / 30))
        
        # Adjust for lie difficulty
        lie_difficulty = {
            "tee": 0.9,
            "fairway": 1.0,
            "green": 1.1,
            "rough": 0.7,
            "bunker": 0.5
        }
        
        adjusted_skill = skill_factor * lie_difficulty.get(lie_type, 1.0)
        
        # Determine quality
        rand = random.random()
        if rand < adjusted_skill * 0.2:
            return "excellent"
        elif rand < adjusted_skill * 0.5:
            return "good"
        elif rand < adjusted_skill * 0.8:
            return "average"
        elif rand < 0.9:
            return "poor"
        else:
            return "terrible"
    
    def _analyze_betting_opportunity(self, shot_result: WGPShotResult) -> Optional[WGPBettingOpportunity]:
        """Analyze if this shot creates a betting opportunity"""
        hole_state = self.hole_states[self.current_hole]
        
        # Skip if teams not formed yet
        if hole_state.teams.type == "pending":
            return None
        
        # Skip if already doubled
        if hole_state.betting.doubled:
            return None
        
        # Analyze shot for betting implications
        opportunity = None
        
        if shot_result.shot_quality == "excellent":
            opportunity = WGPBettingOpportunity(
                opportunity_type="double",
                message=f"💎 {self._get_player_name(shot_result.player_id)} hit an EXCELLENT shot! Perfect time to double!",
                options=["offer_double", "pass"],
                probability_analysis=self._calculate_doubling_odds(shot_result),
                recommended_action="offer_double",
                risk_assessment="low"
            )
        
        elif shot_result.shot_quality == "terrible":
            opportunity = WGPBettingOpportunity(
                opportunity_type="double",
                message=f"😬 {self._get_player_name(shot_result.player_id)} hit a TERRIBLE shot! Your team has the advantage!",
                options=["offer_double", "pass"],
                probability_analysis=self._calculate_doubling_odds(shot_result),
                recommended_action="offer_double",
                risk_assessment="medium"
            )
        
        elif shot_result.distance_to_pin < 20 and shot_result.shot_quality in ["good", "excellent"]:
            opportunity = WGPBettingOpportunity(
                opportunity_type="strategic",
                message=f"🎯 {self._get_player_name(shot_result.player_id)} is close to the pin! Great doubling position!",
                options=["offer_double", "wait", "pass"],
                probability_analysis=self._calculate_doubling_odds(shot_result),
                recommended_action="offer_double",
                risk_assessment="low"
            )
        
        elif random.random() < 0.25:  # 25% chance for general opportunities
            opportunity = WGPBettingOpportunity(
                opportunity_type="strategic",
                message=f"🎲 Good time to press the action after {self._get_player_name(shot_result.player_id)}'s {shot_result.shot_quality} shot",
                options=["offer_double", "pass"],
                probability_analysis=self._calculate_doubling_odds(shot_result),
                recommended_action="pass",
                risk_assessment="medium"
            )
        
        return opportunity
    
    def _calculate_doubling_odds(self, shot_result: WGPShotResult) -> Dict[str, float]:
        """Calculate odds for doubling based on current shot and team situation"""
        # Get current hole state
        hole_state = self.hole_states.get(self.current_hole)
        if not hole_state:
            return {
                "win_probability": 0.5,
                "confidence": 0.0,
                "shot_quality_factor": 0.0,
                "team_skill_factor": 0.0,
                "distance_factor": shot_result.distance_to_pin
            }
        
        # Base shot advantage
        shot_advantage = 0.0
        if shot_result.shot_quality == "excellent":
            shot_advantage += 0.3
        elif shot_result.shot_quality == "good":
            shot_advantage += 0.2
        elif shot_result.shot_quality == "average":
            shot_advantage += 0.1
        elif shot_result.shot_quality == "poor":
            shot_advantage -= 0.1
        elif shot_result.shot_quality == "terrible":
            shot_advantage -= 0.2
        
        # Distance factor
        if shot_result.distance_to_pin < 20:
            shot_advantage += 0.1
        elif shot_result.distance_to_pin > 100:
            shot_advantage -= 0.1
        
        # Calculate team handicap advantages
        team_skill_diff = self._calculate_team_skill_difference(hole_state.teams)
        
        # Combine factors
        win_probability = min(0.95, max(0.05, shot_advantage + team_skill_diff))
        confidence = abs(win_probability - 0.5) * 2  # How confident we are
        
        return {
            "win_probability": round(win_probability, 2),
            "confidence": round(confidence, 2),
            "shot_quality_factor": shot_advantage,
            "team_skill_factor": team_skill_diff,
            "distance_factor": shot_result.distance_to_pin
        }
    
    def _calculate_team_skill_difference(self, teams: TeamFormation) -> float:
        """Calculate the skill difference between teams based on handicaps"""
        if teams.type not in ["partners", "solo"]:
            return 0.0
        
        # Get current hole state
        hole_state = self.hole_states.get(self.current_hole)
        if not hole_state:
            return 0.0
        
        if teams.type == "partners":
            # Calculate average handicaps for each team
            team1_handicaps = []
            team2_handicaps = []
            
            for player in self.players:
                if player.id in teams.team1:
                    team1_handicaps.append(player.handicap)
                elif player.id in teams.team2:
                    team2_handicaps.append(player.handicap)
            
            if not team1_handicaps or not team2_handicaps:
                return 0.0
            
            avg_team1 = sum(team1_handicaps) / len(team1_handicaps)
            avg_team2 = sum(team2_handicaps) / len(team2_handicaps)
            
            # Lower handicap = better, so team1 advantage is (team2_avg - team1_avg)
            # Normalize to -1 to 1 range
            skill_diff = (avg_team2 - avg_team1) / 20.0
            return max(-1.0, min(1.0, skill_diff))
        
        elif teams.type == "solo":
            # Solo player vs opponents
            captain = None
            opponents = []
            
            for player in self.players:
                if player.id == teams.captain:
                    captain = player
                elif player.id in teams.opponents:
                    opponents.append(player)
            
            if not captain or not opponents:
                return 0.0
            
            avg_opponent_handicap = sum(p.handicap for p in opponents) / len(opponents)
            
            # Solo advantage: (opponent_avg - captain_handicap) / 20.0
            skill_diff = (avg_opponent_handicap - captain.handicap) / 20.0
            return max(-1.0, min(1.0, skill_diff))
        
        return 0.0
    
    def _generate_betting_analysis(self, shot_result: WGPShotResult) -> Dict[str, Any]:
        """Generate comprehensive betting analysis for human players"""
        analysis = {
            "shot_assessment": {
                "quality_rating": shot_result.shot_quality,
                "distance_remaining": shot_result.distance_to_pin,
                "strategic_value": "high" if shot_result.shot_quality in ["excellent", "good"] else "low"
            },
            "team_position": {
                "current_wager": self.hole_states[self.current_hole].betting.current_wager,
                "potential_double": self.hole_states[self.current_hole].betting.current_wager * 2,
                "momentum": "positive" if shot_result.shot_quality in ["excellent", "good"] else "negative"
            },
            "strategic_recommendations": self._generate_strategic_recommendations(shot_result),
            "computer_tendencies": self._analyze_computer_tendencies()
        }
        
        return analysis
    
    def _generate_strategic_recommendations(self, shot_result: WGPShotResult) -> List[str]:
        """Generate strategic recommendations based on current situation"""
        recommendations = []
        
        if shot_result.shot_quality == "excellent":
            recommendations.append("🎯 Consider doubling immediately - excellent shot gives strong advantage")
            recommendations.append("💪 This is an ideal time to press the action")
        
        elif shot_result.shot_quality == "terrible":
            recommendations.append("🛡️ Be cautious - opponent's poor shot creates opportunity but don't overcommit")
            recommendations.append("⚖️ Evaluate team strength before doubling")
        
        elif shot_result.distance_to_pin < 20:
            recommendations.append("🥅 Close to pin - high probability scoring opportunity")
            recommendations.append("🎲 Good position for strategic doubling")
        
        return recommendations
    
    def _analyze_computer_tendencies(self) -> Dict[str, Any]:
        """Analyze computer player tendencies for strategic insight"""
        if not hasattr(self, 'computer_players'):
            return {}
        
        tendencies = {}
        for player_id, computer_player in self.computer_players.items():
            personality = computer_player.personality
            tendencies[player_id] = {
                "personality": personality,
                "betting_style": self._get_personality_betting_style(personality),
                "double_acceptance": self._get_personality_double_tendency(personality)
            }
        
        return tendencies
    
    def _get_personality_betting_style(self, personality: str) -> str:
        """Get betting style description for personality"""
        styles = {
            "aggressive": "High risk, frequent doubling",
            "conservative": "Low risk, selective doubling", 
            "balanced": "Moderate risk, situational doubling",
            "strategic": "Calculated risk, position-based doubling"
        }
        return styles.get(personality, "Unknown")
    
    def _get_personality_double_tendency(self, personality: str) -> str:
        """Get double acceptance tendency for personality"""
        tendencies = {
            "aggressive": "Accepts most doubles",
            "conservative": "Declines risky doubles",
            "balanced": "Situational acceptance",
            "strategic": "Analyzes before accepting"
        }
        return tendencies.get(personality, "Unknown")
    
    def _get_next_shot_player(self) -> Optional[str]:
        """Get the next player to hit based on current ball positions"""
        hole_state = self.hole_states[self.current_hole]
        
        # Check if all tee shots have been completed
        all_tee_shots_complete = all(
            player_id in hole_state.ball_positions 
            for player_id in hole_state.hitting_order
        )
        
        if not all_tee_shots_complete:
            # Still in tee shot phase - follow hitting order
            for player_id in hole_state.hitting_order:
                if player_id not in hole_state.ball_positions:
                    return player_id
            return None
        else:
            # All tee shots complete - use distance-based order
            return hole_state.next_player_to_hit
    
    def _check_hole_completion(self) -> bool:
        """Check if hole is complete (all players holed out or max shots reached)"""
        if not self.hole_progression:
            return False
        
        for player_id in self.hole_progression.current_shot_order:
            shots = self.hole_progression.shots_taken[player_id]
            if not shots:
                return False
            
            last_shot = shots[-1]
            # Continue if player hasn't holed out and hasn't reached max shots
            if not last_shot.made_shot and len(shots) < 8:
                return False
        
        return True

    def _get_comprehensive_hole_state(self) -> Dict[str, Any]:
        """Get comprehensive hole state including all ball positions and game state"""
        hole_state = self.hole_states[self.current_hole]
        
        return {
            "hole_number": hole_state.hole_number,
            "current_shot_number": hole_state.current_shot_number,
            "hole_complete": hole_state.hole_complete,
            "wagering_closed": hole_state.wagering_closed,
            
            # Ball positions for all players
            "ball_positions": {
                player_id: {
                    "distance_to_pin": ball.distance_to_pin,
                    "lie_type": ball.lie_type,
                    "shot_count": ball.shot_count,
                    "holed": ball.holed,
                    "conceded": ball.conceded,
                    "penalty_strokes": ball.penalty_strokes
                } if ball else None
                for player_id in [p.id for p in self.players]
                for ball in [hole_state.get_player_ball_position(player_id)]
            },
            
            # Order of play and line of scrimmage
            "current_order_of_play": hole_state.current_order_of_play,
            "line_of_scrimmage": hole_state.line_of_scrimmage,
            "next_player_to_hit": hole_state.next_player_to_hit,
            
            # Stroke advantages for all players
            "stroke_advantages": {
                player_id: {
                    "handicap": stroke_adv.handicap,
                    "strokes_received": stroke_adv.strokes_received,
                    "net_score": stroke_adv.net_score,
                    "stroke_index": stroke_adv.stroke_index
                } if stroke_adv else None
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
                "solo_player": hole_state.teams.solo_player,
                "opponents": hole_state.teams.opponents
            },
            
            # Betting state
            "betting": {
                "base_wager": hole_state.betting.base_wager,
                "current_wager": hole_state.betting.current_wager,
                "doubled": hole_state.betting.doubled,
                "redoubled": hole_state.betting.redoubled,
                "carry_over": hole_state.betting.carry_over,
                "float_invoked": hole_state.betting.float_invoked,
                "option_invoked": hole_state.betting.option_invoked,
                "duncan_invoked": hole_state.betting.duncan_invoked,
                "tunkarri_invoked": hole_state.betting.tunkarri_invoked,
                "joes_special_value": hole_state.betting.joes_special_value,
                "wagering_closed": hole_state.wagering_closed
            },
            
            # Completion tracking
            "balls_in_hole": hole_state.balls_in_hole,
            "concessions": hole_state.concessions,
            "scores": hole_state.scores
        }

# Utility functions for AI decision making
    
    def _check_partnership_requests(self, human_player_id: str) -> List[Dict[str, Any]]:
        """Check if any computer players want to request the human as partner"""
        hole_state = self.hole_states[self.current_hole]
        requests = []
        
        for player in self.players:
            if player.id != human_player_id and player.id in self.computer_players:
                computer_player = self.computer_players[player.id]
                
                # Check if computer player wants to request human as partner
                if computer_player.should_request_partner(human_player_id, self.get_game_state()):
                    requests.append({
                        "requesting_player": player.id,
                        "requesting_player_name": player.name,
                        "target_player": human_player_id,
                        "message": f"{player.name} wants you as a partner!"
                    })
        
        return requests
    
    def _get_available_partners(self, human_player_id: str) -> List[Dict[str, Any]]:
        """Get list of players the human can request as partners"""
        hole_state = self.hole_states[self.current_hole]
        available = []
        
        for player in self.players:
            if player.id != human_player_id:
                # Check if player is still eligible for partnership
                if self._is_player_eligible_for_partnership(player.id, hole_state):
                    available.append({
                        "player_id": player.id,
                        "player_name": player.name,
                        "handicap": player.handicap,
                        "is_computer": player.id in self.computer_players
                    })
        
        return available
    
    def human_requests_partner(self, human_player_id: str, partner_id: str) -> Dict[str, Any]:
        """
        Human requests a specific player as partner (simulating "rolling the dice")
        """
        hole_state = self.hole_states[self.current_hole]
        
        # Check if partner is still eligible
        if not self._is_player_eligible_for_partnership(partner_id, hole_state):
            return {
                "status": "error",
                "message": f"{self._get_player_name(partner_id)} is no longer eligible for partnership"
            }
        
        # Check if partner is computer or human
        partner = next(p for p in self.players if p.id == partner_id)
        
        if partner_id in self.computer_players:
            # Computer partner - simulate their decision
            computer_player = self.computer_players[partner_id]
            accept = computer_player.should_accept_partnership(
                next(p for p in self.players if p.id == human_player_id),
                self.get_game_state()
            )
            
            if accept:
                # Computer accepts partnership
                result = self._accept_partnership(human_player_id, partner_id, hole_state)
                result["computer_response"] = f"{partner.name} accepts your partnership request!"
                return result
            else:
                # Computer declines - human goes solo
                result = self._decline_partnership(human_player_id, partner_id, hole_state)
                result["computer_response"] = f"{partner.name} declines your partnership request."
                return result
        else:
            # Human partner - create pending request
            hole_state.teams.pending_request = {
                "type": "partnership",
                "captain": human_player_id,
                "requested": partner_id
            }
            
            return {
                "status": "partnership_request_pending",
                "message": f"Partnership request sent to {partner.name}. Waiting for response...",
                "pending_request": hole_state.teams.pending_request,
                "hole_state": self._get_comprehensive_hole_state()
            }
    
    def human_goes_solo(self, human_player_id: str, use_duncan: bool = False) -> Dict[str, Any]:
        """
        Human decides to go solo (either by choice or after being declined)
        """
        hole_state = self.hole_states[self.current_hole]
        
        # Track solo count for 4-man requirement
        if self.player_count == 4:
            human_player = next(p for p in self.players if p.id == human_player_id)
            human_player.solo_count += 1
        
        # Set up solo formation
        others = [p.id for p in self.players if p.id != human_player_id]
        
        hole_state.teams = TeamFormation(
            type="solo",
            captain=human_player_id,
            solo_player=human_player_id,
            opponents=others
        )
        
        # Apply Duncan if requested
        if use_duncan:
            hole_state.betting.duncan_invoked = True
            hole_state.betting.current_wager = int(hole_state.betting.current_wager * 1.5)
        
        return {
            "status": "human_going_solo",
            "message": f"{self._get_player_name(human_player_id)} is going solo!",
            "duncan_invoked": use_duncan,
            "current_wager": hole_state.betting.current_wager,
            "hole_state": self._get_comprehensive_hole_state(),
            "next_action": "continue_with_other_players"
        }

    def captain_partnership_decision(self, human_player_id: str, action: str, target_player_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Captain (human) makes partnership decision after seeing a player's tee shot.
        Action can be: 'ask_partnership', 'wait_for_next', 'go_solo'
        """
        hole_state = self.hole_states[self.current_hole]
        
        if action == "ask_partnership":
            if not target_player_id:
                return {
                    "status": "error",
                    "message": "Must specify target_player_id when asking for partnership"
                }
            
            # Check if target player is still eligible
            if not self._is_player_eligible_for_partnership(target_player_id, hole_state):
                return {
                    "status": "error",
                    "message": f"{self._get_player_name(target_player_id)} is no longer eligible for partnership"
                }
            
            # Check if target player is computer or human
            if target_player_id in self.computer_players:
                # Computer partner - simulate their decision
                computer_player = self.computer_players[target_player_id]
                accept = computer_player.should_accept_partnership(
                    next(p for p in self.players if p.id == human_player_id),
                    self.get_game_state()
                )
                
                if accept:
                    # Computer accepts partnership
                    result = self._accept_partnership(human_player_id, target_player_id, hole_state)
                    result["computer_response"] = f"{self._get_player_name(target_player_id)} accepts your partnership request!"
                    result["next_action"] = "partnership_formed_continue_hole"
                    return result
                else:
                    # Computer declines - human goes solo
                    result = self._decline_partnership(human_player_id, target_player_id, hole_state)
                    result["computer_response"] = f"{self._get_player_name(target_player_id)} declines your partnership request."
                    result["next_action"] = "human_going_solo_continue_hole"
                    return result
            else:
                # Human partner - create pending request
                hole_state.teams.pending_request = {
                    "type": "partnership",
                    "captain": human_player_id,
                    "requested": target_player_id
                }
                
                return {
                    "status": "partnership_request_pending",
                    "message": f"Partnership request sent to {self._get_player_name(target_player_id)}. Waiting for response...",
                    "pending_request": hole_state.teams.pending_request,
                    "hole_state": self._get_comprehensive_hole_state(),
                    "next_action": "wait_for_partnership_response"
                }
        
        elif action == "wait_for_next":
            # Check if there are more players to hit
            hitting_order = hole_state.hitting_order
            captain_index = hitting_order.index(human_player_id)
            current_players_hit = len(hole_state.ball_positions)
            
            if current_players_hit < len(hitting_order):
                # More players to hit - continue
                return {
                    "status": "waiting_for_next_player",
                    "message": "Captain waits for next player to tee off...",
                    "hole_state": self._get_comprehensive_hole_state(),
                    "next_action": "next_player_tees_off"
                }
            else:
                # All players have hit - captain goes solo
                return self.human_goes_solo(human_player_id)
        
        elif action == "go_solo":
            return self.human_goes_solo(human_player_id)
        
        else:
            return {
                "status": "error",
                "message": f"Invalid action: {action}. Must be 'ask_partnership', 'wait_for_next', or 'go_solo'"
            }

    # AI Decision Making Methods (moved from WGPComputerPlayer)
    
    def should_accept_partnership(self, captain: WGPPlayer, game_state: Dict) -> bool:
        """Decide whether to accept partnership request"""
        # For simulation purposes, use a simple decision based on handicap difference
        # In a real implementation, this would be called on a specific player
        handicap_diff = abs(captain.handicap - 12.0)  # Assume average handicap
        current_position = 2  # Assume middle position
        
        # Simple decision logic
        if handicap_diff < 8:
            return True
        elif current_position > 2:
            return True
        else:
            return random.random() > 0.4
    
    def should_request_partner(self, target_player_id: str, game_state: Dict) -> bool:
        """Determine if this computer player should request a specific player as partner"""
        # This would be used if computer players could request human as partner
        # For now, computer players don't actively request partners
        return False
    
    def should_go_solo(self, game_state: Dict) -> bool:
        """Decide whether to go solo as captain"""
        # For simulation purposes, use simple decision logic
        current_position = 2  # Assume middle position
        individual_skill = 0.5  # Assume average skill
        
        # Simple decision logic
        if individual_skill > 0.4:
            return random.random() > 0.7
        else:
            return current_position > 3
    
    def should_use_float(self, game_state: Dict) -> bool:
        """Decide whether to use float as captain"""
        # For simulation purposes, use simple decision logic
        current_position = 2  # Assume middle position
        hole_confidence = 0.6  # Assume moderate confidence
        
        # Simple decision logic
        if hole_confidence > 0.6:
            return random.random() > 0.5
        else:
            return current_position > 3
    
    def should_offer_double(self, game_state: Dict) -> bool:
        """Decide whether to offer a double"""
        # For simulation purposes, use simple decision logic
        team_advantage = 0.5  # Assume moderate advantage
        current_position = 2  # Assume middle position
        
        # Simple decision logic
        if team_advantage > 0.5:
            return random.random() > 0.3
        else:
            return current_position > 2
    
    def should_accept_double(self, game_state: Dict) -> bool:
        """Decide whether to accept a double"""
        # For simulation purposes, use simple decision logic
        current_points = 0  # Assume neutral position
        hole_advantage = 0.1  # Assume slight advantage
        
        # Simple decision logic
        if hole_advantage > 0:
            return random.random() > 0.4
        else:
            return current_points < 0

    # Compatibility methods for old simulation API
    def setup_simulation(self, human_player, computer_configs, course_name=None):
        """Compatibility method for old simulation API"""
        # Convert human player to WGPPlayer (handle both dict and object)
        if isinstance(human_player, dict):
            wgp_human = WGPPlayer(
                id=human_player["id"],
                name=human_player["name"],
                handicap=human_player["handicap"]
            )
        else:
            wgp_human = WGPPlayer(
                id=human_player.id,
                name=human_player.name,
                handicap=human_player.handicap
            )
        
        # Convert computer configs to WGPPlayers
        wgp_players = [wgp_human]
        computer_player_ids = []
        personalities = []
        
        for config in computer_configs:
            wgp_player = WGPPlayer(
                id=config["id"],
                name=config["name"],
                handicap=config["handicap"]
            )
            wgp_players.append(wgp_player)
            computer_player_ids.append(config["id"])
            personalities.append(config.get("personality", "balanced"))
        
        # Create new simulation with these players
        new_sim = WolfGoatPigSimulation(player_count=len(wgp_players), players=wgp_players)
        
        # Set computer players
        new_sim.set_computer_players(computer_player_ids, personalities)
        
        # Store course name for reference
        new_sim.course_name = course_name
        
        # Create a GameState-like object for compatibility
        class GameStateCompat:
            def __init__(self, wgp_sim):
                self.wgp_sim = wgp_sim
                self.selected_course = course_name
                self.hole_pars = [4] * 18  # Default pars
                self.hole_yards = [400] * 18  # Default yards
                self.hole_stroke_indexes = list(range(1, 19))  # Default stroke indexes
                self.hole_descriptions = ["Standard hole"] * 18  # Default descriptions
                self.current_hole = 1
                self.betting_state = wgp_sim.hole_states[1].betting if 1 in wgp_sim.hole_states else None
                self.player_manager = None  # Placeholder
        
        return GameStateCompat(new_sim)

    def simulate_hole(self, game_state, human_decisions):
        """Compatibility method for old simulation API"""
        # Convert human decisions to Wolf Goat Pig format
        if "accept" in human_decisions and "partner_id" in human_decisions:
            if human_decisions["accept"]:
                return self.respond_to_partnership(human_decisions["partner_id"], True)
            else:
                return self.respond_to_partnership(human_decisions["partner_id"], False)
        
        if "action" in human_decisions:
            if human_decisions["action"] == "go_solo":
                return self.captain_go_solo("human")
            elif human_decisions["action"] == "request_partner":
                return self.request_partner("human", human_decisions["requested_partner"])
        
        # Default: advance hole
        return self.advance_to_next_hole()

    def run_monte_carlo_simulation(self, human_player, computer_configs, num_simulations=100, course_name=None):
        """Compatibility method for old simulation API"""
        # Create a simple Monte Carlo results object
        class MonteCarloResults:
            def __init__(self):
                self.detailed_results = []
                self.summary = {}
            
            def get_summary(self):
                return self.summary
        
        results = MonteCarloResults()
        
        # Run basic simulations
        for i in range(num_simulations):
            # Create simulation
            game_state = self.setup_simulation(human_player, computer_configs, course_name)
            
            # Run a simple simulation (just advance through holes)
            for hole in range(1, 19):
                if hasattr(game_state, 'wgp_sim'):
                    game_state.wgp_sim.advance_to_next_hole()
                else:
                    # Fallback: just increment hole number
                    game_state.current_hole = hole + 1
            
            # Get final state
            if hasattr(game_state, 'wgp_sim'):
                final_state = game_state.wgp_sim.get_game_state()
            else:
                final_state = {"current_hole": 19, "status": "completed"}
            results.detailed_results.append(final_state)
        
        # Calculate summary
        results.summary = {
            "total_simulations": num_simulations,
            "average_points": 0,  # Placeholder
            "win_rate": 0.25,  # Placeholder - 25% chance for 4 players
            "player_statistics": {
                "human": {
                    "win_percentage": 25.0,
                    "average_score": 85.0,
                    "best_score": 78,
                    "worst_score": 92
                }
            }
        }
        
        return results

    def play_next_shot(self, game_state, human_decisions):
        """Compatibility method for old simulation API"""
        # For now, just simulate a shot and return
        if hasattr(self, 'shot_simulation_mode') and self.shot_simulation_mode:
            next_player = self._get_next_shot_player()
            if next_player:
                shot_result = self.simulate_shot(next_player)
                return shot_result, ["Shot simulated"], True, None
        
        # Default: advance hole
        result = self.advance_to_next_hole()
        return None, ["Hole advanced"], False, None

    def calculate_shot_probabilities(self, game_state):
        """Compatibility method for old simulation API"""
        # Return basic probabilities
        return {
            "excellent": 0.1,
            "good": 0.3,
            "average": 0.4,
            "poor": 0.15,
            "terrible": 0.05
        }

    def calculate_betting_probabilities(self, game_state, decision):
        """Compatibility method for old simulation API"""
        # Return basic betting probabilities
        return {
            "partnership_success": 0.6,
            "solo_success": 0.4,
            "double_success": 0.5
        }

    def execute_betting_decision(self, game_state, decision, probabilities):
        """Compatibility method for old simulation API"""
        # Execute the decision and return results
        if "action" in decision:
            if decision["action"] == "go_solo":
                result = self.captain_go_solo("human")
            elif decision["action"] == "request_partner":
                result = self.request_partner("human", decision["requested_partner"])
            else:
                result = {"status": "unknown_action"}
        else:
            result = {"status": "no_action"}
        
        return game_state, result

    def get_current_shot_state(self, game_state):
        """Compatibility method for old simulation API"""
        # Return current shot state
        return {
            "current_player": self._get_next_shot_player(),
            "shot_number": 1,
            "hole_number": self.current_hole
        }

    # Helper methods for compatibility
    def _get_current_points(self, game_state):
        """Get current points for a player (placeholder)"""
        return 0

    def _assess_team_advantage(self, game_state):
        """Assess team advantage (placeholder)"""
        return 0.0

    def _assess_hole_difficulty(self, game_state):
        """Assess hole difficulty (placeholder)"""
        return 0.5

    def _simulate_player_score(self, handicap, par, stroke_index, game_state):
        """Simulate player score (placeholder)"""
        import random
        # Simple score simulation based on handicap
        base_score = par + int(handicap / 4)
        variation = random.randint(-2, 2)
        return max(par - 2, base_score + variation)

import random
import math
from typing import Dict, List, Tuple, Optional, Any, Union
from dataclasses import dataclass, field
from enum import Enum
import logging
from copy import deepcopy

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
class HoleState:
    """Complete state for a single hole"""
    hole_number: int
    hitting_order: List[str]
    teams: TeamFormation
    betting: BettingState
    scores: Dict[str, Optional[int]] = field(default_factory=dict)
    shots_completed: Dict[str, bool] = field(default_factory=dict)
    balls_in_hole: List[str] = field(default_factory=list)  # Players who holed out
    concessions: Dict[str, str] = field(default_factory=dict)  # "good but not in"
    
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
        
        # Game progression tracking
        self.hoepfinger_start_hole = self._get_hoepfinger_start_hole()
        self.vinnie_variation_start = 13 if player_count == 4 else None
        
        # Initialize first hole
        self._initialize_hole(1)
        
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
        
        # Initialize hole state
        self.hole_states[hole_number] = HoleState(
            hole_number=hole_number,
            hitting_order=hitting_order,
            teams=teams,
            betting=betting_state,
            scores={p.id: None for p in self.players},
            shots_completed={p.id: False for p in self.players}
        )
        
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
        
        return {
            "status": "pending",
            "message": f"Partnership request sent to {self._get_player_name(partner_id)}",
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
        
        return {
            "status": "solo",
            "message": f"Captain {self._get_player_name(captain_id)} goes solo!",
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
        
        return {
            "status": "double_offered",
            "message": f"{self._get_player_name(offering_player_id)} offers a double",
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
            "betting": {
                "base_wager": hole_state.betting.base_wager,
                "current_wager": hole_state.betting.current_wager,
                "doubled": hole_state.betting.doubled,
                "special_rules": {
                    "float_invoked": hole_state.betting.float_invoked,
                    "option_invoked": hole_state.betting.option_invoked,
                    "duncan_invoked": hole_state.betting.duncan_invoked,
                    "tunkarri_invoked": hole_state.betting.tunkarri_invoked,
                    "joes_special_value": hole_state.betting.joes_special_value
                }
            },
            "scores": hole_state.scores,
            "balls_in_hole": hole_state.balls_in_hole
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
        
        return {
            "status": "partnership_formed",
            "message": f"Partnership formed: {self._get_player_name(captain_id)} & {self._get_player_name(partner_id)}",
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
        
        return {
            "status": "partnership_declined",
            "message": f"{self._get_player_name(partner_id)} declined. {self._get_player_name(captain_id)} goes solo!",
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

# Utility functions for AI decision making

class WGPComputerPlayer:
    """AI player for Wolf Goat Pig with personality-based decision making"""
    
    def __init__(self, player: WGPPlayer, personality: str = "balanced"):
        self.player = player
        self.personality = personality  # "aggressive", "conservative", "balanced", "strategic"
    
    def should_accept_partnership(self, captain: WGPPlayer, game_state: Dict) -> bool:
        """Decide whether to accept partnership request"""
        handicap_diff = abs(self.player.handicap - captain.handicap)
        current_position = self._get_position_in_standings(game_state)
        
        if self.personality == "aggressive":
            return current_position > 2 or handicap_diff < 8
        elif self.personality == "conservative":
            return captain.handicap < self.player.handicap - 2
        elif self.personality == "strategic":
            hole_difficulty = self._assess_hole_difficulty(game_state)
            return handicap_diff < 6 and (hole_difficulty < 0.6 or current_position > 3)
        else:  # balanced
            return handicap_diff < 7 and random.random() > 0.4
    
    def should_go_solo(self, game_state: Dict) -> bool:
        """Decide whether to go solo as captain"""
        current_position = self._get_position_in_standings(game_state)
        individual_skill = self._assess_individual_advantage(game_state)
        
        if self.personality == "aggressive":
            return individual_skill > 0.2 or current_position > 3
        elif self.personality == "conservative":
            return individual_skill > 0.6 and current_position <= 2
        elif self.personality == "strategic":
            return (current_position > 4 and individual_skill > 0) or individual_skill > 0.5
        else:  # balanced
            return individual_skill > 0.4 and random.random() > 0.7
    
    def should_use_float(self, game_state: Dict) -> bool:
        """Decide whether to use float as captain"""
        if self.player.float_used:
            return False
            
        current_position = self._get_position_in_standings(game_state)
        hole_confidence = self._assess_hole_confidence(game_state)
        
        if self.personality == "aggressive":
            return hole_confidence > 0.4 or current_position > 3
        elif self.personality == "conservative":
            return hole_confidence > 0.7 and current_position <= 2
        elif self.personality == "strategic":
            holes_remaining = 19 - game_state.get("current_hole", 1)
            return hole_confidence > 0.5 and (holes_remaining < 8 or current_position > 3)
        else:  # balanced
            return hole_confidence > 0.6
    
    def should_offer_double(self, game_state: Dict) -> bool:
        """Decide whether to offer a double"""
        team_advantage = self._assess_team_advantage(game_state)
        current_position = self._get_position_in_standings(game_state)
        
        if self.personality == "aggressive":
            return team_advantage > 0.2 or current_position > 2
        elif self.personality == "conservative":
            return team_advantage > 0.6
        elif self.personality == "strategic":
            wager_size = game_state.get("hole_state", {}).get("betting", {}).get("current_wager", 1)
            return team_advantage > 0.4 and (wager_size <= 4 or current_position > 3)
        else:  # balanced
            return team_advantage > 0.5
    
    def should_accept_double(self, game_state: Dict) -> bool:
        """Decide whether to accept a double"""
        team_advantage = self._assess_team_advantage(game_state)
        current_position = self._get_position_in_standings(game_state)
        
        if self.personality == "aggressive":
            return team_advantage > -0.3 or current_position > 3
        elif self.personality == "conservative":
            return team_advantage > 0.1
        elif self.personality == "strategic":
            risk_tolerance = 0.2 if current_position <= 2 else -0.1
            return team_advantage > risk_tolerance
        else:  # balanced
            return team_advantage > -0.1
    
    def _get_position_in_standings(self, game_state: Dict) -> int:
        """Get current position in points standings (1 = leading)"""
        players = game_state.get("players", [])
        sorted_players = sorted(players, key=lambda p: p.get("points", 0), reverse=True)
        
        for i, player in enumerate(sorted_players):
            if player.get("id") == self.player.id:
                return i + 1
        return len(players)
    
    def _assess_hole_difficulty(self, game_state: Dict) -> float:
        """Assess difficulty of current hole (0=easy, 1=hard)"""
        # Simplified - in real implementation would consider stroke index, par, etc.
        return random.uniform(0.3, 0.8)
    
    def _assess_individual_advantage(self, game_state: Dict) -> float:
        """Assess individual advantage for going solo (-1 to 1)"""
        # Consider handicap relative to others
        players = game_state.get("players", [])
        other_handicaps = [p.get("handicap", 20) for p in players if p.get("id") != self.player.id]
        avg_other_handicap = sum(other_handicaps) / len(other_handicaps) if other_handicaps else 20
        
        skill_advantage = (avg_other_handicap - self.player.handicap) / 20.0
        return max(-1.0, min(1.0, skill_advantage + random.uniform(-0.2, 0.2)))
    
    def _assess_team_advantage(self, game_state: Dict) -> float:
        """Assess current team advantage (-1 to 1)"""
        # Simplified assessment
        return random.uniform(-0.5, 0.5)
    
    def _assess_hole_confidence(self, game_state: Dict) -> float:
        """Assess confidence for this hole (0 to 1)"""
        individual_advantage = self._assess_individual_advantage(game_state)
        return max(0.0, min(1.0, 0.5 + individual_advantage))
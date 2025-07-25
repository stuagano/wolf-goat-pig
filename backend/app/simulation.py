import random
import math
from typing import Dict, List, Tuple, Optional, Any
from .game_state import GameState
import logging
import traceback
from .domain.shot_result import ShotResult
from .domain.player import Player
from .state.shot_state import ShotState
from .state.player_manager import PlayerManager
from .services.probability_calculator import ProbabilityCalculator
from .services.shot_simulator import ShotSimulator
from .services.betting_engine import BettingEngine

class GolfShot:
    """Represents a golf shot with distance and accuracy"""
    def __init__(self, distance_to_pin: float, made_shot: bool, shot_quality: str):
        self.distance_to_pin = distance_to_pin
        self.made_shot = made_shot
        self.shot_quality = shot_quality  # "excellent", "good", "average", "poor", "terrible"

class ComputerPlayer:
    """Represents a computer player with AI decision making"""
    def __init__(self, player_id: str, name: str, handicap: float, personality: str = "balanced"):
        self.player_id = player_id
        self.name = name
        self.handicap = handicap
        self.personality = personality  # "aggressive", "conservative", "balanced", "strategic"
        
    def should_accept_partnership(self, captain_handicap: float, game_state: GameState) -> bool:
        """Decide whether to accept a partnership request"""
        current_points = self._get_current_points(game_state)
        captain_points = self._get_points_for_player(captain_handicap, game_state)
        
        # Base decision on handicap difference and current standings
        handicap_diff = abs(self.handicap - captain_handicap)
        
        if self.personality == "aggressive":
            # More likely to accept if behind in points
            return current_points < 0 or handicap_diff < 8
        elif self.personality == "conservative":
            # Only accept if captain is clearly better
            return captain_handicap < self.handicap - 3
        elif self.personality == "strategic":
            # Consider hole difficulty and current game state
            hole_difficulty = self._assess_hole_difficulty(game_state)
            return (handicap_diff < 5 and hole_difficulty < 0.7) or current_points < -3
        else:  # balanced
            return handicap_diff < 6 and random.random() > 0.3
    
    def should_offer_double(self, game_state: GameState) -> bool:
        """Decide whether to offer a double"""
        if game_state.betting_state.doubled_status:
            return False
            
        current_points = self._get_current_points(game_state)
        hole_advantage = self._assess_team_advantage(game_state)
        
        if self.personality == "aggressive":
            return hole_advantage > 0.3 or current_points < -2
        elif self.personality == "conservative":
            return hole_advantage > 0.6 and current_points >= 0
        elif self.personality == "strategic":
            return hole_advantage > 0.4 and (current_points < 0 or game_state.current_hole >= 15)
        else:  # balanced
            return hole_advantage > 0.5 or (current_points < -1 and hole_advantage > 0.2)
    
    def should_accept_double(self, game_state: GameState) -> bool:
        """Decide whether to accept a double"""
        current_points = self._get_current_points(game_state)
        hole_advantage = self._assess_team_advantage(game_state)
        
        if self.personality == "aggressive":
            return current_points < 0 or hole_advantage > -0.2
        elif self.personality == "conservative":
            return hole_advantage > 0.2
        elif self.personality == "strategic":
            # Consider risk/reward based on game situation
            holes_remaining = 18 - game_state.current_hole + 1
            return (hole_advantage > -0.1 and current_points < -2) or \
                   (hole_advantage > 0.1 and holes_remaining > 5)
        else:  # balanced
            return hole_advantage > -0.1 and random.random() > 0.4
    
    def should_go_solo(self, game_state: GameState) -> bool:
        """Decide whether to go solo as captain"""
        current_points = self._get_current_points(game_state)
        individual_advantage = self._assess_individual_advantage(game_state)
        
        if self.personality == "aggressive":
            return individual_advantage > 0.2 or current_points < -4
        elif self.personality == "conservative":
            return individual_advantage > 0.5 and current_points >= -1
        elif self.personality == "strategic":
            # Go solo if significantly behind or have major advantage
            return (current_points < -5 and individual_advantage > 0) or individual_advantage > 0.4
        else:  # balanced
            return individual_advantage > 0.3 and random.random() > 0.6
    
    def _get_current_points(self, game_state: GameState) -> int:
        """Get current points for this player"""
        for player in game_state.player_manager.players:
            if player.id == self.player_id:
                return player.points
        return 0
    
    def _get_points_for_player(self, handicap: float, game_state: GameState) -> int:
        """Get points for a player with given handicap"""
        for player in game_state.player_manager.players:
            if abs(player.handicap - handicap) < 0.1:
                return player.points
        return 0
    
    def _assess_hole_difficulty(self, game_state: GameState) -> float:
        """Assess how difficult the current hole is (0=easy, 1=very hard)"""
        if not game_state.course_manager.hole_stroke_indexes or not game_state.course_manager.hole_pars:
            return 0.5
        
        hole_idx = game_state.current_hole - 1
        if hole_idx >= len(game_state.course_manager.hole_stroke_indexes):
            return 0.5
            
        stroke_index = game_state.course_manager.hole_stroke_indexes[hole_idx]
        par = game_state.course_manager.hole_pars[hole_idx]
        
        # Lower stroke index = harder hole
        difficulty = (19 - stroke_index) / 18.0
        
        # Factor in distance/yards if available
        if hole_idx < len(game_state.course_manager.hole_yards):
            yards = game_state.course_manager.hole_yards[hole_idx]
            # Expected yards by par
            expected_yards = {3: 150, 4: 400, 5: 550}
            expected = expected_yards.get(par, 400)
            
            # Distance factor: longer than expected = harder
            distance_factor = min(1.5, yards / expected)
            # Weight: 70% stroke index, 30% distance
            difficulty = 0.7 * difficulty + 0.3 * (distance_factor - 0.5)
        
        # Adjust based on par
        if par == 5:
            difficulty *= 0.9  # Par 5s are generally easier for high handicappers
        if par == 5 and self.handicap > 15:
            difficulty *= 0.8
        elif par == 3 and self.handicap > 20:
            difficulty *= 1.2
            
        return min(1.0, max(0.0, difficulty))
    
    def _assess_team_advantage(self, game_state: GameState) -> float:
        """Assess team's advantage on current hole (-1 to 1)"""
        if not game_state.betting_state.teams or game_state.betting_state.teams.get("type") not in ["partners", "solo"]:
            return 0.0
        
        # Get player strokes for current hole
        strokes = game_state.get_player_strokes()
        hole = game_state.current_hole
        
        if game_state.betting_state.teams["type"] == "partners":
            team1 = game_state.betting_state.teams["team1"]
            team2 = game_state.betting_state.teams["team2"]
            
            # Check if we're on team1 or team2
            our_team = team1 if self.player_id in team1 else team2
            their_team = team2 if self.player_id in team1 else team1
            
            # Calculate net stroke advantage
            our_strokes = min(strokes[pid][hole] for pid in our_team)
            their_strokes = min(strokes[pid][hole] for pid in their_team)
            
            stroke_advantage = their_strokes - our_strokes
            
            # Consider handicap differences
            our_handicaps = [p.handicap for p in game_state.player_manager.players if p.id in our_team]
            their_handicaps = [p.handicap for p in game_state.player_manager.players if p.id in their_team]
            
            handicap_advantage = (sum(their_handicaps) - sum(our_handicaps)) / 20.0
            
            return min(1.0, max(-1.0, stroke_advantage + handicap_advantage))
        
        elif game_state.betting_state.teams["type"] == "solo":
            captain = game_state.betting_state.teams["captain"]
            opponents = game_state.betting_state.teams["opponents"]
            
            if self.player_id == captain:
                # We're solo
                our_strokes = strokes[captain][hole]
                their_strokes = min(strokes[pid][hole] for pid in opponents)
                stroke_advantage = their_strokes - our_strokes
                
                # Solo is risky, so reduce confidence
                return min(0.5, max(-1.0, stroke_advantage - 0.2))
            else:
                # We're against solo player
                captain_strokes = strokes[captain][hole]
                our_strokes = min(strokes[pid][hole] for pid in opponents)
                stroke_advantage = captain_strokes - our_strokes
                
                return min(1.0, max(-0.5, stroke_advantage + 0.1))
        
        return 0.0
    
    def _assess_individual_advantage(self, game_state: GameState) -> float:
        """Assess individual advantage for going solo"""
        strokes = game_state.get_player_strokes()
        hole = game_state.current_hole
        
        our_strokes = strokes[self.player_id][hole]
        others = [pid for pid in strokes.keys() if pid != self.player_id]
        their_best_strokes = min(strokes[pid][hole] for pid in others)
        
        stroke_advantage = their_best_strokes - our_strokes
        
        # Consider our skill level
        skill_factor = max(0, (25 - self.handicap) / 25.0)
        
        return min(1.0, max(-1.0, stroke_advantage + skill_factor - 0.3))

class MonteCarloResults:
    """Results from Monte Carlo simulation"""
    def __init__(self):
        self.total_simulations = 0
        self.player_results = {}  # player_id -> list of final scores
        self.win_counts = {}      # player_id -> number of wins
        self.avg_scores = {}      # player_id -> average final score
        self.score_distributions = {}  # player_id -> dict of score -> count
        self.detailed_results = []  # list of individual game results
        
    def add_game_result(self, final_scores: Dict[str, Any]):
        """Add results from one complete game"""
        self.total_simulations += 1
        
        # Initialize if first game
        if not self.player_results:
            for player_id in final_scores:
                self.player_results[player_id] = []
                self.win_counts[player_id] = 0
                self.score_distributions[player_id] = {}
        
        # Add scores
        for player_id, score in final_scores.items():
            self.player_results[player_id].append(score)
            
            # Track score distribution
            if score not in self.score_distributions[player_id]:
                self.score_distributions[player_id][score] = 0
            self.score_distributions[player_id][score] += 1
        
        # Determine winner (highest score wins in Wolf Goat Pig)
        max_score = max(final_scores.values())
        winners = [pid for pid, score in final_scores.items() if score == max_score]
        for winner in winners:
            self.win_counts[winner] += 1
            
        # Store detailed result
        self.detailed_results.append({
            "game_number": self.total_simulations,
            "scores": final_scores.copy(),
            "winner": winners[0] if len(winners) == 1 else "tie"
        })
    
    def calculate_statistics(self):
        """Calculate final statistics"""
        for player_id in self.player_results:
            scores = self.player_results[player_id]
            self.avg_scores[player_id] = sum(scores) / len(scores) if scores else 0
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary statistics"""
        self.calculate_statistics()
        
        return {
            "total_simulations": self.total_simulations,
            "player_statistics": {
                player_id: {
                    "wins": self.win_counts[player_id],
                    "win_percentage": (self.win_counts[player_id] / self.total_simulations * 100) if self.total_simulations > 0 else 0,
                    "average_score": round(self.avg_scores[player_id], 2),
                    "best_score": max(self.player_results[player_id]) if self.player_results[player_id] else 0,
                    "worst_score": min(self.player_results[player_id]) if self.player_results[player_id] else 0,
                    "score_distribution": self.score_distributions[player_id]
                }
                for player_id in self.player_results
            }
        }

class SimulationEngine:
    """Main simulation engine for computer vs human matches"""
    
    def __init__(self):
        self.computer_players: List[ComputerPlayer] = []
        self.shot_history: List[Dict] = []
        self.educational_feedback: List[str] = []
        
    def setup_simulation(self, human_player: Player, computer_configs: List[Dict[str, Any]], course_name: Optional[str] = None) -> GameState:
        """Setup a simulation game with one human and three computer players"""
        if len(computer_configs) != 3:
            raise ValueError("Need exactly 3 computer player configurations")
        
        print(f"🔧 setup_simulation called with human_player={human_player}, computer_configs={computer_configs}")
        
        # Create computer players
        self.computer_players = []
        for config in computer_configs:
            comp_player = ComputerPlayer(
                player_id=config["id"],
                name=config["name"], 
                handicap=config["handicap"],
                personality=config.get("personality", "balanced")
            )
            self.computer_players.append(comp_player)
        
        # Setup game state with Player objects
        all_players = [
            {
                "id": human_player.id,
                "name": human_player.name,
                "handicap": human_player.handicap,
                "strength": self._handicap_to_strength_string(human_player.handicap)
            }
        ] + [
            {
                "id": cp.player_id,
                "name": cp.name,
                "handicap": cp.handicap,
                "strength": self._handicap_to_strength_string(cp.handicap)
            } for cp in self.computer_players
        ]
        
        print(f"🔧 All players setup: {[p['name'] for p in all_players]}")
        
        game_state = GameState()
        game_state.setup_players(all_players, course_name)
        
        print(f"🔧 Game state after setup_players: current_hole={game_state.current_hole}, players={[p.id for p in game_state.player_manager.players]}, hitting_order={game_state.player_manager.hitting_order}")
        
        # Initialize shot-by-shot state for event-driven simulation
        if not hasattr(game_state, 'shot_state') or game_state.shot_state is None:
            game_state.shot_state = ShotState()
        else:
            game_state.shot_state.reset_for_hole()
        
        # Initialize tee shot results
        game_state.tee_shot_results = {}
        game_state.current_tee_shot_index = 0
        
        print(f"🔧 Shot state initialized: {game_state.shot_state}")
        
        return game_state
    


    def play_next_shot(self, game_state: GameState, human_decisions: Dict[str, Any]) -> Tuple[Optional[Dict[str, Any]], List[str], bool, Optional[Dict[str, Any]]]:
        """Play the next individual shot in the simulation with interactive betting opportunities"""
        feedback = []
        
        # Handle human decisions first
        if human_decisions:
            # Handle partnership decisions
            if "accept_partnership" in human_decisions:
                partner_id = human_decisions.get("partner_id")
                accept = human_decisions.get("accept_partnership", False)
                
                if accept:
                    game_state.dispatch_action("accept_partner", {"partner_id": partner_id})
                    feedback.append(f"🧑 **You:** \"Absolutely! Let's team up!\"")
                else:
                    if game_state.betting_state.teams.get("type") == "pending":
                        game_state.dispatch_action("decline_partner", {"partner_id": partner_id})
                        feedback.append(f"🧑 **You:** \"Thanks, but I'll pass.\"")
            
            # Handle doubling decisions
            if "offer_double" in human_decisions:
                game_state.dispatch_action("offer_double", {})
                feedback.append(f"💰 **You:** \"I'm doubling the stakes!\"")
            
            if "accept_double" in human_decisions:
                game_state.dispatch_action("accept_double", {})
                feedback.append(f"💰 **You:** \"I accept the double!\"")
            
            if "decline_double" in human_decisions:
                game_state.dispatch_action("decline_double", {})
                feedback.append(f"💰 **You:** \"I'll pass on the double.\"")
            
            # Handle other decisions
            if "action" in human_decisions and human_decisions["action"] == "go_solo":
                game_state.dispatch_action("go_solo", {})
                feedback.append(f"🧑 **You:** \"I'll go solo on this one.\"")
        
        # Get current shot state
        shot_state = game_state.shot_state
        
        # Determine what type of shot to play next
        if shot_state.phase == "tee_shots":
            # Play next tee shot
            current_player_id = game_state.player_manager.hitting_order[shot_state.current_player_index]
            current_player = next(p for p in game_state.player_manager.players if p.id == current_player_id)
            
            # Simulate tee shot
            shot_result = ShotSimulator.simulate_individual_tee_shot(current_player, game_state)
            
            # Add shot to game state
            if game_state.hole_scores is None:
                game_state.hole_scores = {}
            if current_player_id not in game_state.hole_scores or game_state.hole_scores[current_player_id] is None:
                game_state.hole_scores[current_player_id] = []
            game_state.hole_scores[current_player_id].append(shot_result)
            
            # Generate feedback
            shot_description = self._create_shot_description(
                shot_result.drive, shot_result.lie, shot_result.shot_quality, 
                shot_result.remaining, game_state.course_manager.get_current_hole_info(game_state.current_hole)["par"]
            )
            feedback.append(f"🏌️ **{current_player.name}:** {shot_description}")
            
            # Add shot reaction
            reaction = self._generate_shot_reaction(shot_result.shot_quality, current_player.name, True)
            if reaction:
                feedback.append(f"💬 {reaction}")
            
            # Move to next player
            shot_state.current_player_index += 1
            shot_state.add_completed_shot(current_player_id, shot_result.to_dict())
            
            # Check if all tee shots are done
            if shot_state.current_player_index >= len(game_state.player_manager.hitting_order):
                shot_state.phase = "partnership_decisions"
                shot_state.current_player_index = 0
                feedback.append("🎯 **All tee shots complete!** Time for partnership decisions.")
                
                # Check if captain needs to make a decision
                captain_id = game_state.player_manager.captain_id
                if captain_id == self._get_human_player_id(game_state):
                    interaction_needed = {
                        "type": "captain_decision",
                        "message": "You're the captain! Do you want to go solo or request a partner?",
                        "options": ["go_solo", "request_partner"]
                    }
                    return None, feedback, False, interaction_needed
                else:
                    # Computer captain makes decision
                    computer_captain = self._get_computer_player(captain_id)
                    if computer_captain.should_go_solo(game_state):
                        game_state.dispatch_action("go_solo", {})
                        captain_name = next(p.name for p in game_state.player_manager.players if p.id == captain_id)
                        feedback.append(f"💻 **{captain_name}:** \"I'll go solo on this one!\"")
                    else:
                        # Request partner
                        available_partners = [pid for pid in game_state.player_manager.hitting_order if pid != captain_id]
                        if available_partners:
                            partner_id = available_partners[0]  # Simple selection for now
                            game_state.dispatch_action("request_partner", {"partner_id": partner_id})
                            captain_name = next(p.name for p in game_state.player_manager.players if p.id == captain_id)
                            partner_name = next(p.name for p in game_state.player_manager.players if p.id == partner_id)
                            feedback.append(f"💻 **{captain_name}:** \"{partner_name}, want to team up?\"")
                            
                            # Check if partner is human
                            if partner_id == self._get_human_player_id(game_state):
                                interaction_needed = {
                                    "type": "partnership_response",
                                    "message": f"{captain_name} wants to team up with you!",
                                    "captain_name": captain_name
                                }
                                return None, feedback, False, interaction_needed
            
            # Check for betting opportunities after each shot
            betting_opportunity = self.check_betting_opportunity(game_state, shot_result)
            if betting_opportunity:
                interaction_needed = {
                    "type": "betting_opportunity",
                    "message": betting_opportunity["message"],
                    "options": betting_opportunity["options"]
                }
                return shot_result.to_dict(), feedback, False, interaction_needed
            
            return shot_result.to_dict(), feedback, True, None
            
        elif shot_state.phase == "partnership_decisions":
            # Handle partnership phase
            if not game_state.betting_state.teams or game_state.betting_state.teams.get("type") == "none":
                # No partnerships formed, move to approach shots
                shot_state.phase = "approach_shots"
                shot_state.current_player_index = 0
                feedback.append("⛳ **No partnerships formed.** Moving to approach shots.")
            
            return None, feedback, True, None
            
        elif shot_state.phase == "approach_shots":
            # Play approach shots with betting opportunities
            current_player_id = game_state.player_manager.hitting_order[shot_state.current_player_index]
            current_player = next(p for p in game_state.player_manager.players if p.id == current_player_id)
            
            # Simulate approach shot
            remaining_distance = 150  # Simplified for now
            shot_result = ShotSimulator.simulate_approach_shot(current_player, remaining_distance, game_state)
            
            # Add shot to game state
            if current_player_id not in game_state.hole_scores or game_state.hole_scores[current_player_id] is None:
                game_state.hole_scores[current_player_id] = []
            game_state.hole_scores[current_player_id].append(shot_result)
            
            # Generate feedback
            shot_description = self._create_shot_description(
                shot_result.drive, shot_result.lie, shot_result.shot_quality, 
                shot_result.remaining, game_state.course_manager.get_current_hole_info(game_state.current_hole)["par"]
            )
            feedback.append(f"⛳ **{current_player.name}:** {shot_description}")
            
            # Move to next player
            shot_state.current_player_index += 1
            shot_state.add_completed_shot(current_player_id, shot_result.to_dict())
            
            # Check if all approach shots are done
            if shot_state.current_player_index >= len(game_state.player_manager.hitting_order):
                shot_state.phase = "putting"
                shot_state.current_player_index = 0
                feedback.append("🏌️ **Approach shots complete.** Moving to putting.")
            
            # Check for betting opportunities after approach shots
            betting_opportunity = self.check_betting_opportunity(game_state, shot_result)
            if betting_opportunity:
                interaction_needed = {
                    "type": "betting_opportunity",
                    "message": betting_opportunity["message"],
                    "options": betting_opportunity["options"]
                }
                return shot_result.to_dict(), feedback, False, interaction_needed
            
            return shot_result.to_dict(), feedback, True, None
            
        elif shot_state.phase == "putting":
            # Play putting with betting opportunities
            current_player_id = game_state.player_manager.hitting_order[shot_state.current_player_index]
            current_player = next(p for p in game_state.player_manager.players if p.id == current_player_id)
            
            # Simulate putt
            distance_to_pin = 10  # Simplified for now
            shot_result = ShotSimulator._simulate_putt(current_player, distance_to_pin, game_state)
            
            # Add shot to game state
            if current_player_id not in game_state.hole_scores or game_state.hole_scores[current_player_id] is None:
                game_state.hole_scores[current_player_id] = []
            game_state.hole_scores[current_player_id].append(shot_result)
            
            # Generate feedback
            if shot_result.made_shot:
                feedback.append(f"🏁 **{current_player.name}:** **Hole completed in {len(game_state.hole_scores[current_player_id])} strokes**")
            else:
                shot_description = self._create_shot_description(
                    shot_result.drive, shot_result.lie, shot_result.shot_quality, 
                    shot_result.remaining, game_state.course_manager.get_current_hole_info(game_state.current_hole)["par"]
                )
                feedback.append(f"🏌️ **{current_player.name}:** {shot_description}")
            
            # Move to next player
            shot_state.current_player_index += 1
            shot_state.add_completed_shot(current_player_id, shot_result.to_dict())
            
            # Check if all players have completed the hole
            completed_players = sum(1 for pid in game_state.player_manager.hitting_order 
                                  if game_state.hole_scores.get(pid) and any(hasattr(shot, 'made_shot') and shot.made_shot for shot in game_state.hole_scores[pid]))
            
            if completed_players >= len(game_state.player_manager.hitting_order):
                shot_state.phase = "hole_complete"
                feedback.append("🏁 **Hole complete!**")
                return None, feedback, False, None
            
            # Check for betting opportunities after putts
            betting_opportunity = self.check_betting_opportunity(game_state, shot_result)
            if betting_opportunity:
                interaction_needed = {
                    "type": "betting_opportunity",
                    "message": betting_opportunity["message"],
                    "options": betting_opportunity["options"]
                }
                return shot_result.to_dict(), feedback, False, interaction_needed
            
            return shot_result.to_dict(), feedback, True, None
        
        return None, feedback, False, None

    def simulate_hole(self, game_state: GameState, human_decisions: Dict[str, Any]) -> Tuple[GameState, List[str], Optional[Dict[str, Any]]]:
        """Simulate a complete hole chronologically - shot by shot, decision by decision"""
        feedback = []
        interaction_needed = None

        # Handle partnership response if this is a response to a partnership request
        if "accept_partnership" in human_decisions:
            partner_id = human_decisions.get("partner_id")
            accept = human_decisions.get("accept_partnership", False)
            
            # Check if there's actually a pending partnership request
            if game_state.betting_state.teams.get("type") == "pending":
                if accept:
                    game_state.dispatch_action("accept_partner", {"partner_id": partner_id})
                    partner_name = next(p.name for p in game_state.player_manager.players if p.id == partner_id)
                    feedback.append(f"🧑 **You:** \"Absolutely! Let's team up!\"")
                else:
                    game_state.dispatch_action("decline_partner", {"partner_id": partner_id})
                    captain_name = next(p.name for p in game_state.player_manager.players if p.id == game_state.player_manager.captain_id)
                    feedback.append(f"🧑 **You:** \"Thanks, but I'll pass.\"")
                    feedback.append(f"💻 **{captain_name}:** \"Fine, I'll go solo then!\"")
            else:
                # No pending request, just continue with normal play
                feedback.append(f"🧑 **You:** \"I'll play my own game.\"")

        # Handle partnership response from human partner (when human is asked to be partner)
        if "accept" in human_decisions and "partner_id" in human_decisions:
            # When human is asked to be partner, partner_id should be the human's ID
            human_id = self._get_human_player_id(game_state)
            accept = human_decisions.get("accept", False)
            
            if accept:
                game_state.dispatch_action("accept_partner", {"partner_id": human_id})
                captain_name = next(p.name for p in game_state.player_manager.players if p.id == game_state.player_manager.captain_id)
                feedback.append(f"🧑 **You:** \"Absolutely! Let's do this!\"")
            else:
                # Check if there's a pending partnership request
                if game_state.betting_state.teams.get("type") == "pending":
                    game_state.dispatch_action("decline_partner", {"partner_id": human_id})
                    feedback.append(f"🧑 **You:** \"Thanks, but I think I'll pass. Keep looking!\"")
                    # Get the actual captain name from the pending request
                    pending_captain_id = game_state.betting_state.teams.get("captain")
                    pending_captain_name = next(p.name for p in game_state.player_manager.players if p.id == pending_captain_id)
                    feedback.append(f"💻 **{pending_captain_name}:** \"Fine, I'll go solo then!\"")
                else:
                    # No pending request, just continue with normal play
                    feedback.append(f"🧑 **You:** \"I'll play my own game.\"")

        # Show hole setup
        feedback.append(f"\n🏌️ **Hole {game_state.current_hole} Setup**")
        captain_name = next(p.name for p in game_state.player_manager.players if p.id == game_state.player_manager.captain_id)
        hitting_order_names = [next(p.name for p in game_state.player_manager.players if p.id == pid) for pid in game_state.player_manager.hitting_order]
        feedback.append(f"👑 **Captain:** {captain_name}")
        feedback.append(f"🎯 **Hitting Order:** {' → '.join(hitting_order_names)}")
        
        # Show hole details
        hole_info = game_state.course_manager.get_current_hole_info(game_state.current_hole)
        par = hole_info.get("par", 4)
        yards = hole_info.get("yards", 400)
        stroke_index = hole_info.get("stroke_index", 10)
        description = hole_info.get("description", "")
        
        feedback.append(f"📊 **Hole Info:** Par {par}, {yards} yards, Stroke Index {stroke_index}")
        if description:
            feedback.append(f"📝 **Description:** {description}")
        feedback.append("")

        # Phase 1: All players tee off first
        feedback.append("🏌️ **TEE SHOTS**")
        hitting_order = game_state.player_manager.hitting_order or [p.id for p in game_state.player_manager.players]
        
        # Simulate all tee shots first
        tee_shot_results = {}
        for player_id in hitting_order:
            player = next(p for p in game_state.player_manager.players if p.id == player_id)
            player_name = player.name
            
            # Simulate tee shot
            tee_result = ShotSimulator.simulate_individual_tee_shot(player, game_state)
            tee_shot_results[player_id] = tee_result
            
            # Show the tee shot result
            drive_distance = tee_result.drive
            lie_description = tee_result.lie
            remaining = tee_result.remaining
            shot_quality = tee_result.shot_quality
            
            shot_desc = self._create_shot_description(drive_distance, lie_description, shot_quality, remaining, par)
            
            if player_id == self._get_human_player_id(game_state):
                feedback.append(f"🧑 **{player_name}:** {shot_desc}")
            else:
                feedback.append(f"💻 **{player_name}:** {shot_desc}")
            
            # Add shot reaction
            reaction = self._generate_shot_reaction(shot_quality, player_name, True)
            if reaction:
                feedback.append(f"  💬 {reaction}")
        
        # Phase 2: Partnership decisions after all tee shots
        captain_id = game_state.player_manager.captain_id
        captain_name = next(p.name for p in game_state.player_manager.players if p.id == captain_id)
        
        # Check if captain needs to make partnership decisions
        if game_state.betting_state.teams.get("type") == "pending":
            requested_partner = game_state.betting_state.teams.get("requested")
            if requested_partner:
                requested_name = next(p.name for p in game_state.player_manager.players if p.id == requested_partner)
                feedback.append(f"\n🤝 **Partnership Decision:** {captain_name} asked {requested_name} to be partner")
                
                # Check if human needs to respond
                if requested_partner == self._get_human_player_id(game_state):
                    interaction_needed = {
                        "type": "partnership_response",
                        "message": f"{captain_name} is asking you to be their partner. Do you accept?",
                        "captain_name": captain_name,
                        "captain_id": captain_id,
                        "partner_id": requested_partner
                    }
                    return game_state, feedback, interaction_needed
                else:
                    # Computer partner responds
                    partner_player = next(p for p in game_state.player_manager.players if p.id == requested_partner)
                    computer_partner = self._get_computer_player(requested_partner)
                    
                    if computer_partner.should_accept_partnership(captain_player.handicap, game_state):
                        game_state.betting_state.accept_partner(requested_partner, game_state.player_manager.players)
                        feedback.append(f"💻 **{requested_name}:** \"Absolutely! Let's do this!\"")
                    else:
                        # Check if there's still a pending request before declining
                        if game_state.betting_state.teams.get("type") == "pending":
                            game_state.betting_state.decline_partner(requested_partner, game_state.player_manager.players)
                            feedback.append(f"💻 **{requested_name}:** \"Thanks, but I'll pass.\"")
                            feedback.append(f"💻 **{captain_name}:** \"Fine, I'll go solo then!\"")
                        else:
                            # No pending request, captain goes solo
                            game_state.betting_state.go_solo(captain_id, game_state.player_manager.players)
                            feedback.append(f"💻 **{captain_name}:** \"I'll go solo.\"")
        
                # Phase 3: Simulate remaining shots chronologically
        feedback.append("\n🎯 **APPROACH SHOTS & PUTTING**")
        remaining_feedback = self._simulate_remaining_shots_chronological(game_state, tee_shot_results)
        feedback.extend(remaining_feedback)
        
        # Phase 4: Calculate points and provide educational feedback
        if game_state.betting_state.teams and game_state.betting_state.teams.get("type") in ("partners", "solo"):
            points_message = game_state.calculate_hole_points()
            feedback.append(f"💰 **Points:** {points_message}")
        else:
            # No teams formed, just show individual scores
            feedback.append("💰 **Points:** No partnerships formed - individual stroke play")
        
        # Add educational feedback
        educational_feedback = self._generate_educational_feedback(game_state, human_decisions)
        feedback.extend(educational_feedback)
        
        # Move to next hole
        game_state.next_hole()
        
        return game_state, feedback, None
        


    def _calculate_partnership_advantage(self, captain_id: str, partner_id: str, game_state: GameState) -> float:
        """Calculate the advantage of a potential partnership"""
        captain_handicap = self._get_player_handicap(captain_id, game_state)
        partner_handicap = self._get_player_handicap(partner_id, game_state)
        
        # Lower handicap is better
        team_avg_handicap = (captain_handicap + partner_handicap) / 2
        other_players = [p for p in game_state.player_manager.players if p.id not in [captain_id, partner_id]]
        other_avg_handicap = sum(self._get_player_handicap(p.id, game_state) for p in other_players) / len(other_players)
        
        # Positive advantage means team is stronger
        advantage = other_avg_handicap - team_avg_handicap
        
        # Consider current game position
        captain_points = self._get_current_points(captain_id, game_state)
        if captain_points < -3:  # Behind in game
            advantage += 0.5  # More willing to partner when behind
        elif captain_points > 3:  # Ahead in game
            advantage -= 0.3  # Less willing to partner when ahead
            
        return advantage



    def _simulate_remaining_shots_chronological(self, game_state: GameState, tee_shot_results: Dict[str, Any]) -> List[str]:
        """Simulate the remaining shots after tee shots to complete the hole"""
        return ShotSimulator.simulate_remaining_shots_chronological(game_state, tee_shot_results)


    
    def _generate_educational_feedback(self, game_state: GameState, human_decisions: Dict[str, Any]) -> List[str]:
        """Generate educational feedback about what the human could have done differently"""
        feedback = []
        
        # Analyze the hole result
        hole_history = game_state.hole_history[-1] if game_state.hole_history else None
        if not hole_history:
            return feedback
        
        points_delta = hole_history["points_delta"]
        human_id = self._get_human_player_id(game_state)
        human_points_change = points_delta.get(human_id, 0)
        hole_number = hole_history["hole"]
        
        feedback.append(f"\n📚 **Educational Analysis - Hole {hole_number}:**")
        
        # Course management feedback based on hole type and scoring
        par = game_state.course_manager.hole_pars[hole_number - 1] if game_state.course_manager.hole_pars else 4
        stroke_index = game_state.course_manager.hole_stroke_indexes[hole_number - 1] if game_state.course_manager.hole_stroke_indexes else 10
        
        feedback.append(f"🏌️ **Course Management:**")
        feedback.append(f"• Par {par}, Stroke Index {stroke_index} (1=hardest, 18=easiest)")
        
        # Difficulty-based strategy advice
        if stroke_index <= 6:  # Hard holes
            feedback.append(f"• This is a difficult hole - focus on avoiding big numbers rather than attacking pins")
            feedback.append(f"• On tough holes, partnership is often safer than going solo")
        elif stroke_index >= 13:  # Easy holes  
            feedback.append(f"• This is a scoring opportunity - consider more aggressive play and betting")
            feedback.append(f"• Good holes to consider going solo if you have an advantage")
        
        # Distance control and putting insights
        human_handicap = self._get_player_handicap(human_id, game_state)
        expected_distance_control = self._get_distance_expectations(human_handicap, par)
        feedback.append(f"• **Distance Control Expectations for {human_handicap:.1f} handicap:**")
        feedback.extend(expected_distance_control)
        
        # Partnership decision analysis with opponent insights
        if hole_history["teams"].get("type") == "partners":
            team1 = hole_history["teams"]["team1"]
            team2 = hole_history["teams"]["team2"]
            
            if human_id in team1:
                partner_id = [pid for pid in team1 if pid != human_id][0]
                partner_name = self._get_player_name(partner_id, game_state)
                partner_handicap = self._get_player_handicap(partner_id, game_state)
                
                feedback.append(f"\n🤝 **Partnership Analysis:**")
                if human_points_change > 0:
                    feedback.append(f"✅ Good partnership choice with {partner_name}! You won {human_points_change} points.")
                    feedback.append(f"• {partner_name} (hdcp {partner_handicap:.1f}) complemented your game well")
                else:
                    feedback.append(f"❌ Partnership with {partner_name} didn't work out. Lost {abs(human_points_change)} points.")
                    
                    # Detailed analysis of why partnership failed
                    handicap_diff = abs(human_handicap - partner_handicap)
                    if handicap_diff > 8:
                        feedback.append(f"• Large handicap difference ({handicap_diff:.1f}) may have hurt team dynamics")
                    
                    # Analyze opposing team strength
                    opposing_team = team2
                    opp_handicaps = [self._get_player_handicap(pid, game_state) for pid in opposing_team]
                    avg_opp_handicap = sum(opp_handicaps) / len(opp_handicaps)
                    your_team_avg = (human_handicap + partner_handicap) / 2
                    
                    if avg_opp_handicap < your_team_avg - 3:
                        feedback.append(f"• Opposing team was significantly stronger (avg {avg_opp_handicap:.1f} vs {your_team_avg:.1f})")
                        feedback.append(f"• Consider offering a double when facing stronger opponents to increase pressure")
                    
                    # Suggest better partners
                    alternative_partners = [p for p in game_state.player_manager.players if p.id not in team1 and p.id != human_id]
                    if alternative_partners:
                        best_alt = min(alternative_partners, key=lambda p: abs(p.handicap - human_handicap))
                        feedback.append(f"💡 {best_alt.name} (hdcp {best_alt.handicap:.1f}) might have been a better handicap match")
        
        elif hole_history["teams"].get("type") == "solo":
            captain = hole_history["teams"]["captain"]
            captain_name = self._get_player_name(captain, game_state)
            
            feedback.append(f"\n🎯 **Solo Play Analysis:**")
            if captain == human_id:
                if human_points_change > 0:
                    feedback.append(f"✅ Excellent solo play! You won {human_points_change} points against the field.")
                    feedback.append(f"• Your aggressive strategy paid off on this hole")
                else:
                    feedback.append(f"❌ Going solo backfired. Lost {abs(human_points_change)} points.")
                    feedback.append("• **When to go solo:** You have stroke advantage, feeling confident, or need to catch up")
                    feedback.append("• **When to avoid solo:** On difficult holes, when playing poorly, or when ahead")
                    
                    # Specific tactical advice
                    strokes_received = game_state.get_player_strokes()[human_id][hole_number]
                    if strokes_received == 0:
                        feedback.append("• You received no strokes - solo is riskier without handicap help")
                    else:
                        feedback.append(f"• You had {strokes_received} stroke(s) - should have been more confident")
            else:
                comp_name = self._get_player_name(captain, game_state)
                comp_personality = next((cp.personality for cp in self.computer_players if cp.player_id == captain), "unknown")
                
                if human_points_change < 0:
                    feedback.append(f"❌ {comp_name} beat your team going solo.")
                    feedback.append(f"• {comp_name} has '{comp_personality}' personality - learn their patterns")
                    feedback.append("• Consider offering doubles earlier when sensing a solo attempt")
                else:
                    feedback.append(f"✅ Good job defending against {comp_name}'s solo attempt!")
        
        # Betting and doubling strategy analysis
        current_base_wager = game_state.betting_state.base_wager
        feedback.append(f"\n💰 **Betting Strategy Analysis:**")
        
        if current_base_wager > 1:
            if human_points_change > 0:
                feedback.append(f"✅ The doubling strategy paid off! Doubled stakes increased your win to {human_points_change} points.")
            else:
                feedback.append(f"❌ Doubling magnified your losses to {abs(human_points_change)} points.")
                feedback.append("• **Doubling guidelines:** Accept when you have strokes or team advantage")
                feedback.append("• **Decline doubles:** When facing much stronger opponents without stroke help")
        
        # Stroke analysis and what it means for betting
        strokes = game_state.get_player_strokes()
        human_strokes = strokes[human_id][hole_number]
        
        feedback.append(f"\n📏 **Handicap Stroke Analysis:**")
        if human_strokes > 0:
            feedback.append(f"• You received {human_strokes} stroke(s) - this is a significant advantage!")
            feedback.append(f"• With strokes, you should be more aggressive in betting and partnerships")
            if human_points_change <= 0:
                feedback.append(f"• You should have won with stroke advantage - focus on course management")
        else:
            feedback.append(f"• No strokes on this hole - play more conservatively")
            feedback.append(f"• Without stroke help, be selective about doubles and solo attempts")
        
        # Game situation and psychological factors
        current_position = self._get_current_points(human_id, game_state)
        holes_remaining = 18 - game_state.current_hole + 1
        
        feedback.append(f"\n🧠 **Game Psychology & Position:**")
        feedback.append(f"• Current position: {current_position:+d} points with {holes_remaining} holes remaining")
        
        if current_position < -3 and holes_remaining > 8:
            feedback.append("• You're behind - consider taking calculated risks:")
            feedback.append("  - Go solo when you have stroke advantage")
            feedback.append("  - Accept doubles more readily")
            feedback.append("  - Look for partnerships with hot players")
        elif current_position < -6 and holes_remaining <= 8:
            feedback.append("• You're significantly behind with few holes left - time for aggressive play:")
            feedback.append("  - Go solo on any hole where you have an edge")
            feedback.append("  - Accept all doubles")
            feedback.append("  - Create pressure on opponents")
        elif current_position > 3 and holes_remaining < 8:
            feedback.append("• You're ahead - protect your lead:")
            feedback.append("  - Avoid solo unless overwhelming advantage")
            feedback.append("  - Be selective about accepting doubles")
            feedback.append("  - Choose reliable partners")
        
        # Opponent analysis and tendencies
        feedback.append(f"\n🤖 **Opponent Analysis:**")
        for comp_player in self.computer_players:
            points = self._get_current_points(comp_player.player_id, game_state)
            personality_insights = {
                "aggressive": "Takes risks when behind, offers doubles frequently, goes solo often",
                "conservative": "Plays it safe, selective about partnerships, avoids unnecessary risks", 
                "strategic": "Analyzes hole difficulty and game situation, adapts strategy accordingly",
                "balanced": "Makes steady decisions with some unpredictability"
            }
            
            tendency = personality_insights.get(comp_player.personality, "Standard play")
            feedback.append(f"• {comp_player.name} ({comp_player.handicap:.1f} hdcp, {points:+d} pts): {tendency}")
            
            # Specific tactical advice against this opponent
            if comp_player.personality == "aggressive" and points < -2:
                feedback.append(f"  → Expect {comp_player.name} to take big risks soon - be ready to capitalize")
            elif comp_player.personality == "conservative" and points > 2:
                feedback.append(f"  → {comp_player.name} will play very safely - pressure them with doubles")
        
        return feedback
    
    def _handicap_to_strength(self, handicap: float) -> int:
        """Convert handicap to strength value (1-10 scale)"""
        if handicap <= 0:
            return 10
        elif handicap <= 5:
            return 9
        elif handicap <= 10:
            return 8
        elif handicap <= 15:
            return 7
        elif handicap <= 20:
            return 6
        elif handicap <= 25:
            return 5
        else:
            return 4
    
    def _handicap_to_strength_string(self, handicap: float) -> str:
        """Convert handicap to strength string for Player objects"""
        if handicap <= 5:
            return "excellent"
        elif handicap <= 10:
            return "good"
        elif handicap <= 15:
            return "average"
        elif handicap <= 20:
            return "below_average"
        else:
            return "poor"
    
    def _assess_hole_difficulty(self, game_state: GameState) -> float:
        """Assess how difficult the current hole is (0=easy, 1=very hard)"""
        if not game_state.course_manager.hole_stroke_indexes or not game_state.course_manager.hole_pars:
            return 0.5
        
        hole_idx = game_state.current_hole - 1
        if hole_idx >= len(game_state.course_manager.hole_stroke_indexes):
            return 0.5
            
        stroke_index = game_state.course_manager.hole_stroke_indexes[hole_idx]
        par = game_state.course_manager.hole_pars[hole_idx]
        
        # Lower stroke index = harder hole
        difficulty = (19 - stroke_index) / 18.0
        
        # Factor in distance/yards if available
        if hole_idx < len(game_state.course_manager.hole_yards):
            yards = game_state.course_manager.hole_yards[hole_idx]
            # Expected yards by par
            expected_yards = {3: 150, 4: 400, 5: 550}
            expected = expected_yards.get(par, 400)
            
            # Distance factor: longer than expected = harder
            distance_factor = min(1.5, yards / expected)
            # Weight: 70% stroke index, 30% distance
            difficulty = 0.7 * difficulty + 0.3 * (distance_factor - 0.5)
        
        # Adjust based on par - this is for average handicap golfer
        if par == 5:
            difficulty *= 0.9  # Par 5s are generally easier
        elif par == 3:
            difficulty *= 1.1  # Par 3s can be tricky
            
        return min(1.0, max(0.0, difficulty))
    
    def _assess_team_advantage(self, game_state: GameState) -> float:
        """Assess team's advantage on current hole (-1 to 1)"""
        if not game_state.betting_state.teams or game_state.betting_state.teams.get("type") not in ["partners", "solo"]:
            return 0.0
        
        # Get player strokes for current hole
        try:
            strokes = game_state.get_player_strokes()
        except:
            # If no strokes available, return neutral
            return 0.0
        
        hole = game_state.current_hole
        
        if game_state.betting_state.teams["type"] == "partners":
            # For now, return neutral for partnerships
            return 0.0
        elif game_state.betting_state.teams["type"] == "solo":
            captain_id = game_state.betting_state.teams["captain"]
            captain_strokes = strokes.get(captain_id, 0)
            
            # Simple assessment: if captain gets strokes, it's advantageous
            if captain_strokes > 0:
                return 0.3 + (captain_strokes * 0.1)
            else:
                return -0.2
                
        return 0.0
    
    def _get_computer_player(self, player_id: str) -> ComputerPlayer:
        """Get computer player by ID"""
        for cp in self.computer_players:
            if cp.player_id == player_id:
                return cp
        raise ValueError(f"Computer player {player_id} not found")
    
    def _get_human_player_id(self, game_state: GameState) -> str:
        """Get the human player ID consistently using GameState utility"""
        return game_state.get_human_player_id()
    
    def _get_current_points(self, player_id: str, game_state: GameState) -> int:
        """Get current points for a specific player"""
        for player in game_state.player_manager.players:
            if player.id == player_id:
                return player.points
        return 0
    
    def _get_player_handicap(self, player_id: str, game_state: GameState) -> float:
        """Get handicap for a player"""
        for player in game_state.player_manager.players:
            if player.id == player_id:
                return player.handicap
        return 18.0
    
    def _get_player_name(self, player_id: str, game_state: GameState) -> str:
        """Get name for a player"""
        for player in game_state.player_manager.players:
            if player.id == player_id:
                return player.name
        return player_id
    
    def _get_team_id_for_player(self, game_state: GameState, player_id: str) -> str:
        """Get team ID for a player"""
        if not game_state.betting_state.teams or game_state.betting_state.teams.get("type") not in ["partners", "solo"]:
            return "1"
        
        if game_state.betting_state.teams["type"] == "partners":
            if player_id in game_state.betting_state.teams["team1"]:
                return "1"
            else:
                return "2"
        else:  # solo
            if player_id == game_state.betting_state.teams["captain"]:
                return "1"
            else:
                return "2"
    
    def _get_opposing_team_id(self, game_state: GameState, player_id: str) -> str:
        """Get opposing team ID for a player"""
        team_id = self._get_team_id_for_player(game_state, player_id)
        return "2" if team_id == "1" else "1"
    
    def _get_computer_double_response(self, game_state: GameState, target_team_id: str) -> str:
        """Get computer team's response to a double offer"""
        # Find a computer player on the target team
        target_players = []
        
        if game_state.betting_state.teams.get("type") == "partners":
            if target_team_id == "1":
                target_players = game_state.betting_state.teams["team1"]
            else:
                target_players = game_state.betting_state.teams["team2"]
        elif game_state.betting_state.teams.get("type") == "solo":
            if target_team_id == "1":
                target_players = [game_state.betting_state.teams["captain"]]
            else:
                target_players = game_state.betting_state.teams["opponents"]
        
        # Find a computer player to make the decision
        for player_id in target_players:
            if player_id in [cp.player_id for cp in self.computer_players]:
                comp_player = self._get_computer_player(player_id)
                return "accept" if comp_player.should_accept_double(game_state) else "decline"
        
        return "decline"  # Default fallback
    
    def _handicap_to_strength(self, handicap: float) -> str:
        """Convert handicap to strength category"""
        if handicap <= 5:
            return "Expert"
        elif handicap <= 12:
            return "Strong"
        elif handicap <= 20:
            return "Average"
        else:
            return "Beginner"

    def _get_distance_expectations(self, handicap: float, par: int) -> List[str]:
        """Get realistic distance expectations based on handicap"""
        expectations = []
        
        if handicap <= 5:  # Low handicap
            expectations.append("• Drive: 250-270 yards consistently")
            expectations.append("• Approach shots: Within 20 feet from 100-150 yards")
            expectations.append("• Short game: Up and down 60%+ of the time")
            expectations.append("• Putting: Rarely 3-putt, make most putts under 6 feet")
        elif handicap <= 10:  # Mid handicap
            expectations.append("• Drive: 230-250 yards, occasional mishits")
            expectations.append("• Approach shots: Green in regulation 50% on par 4s")
            expectations.append("• Short game: Get up and down 40% of the time")
            expectations.append("• Putting: Average 30-32 putts per round")
        elif handicap <= 18:  # Higher handicap
            expectations.append("• Drive: 200-230 yards, accuracy more important than distance")
            expectations.append("• Approach shots: Focus on hitting greens, pin hunting risky")
            expectations.append("• Short game: Biggest opportunity for improvement")
            expectations.append("• Putting: Work on lag putting, avoid 3-putts")
        else:  # High handicap
            expectations.append("• Drive: Focus on keeping it in play vs distance")
            expectations.append("• Approach shots: Aim for center of greens")
            expectations.append("• Short game: Use most forgiving clubs (pitching wedge vs sand wedge)")
            expectations.append("• Putting: Two-putt strategy, don't be too aggressive")
        
        # Add par-specific advice
        if par == 3:
            expectations.append(f"• Par 3 strategy: Club up, aim for center of green")
        elif par == 5:
            expectations.append(f"• Par 5 strategy: {'Go for it in 2 if well-positioned' if handicap <= 10 else 'Lay up for easy wedge shot'}")
        
        # Add course management advice based on handicap
        if handicap > 15:
            expectations.append("  - Course Management: Play to fat part of greens, avoid pin hunting")
            expectations.append("  - Strategy: Take what the course gives you, avoid heroic shots")
        elif handicap > 8:
            expectations.append("  - Course Management: Mix conservative and aggressive play based on situation")
            expectations.append("  - Strategy: Attack pins when you have stroke advantage")
        else:
            expectations.append("  - Course Management: You can be aggressive with good distance control")
            expectations.append("  - Strategy: Attack pins regularly, especially on easier holes")
            
        return expectations

    def _get_next_approach_shot(self, game_state: GameState) -> Optional[Dict[str, Any]]:
        """Get the next approach shot event for team members"""
        shot_state = game_state.shot_state
        hitting_order = game_state.player_manager.hitting_order or [p.id for p in game_state.player_manager.players]
        
        # Get next player for approach shot
        current_player_id = shot_state.get_current_player_id(hitting_order)
        if current_player_id:
            player = next(p for p in game_state.player_manager.players if p.id == current_player_id)
            
            return {
                "type": "approach_shot",
                "player": player,
                "hole_info": ProbabilityCalculator._get_hole_info(game_state),
                "shot_number": shot_state.current_player_index + 1,
                "total_players": 2  # Only 2 players take approach shots in partnership
            }
        
        return None

    def _execute_approach_shot_event(self, game_state: GameState, shot_event: Dict[str, Any]) -> Tuple[GameState, Dict[str, Any], Dict[str, Any]]:
        """Execute an approach shot event and return result with probabilities"""
        player = shot_event.get("player")
        if not player:
            raise ValueError("Missing 'player' key in shot_event")
        
        # Get remaining distance from tee shot results
        tee_results = getattr(game_state, 'tee_shot_results', {})
        player_tee_result = tee_results.get(player.id, {})
        remaining_distance = player_tee_result.get('remaining', 150) if isinstance(player_tee_result, dict) else 150
        
        # Execute the approach shot using ShotSimulator service
        shot_result = ShotSimulator.simulate_approach_shot(player, remaining_distance, game_state)
        
        # Calculate post-shot probabilities
        post_shot_probs = ProbabilityCalculator.calculate_post_shot_probabilities(shot_result, game_state)
        
        # Update shot state
        game_state.shot_state.add_completed_shot(
            player.id,
            shot_result,
            {}  # No pre-shot probabilities for approach shots
        )
        game_state.shot_state.next_shot()
        
        # Create enhanced shot result with ShotResult object
        enhanced_result = {
            "shot_result": shot_result,
            "player": player,
            "shot_description": self._create_detailed_shot_description(shot_result, player, game_state),
            "reactions": self._generate_shot_reactions(shot_result, player, game_state)
        }
        
        # Combine probability information
        probabilities = {
            "outcome": post_shot_probs,
            "betting_implications": self._calculate_betting_implications(shot_result, game_state)
        }
        
        return game_state, enhanced_result, probabilities

    def run_monte_carlo_simulation(self, human_player: Player, computer_configs: List[Dict[str, Any]], 
                                   num_simulations: int = 100, course_name: Optional[str] = None,
                                   progress_callback=None) -> MonteCarloResults:
        """
        Run Monte Carlo simulation with specified number of games
        
        Args:
            human_player: Human player configuration
            computer_configs: List of 3 computer player configurations
            num_simulations: Number of complete games to simulate
            course_name: Optional course to play on
            progress_callback: Optional callback function for progress updates
        
        Returns:
            MonteCarloResults object with statistical analysis
        """
        results = MonteCarloResults()
        
        for sim_num in range(num_simulations):
            # Setup a fresh game for each simulation
            game_state = self.setup_simulation(human_player, computer_configs, course_name)
            
            # Simulate all 18 holes
            for hole in range(1, 19):
                game_state.current_hole = hole
                
                # For Monte Carlo, we'll make automatic decisions for the human player
                # Using a "balanced" strategy similar to the computer AI
                human_decisions = self._generate_monte_carlo_human_decisions(game_state, human_player)
                
                # Ensure we have valid decisions structure
                if not human_decisions:
                    human_decisions = {
                        "action": None,
                        "requested_partner": None,
                        "offer_double": False,
                        "accept_double": False
                    }
                
                # Simulate the hole
                game_state, _ = self.simulate_hole(game_state, human_decisions)
                
                # Move to next hole
                if hole < 18:
                    game_state.next_hole()
            
            # Get final scores
            final_scores = {
                player.id: player.points
                for player in game_state.player_manager.players
            }
            
            # Add to results
            results.add_game_result(final_scores)
            
            # Progress callback
            if progress_callback:
                progress_callback(sim_num + 1, num_simulations)
        
        return results
    
    def _generate_monte_carlo_human_decisions(self, game_state: GameState, human_player: Player) -> Dict[str, Any]:
        """
        Generate automatic decisions for human player in Monte Carlo simulation
        Uses a balanced strategy similar to computer AI
        """
        captain_id = game_state.player_manager.captain_id
        # Get current points for human player
        current_points = 0
        for player in game_state.player_manager.players:
            if player.id == human_player.id:
                current_points = player.points
                break
        
        # Default decisions
        decisions = {
            "action": None,
            "requested_partner": None,
            "offer_double": False,
            "accept_double": False
        }
        
        if captain_id == human_player.id:
            # Human is captain - make partnership decision
            
            # Assess potential partners
            potential_partners = [p for p in game_state.player_manager.players if p.id != human_player.id]
            
            # Simple strategy: prefer partners with similar or better handicaps
            human_handicap = human_player.handicap
            best_partner = None
            best_compatibility = -999
            
            for partner in potential_partners:
                partner_handicap = partner.handicap
                partner_points = partner.points
                
                # Calculate compatibility score
                handicap_diff = abs(human_handicap - partner_handicap)
                point_advantage = partner_points - current_points
                
                compatibility = -handicap_diff + (point_advantage * 0.5)
                
                # Prefer better players when behind
                if current_points < -2:
                    compatibility += max(0, human_handicap - partner_handicap) * 2
                
                if compatibility > best_compatibility:
                    best_compatibility = compatibility
                    best_partner = partner
            
            # Decide whether to go solo or pick partner
            hole_difficulty = self._assess_hole_difficulty(game_state)
            go_solo_threshold = 0.3 + (current_points * 0.1)  # More likely to go solo when behind
            
            if (random.random() < go_solo_threshold and 
                hole_difficulty < 0.6 and 
                current_points < 2):  # Don't go solo when ahead
                decisions["action"] = "go_solo"
            elif best_partner:
                decisions["requested_partner"] = best_partner.id
        
        # Doubling decisions (simplified strategy)
        if not game_state.betting_state.doubled_status:
            # Offer double if significantly behind or have good advantage
            if current_points < -3 or (current_points > 2 and random.random() < 0.3):
                decisions["offer_double"] = True
        
        # Accept double based on position and hole advantage
        if game_state.betting_state.doubled_status and not game_state.betting_state.doubled_status.get("accepted", False):
            team_advantage = self._assess_team_advantage(game_state)
            accept_threshold = 0.4 - (current_points * 0.1)  # More likely to accept when ahead
            
            if team_advantage > 0.2 or random.random() < accept_threshold:
                decisions["accept_double"] = True
        
        return decisions

    def _create_shot_description(self, drive_distance: int, lie_description: str, shot_quality: str, remaining: int, par: int) -> str:
        """Create a realistic and detailed shot description."""
        distance_words = {
            100: "short", 150: "medium", 200: "long", 250: "very long", 300: "extremely long"
        }
        remaining_words = {
            30: "very short", 50: "short", 70: "medium", 100: "long", 150: "very long"
        }

        distance_desc = distance_words.get(drive_distance, "a distance")
        remaining_desc = remaining_words.get(remaining, "a distance")

        if shot_quality == "excellent":
            return f"He hits a {distance_desc} drive, {lie_description} lie, and lands it {remaining_desc} to the pin."
        elif shot_quality == "good":
            return f"He hits a {distance_desc} drive, {lie_description} lie, and lands it {remaining_desc} to the pin."
        elif shot_quality == "average":
            return f"He hits a {distance_desc} drive, {lie_description} lie, and lands it {remaining_desc} to the pin."
        elif shot_quality == "poor":
            return f"He hits a {distance_desc} drive, {lie_description} lie, and lands it {remaining_desc} to the pin."
        else: # terrible
            return f"He hits a {distance_desc} drive, {lie_description} lie, and lands it {remaining_desc} to the pin."

    def _generate_shot_reaction(self, shot_quality: str, player_name: str, is_first_shot: bool) -> Optional[str]:
        """Generate a reaction from other players based on the shot quality."""
        if shot_quality == "excellent":
            return f"{player_name} hits a great shot!"
        elif shot_quality == "good":
            return f"{player_name} hits a solid shot."
        elif shot_quality == "average":
            return f"{player_name} hits a decent shot."
        elif shot_quality == "poor":
            return f"{player_name} hits a poor shot."
        else: # terrible
            return f"{player_name} hits a terrible shot."

    def _generate_hole_summary(self, game_state: GameState) -> List[str]:
        """Generate a summary of the hole's outcome and provide learning points."""
        feedback = []
        
        # Get the last hole's history
        hole_history = game_state.hole_history[-1] if game_state.hole_history else None
        if not hole_history:
            return feedback
        
        human_id = self._get_human_player_id(game_state)
        human_points_change = hole_history["points_delta"].get(human_id, 0)
        hole_number = hole_history["hole"]
        
        feedback.append(f"\n📚 **Hole {hole_number} Summary:**")
        
        # Course management feedback
        par = game_state.course_manager.hole_pars[hole_number - 1] if game_state.course_manager.hole_pars else 4
        stroke_index = game_state.course_manager.hole_stroke_indexes[hole_number - 1] if game_state.course_manager.hole_stroke_indexes else 10
        
        feedback.append(f"🏌️ **Course Management:**")
        feedback.append(f"• Par {par}, Stroke Index {stroke_index} (1=hardest, 18=easiest)")
        
        # Difficulty-based strategy advice
        if stroke_index <= 6:  # Hard holes
            feedback.append(f"• This was a difficult hole - {self._get_player_name(human_id, game_state)} focused on avoiding big numbers.")
            feedback.append(f"• On tough holes, partnership is often safer than going solo.")
        elif stroke_index >= 13:  # Easy holes  
            feedback.append(f"• This was a scoring opportunity - {self._get_player_name(human_id, game_state)} considered more aggressive play.")
            feedback.append(f"• Good holes to consider going solo if you have an advantage.")
        
        # Distance control and putting insights
        human_handicap = self._get_player_handicap(human_id, game_state)
        expected_distance_control = self._get_distance_expectations(human_handicap, par)
        feedback.append(f"• **Distance Control Expectations for {human_handicap:.1f} handicap:**")
        feedback.extend(expected_distance_control)
        
        # Partnership decision analysis
        if hole_history["teams"].get("type") == "partners":
            team1 = hole_history["teams"]["team1"]
            team2 = hole_history["teams"]["team2"]
            
            if human_id in team1:
                partner_id = [pid for pid in team1 if pid != human_id][0]
                partner_name = self._get_player_name(partner_id, game_state)
                partner_handicap = self._get_player_handicap(partner_id, game_state)
                
                feedback.append(f"\n🤝 **Partnership Decision:**")
                if human_points_change > 0:
                    feedback.append(f"✅ Good partnership choice with {partner_name}! You won {human_points_change} points.")
                    feedback.append(f"• {partner_name} (hdcp {partner_handicap:.1f}) complemented your game well.")
                else:
                    feedback.append(f"❌ Partnership with {partner_name} didn't work out. Lost {abs(human_points_change)} points.")
                    
                    # Detailed analysis of why partnership failed
                    handicap_diff = abs(human_handicap - partner_handicap)
                    if handicap_diff > 8:
                        feedback.append(f"• Large handicap difference ({handicap_diff:.1f}) may have hurt team dynamics.")
                    
                    # Analyze opposing team strength
                    opposing_team = team2
                    opp_handicaps = [self._get_player_handicap(pid, game_state) for pid in opposing_team]
                    avg_opp_handicap = sum(opp_handicaps) / len(opp_handicaps)
                    your_team_avg = (human_handicap + partner_handicap) / 2
                    
                    if avg_opp_handicap < your_team_avg - 3:
                        feedback.append(f"• Opposing team was significantly stronger (avg {avg_opp_handicap:.1f} vs {your_team_avg:.1f}).")
                        feedback.append(f"• Consider offering a double when facing stronger opponents to increase pressure.")
                    
                    # Suggest better partners
                    alternative_partners = [p for p in game_state.player_manager.players if p.id not in team1 and p.id != human_id]
                    if alternative_partners:
                        best_alt = min(alternative_partners, key=lambda p: abs(p.handicap - human_handicap))
                        feedback.append(f"💡 {best_alt.name} (hdcp {best_alt.handicap:.1f}) might have been a better handicap match.")
        
        elif hole_history["teams"].get("type") == "solo":
            captain = hole_history["teams"]["captain"]
            captain_name = self._get_player_name(captain, game_state)
            
            feedback.append(f"\n🎯 **Solo Play Decision:**")
            if captain == human_id:
                if human_points_change > 0:
                    feedback.append(f"✅ Excellent solo play! You won {human_points_change} points against the field.")
                    feedback.append(f"• Your aggressive strategy paid off on this hole.")
                else:
                    feedback.append(f"❌ Going solo backfired. Lost {abs(human_points_change)} points.")
                    feedback.append("• **When to go solo:** You have stroke advantage, feeling confident, or need to catch up.")
                    feedback.append("• **When to avoid solo:** On difficult holes, when playing poorly, or when ahead.")
                    
                    # Specific tactical advice
                    strokes_received = game_state.get_player_strokes()[human_id][hole_number]
                    if strokes_received == 0:
                        feedback.append("• You received no strokes - solo is riskier without handicap help.")
                    else:
                        feedback.append(f"• You had {strokes_received} stroke(s) - should have been more confident.")
            else:
                comp_name = self._get_player_name(captain, game_state)
                comp_personality = next((cp.personality for cp in self.computer_players if cp.player_id == captain), "unknown")
                
                if human_points_change < 0:
                    feedback.append(f"❌ {comp_name} beat your team going solo.")
                    feedback.append(f"• {comp_name} has '{comp_personality}' personality - learn their patterns.")
                    feedback.append("• Consider offering doubles earlier when sensing a solo attempt.")
                else:
                    feedback.append(f"✅ Good job defending against {comp_name}'s solo attempt!")
        
        # Betting and doubling strategy analysis
        current_base_wager = game_state.betting_state.base_wager
        feedback.append(f"\n💰 **Betting Strategy:**")
        
        if current_base_wager > 1:
            if human_points_change > 0:
                feedback.append(f"✅ The doubling strategy paid off! Doubled stakes increased your win to {human_points_change} points.")
            else:
                feedback.append(f"❌ Doubling magnified your losses to {abs(human_points_change)} points.")
                feedback.append("• **Doubling guidelines:** Accept when you have strokes or team advantage.")
                feedback.append("• **Decline doubles:** When facing much stronger opponents without stroke help.")
        
        # Stroke analysis and what it means for betting
        strokes = game_state.get_player_strokes()
        human_strokes = strokes[human_id][hole_number]
        
        feedback.append(f"\n📏 **Handicap Stroke Analysis:**")
        if human_strokes > 0:
            feedback.append(f"• You received {human_strokes} stroke(s) - this is a significant advantage!")
            feedback.append(f"• With strokes, you should be more aggressive in betting and partnerships.")
            if human_points_change <= 0:
                feedback.append(f"• You should have won with stroke advantage - focus on course management.")
        else:
            feedback.append(f"• No strokes on this hole - play more conservatively.")
            feedback.append(f"• Without stroke help, be selective about doubles and solo attempts.")
        
        # Game situation and psychological factors
        current_position = self._get_current_points(human_id, game_state)
        holes_remaining = 18 - game_state.current_hole + 1
        
        feedback.append(f"\n🧠 **Game Psychology & Position:**")
        feedback.append(f"• Current position: {current_position:+d} points with {holes_remaining} holes remaining.")
        
        if current_position < -3 and holes_remaining > 8:
            feedback.append("• You're behind - consider taking calculated risks:")
            feedback.append("  - Go solo when you have stroke advantage.")
            feedback.append("  - Accept doubles more readily.")
            feedback.append("  - Look for partnerships with hot players.")
        elif current_position < -6 and holes_remaining <= 8:
            feedback.append("• You're significantly behind with few holes left - time for aggressive play:")
            feedback.append("  - Go solo on any hole where you have an edge.")
            feedback.append("  - Accept all doubles.")
            feedback.append("  - Create pressure on opponents.")
        elif current_position > 3 and holes_remaining < 8:
            feedback.append("• You're ahead - protect your lead:")
            feedback.append("  - Avoid solo unless overwhelming advantage.")
            feedback.append("  - Be selective about accepting doubles.")
            feedback.append("  - Choose reliable partners.")
        
        # Opponent analysis and tendencies
        feedback.append(f"\n🤖 **Opponent Analysis:**")
        for comp_player in self.computer_players:
            points = self._get_current_points(comp_player.player_id, game_state)
            personality_insights = {
                "aggressive": "Takes risks when behind, offers doubles frequently, goes solo often",
                "conservative": "Plays it safe, selective about partnerships, avoids unnecessary risks", 
                "strategic": "Analyzes hole difficulty and game situation, adapts strategy accordingly",
                "balanced": "Makes steady decisions with some unpredictability"
            }
            
            tendency = personality_insights.get(comp_player.personality, "Standard play")
            feedback.append(f"• {comp_player.name} ({comp_player.handicap:.1f} hdcp, {points:+d} pts): {tendency}")
            
            # Specific tactical advice against this opponent
            if comp_player.personality == "aggressive" and points < -2:
                feedback.append(f"  → Expect {comp_player.name} to take big risks soon - be ready to capitalize.")
            elif comp_player.personality == "conservative" and points > 2:
                feedback.append(f"  → {comp_player.name} will play very safely - pressure them with doubles.")
        
        return feedback

    # NEW EVENT-DRIVEN SHOT ARCHITECTURE
    

    

    
    def check_betting_opportunity(self, game_state: GameState, shot_result: ShotResult) -> Optional[Dict[str, Any]]:
        """Check if there's a betting opportunity after this shot"""
        return BettingEngine.check_betting_opportunity(game_state, shot_result, self.computer_players)
    
    def calculate_betting_probabilities(self, game_state: GameState, decision: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate probabilities for betting decisions"""
        return ProbabilityCalculator.calculate_betting_probabilities(game_state, decision)
    

    

    


# Global simulation engine instance
simulation_engine = SimulationEngine()
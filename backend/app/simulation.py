import random
import math
from typing import Dict, List, Tuple, Optional
from .game_state import GameState

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
        if game_state.doubled_status:
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
        for player in game_state.players:
            if player["id"] == self.player_id:
                return player["points"]
        return 0
    
    def _get_points_for_player(self, handicap: float, game_state: GameState) -> int:
        """Get points for a player with given handicap"""
        for player in game_state.players:
            if abs(player["handicap"] - handicap) < 0.1:
                return player["points"]
        return 0
    
    def _assess_hole_difficulty(self, game_state: GameState) -> float:
        """Assess how difficult the current hole is (0=easy, 1=very hard)"""
        if not game_state.hole_stroke_indexes or not game_state.hole_pars:
            return 0.5
        
        hole_idx = game_state.current_hole - 1
        if hole_idx >= len(game_state.hole_stroke_indexes):
            return 0.5
            
        stroke_index = game_state.hole_stroke_indexes[hole_idx]
        par = game_state.hole_pars[hole_idx]
        
        # Lower stroke index = harder hole
        difficulty = (19 - stroke_index) / 18.0
        
        # Factor in distance/yards if available
        if hasattr(game_state, 'hole_yards') and hole_idx < len(game_state.hole_yards):
            yards = game_state.hole_yards[hole_idx]
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
        if not game_state.teams or game_state.teams.get("type") not in ["partners", "solo"]:
            return 0.0
        
        # Get player strokes for current hole
        strokes = game_state.get_player_strokes()
        hole = game_state.current_hole
        
        if game_state.teams["type"] == "partners":
            team1 = game_state.teams["team1"]
            team2 = game_state.teams["team2"]
            
            # Check if we're on team1 or team2
            our_team = team1 if self.player_id in team1 else team2
            their_team = team2 if self.player_id in team1 else team1
            
            # Calculate net stroke advantage
            our_strokes = min(strokes[pid][hole] for pid in our_team)
            their_strokes = min(strokes[pid][hole] for pid in their_team)
            
            stroke_advantage = their_strokes - our_strokes
            
            # Consider handicap differences
            our_handicaps = [p["handicap"] for p in game_state.players if p["id"] in our_team]
            their_handicaps = [p["handicap"] for p in game_state.players if p["id"] in their_team]
            
            handicap_advantage = (sum(their_handicaps) - sum(our_handicaps)) / 20.0
            
            return min(1.0, max(-1.0, stroke_advantage + handicap_advantage))
        
        elif game_state.teams["type"] == "solo":
            captain = game_state.teams["captain"]
            opponents = game_state.teams["opponents"]
            
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
        
    def add_game_result(self, final_scores: dict):
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
    
    def get_summary(self) -> dict:
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
        
    def setup_simulation(self, human_player: dict, computer_configs: List[dict], course_name: Optional[str] = None) -> GameState:
        """Setup a simulation game with one human and three computer players"""
        if len(computer_configs) != 3:
            raise ValueError("Need exactly 3 computer player configurations")
        
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
        
        # Setup game state with all players
        all_players = [
            {
                "id": human_player["id"],
                "name": human_player["name"],
                "handicap": human_player["handicap"],
                "strength": self._handicap_to_strength(human_player["handicap"])
            }
        ] + [
            {
                "id": cp.player_id,
                "name": cp.name,
                "handicap": cp.handicap,
                "strength": self._handicap_to_strength(cp.handicap)
            } for cp in self.computer_players
        ]
        
        game_state = GameState()
        game_state.setup_players(all_players, course_name)
        
        return game_state
    
    def simulate_hole(self, game_state: GameState, human_decisions: dict) -> Tuple[GameState, List[str]]:
        """Simulate a complete hole with AI decisions and shot outcomes"""
        feedback = []
        
        # Phase 1: Partnership decisions
        captain_id = game_state.captain_id
        
        if captain_id in [cp.player_id for cp in self.computer_players]:
            # Computer is captain - make partnership decision
            captain_player = self._get_computer_player(captain_id)
            partnership_decision = self._make_computer_partnership_decision(captain_player, game_state)
            
            if partnership_decision == "solo":
                game_state.dispatch_action("go_solo", {"captain_id": captain_id})
                feedback.append(f"💻 {captain_player.name} decided to go solo!")
            elif partnership_decision:
                # Request partnership
                game_state.dispatch_action("request_partner", {
                    "captain_id": captain_id, 
                    "partner_id": partnership_decision
                })
                
                # Partner response (if computer)
                if partnership_decision in [cp.player_id for cp in self.computer_players]:
                    partner_player = self._get_computer_player(partnership_decision)
                    accept = partner_player.should_accept_partnership(captain_player.handicap, game_state)
                    
                    if accept:
                        game_state.dispatch_action("accept_partner", {"partner_id": partnership_decision})
                        feedback.append(f"💻 {partner_player.name} accepted the partnership with {captain_player.name}")
                    else:
                        game_state.dispatch_action("decline_partner", {"partner_id": partnership_decision})
                        feedback.append(f"💻 {partner_player.name} declined the partnership - {captain_player.name} goes solo!")
        else:
            # Human is captain - use their decisions
            if human_decisions.get("action") == "go_solo":
                game_state.dispatch_action("go_solo", {"captain_id": captain_id})
                feedback.append(f"🧑 You decided to go solo!")
            elif human_decisions.get("requested_partner"):
                partner_id = human_decisions["requested_partner"]
                game_state.dispatch_action("request_partner", {
                    "captain_id": captain_id,
                    "partner_id": partner_id
                })
                
                # Computer partner response
                if partner_id in [cp.player_id for cp in self.computer_players]:
                    partner_player = self._get_computer_player(partner_id)
                    human_handicap = self._get_player_handicap(captain_id, game_state)
                    accept = partner_player.should_accept_partnership(human_handicap, game_state)
                    
                    if accept:
                        game_state.dispatch_action("accept_partner", {"partner_id": partner_id})
                        feedback.append(f"💻 {partner_player.name} accepted your partnership request")
                    else:
                        game_state.dispatch_action("decline_partner", {"partner_id": partner_id})
                        feedback.append(f"💻 {partner_player.name} declined your partnership - you go solo!")
        
        # Phase 2: Doubling phase
        doubling_feedback = self._simulate_doubling_phase(game_state, human_decisions)
        feedback.extend(doubling_feedback)
        
        # Phase 3: Simulate actual golf shots
        shot_feedback = self._simulate_shots(game_state)
        feedback.extend(shot_feedback)
        
        # Phase 4: Set up teams and calculate results
        # Ensure teams are properly set for point calculation
        if not hasattr(game_state, 'teams') or not game_state.teams:
            # Default to solo play if no teams were set during partnership phase
            game_state.teams = {"type": "solo", "captain": game_state.captain_id, "opponents": [p["id"] for p in game_state.players if p["id"] != game_state.captain_id]}
        
        game_state.dispatch_action("calculate_hole_points", {})
        
        educational_feedback = self._generate_educational_feedback(game_state, human_decisions)
        feedback.extend(educational_feedback)
        
        # Advance to next hole
        if game_state.current_hole < 18:
            game_state.dispatch_action("next_hole", {})
        
        return game_state, feedback
    
    def _make_computer_partnership_decision(self, captain: ComputerPlayer, game_state: GameState) -> Optional[str]:
        """Computer captain decides on partnership"""
        other_players = [cp for cp in self.computer_players if cp.player_id != captain.player_id]
        
        # Check if should go solo first
        if captain.should_go_solo(game_state):
            return "solo"
        
        # Evaluate potential partners
        best_partner = None
        best_score = -1
        
        for potential_partner in other_players:
            # Skip if already hit (in real game this would be enforced by hitting order)
            handicap_diff = abs(captain.handicap - potential_partner.handicap)
            team_strength = (captain.handicap + potential_partner.handicap) / 2
            
            # Prefer partners with complementary handicaps
            score = 1.0 - (handicap_diff / 25.0) + (25 - team_strength) / 50.0
            
            if score > best_score and random.random() > 0.3:  # Add some randomness
                best_score = score
                best_partner = potential_partner
        
        return best_partner.player_id if best_partner else None
    
    def _simulate_doubling_phase(self, game_state: GameState, human_decisions: dict) -> List[str]:
        """Simulate the doubling/betting phase"""
        feedback = []
        
        # Check if human wants to offer double
        if human_decisions.get("offer_double") and not game_state.doubled_status:
            # Determine target team
            target_team = self._get_opposing_team_id(game_state, self._get_human_player_id(game_state))
            game_state.dispatch_action("offer_double", {
                "offering_team_id": self._get_team_id_for_player(game_state, self._get_human_player_id(game_state)),
                "target_team_id": target_team
            })
            
            # Computer response to double
            computer_response = self._get_computer_double_response(game_state, target_team)
            if computer_response == "accept":
                game_state.dispatch_action("accept_double", {"team_id": target_team})
                feedback.append("💻 Computer team accepted your double! Stakes doubled!")
            else:
                game_state.dispatch_action("decline_double", {"team_id": target_team})
                feedback.append("💻 Computer team declined your double - you win the hole at current stakes!")
        
        # Check if computer wants to offer double
        elif not game_state.doubled_status:
            for comp_player in self.computer_players:
                if comp_player.should_offer_double(game_state):
                    offering_team = self._get_team_id_for_player(game_state, comp_player.player_id)
                    target_team = self._get_opposing_team_id(game_state, comp_player.player_id)
                    
                    game_state.dispatch_action("offer_double", {
                        "offering_team_id": offering_team,
                        "target_team_id": target_team
                    })
                    
                    feedback.append(f"💻 {comp_player.name} offers to double your team!")
                    
                    # Human response (from decisions or default)
                    if human_decisions.get("accept_double", False):
                        game_state.dispatch_action("accept_double", {"team_id": target_team})
                        feedback.append("🧑 You accepted the double! Stakes doubled!")
                    else:
                        game_state.dispatch_action("decline_double", {"team_id": target_team})
                        feedback.append("🧑 You declined the double - computer team wins at current stakes!")
                    break
        
        return feedback
    
    def _simulate_shots(self, game_state: GameState) -> List[str]:
        """Simulate golf shots for all players based on their handicaps"""
        feedback = []
        hole_par = game_state.hole_pars[game_state.current_hole - 1] if game_state.hole_pars else 4
        
        scores = {}
        shot_details = {}
        
        for player in game_state.players:
            player_id = player["id"]
            handicap = player["handicap"]
            
            # Get net strokes for this hole
            strokes = game_state.get_player_strokes()
            net_strokes = strokes[player_id][game_state.current_hole]
            
            # Simulate score based on handicap and hole difficulty
            gross_score = self._simulate_player_score(handicap, hole_par, game_state.current_hole, game_state)
            net_score = max(1, gross_score - net_strokes)  # Can't go below 1
            
            scores[player_id] = int(net_score)
            shot_details[player_id] = {
                "gross": gross_score,
                "net": net_score,
                "strokes_received": net_strokes
            }
            
            # Record score in game state
            game_state.dispatch_action("record_net_score", {
                "player_id": player_id,
                "score": int(net_score)
            })
        
        # Generate shot feedback
        for player in game_state.players:
            player_id = player["id"]
            details = shot_details[player_id]
            
            if player_id == self._get_human_player_id(game_state):
                feedback.append(f"🧑 Your score: {details['gross']} gross, {details['net']} net (received {details['strokes_received']} strokes)")
            else:
                feedback.append(f"💻 {player['name']}: {details['gross']} gross, {details['net']} net (received {details['strokes_received']} strokes)")
        
        return feedback
    
    def _simulate_player_score(self, handicap: float, par: int, hole_number: int, game_state: 'GameState' = None) -> int:
        """Simulate a realistic score for a player based on their handicap and hole characteristics"""
        # More realistic probability distributions based on actual golf statistics
        
        # Get distance factor if available
        distance_factor = 1.0
        if game_state and hasattr(game_state, 'hole_yards'):
            hole_idx = hole_number - 1
            if hole_idx < len(game_state.hole_yards):
                yards = game_state.hole_yards[hole_idx]
                expected_yards = {3: 150, 4: 400, 5: 550}
                expected = expected_yards.get(par, 400)
                
                # Distance factor affects difficulty (longer = harder)
                distance_factor = min(1.3, max(0.7, yards / expected))
        
        # Adjust base probabilities by handicap level
        if handicap <= 0:  # Plus handicap/scratch
            prob_eagle = 0.02 if par >= 4 else 0.0
            prob_birdie = 0.25 if par == 5 else 0.20 if par == 4 else 0.15
            prob_par = 0.65 if par == 4 else 0.60 if par == 3 else 0.70
            prob_bogey = 0.08
            prob_double = 0.02
        elif handicap <= 5:  # Low handicap
            prob_eagle = 0.01 if par == 5 else 0.0
            prob_birdie = 0.15 if par == 5 else 0.12 if par == 4 else 0.08
            prob_par = 0.55 if par == 4 else 0.50 if par == 3 else 0.60
            prob_bogey = 0.25
            prob_double = 0.05
        elif handicap <= 10:  # Mid handicap
            prob_eagle = 0.005 if par == 5 else 0.0
            prob_birdie = 0.08 if par == 5 else 0.06 if par == 4 else 0.03
            prob_par = 0.42 if par == 4 else 0.35 if par == 3 else 0.50
            prob_bogey = 0.35
            prob_double = 0.15
        elif handicap <= 18:  # Higher handicap
            prob_eagle = 0.0
            prob_birdie = 0.03 if par == 5 else 0.02 if par == 4 else 0.01
            prob_par = 0.25 if par == 4 else 0.20 if par == 3 else 0.35
            prob_bogey = 0.42
            prob_double = 0.30
        else:  # High handicap
            prob_eagle = 0.0
            prob_birdie = 0.01
            prob_par = 0.15 if par == 4 else 0.10 if par == 3 else 0.20
            prob_bogey = 0.34
            prob_double = 0.50
        
        # Normalize probabilities and add pressure factor for close games
        total_good = prob_eagle + prob_birdie + prob_par
        pressure_factor = 1.0
        
        # Add late-round pressure
        if hole_number > 15:
            pressure_factor = 0.9  # Slightly more likely to make mistakes
        
        # Adjust for putting distance expectations based on handicap
        putting_factor = 1.0
        if handicap <= 5:
            putting_factor = 1.1  # Better putting
        elif handicap > 15:
            putting_factor = 0.9  # Worse putting
        
        # Apply distance factor - longer holes make good scores harder
        distance_adjustment = 1.0 / distance_factor if distance_factor > 1.0 else distance_factor
        
        # Final probability calculation
        prob_birdie *= pressure_factor * putting_factor * distance_adjustment
        prob_par *= pressure_factor * distance_adjustment
        
        # Longer holes increase chance of bogey/double
        if distance_factor > 1.1:
            prob_bogey *= distance_factor * 0.8
            prob_double *= distance_factor * 0.6
        
        rand = random.random()
        
        if rand < prob_eagle:
            return par - 2
        elif rand < prob_eagle + prob_birdie:
            return par - 1
        elif rand < prob_eagle + prob_birdie + prob_par:
            return par
        elif rand < prob_eagle + prob_birdie + prob_par + prob_bogey:
            return par + 1
        elif rand < prob_eagle + prob_birdie + prob_par + prob_bogey + prob_double:
            return par + 2
        else:
            # Worst case scenarios
            return par + 3 + random.randint(0, 2)
    
    def _generate_educational_feedback(self, game_state: GameState, human_decisions: dict) -> List[str]:
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
        par = game_state.hole_pars[hole_number - 1] if game_state.hole_pars else 4
        stroke_index = game_state.hole_stroke_indexes[hole_number - 1] if game_state.hole_stroke_indexes else 10
        
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
                    alternative_partners = [p for p in game_state.players if p["id"] not in team1 and p["id"] != human_id]
                    if alternative_partners:
                        best_alt = min(alternative_partners, key=lambda p: abs(p["handicap"] - human_handicap))
                        feedback.append(f"💡 {best_alt['name']} (hdcp {best_alt['handicap']:.1f}) might have been a better handicap match")
        
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
        current_base_wager = game_state.base_wager
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
    
    def _assess_hole_difficulty(self, game_state: GameState) -> float:
        """Assess how difficult the current hole is (0=easy, 1=very hard)"""
        if not game_state.hole_stroke_indexes or not game_state.hole_pars:
            return 0.5
        
        hole_idx = game_state.current_hole - 1
        if hole_idx >= len(game_state.hole_stroke_indexes):
            return 0.5
            
        stroke_index = game_state.hole_stroke_indexes[hole_idx]
        par = game_state.hole_pars[hole_idx]
        
        # Lower stroke index = harder hole
        difficulty = (19 - stroke_index) / 18.0
        
        # Factor in distance/yards if available
        if hasattr(game_state, 'hole_yards') and hole_idx < len(game_state.hole_yards):
            yards = game_state.hole_yards[hole_idx]
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
        if not game_state.teams or game_state.teams.get("type") not in ["partners", "solo"]:
            return 0.0
        
        # Get player strokes for current hole
        try:
            strokes = game_state.get_player_strokes()
        except:
            # If no strokes available, return neutral
            return 0.0
        
        hole = game_state.current_hole
        
        if game_state.teams["type"] == "partners":
            # For now, return neutral for partnerships
            return 0.0
        elif game_state.teams["type"] == "solo":
            captain_id = game_state.teams["captain"]
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
        """Get the human player ID (first player that's not a computer)"""
        comp_ids = {cp.player_id for cp in self.computer_players}
        for player in game_state.players:
            if player["id"] not in comp_ids:
                return player["id"]
        return game_state.players[0]["id"]  # Fallback
    
    def _get_current_points(self, player_id: str, game_state: GameState) -> int:
        """Get current points for a player"""
        for player in game_state.players:
            if player["id"] == player_id:
                return player["points"]
        return 0
    
    def _get_player_handicap(self, player_id: str, game_state: GameState) -> float:
        """Get player's handicap from game state"""
        for player in game_state.players:
            if player["id"] == player_id:
                return player["handicap"]
        return 18.0  # Default handicap
    
    def _make_computer_partnership_decision(self, captain_player: ComputerPlayer, game_state: GameState) -> str:
        """Make partnership decision for computer captain"""
        potential_partners = [p for p in game_state.players if p["id"] != captain_player.player_id]
        
        # Simple strategy: pick best handicap player
        best_partner = None
        best_handicap = 50
        
        for partner in potential_partners:
            if partner["handicap"] < best_handicap:
                best_handicap = partner["handicap"]
                best_partner = partner["id"]
        
        # Sometimes go solo based on personality
        if captain_player.personality == "aggressive" and random.random() < 0.3:
            return "solo"
        elif captain_player.personality == "conservative" and random.random() < 0.1:
            return "solo"
        
        return best_partner if best_partner else "solo"
    
    def _get_player_name(self, player_id: str, game_state: GameState) -> str:
        """Get name for a player"""
        for player in game_state.players:
            if player["id"] == player_id:
                return player["name"]
        return "Unknown"
    
    def _get_team_id_for_player(self, game_state: GameState, player_id: str) -> str:
        """Get team ID for a player"""
        if not game_state.teams or game_state.teams.get("type") not in ["partners", "solo"]:
            return "1"
        
        if game_state.teams["type"] == "partners":
            if player_id in game_state.teams["team1"]:
                return "1"
            else:
                return "2"
        else:  # solo
            if player_id == game_state.teams["captain"]:
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
        
        if game_state.teams.get("type") == "partners":
            if target_team_id == "1":
                target_players = game_state.teams["team1"]
            else:
                target_players = game_state.teams["team2"]
        elif game_state.teams.get("type") == "solo":
            if target_team_id == "1":
                target_players = [game_state.teams["captain"]]
            else:
                target_players = game_state.teams["opponents"]
        
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
        """Provide realistic distance control expectations based on handicap"""
        feedback = []
        
        if handicap <= 0:  # Plus handicap/scratch
            if par == 3:
                feedback.append("  - Par 3s: Should hit 80%+ greens, 6-foot putts average")
            elif par == 4:
                feedback.append("  - Par 4s: Hit 70%+ greens in regulation, 12-foot putts average")
            else:  # par 5
                feedback.append("  - Par 5s: Reach in 2 shots 40%+, always in 3, 10-foot putts average")
            feedback.append("  - Putting: Make 90%+ from 3 feet, 50%+ from 6 feet")
            
        elif handicap <= 5:  # Low handicap
            if par == 3:
                feedback.append("  - Par 3s: Should hit 60%+ greens, 10-foot putts average")
            elif par == 4:
                feedback.append("  - Par 4s: Hit 50%+ greens in regulation, 15-foot putts average")
            else:  # par 5
                feedback.append("  - Par 5s: Reach in 2 shots 20%+, usually in 3, 12-foot putts average")
            feedback.append("  - Putting: Make 85%+ from 3 feet, 35%+ from 6 feet")
            
        elif handicap <= 10:  # Mid handicap
            if par == 3:
                feedback.append("  - Par 3s: Should hit 40%+ greens, 15-foot putts average")
            elif par == 4:
                feedback.append("  - Par 4s: Hit 30%+ greens in regulation, 20-foot putts average")
            else:  # par 5
                feedback.append("  - Par 5s: Reach in 2 shots 10%+, usually in 3, 18-foot putts average")
            feedback.append("  - Putting: Make 80%+ from 3 feet, 25%+ from 6 feet")
            
        elif handicap <= 18:  # Higher handicap
            if par == 3:
                feedback.append("  - Par 3s: Should hit 25%+ greens, 20-foot putts average")
            elif par == 4:
                feedback.append("  - Par 4s: Hit 15%+ greens in regulation, 25-foot putts average")
            else:  # par 5
                feedback.append("  - Par 5s: Rarely reach in 2, usually in 4, 25-foot putts average")
            feedback.append("  - Putting: Make 70%+ from 3 feet, 15%+ from 6 feet")
            
        else:  # High handicap
            if par == 3:
                feedback.append("  - Par 3s: Hit 10%+ greens, 30-foot putts average, avoid big misses")
            elif par == 4:
                feedback.append("  - Par 4s: Hit 5%+ greens in regulation, 30-foot putts average")
            else:  # par 5
                feedback.append("  - Par 5s: Focus on reaching in 4-5 shots, 30+ foot putts")
            feedback.append("  - Putting: Make 60%+ from 3 feet, 8%+ from 6 feet")
            
        # Add course management advice based on handicap
        if handicap > 15:
            feedback.append("  - Course Management: Play to fat part of greens, avoid pin hunting")
            feedback.append("  - Strategy: Take what the course gives you, avoid heroic shots")
        elif handicap > 8:
            feedback.append("  - Course Management: Mix conservative and aggressive play based on situation")
            feedback.append("  - Strategy: Attack pins when you have stroke advantage")
        else:
            feedback.append("  - Course Management: You can be aggressive with good distance control")
            feedback.append("  - Strategy: Attack pins regularly, especially on easier holes")
            
        return feedback

    def run_monte_carlo_simulation(self, human_player: dict, computer_configs: List[dict], 
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
                player["id"]: player["points"]
                for player in game_state.players
            }
            
            # Add to results
            results.add_game_result(final_scores)
            
            # Progress callback
            if progress_callback:
                progress_callback(sim_num + 1, num_simulations)
        
        return results
    
    def _generate_monte_carlo_human_decisions(self, game_state: GameState, human_player: dict) -> dict:
        """
        Generate automatic decisions for human player in Monte Carlo simulation
        Uses a balanced strategy similar to computer AI
        """
        captain_id = game_state.captain_id
        # Get current points for human player
        current_points = 0
        for player in game_state.players:
            if player["id"] == human_player["id"]:
                current_points = player["points"]
                break
        
        # Default decisions
        decisions = {
            "action": None,
            "requested_partner": None,
            "offer_double": False,
            "accept_double": False
        }
        
        if captain_id == human_player["id"]:
            # Human is captain - make partnership decision
            
            # Assess potential partners
            potential_partners = [p for p in game_state.players if p["id"] != human_player["id"]]
            
            # Simple strategy: prefer partners with similar or better handicaps
            human_handicap = human_player["handicap"]
            best_partner = None
            best_compatibility = -999
            
            for partner in potential_partners:
                partner_handicap = partner["handicap"]
                partner_points = partner["points"]
                
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
                decisions["requested_partner"] = best_partner["id"]
        
        # Doubling decisions (simplified strategy)
        if not game_state.doubled_status:
            # Offer double if significantly behind or have good advantage
            if current_points < -3 or (current_points > 2 and random.random() < 0.3):
                decisions["offer_double"] = True
        
        # Accept double based on position and hole advantage
        if game_state.doubled_status and not game_state.doubled_status.get("accepted", False):
            team_advantage = self._assess_team_advantage(game_state)
            accept_threshold = 0.4 - (current_points * 0.1)  # More likely to accept when ahead
            
            if team_advantage > 0.2 or random.random() < accept_threshold:
                decisions["accept_double"] = True
        
        return decisions

# Global simulation engine instance
simulation_engine = SimulationEngine()
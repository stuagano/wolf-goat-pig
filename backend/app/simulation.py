import random
import math
from typing import Dict, List, Tuple, Optional
from .game_state import GameState
from .utils import PlayerUtils, GameUtils
from .constants import EXPECTED_YARDS_BY_PAR

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
        
        personality_decisions = {
            "aggressive": current_points < 0 or handicap_diff < 8,
            "conservative": captain_handicap < self.handicap - 3,
            "strategic": self._strategic_partnership_decision(handicap_diff, game_state),
            "balanced": handicap_diff < 6 and random.random() > 0.3
        }
        
        return personality_decisions.get(self.personality, False)
    
    def _strategic_partnership_decision(self, handicap_diff: float, game_state: GameState) -> bool:
        """Strategic decision making for partnerships"""
        hole_difficulty = self._assess_hole_difficulty(game_state)
        current_points = self._get_current_points(game_state)
        return (handicap_diff < 5 and hole_difficulty < 0.7) or current_points < -3
    
    def should_offer_double(self, game_state: GameState) -> bool:
        """Decide whether to offer a double"""
        if game_state.doubled_status:
            return False
            
        current_points = self._get_current_points(game_state)
        hole_advantage = self._assess_team_advantage(game_state)
        
        personality_decisions = {
            "aggressive": hole_advantage > 0.3 or current_points < -2,
            "conservative": hole_advantage > 0.6 and current_points >= 0,
            "strategic": self._strategic_double_decision(hole_advantage, current_points, game_state),
            "balanced": hole_advantage > 0.5 or (current_points < -1 and hole_advantage > 0.2)
        }
        
        return personality_decisions.get(self.personality, False)
    
    def _strategic_double_decision(self, hole_advantage: float, current_points: int, game_state: GameState) -> bool:
        """Strategic decision for offering doubles"""
        return hole_advantage > 0.4 and (current_points < 0 or game_state.current_hole >= 15)
    
    def should_accept_double(self, game_state: GameState) -> bool:
        """Decide whether to accept a double"""
        current_points = self._get_current_points(game_state)
        hole_advantage = self._assess_team_advantage(game_state)
        
        personality_decisions = {
            "aggressive": current_points < 0 or hole_advantage > -0.2,
            "conservative": hole_advantage > 0.2,
            "strategic": self._strategic_double_acceptance(hole_advantage, current_points, game_state),
            "balanced": hole_advantage > -0.1 and random.random() > 0.4
        }
        
        return personality_decisions.get(self.personality, False)
    
    def _strategic_double_acceptance(self, hole_advantage: float, current_points: int, game_state: GameState) -> bool:
        """Strategic decision for accepting doubles"""
        holes_remaining = 18 - game_state.current_hole + 1
        return ((hole_advantage > -0.1 and current_points < -2) or 
                (hole_advantage > 0.1 and holes_remaining > 5))
    
    def should_go_solo(self, game_state: GameState) -> bool:
        """Decide whether to go solo as captain"""
        current_points = self._get_current_points(game_state)
        individual_advantage = self._assess_individual_advantage(game_state)
        
        personality_decisions = {
            "aggressive": individual_advantage > 0.2 or current_points < -4,
            "conservative": individual_advantage > 0.5 and current_points >= -1,
            "strategic": self._strategic_solo_decision(current_points, individual_advantage),
            "balanced": individual_advantage > 0.3 and random.random() > 0.6
        }
        
        return personality_decisions.get(self.personality, False)
    
    def _strategic_solo_decision(self, current_points: int, individual_advantage: float) -> bool:
        """Strategic decision for going solo"""
        return (current_points < -5 and individual_advantage > 0) or individual_advantage > 0.4
    
    def _get_current_points(self, game_state: GameState) -> int:
        """Get current points for this player"""
        player = PlayerUtils.find_player_by_id(game_state.players, self.player_id)
        return player.get("points", 0) if player else 0
    
    def _get_points_for_player(self, handicap: float, game_state: GameState) -> int:
        """Get points for a player with given handicap"""
        for player in game_state.players:
            if abs(player["handicap"] - handicap) < 0.1:
                return player["points"]
        return 0
    
    def _assess_hole_difficulty(self, game_state: GameState) -> float:
        """Assess how difficult the current hole is using utility function"""
        if not game_state.hole_stroke_indexes or not game_state.hole_pars:
            return 0.5
        
        hole_idx = game_state.current_hole - 1
        if hole_idx >= len(game_state.hole_stroke_indexes):
            return 0.5
            
        stroke_index = game_state.hole_stroke_indexes[hole_idx]
        par = game_state.hole_pars[hole_idx]
        yards = game_state.hole_yards[hole_idx] if hasattr(game_state, 'hole_yards') and hole_idx < len(game_state.hole_yards) else None
        
        return GameUtils.assess_hole_difficulty(stroke_index, par, yards, self.handicap)
    
    def _assess_team_advantage(self, game_state: GameState) -> float:
        """Assess team's advantage on current hole (-1 to 1)"""
        if not game_state.teams or game_state.teams.get("type") not in ["partners", "solo"]:
            return 0.0
        
        # Get player strokes for current hole
        strokes = game_state.get_player_strokes()
        hole = game_state.current_hole
        
        if game_state.teams["type"] == "partners":
            return self._assess_partnership_advantage(game_state, strokes, hole)
        elif game_state.teams["type"] == "solo":
            return self._assess_solo_advantage(game_state, strokes, hole)
        
        return 0.0
    
    def _assess_partnership_advantage(self, game_state: GameState, strokes: Dict, hole: int) -> float:
        """Assess advantage in partnership scenario"""
        team1 = game_state.teams["team1"]
        team2 = game_state.teams["team2"]
        
        # Check if we're on team1 or team2
        our_team = team1 if self.player_id in team1 else team2
        their_team = team2 if self.player_id in team1 else team1
        
        # Calculate net stroke advantage
        our_strokes = min(strokes[pid][hole] for pid in our_team)
        their_strokes = min(strokes[pid][hole] for pid in their_team)
        
        # Get handicaps for team advantage calculation
        our_handicaps = [PlayerUtils.get_player_handicap(game_state.players, pid) for pid in our_team]
        their_handicaps = [PlayerUtils.get_player_handicap(game_state.players, pid) for pid in their_team]
        
        return GameUtils.calculate_stroke_advantage(our_handicaps, their_handicaps, [our_strokes], [their_strokes])
    
    def _assess_solo_advantage(self, game_state: GameState, strokes: Dict, hole: int) -> float:
        """Assess advantage in solo scenario"""
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
        
    def setup_simulation(self, human_player: dict, computer_configs: List[dict]) -> GameState:
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
        
        # Setup game state with all players using utility function
        from .utils import SimulationUtils
        all_players = SimulationUtils.setup_all_players(human_player, computer_configs)
        
        game_state = GameState()
        game_state.setup_players(all_players)
        
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
        
        # Phase 4: Calculate results
        game_state.dispatch_action("calculate_hole_points", {})
        
        educational_feedback = self._generate_educational_feedback(game_state, human_decisions)
        feedback.extend(educational_feedback)
        
        return game_state, feedback

    def run_monte_carlo_simulation(self, human_player: dict, computer_configs: List[dict], 
                                   num_simulations: int = 100, course_name: Optional[str] = None) -> MonteCarloResults:
        """Run Monte Carlo simulation with specified number of games"""
        results = MonteCarloResults()
        
        for sim_num in range(num_simulations):
            # Setup a fresh game for each simulation
            game_state = self.setup_simulation(human_player, computer_configs)
            
            # Set course if provided
            if course_name and course_name in game_state.courses:
                course = game_state.courses[course_name]
                game_state.selected_course = course_name
                game_state.hole_stroke_indexes = [h["stroke_index"] for h in course]
                game_state.hole_pars = [h["par"] for h in course]
            
            # Simulate all 18 holes
            for hole in range(1, 19):
                game_state.current_hole = hole
                
                # Generate automatic decisions for human player
                human_decisions = self._generate_monte_carlo_human_decisions(game_state, human_player)
                
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
        
        return results

    def _get_computer_player(self, player_id: str) -> Optional[ComputerPlayer]:
        """Get computer player by ID"""
        for cp in self.computer_players:
            if cp.player_id == player_id:
                return cp
        return None

    def _get_player_handicap(self, player_id: str, game_state: GameState) -> float:
        """Get player handicap by ID"""
        return PlayerUtils.get_player_handicap(game_state.players, player_id)

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
            handicap_diff = abs(captain.handicap - potential_partner.handicap)
            team_strength = (captain.handicap + potential_partner.handicap) / 2
            
            # Prefer partners with complementary handicaps
            score = 1.0 - (handicap_diff / 25.0) + (25 - team_strength) / 50.0
            
            if score > best_score and random.random() > 0.3:
                best_score = score
                best_partner = potential_partner
        
        return best_partner.player_id if best_partner else None

    def _simulate_doubling_phase(self, game_state: GameState, human_decisions: dict) -> List[str]:
        """Simulate the doubling/betting phase"""
        feedback = []
        
        # Check if human wants to offer double
        if human_decisions.get("offer_double") and not game_state.doubled_status:
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
        """Simulate golf shots for all players"""
        feedback = []
        hole_par = game_state.hole_pars[game_state.current_hole - 1] if game_state.hole_pars else 4
        
        for player in game_state.players:
            player_id = player["id"]
            handicap = player["handicap"]
            
            # Get net strokes for this hole
            strokes = game_state.get_player_strokes()
            net_strokes = strokes[player_id][game_state.current_hole]
            
            # Simulate score based on handicap and hole difficulty
            gross_score = self._simulate_player_score(handicap, hole_par, game_state.current_hole, game_state)
            net_score = max(1, gross_score - net_strokes)
            
            game_state.hole_scores[player_id] = net_score
            
            feedback.append(f"{player['name']}: {gross_score} gross, {net_score} net")
        
        return feedback

    def _simulate_player_score(self, handicap: float, par: int, hole_number: int, game_state: GameState) -> int:
        """Simulate a player's gross score on a hole"""
        # Basic simulation based on handicap and hole difficulty
        difficulty_factor = game_state.get_hole_difficulty_factor(hole_number)
        
        # Expected score relative to par
        expected_over_par = (handicap / 18) * difficulty_factor
        
        # Add randomness
        variance = 1.5 + (handicap * 0.05)  # Higher handicaps have more variance
        actual_over_par = random.normalvariate(expected_over_par, variance)
        
        # Calculate gross score
        gross_score = max(1, int(par + actual_over_par + 0.5))  # Round to nearest int, min 1
        
        return gross_score

    def _generate_educational_feedback(self, game_state: GameState, human_decisions: dict) -> List[str]:
        """Generate educational feedback about the hole"""
        feedback = []
        
        # Add basic strategy tips based on game state
        if game_state.teams.get("type") == "solo":
            feedback.append("💡 Solo Strategy: You need to beat the best ball of 3 players - play aggressively!")
        elif game_state.teams.get("type") == "partners":
            feedback.append("💡 Partnership Strategy: Play to your strengths and let your partner cover weaknesses")
        
        return feedback

    def _generate_monte_carlo_human_decisions(self, game_state: GameState, human_player: dict) -> dict:
        """Generate automatic decisions for human player in Monte Carlo simulation"""
        captain_id = game_state.captain_id
        current_points = 0
        
        # Get current points for human player
        for player in game_state.players:
            if player["id"] == human_player["id"]:
                current_points = player["points"]
                break
        
        decisions = {
            "action": None,
            "requested_partner": None,
            "offer_double": False,
            "accept_double": False
        }
        
        if captain_id == human_player["id"]:
            # Human is captain - make partnership decision
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
            go_solo_threshold = 0.3 + (current_points * 0.1)
            
            if (random.random() < go_solo_threshold and current_points < 2):
                decisions["action"] = "go_solo"
            elif best_partner:
                decisions["requested_partner"] = best_partner["id"]
        
        # Doubling decisions
        if not game_state.doubled_status:
            if current_points < -3 or (current_points > 2 and random.random() < 0.3):
                decisions["offer_double"] = True
        
        # Accept double based on position
        if game_state.doubled_status:
            accept_threshold = 0.4 - (current_points * 0.1)
            if random.random() < accept_threshold:
                decisions["accept_double"] = True
        
        return decisions

    def _get_human_player_id(self, game_state: GameState) -> str:
        """Get the human player ID (assumes first non-computer player)"""
        computer_ids = [cp.player_id for cp in self.computer_players]
        for player in game_state.players:
            if player["id"] not in computer_ids:
                return player["id"]
        return game_state.players[0]["id"]  # Fallback

    def _get_team_id_for_player(self, game_state: GameState, player_id: str) -> str:
        """Get team ID for a given player"""
        if game_state.teams.get("type") == "partners":
            if player_id in game_state.teams.get("team1", []):
                return "team1"
            elif player_id in game_state.teams.get("team2", []):
                return "team2"
        elif game_state.teams.get("type") == "solo":
            if player_id == game_state.teams.get("captain"):
                return "solo"
            else:
                return "opponents"
        return "unknown"

    def _get_opposing_team_id(self, game_state: GameState, player_id: str) -> str:
        """Get opposing team ID for a given player"""
        our_team = self._get_team_id_for_player(game_state, player_id)
        if our_team == "team1":
            return "team2"
        elif our_team == "team2":
            return "team1"
        elif our_team == "solo":
            return "opponents"
        elif our_team == "opponents":
            return "solo"
        return "unknown"

    def _get_computer_double_response(self, game_state: GameState, target_team: str) -> str:
        """Get computer response to a double offer"""
        # Find a computer player on the target team
        for cp in self.computer_players:
            if self._get_team_id_for_player(game_state, cp.player_id) == target_team:
                return "accept" if cp.should_accept_double(game_state) else "decline"
        return "decline"

# Global simulation engine instance
simulation_engine = SimulationEngine()
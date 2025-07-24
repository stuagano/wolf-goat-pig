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
    
    def _simulate_tee_shots(self, game_state: GameState) -> List[str]:
        """Simulate tee shots for all players and report drive distance, accuracy, and remaining to green."""
        feedback = []
        hole_idx = game_state.current_hole - 1
        par = game_state.hole_pars[hole_idx] if game_state.hole_pars else 4
        yards = game_state.hole_yards[hole_idx] if hasattr(game_state, 'hole_yards') and game_state.hole_yards else 400
        tee_shot_results = {}
        for player in game_state.players:
            player_id = player["id"]
            handicap = player["handicap"]
            # Simulate drive distance based on handicap
            if handicap <= 5:
                drive = int(random.gauss(265, 12))
            elif handicap <= 12:
                drive = int(random.gauss(245, 15))
            elif handicap <= 20:
                drive = int(random.gauss(225, 18))
            else:
                drive = int(random.gauss(200, 20))
            drive = max(100, min(drive, yards - 30))
            # Simulate accuracy
            shot_quality = random.choices(
                ["excellent", "good", "average", "poor", "terrible"],
                weights=[0.12, 0.38, 0.32, 0.15, 0.03], k=1
            )[0]
            if shot_quality == "excellent":
                lie = "fairway"
                penalty = 0
            elif shot_quality == "good":
                lie = random.choice(["fairway", "first cut"])
                penalty = 0
            elif shot_quality == "average":
                lie = random.choice(["fairway", "rough"])
                penalty = 0
            elif shot_quality == "poor":
                lie = random.choice(["rough", "bunker"])
                penalty = 0
            else:
                lie = random.choice(["trees", "hazard", "deep rough"])
                penalty = random.randint(1, 2)
            remaining = max(30, yards - drive + penalty * 20)
            tee_shot_results[player_id] = {
                "drive": drive,
                "lie": lie,
                "remaining": remaining,
                "shot_quality": shot_quality
            }
            player_name = player["name"]
            feedback.append(f"{player_name}: {drive} yards, {lie}, {remaining} yards to green (tee shot: {shot_quality})")
        # Optionally, store tee_shot_results in game_state for later phases
        game_state.tee_shot_results = tee_shot_results
        return feedback

    def simulate_hole(self, game_state: GameState, human_decisions: dict) -> Tuple[GameState, List[str], dict]:
        """Simulate a complete hole chronologically - shot by shot, decision by decision"""
        feedback = []
        interaction_needed = None

        # Show hole setup
        feedback.append(f"\n🏌️ **Hole {game_state.current_hole} Setup**")
        captain_name = next(p["name"] for p in game_state.players if p["id"] == game_state.captain_id)
        hitting_order_names = [next(p["name"] for p in game_state.players if p["id"] == pid) for pid in game_state.hitting_order]
        feedback.append(f"👑 **Captain:** {captain_name}")
        feedback.append(f"🎯 **Hitting Order:** {' → '.join(hitting_order_names)}")
        
        # Show hole details
        hole_idx = game_state.current_hole - 1
        par = game_state.hole_pars[hole_idx] if game_state.hole_pars else 4
        yards = game_state.hole_yards[hole_idx] if hasattr(game_state, 'hole_yards') and game_state.hole_yards else 400
        stroke_index = game_state.hole_stroke_indexes[hole_idx] if game_state.hole_stroke_indexes else 10
        description = game_state.hole_descriptions[hole_idx] if hasattr(game_state, 'hole_descriptions') and game_state.hole_descriptions else ""
        
        feedback.append(f"📊 **Hole Info:** Par {par}, {yards} yards, Stroke Index {stroke_index}")
        if description:
            feedback.append(f"📝 **Description:** {description}")
        feedback.append("")

        # Phase 1: Progressive tee shots with immediate captain decisions
        feedback.append("🏌️ **TEE SHOTS**")
        hitting_order = game_state.hitting_order or [p["id"] for p in game_state.players]
        captain_id = game_state.captain_id
        
        # Initialize tee shot tracking
        if not hasattr(game_state, 'tee_shot_results'):
            game_state.tee_shot_results = {}
        if not hasattr(game_state, 'current_tee_shot_index'):
            game_state.current_tee_shot_index = 0
            
        tee_shot_results = game_state.tee_shot_results
        current_index = game_state.current_tee_shot_index
        
        # Process tee shots one by one, allowing captain decisions after each
        while current_index < len(hitting_order):
            player_id = hitting_order[current_index]
            player = next(p for p in game_state.players if p["id"] == player_id)
            player_name = player["name"]
            
            # If this player hasn't hit yet, simulate their tee shot
            if player_id not in tee_shot_results:
                tee_result = self._simulate_individual_tee_shot(player, game_state)
                tee_shot_results[player_id] = tee_result
                
                # Show the tee shot result
                drive_distance = tee_result['drive']
                lie_description = tee_result['lie']
                remaining = tee_result['remaining']
                shot_quality = tee_result['shot_quality']
                
                shot_desc = self._create_shot_description(drive_distance, lie_description, shot_quality, remaining, par)
                
                if player_id == self._get_human_player_id(game_state):
                    feedback.append(f"🧑 **{player_name}:** {shot_desc}")
                else:
                    feedback.append(f"💻 **{player_name}:** {shot_desc}")
                
                # Add reactions from other players after good/bad shots
                if shot_quality in ["excellent", "terrible"]:
                    reaction = self._generate_shot_reaction(shot_quality, player_name, current_index == 0)
                    if reaction:
                        feedback.append(f"   💬 {reaction}")
                feedback.append("")
                
                # NOW CHECK IF CAPTAIN WANTS TO MAKE A DECISION
                # Captain can only decide after seeing at least one non-captain shot
                if current_index > 0 and (not hasattr(game_state, 'teams') or not game_state.teams):
                    # Captain evaluates this shot for potential partnership
                    if captain_id in [cp.player_id for cp in self.computer_players]:
                        # Computer captain decides immediately after each shot
                        captain_decision = self._evaluate_shot_for_partnership(
                            captain_id, player_id, tee_result, game_state, current_index
                        )
                        
                        if captain_decision == "request_partner":
                            captain_name = next(p["name"] for p in game_state.players if p["id"] == captain_id)
                            game_state.dispatch_action("request_partner", {
                                "captain_id": captain_id,
                                "partner_id": player_id
                            })
                            feedback.append(f"💻 **{captain_name}:** \"Great shot {player_name}! Want to be partners?\"")
                            
                            # Handle partner response immediately
                            if player_id == self._get_human_player_id(game_state):
                                # Human player - need decision
                                interaction_needed = {
                                    "type": "partnership_response",
                                    "message": f"{captain_name} saw your {shot_quality} shot and wants you as a partner!",
                                    "captain_name": captain_name,
                                    "partner_id": player_id,
                                    "shot_context": f"Your shot: {shot_desc}"
                                }
                                game_state.current_tee_shot_index = current_index + 1
                                return game_state, feedback, interaction_needed
                            else:
                                # Computer player responds
                                partner_player = self._get_computer_player(player_id)
                                captain_player = self._get_computer_player(captain_id)
                                accept = partner_player.should_accept_partnership(captain_player.handicap, game_state)
                                if accept:
                                    game_state.dispatch_action("accept_partner", {"partner_id": player_id})
                                    feedback.append(f"💻 **{player_name}:** \"Absolutely! Let's team up!\"")
                                    break  # Partnership formed, stop taking more tee shots
                                else:
                                    game_state.dispatch_action("decline_partner", {"partner_id": player_id})
                                    feedback.append(f"💻 **{player_name}:** \"Thanks, but I'll pass. Keep looking!\"")
                        elif captain_decision == "go_solo" and current_index == len(hitting_order) - 1:
                            # Captain decides to go solo after seeing all shots
                            captain_name = next(p["name"] for p in game_state.players if p["id"] == captain_id)
                            game_state.dispatch_action("go_solo", {"captain_id": captain_id})
                            feedback.append(f"💻 **{captain_name}:** \"I've seen enough. Going solo!\"")
                            break
                    else:
                        # Human captain - check if they've made a decision or need to make one
                        if "action" in human_decisions:
                            # Process human captain's mid-tee decision
                            if human_decisions.get("action") == "request_partner":
                                partner_id = human_decisions.get("requested_partner", player_id)
                                partner_name = next(p["name"] for p in game_state.players if p["id"] == partner_id)
                                game_state.dispatch_action("request_partner", {
                                    "captain_id": captain_id,
                                    "partner_id": partner_id
                                })
                                feedback.append(f"🧑 **You:** \"{partner_name}, want to be my partner?\"")
                                
                                # Computer partner responds immediately
                                if partner_id in [cp.player_id for cp in self.computer_players]:
                                    partner_player = self._get_computer_player(partner_id)
                                    human_handicap = self._get_player_handicap(captain_id, game_state)
                                    accept = partner_player.should_accept_partnership(human_handicap, game_state)
                                    if accept:
                                        game_state.dispatch_action("accept_partner", {"partner_id": partner_id})
                                        feedback.append(f"💻 **{partner_name}:** \"Absolutely! Let's do this.\"")
                                        break  # Partnership formed, stop taking more tee shots
                                    else:
                                        game_state.dispatch_action("decline_partner", {"partner_id": partner_id})
                                        feedback.append(f"💻 **{partner_name}:** \"Thanks, but I think I'll pass. Keep looking!\"")
                                else:
                                    # Human partner - need separate interaction
                                    interaction_needed = {
                                        "type": "partnership_response",
                                        "message": f"You asked {partner_name} to be your partner. They need to respond.",
                                        "captain_name": "You",
                                        "partner_id": partner_id,
                                        "shot_context": f"Partnership request after: {shot_desc}"
                                    }
                                    game_state.current_tee_shot_index = current_index + 1
                                    return game_state, feedback, interaction_needed
                            elif human_decisions.get("action") == "go_solo":
                                captain_name = next(p["name"] for p in game_state.players if p["id"] == captain_id)
                                game_state.dispatch_action("go_solo", {"captain_id": captain_id})
                                feedback.append(f"🧑 **You:** \"I'm going solo!\"")
                                break
                            elif human_decisions.get("action") == "keep_watching":
                                # Continue to next player
                                pass
                        else:
                            # Offer decision after each shot (if shot was good enough)
                            if shot_quality in ["excellent", "good"] and player_id != captain_id:
                                others_remaining = [p for p in game_state.players 
                                                 if p["id"] != captain_id and p["id"] not in tee_shot_results]
                                
                                interaction_needed = {
                                    "type": "captain_decision_mid_tee",
                                    "message": f"{player_name} just hit a {shot_quality} shot! Do you want to ask them to be your partner, or keep watching?",
                                    "shot_context": f"{player_name}: {shot_desc}",
                                    "options": [
                                        {"action": "request_partner", "partner_id": player_id, "partner_name": player_name},
                                        {"action": "keep_watching", "remaining_players": len(others_remaining)}
                                    ],
                                    "can_go_solo": current_index == len(hitting_order) - 1
                                }
                                game_state.current_tee_shot_index = current_index + 1
                                return game_state, feedback, interaction_needed
            
            current_index += 1
            game_state.current_tee_shot_index = current_index
            
            # Break if teams are formed
            if hasattr(game_state, 'teams') and game_state.teams:
                break

        # Phase 2: Final captain decision (if no partnership formed during tee shots)
        captain_id = game_state.captain_id
        captain_name = next(p["name"] for p in game_state.players if p["id"] == captain_id)
        
        # Check if teams are already formed during tee shots
        if not hasattr(game_state, 'teams') or not game_state.teams:
            feedback.append("🤝 **CAPTAIN'S DECISION**")
            
            # Show captain's position after their tee shot
            captain_result = tee_shot_results[captain_id]
            feedback.append(f"👑 **{captain_name}** (Captain) analyzes the situation:")
            feedback.append(f"   • Your shot: {captain_result['drive']} yards, {captain_result['lie']}, {captain_result['remaining']} to pin")
            
            # Show other players' positions for captain's consideration
            others = [pid for pid in hitting_order if pid != captain_id]
            feedback.append("   • Other players:")
            for pid in others:
                p_name = next(p["name"] for p in game_state.players if p["id"] == pid)
                result = tee_shot_results[pid]
                feedback.append(f"     - {p_name}: {result['drive']} yards, {result['lie']}, {result['remaining']} to pin")
            feedback.append("")
            
            if captain_id in [cp.player_id for cp in self.computer_players]:
                # Computer captain makes decision
                captain_player = self._get_computer_player(captain_id)
                partnership_decision = self._make_computer_partnership_decision(captain_player, game_state)
                
                if partnership_decision == "solo":
                    game_state.dispatch_action("go_solo", {"captain_id": captain_id})
                    feedback.append(f"💻 **{captain_name}:** \"I'm going solo! I like my chances.\"")
                elif partnership_decision:
                    partner_name = next(p["name"] for p in game_state.players if p["id"] == partnership_decision)
                    game_state.dispatch_action("request_partner", {
                        "captain_id": captain_id,
                        "partner_id": partnership_decision
                    })
                    feedback.append(f"💻 **{captain_name}:** \"{partner_name}, want to be my partner?\"")
                    
                    # Partner responds immediately
                    if partnership_decision in [cp.player_id for cp in self.computer_players]:
                        partner_player = self._get_computer_player(partnership_decision)
                        accept = partner_player.should_accept_partnership(captain_player.handicap, game_state)
                        if accept:
                            game_state.dispatch_action("accept_partner", {"partner_id": partnership_decision})
                            feedback.append(f"💻 **{partner_name}:** \"Yes! Let's team up.\"")
                        else:
                            game_state.dispatch_action("decline_partner", {"partner_id": partnership_decision})
                            feedback.append(f"💻 **{partner_name}:** \"Sorry, I'm going to pass. You're solo {captain_name}!\"")
                    else:
                        # Human partner - need decision
                        if "accept_partnership" in human_decisions:
                            if human_decisions.get("accept_partnership", False):
                                game_state.dispatch_action("accept_partner", {"partner_id": partnership_decision})
                                feedback.append(f"🧑 **You:** \"Yes, let's be partners!\"")
                            else:
                                game_state.dispatch_action("decline_partner", {"partner_id": partnership_decision})
                                feedback.append(f"🧑 **You:** \"I'm going to pass. You're solo {captain_name}!\"")
                        else:
                            # Need human decision
                            interaction_needed = {
                                "type": "partnership_response",
                                "message": f"{captain_name} wants you as a partner. Do you accept?",
                                "captain_name": captain_name,
                                "partner_id": partnership_decision
                            }
                            return game_state, feedback, interaction_needed
                else:
                    feedback.append(f"💻 **{captain_name}:** \"I can't find a good partner... going solo.\"")
                    game_state.dispatch_action("go_solo", {"captain_id": captain_id})
            else:
                # Human captain makes decision
                if "action" in human_decisions:
                    if human_decisions.get("action") == "go_solo":
                        game_state.dispatch_action("go_solo", {"captain_id": captain_id})
                        feedback.append(f"🧑 **You:** \"I'm going solo!\"")
                    elif human_decisions.get("requested_partner"):
                        partner_id = human_decisions["requested_partner"]
                        partner_name = next(p["name"] for p in game_state.players if p["id"] == partner_id)
                        game_state.dispatch_action("request_partner", {
                            "captain_id": captain_id,
                            "partner_id": partner_id
                        })
                        feedback.append(f"🧑 **You:** \"{partner_name}, want to be my partner?\"")
                        
                        # Computer partner responds
                        if partner_id in [cp.player_id for cp in self.computer_players]:
                            partner_player = self._get_computer_player(partner_id)
                            human_handicap = self._get_player_handicap(captain_id, game_state)
                            accept = partner_player.should_accept_partnership(human_handicap, game_state)
                            if accept:
                                game_state.dispatch_action("accept_partner", {"partner_id": partner_id})
                                feedback.append(f"💻 **{partner_name}:** \"Absolutely! Let's do this.\"")
                            else:
                                game_state.dispatch_action("decline_partner", {"partner_id": partner_id})
                                feedback.append(f"💻 **{partner_name}:** \"Thanks, but I think I'll pass. You're going solo!\"")
                        else:
                            feedback.append(f"🧑 **You:** \"I need to think... going solo by default.\"")
                            game_state.dispatch_action("go_solo", {"captain_id": captain_id})
                    else:
                        # Need human captain decision
                        others = [p for p in game_state.players if p["id"] != captain_id]
                        interaction_needed = {
                            "type": "captain_decision",
                            "message": "You're the captain! Choose your strategy:",
                            "options": others,
                            "tee_results": tee_shot_results
                        }
                        return game_state, feedback, interaction_needed
                
                feedback.append("")
                
        # Teams formation complete
        feedback.append("🤝 **TEAMS FORMED**")
        feedback.append("")

        # Continue with rest of hole only if teams are formed
        if hasattr(game_state, 'teams') and game_state.teams:
            # Phase 3: Approach shots and hole completion
            feedback.append("⛳ **COMPLETING THE HOLE**")
            shot_feedback = self._simulate_remaining_shots_chronological(game_state, tee_shot_results)
            feedback.extend(shot_feedback)

            # Phase 4: Doubling phase
            feedback.append("💰 **BETTING OPPORTUNITY**")
            doubling_feedback, doubling_interaction = self._simulate_doubling_phase_chronological(game_state, human_decisions)
            if doubling_interaction:
                # Human betting decision needed
                feedback.extend(doubling_feedback)
                return game_state, feedback, doubling_interaction
            elif doubling_feedback:
                feedback.extend(doubling_feedback)
            else:
                feedback.append("No additional betting this hole.")
            feedback.append("")

            # Phase 5: Set up teams and calculate results
            game_state.dispatch_action("calculate_hole_points", {})

            # Phase 6: Hole summary and learning
            hole_summary = self._generate_hole_summary(game_state)
            feedback.extend(hole_summary)

            # Advance to next hole
            if game_state.current_hole < 18:
                game_state.dispatch_action("next_hole", {})
                next_captain_name = next(p["name"] for p in game_state.players if p["id"] == game_state.captain_id)
                feedback.append(f"\n🔄 **Moving to Hole {game_state.current_hole}** - {next_captain_name} will be captain")
        else:
            # Debug: Teams not formed properly
            feedback.append(f"⚠️ **DEBUG:** Teams not formed. hasattr: {hasattr(game_state, 'teams')}, teams: {getattr(game_state, 'teams', 'MISSING')}")

        return game_state, feedback, None

    def _simulate_individual_tee_shot(self, player: dict, game_state: GameState) -> dict:
        """Simulate tee shot for a single player"""
        player_id = player["id"]
        handicap = player["handicap"]
        
        hole_idx = game_state.current_hole - 1
        par = game_state.hole_pars[hole_idx] if game_state.hole_pars else 4
        yards = game_state.hole_yards[hole_idx] if hasattr(game_state, 'hole_yards') and game_state.hole_yards else 400
        
        # Simulate drive distance based on handicap
        if handicap <= 5:
            drive = int(random.gauss(265, 12))
        elif handicap <= 12:
            drive = int(random.gauss(245, 15))
        elif handicap <= 20:
            drive = int(random.gauss(225, 18))
        else:
            drive = int(random.gauss(200, 20))
        drive = max(100, min(drive, yards - 30))
        
        # Simulate accuracy
        shot_quality = random.choices(
            ["excellent", "good", "average", "poor", "terrible"],
            weights=[0.12, 0.38, 0.32, 0.15, 0.03], k=1
        )[0]
        
        if shot_quality == "excellent":
            lie = "fairway"
            penalty = 0
        elif shot_quality == "good":
            lie = random.choice(["fairway", "first cut"])
            penalty = 0
        elif shot_quality == "average":
            lie = random.choice(["fairway", "rough"])
            penalty = 0
        elif shot_quality == "poor":
            lie = random.choice(["rough", "bunker"])
            penalty = 0
        else:
            lie = random.choice(["trees", "hazard", "deep rough"])
            penalty = random.randint(1, 2)
        
        remaining = max(30, yards - drive + penalty * 20)
        
        return {
            "drive": drive,
            "lie": lie,
            "remaining": remaining,
            "shot_quality": shot_quality,
            "penalty": penalty
        }

    def _simulate_remaining_shots(self, game_state: GameState, tee_shot_results: dict) -> List[str]:
        """Simulate the remaining shots after tee shots to complete the hole"""
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
            
            # Use tee shot result to influence final score
            tee_result = tee_shot_results.get(player_id, {})
            tee_quality = tee_result.get("shot_quality", "average")
            remaining_distance = tee_result.get("remaining", 150)
            
            # Simulate remaining shots and final score
            gross_score = self._simulate_player_final_score(handicap, hole_par, game_state.current_hole, game_state, tee_quality, remaining_distance)
            net_score = max(1, gross_score - net_strokes)  # Can't go below 1
            
            scores[player_id] = int(net_score)
            shot_details[player_id] = {
                "gross": gross_score,
                "net": net_score,
                "strokes_received": net_strokes,
                "tee_quality": tee_quality
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
                feedback.append(f"🧑 **Your final score:** {details['gross']} gross, {details['net']} net (received {details['strokes_received']} strokes)")
            else:
                feedback.append(f"💻 **{player['name']}:** {details['gross']} gross, {details['net']} net (received {details['strokes_received']} strokes)")
        
        return feedback

    def _simulate_remaining_shots_chronological(self, game_state: GameState, tee_shot_results: dict) -> List[str]:
        """Simulate the remaining shots after tee shots to complete the hole"""
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
            
            # Use tee shot result to influence final score
            tee_result = tee_shot_results.get(player_id, {})
            tee_quality = tee_result.get("shot_quality", "average")
            remaining_distance = tee_result.get("remaining", 150)
            
            # Simulate remaining shots and final score
            gross_score = self._simulate_player_final_score(handicap, hole_par, game_state.current_hole, game_state, tee_quality, remaining_distance)
            net_score = max(1, gross_score - net_strokes)  # Can't go below 1
            
            scores[player_id] = int(net_score)
            shot_details[player_id] = {
                "gross": gross_score,
                "net": net_score,
                "strokes_received": net_strokes,
                "tee_quality": tee_quality
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
                feedback.append(f"🧑 **Your final score:** {details['gross']} gross, {details['net']} net (received {details['strokes_received']} strokes)")
            else:
                feedback.append(f"💻 **{player['name']}:** {details['gross']} gross, {details['net']} net (received {details['strokes_received']} strokes)")
        
        return feedback

    def _simulate_player_final_score(self, handicap: float, par: int, hole_number: int, game_state: 'GameState' = None, tee_quality: str = "average", remaining_distance: float = 150) -> int:
        """Simulate final score considering tee shot quality and remaining distance"""
        base_score = self._simulate_player_score(handicap, par, hole_number, game_state)
        
        # Adjust based on tee shot quality
        if tee_quality == "excellent":
            adjustment = -0.3  # Excellent tee shot helps
        elif tee_quality == "good":
            adjustment = -0.1
        elif tee_quality == "average":
            adjustment = 0
        elif tee_quality == "poor":
            adjustment = 0.2
        else:  # terrible
            adjustment = 0.5
        
        # Adjust based on remaining distance (longer = harder)
        if remaining_distance > 200:
            adjustment += 0.3
        elif remaining_distance > 150:
            adjustment += 0.1
        elif remaining_distance < 100:
            adjustment -= 0.1
        
        # Apply adjustment with some randomness
        if random.random() < abs(adjustment):
            if adjustment > 0:
                base_score += 1
            else:
                base_score = max(1, base_score - 1)
        
        return base_score

    def _evaluate_shot_for_partnership(self, captain_id: str, shot_player_id: str, 
                                      tee_result: dict, game_state: GameState, shot_index: int) -> str:
        """Evaluate if captain should make partnership decision after seeing this shot"""
        if captain_id == shot_player_id:
            return "continue"  # Captain doesn't partner with themselves
        
        shot_quality = tee_result['shot_quality']
        captain_player = self._get_computer_player(captain_id)
        
        # Aggressive personalities act faster on good shots
        if captain_player.personality == "aggressive":
            if shot_quality == "excellent":
                return "request_partner"
            elif shot_quality == "good" and shot_index >= 2:
                return "request_partner"
        
        # Conservative personalities wait to see more shots
        elif captain_player.personality == "conservative":
            if shot_quality == "excellent" and shot_index >= 2:
                return "request_partner"
            elif shot_index == 3:  # Last shot, decide now
                if shot_quality in ["excellent", "good"]:
                    return "request_partner"
                else:
                    return "go_solo"
        
        # Strategic personalities consider handicap compatibility
        elif captain_player.personality == "strategic":
            shot_player = next(p for p in game_state.players if p["id"] == shot_player_id)
            handicap_diff = abs(captain_player.handicap - shot_player["handicap"])
            
            if shot_quality == "excellent":
                return "request_partner"
            elif shot_quality == "good" and handicap_diff <= 5:
                return "request_partner"
            elif shot_index == 3 and shot_quality in ["good", "average"]:
                return "request_partner" if handicap_diff <= 8 else "go_solo"
        
        # Balanced personalities use moderate criteria
        else:  # balanced
            if shot_quality == "excellent":
                return "request_partner"
            elif shot_quality == "good" and shot_index >= 1:
                return "request_partner" 
            elif shot_index == 3:
                return "go_solo" if shot_quality in ["poor", "terrible"] else "request_partner"
        
        return "continue"  # Keep watching

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
    
    def _simulate_doubling_phase_chronological(self, game_state: GameState, human_decisions: dict) -> Tuple[List[str], dict]:
        """Simulate the doubling/betting phase - INTERACTIVE for human training"""
        feedback = []
        interaction_needed = None
        
        # First check if human should be given opportunity to offer double
        if not game_state.doubled_status:
            human_id = self._get_human_player_id(game_state)
            
            # If human hasn't made their double decision yet, prompt them
            if "offer_double" not in human_decisions:
                # Give human the opportunity to offer a double
                current_position = self._get_current_points(human_id, game_state)
                team_advantage = self._assess_team_advantage(game_state)
                
                interaction_needed = {
                    "type": "doubling_decision",
                    "message": "Do you want to offer a double to increase the stakes?",
                    "current_wager": game_state.base_wager,
                    "doubled_wager": game_state.base_wager * 2,
                    "current_position": current_position,
                    "team_advantage": team_advantage,
                    "context": "You can offer to double the stakes before the hole is scored."
                }
                return feedback, interaction_needed
        
        # Process human double offer if provided
        if human_decisions.get("offer_double") and not game_state.doubled_status:
            human_id = self._get_human_player_id(game_state)
            target_team = self._get_opposing_team_id(game_state, human_id)
            game_state.dispatch_action("offer_double", {
                "offering_team_id": self._get_team_id_for_player(game_state, human_id),
                "target_team_id": target_team
            })
            
            feedback.append("🧑 **You:** \"I'd like to double the stakes!\"")
            
            # Computer response to double
            computer_response = self._get_computer_double_response(game_state, target_team)
            if computer_response == "accept":
                game_state.dispatch_action("accept_double", {"team_id": target_team})
                feedback.append("💻 **Computer team:** \"We accept your double! Stakes doubled!\"")
            else:
                game_state.dispatch_action("decline_double", {"team_id": target_team})
                feedback.append("💻 **Computer team:** \"We decline - you win the hole at current stakes!\"")
        
        # Check if computer wants to offer double (only if human didn't offer)
        elif not game_state.doubled_status and not human_decisions.get("offer_double", False):
            for comp_player in self.computer_players:
                if comp_player.should_offer_double(game_state):
                    offering_team = self._get_team_id_for_player(game_state, comp_player.player_id)
                    target_team = self._get_opposing_team_id(game_state, comp_player.player_id)
                    
                    game_state.dispatch_action("offer_double", {
                        "offering_team_id": offering_team,
                        "target_team_id": target_team
                    })
                    
                    feedback.append(f"💻 **{comp_player.name}:** \"We'd like to double your team!\"")
                    
                    # Human needs to respond to computer double offer
                    if "accept_double" not in human_decisions:
                        current_position = self._get_current_points(self._get_human_player_id(game_state), game_state)
                        team_advantage = self._assess_team_advantage(game_state)
                        
                        interaction_needed = {
                            "type": "double_response",
                            "message": f"{comp_player.name} wants to double the stakes! Do you accept?",
                            "offering_player": comp_player.name,
                            "current_wager": game_state.base_wager,
                            "doubled_wager": game_state.base_wager * 2,
                            "current_position": current_position,
                            "team_advantage": team_advantage,
                            "context": "If you decline, they win the hole at current stakes. If you accept, stakes double for everyone."
                        }
                        return feedback, interaction_needed
                    
                    # Process human response to computer double
                    if human_decisions.get("accept_double", False):
                        game_state.dispatch_action("accept_double", {"team_id": target_team})
                        feedback.append("🧑 **You:** \"We accept the double! Stakes doubled!\"")
                    else:
                        game_state.dispatch_action("decline_double", {"team_id": target_team})
                        feedback.append("🧑 **You:** \"We decline the double - you win at current stakes.\"")
                    break
        
        # If no doubling happened, show neutral message
        if not feedback:
            feedback.append("No doubling this hole - continuing with current stakes.")
        
        return feedback, interaction_needed
    
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
        """Get current points for a specific player"""
        for player in game_state.players:
            if player["id"] == player_id:
                return player["points"]
        return 0
    
    def _get_player_handicap(self, player_id: str, game_state: GameState) -> float:
        """Get handicap for a player"""
        for player in game_state.players:
            if player["id"] == player_id:
                return player["handicap"]
        return 18.0
    
    def _get_player_name(self, player_id: str, game_state: GameState) -> str:
        """Get name for a player"""
        for player in game_state.players:
            if player["id"] == player_id:
                return player["name"]
        return player_id
    
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
        par = game_state.hole_pars[hole_number - 1] if game_state.hole_pars else 4
        stroke_index = game_state.hole_stroke_indexes[hole_number - 1] if game_state.hole_stroke_indexes else 10
        
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
                    alternative_partners = [p for p in game_state.players if p["id"] not in team1 and p["id"] != human_id]
                    if alternative_partners:
                        best_alt = min(alternative_partners, key=lambda p: abs(p["handicap"] - human_handicap))
                        feedback.append(f"💡 {best_alt['name']} (hdcp {best_alt['handicap']:.1f}) might have been a better handicap match.")
        
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
        current_base_wager = game_state.base_wager
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
    
    def get_next_shot_event(self, game_state: GameState) -> Optional[dict]:
        """Determine what the next shot event should be"""
        # Initialize shot tracking if needed
        if not hasattr(game_state, 'shot_sequence'):
            game_state.shot_sequence = {
                "phase": "tee_shots",
                "current_player_index": 0,
                "completed_shots": [],
                "pending_decisions": []
            }
        
        shot_seq = game_state.shot_sequence
        hitting_order = game_state.hitting_order or [p["id"] for p in game_state.players]
        
        if shot_seq["phase"] == "tee_shots":
            if shot_seq["current_player_index"] < len(hitting_order):
                player_id = hitting_order[shot_seq["current_player_index"]]
                player = next(p for p in game_state.players if p["id"] == player_id)
                
                return {
                    "type": "tee_shot",
                    "player": player,
                    "hole_info": self._get_hole_info(game_state),
                    "shot_number": shot_seq["current_player_index"] + 1,
                    "total_players": len(hitting_order)
                }
        
        elif shot_seq["phase"] == "approach_shots":
            # Handle approach shots for team members
            if hasattr(game_state, 'teams') and game_state.teams:
                # Logic for approach shots based on teams
                return self._get_next_approach_shot(game_state)
        
        return None
    
    def execute_shot_event(self, game_state: GameState, shot_event: dict) -> Tuple[GameState, dict, dict]:
        """Execute a shot event and return result with probabilities"""
        if shot_event["type"] == "tee_shot":
            return self._execute_tee_shot_event(game_state, shot_event)
        elif shot_event["type"] == "approach_shot":
            return self._execute_approach_shot_event(game_state, shot_event)
        else:
            raise ValueError(f"Unknown shot event type: {shot_event['type']}")
    
    def _execute_tee_shot_event(self, game_state: GameState, shot_event: dict) -> Tuple[GameState, dict, dict]:
        """Execute a tee shot with detailed probabilities"""
        player = shot_event["player"]
        
        # Calculate pre-shot probabilities
        pre_shot_probs = self._calculate_tee_shot_probabilities(player, game_state)
        
        # Execute the actual shot
        shot_result = self._simulate_individual_tee_shot(player, game_state)
        
        # Calculate post-shot probabilities and outcomes
        post_shot_probs = self._calculate_post_shot_probabilities(shot_result, game_state)
        
        # Update shot sequence
        game_state.shot_sequence["completed_shots"].append({
            "player_id": player["id"],
            "shot_result": shot_result,
            "probabilities": pre_shot_probs
        })
        game_state.shot_sequence["current_player_index"] += 1
        
        # Create enhanced shot result
        enhanced_result = {
            **shot_result,
            "player": player,
            "shot_description": self._create_detailed_shot_description(shot_result, player, game_state),
            "reactions": self._generate_shot_reactions(shot_result, player, game_state)
        }
        
        # Combine probability information
        probabilities = {
            "pre_shot": pre_shot_probs,
            "outcome": post_shot_probs,
            "betting_implications": self._calculate_betting_implications(shot_result, game_state)
        }
        
        return game_state, enhanced_result, probabilities
    
    def _calculate_tee_shot_probabilities(self, player: dict, game_state: GameState) -> dict:
        """Calculate detailed probabilities for a tee shot"""
        handicap = player["handicap"]
        hole_info = self._get_hole_info(game_state)
        
        # Base probabilities based on handicap and hole difficulty
        base_excellent = max(0.05, 0.25 - (handicap * 0.01))
        base_good = max(0.15, 0.35 - (handicap * 0.008))
        base_average = 0.35
        base_poor = max(0.10, 0.15 + (handicap * 0.005))
        base_terrible = max(0.05, 0.10 + (handicap * 0.003))
        
        # Adjust for hole difficulty
        stroke_index = hole_info.get("stroke_index", 10)
        difficulty_factor = (19 - stroke_index) / 18.0  # 1.0 = hardest, 0.055 = easiest
        
        # Harder holes reduce excellent/good, increase poor/terrible
        excellent = base_excellent * (1 - difficulty_factor * 0.3)
        good = base_good * (1 - difficulty_factor * 0.2)
        average = base_average
        poor = base_poor * (1 + difficulty_factor * 0.4)
        terrible = base_terrible * (1 + difficulty_factor * 0.6)
        
        # Normalize to 100%
        total = excellent + good + average + poor + terrible
        
        return {
            "excellent": round(excellent / total * 100, 1),
            "good": round(good / total * 100, 1),
            "average": round(average / total * 100, 1),
            "poor": round(poor / total * 100, 1),
            "terrible": round(terrible / total * 100, 1),
            "expected_distance": self._calculate_expected_distance(handicap, hole_info),
            "handicap_factor": f"Handicap {handicap}: {'Low' if handicap <= 5 else 'Mid' if handicap <= 15 else 'High'} skill level",
            "hole_difficulty": f"Stroke Index {stroke_index}: {'Hard' if stroke_index <= 6 else 'Medium' if stroke_index <= 12 else 'Easy'} hole"
        }
    
    def _calculate_post_shot_probabilities(self, shot_result: dict, game_state: GameState) -> dict:
        """Calculate probabilities and implications after a shot"""
        shot_quality = shot_result["shot_quality"]
        remaining = shot_result["remaining"]
        lie = shot_result["lie"]
        
        # Calculate scoring probabilities from this position
        scoring_probs = self._calculate_scoring_probabilities(remaining, lie, game_state)
        
        # Calculate partnership value
        partnership_value = self._calculate_partnership_value(shot_result, game_state)
        
        return {
            "scoring_probabilities": scoring_probs,
            "partnership_value": partnership_value,
            "position_quality": self._assess_position_quality(shot_result),
            "strategic_implications": self._get_strategic_implications(shot_result, game_state)
        }
    
    def _calculate_scoring_probabilities(self, remaining_yards: int, lie: str, game_state: GameState) -> dict:
        """Calculate probability of different scores from current position"""
        par = self._get_hole_info(game_state).get("par", 4)
        
        # Base probabilities by distance and lie
        if remaining_yards <= 100:
            if lie == "fairway":
                birdie, par_score, bogey, double_bogey = 0.15, 0.55, 0.25, 0.05
            elif lie in ["first cut", "rough"]:
                birdie, par_score, bogey, double_bogey = 0.08, 0.45, 0.35, 0.12
            else:  # bunker, trees, hazard
                birdie, par_score, bogey, double_bogey = 0.02, 0.25, 0.45, 0.28
        elif remaining_yards <= 150:
            if lie == "fairway":
                birdie, par_score, bogey, double_bogey = 0.10, 0.45, 0.35, 0.10
            elif lie in ["first cut", "rough"]:
                birdie, par_score, bogey, double_bogey = 0.05, 0.35, 0.45, 0.15
            else:
                birdie, par_score, bogey, double_bogey = 0.01, 0.20, 0.50, 0.29
        else:  # > 150 yards
            if lie == "fairway":
                birdie, par_score, bogey, double_bogey = 0.05, 0.35, 0.45, 0.15
            elif lie in ["first cut", "rough"]:
                birdie, par_score, bogey, double_bogey = 0.02, 0.25, 0.50, 0.23
            else:
                birdie, par_score, bogey, double_bogey = 0.01, 0.15, 0.55, 0.29
        
        return {
            "birdie": round(birdie * 100, 1),
            "par": round(par_score * 100, 1),
            "bogey": round(bogey * 100, 1),
            "double_bogey_or_worse": round(double_bogey * 100, 1),
            "expected_score": round(par - birdie + bogey + 2*double_bogey, 2)
        }
    
    def check_betting_opportunity(self, game_state: GameState, shot_result: dict) -> Optional[dict]:
        """Check if there's a betting opportunity after this shot"""
        captain_id = game_state.captain_id
        shot_player_id = shot_result["player"]["id"]
        shot_quality = shot_result["shot_quality"]
        
        # Only offer betting opportunities for human captain or after good shots
        if captain_id == self._get_human_player_id(game_state):
            if shot_quality in ["excellent", "good"] and shot_player_id != captain_id:
                return {
                    "type": "partnership_opportunity",
                    "target_player": shot_result["player"],
                    "shot_context": shot_result,
                    "betting_probabilities": self._calculate_betting_probabilities(game_state, {
                        "action": "request_partner",
                        "partner_id": shot_player_id
                    })
                }
        
        return None
    
    def calculate_betting_probabilities(self, game_state: GameState, decision: dict) -> dict:
        """Calculate probabilities for betting decisions"""
        if decision.get("action") == "request_partner":
            return self._calculate_partnership_probabilities(game_state, decision)
        elif decision.get("action") == "go_solo":
            return self._calculate_solo_probabilities(game_state)
        else:
            return {}
    
    def _calculate_partnership_probabilities(self, game_state: GameState, decision: dict) -> dict:
        """Calculate success probabilities for partnership strategy"""
        captain_id = game_state.captain_id
        partner_id = decision.get("partner_id")
        
        if not partner_id:
            return {}
        
        captain = next(p for p in game_state.players if p["id"] == captain_id)
        partner = next(p for p in game_state.players if p["id"] == partner_id)
        
        # Calculate team strength
        avg_handicap = (captain["handicap"] + partner["handicap"]) / 2
        handicap_synergy = 1.0 - abs(captain["handicap"] - partner["handicap"]) * 0.02
        
        # Base win probability against other team
        base_win_prob = 0.5  # Start with 50/50
        
        # Adjust for team skill level
        if avg_handicap <= 8:
            base_win_prob += 0.15
        elif avg_handicap <= 15:
            base_win_prob += 0.05
        else:
            base_win_prob -= 0.05
        
        # Adjust for handicap compatibility
        base_win_prob += (handicap_synergy - 1.0) * 0.2
        
        # Hole difficulty factor
        hole_info = self._get_hole_info(game_state)
        stroke_index = hole_info.get("stroke_index", 10)
        if stroke_index <= 6:  # Hard hole
            base_win_prob -= 0.05
        elif stroke_index >= 14:  # Easy hole
            base_win_prob += 0.05
        
        return {
            "win_probability": round(min(0.85, max(0.15, base_win_prob)) * 100, 1),
            "team_strength": round(avg_handicap, 1),
            "handicap_compatibility": round(handicap_synergy * 100, 1),
            "expected_points": round((base_win_prob * 2 - (1 - base_win_prob) * 2), 2),
            "risk_level": "Low" if base_win_prob > 0.6 else "Medium" if base_win_prob > 0.4 else "High"
        }
    
    def _calculate_solo_probabilities(self, game_state: GameState) -> dict:
        """Calculate success probabilities for going solo"""
        captain_id = game_state.captain_id
        captain = next(p for p in game_state.players if p["id"] == captain_id)
        
        # Base solo win probability (1 vs 3 is harder)
        base_win_prob = 0.25  # 25% base chance
        
        # Adjust for captain skill
        if captain["handicap"] <= 5:
            base_win_prob += 0.15
        elif captain["handicap"] <= 10:
            base_win_prob += 0.05
        elif captain["handicap"] >= 20:
            base_win_prob -= 0.10
        
        # Hole difficulty factor
        hole_info = self._get_hole_info(game_state)
        stroke_index = hole_info.get("stroke_index", 10)
        if stroke_index <= 6:  # Hard hole - bad for solo
            base_win_prob -= 0.10
        elif stroke_index >= 14:  # Easy hole - better for solo
            base_win_prob += 0.10
        
        return {
            "win_probability": round(min(0.70, max(0.05, base_win_prob)) * 100, 1),
            "expected_points": round((base_win_prob * 6 - (1 - base_win_prob) * 6), 2),
            "risk_level": "Very High",
            "handicap_advantage": f"Handicap {captain['handicap']}: {'Strong' if captain['handicap'] <= 10 else 'Moderate' if captain['handicap'] <= 18 else 'Challenging'} solo player"
        }
    
    def has_next_shot(self, game_state: GameState) -> bool:
        """Check if there are more shots available in current phase"""
        if not hasattr(game_state, 'shot_sequence'):
            return True
        
        shot_seq = game_state.shot_sequence
        hitting_order = game_state.hitting_order or [p["id"] for p in game_state.players]
        
        if shot_seq["phase"] == "tee_shots":
            return shot_seq["current_player_index"] < len(hitting_order)
        
        return False
    
    def get_current_shot_state(self, game_state: GameState) -> dict:
        """Get comprehensive information about current shot state"""
        if not hasattr(game_state, 'shot_sequence'):
            return {"phase": "ready_to_start", "shots_remaining": 4}
        
        shot_seq = game_state.shot_sequence
        hitting_order = game_state.hitting_order or [p["id"] for p in game_state.players]
        
        return {
            "phase": shot_seq["phase"],
            "current_player_index": shot_seq["current_player_index"],
            "shots_completed": len(shot_seq["completed_shots"]),
            "shots_remaining": len(hitting_order) - shot_seq["current_player_index"],
            "completed_shots": shot_seq["completed_shots"],
            "next_player": hitting_order[shot_seq["current_player_index"]] if shot_seq["current_player_index"] < len(hitting_order) else None,
            "captain_id": game_state.captain_id,
            "teams_formed": hasattr(game_state, 'teams') and bool(game_state.teams)
        }
    
    def _get_hole_info(self, game_state: GameState) -> dict:
        """Get current hole information"""
        hole_idx = game_state.current_hole - 1
        return {
            "hole_number": game_state.current_hole,
            "par": game_state.hole_pars[hole_idx] if game_state.hole_pars else 4,
            "yards": game_state.hole_yards[hole_idx] if hasattr(game_state, 'hole_yards') and game_state.hole_yards else 400,
            "stroke_index": game_state.hole_stroke_indexes[hole_idx] if game_state.hole_stroke_indexes else 10,
            "description": game_state.hole_descriptions[hole_idx] if hasattr(game_state, 'hole_descriptions') and game_state.hole_descriptions else ""
        }
    
    def _calculate_expected_distance(self, handicap: float, hole_info: dict) -> dict:
        """Calculate expected drive distance based on handicap"""
        # Base driving distance decreases with higher handicap
        base_distance = 260 - (handicap * 4)  # Scratch golfer ~260, 20 handicap ~180
        
        # Add some variance
        min_distance = int(base_distance * 0.8)
        max_distance = int(base_distance * 1.2)
        
        return {
            "expected": int(base_distance),
            "range": f"{min_distance}-{max_distance} yards",
            "percentile_25": int(base_distance * 0.9),
            "percentile_75": int(base_distance * 1.1)
        }

    def _calculate_partnership_value(self, shot_result: dict, game_state: GameState) -> dict:
        """Calculate the strategic value of partnering with this player"""
        shot_quality = shot_result["shot_quality"]
        remaining = shot_result["remaining"]
        
        # Base value from shot quality
        if shot_quality == "excellent":
            base_value = 85
        elif shot_quality == "good":
            base_value = 70
        elif shot_quality == "average":
            base_value = 50
        elif shot_quality == "poor":
            base_value = 30
        else:  # terrible
            base_value = 15
        
        # Adjust for position
        if remaining <= 100:
            position_bonus = 15
        elif remaining <= 150:
            position_bonus = 10
        else:
            position_bonus = 0
        
        return {
            "partnership_appeal": min(100, base_value + position_bonus),
            "reason": f"{shot_quality} shot, {remaining} yards remaining",
            "strategic_value": "High" if base_value >= 70 else "Medium" if base_value >= 50 else "Low"
        }
    
    def _assess_position_quality(self, shot_result: dict) -> dict:
        """Assess the quality of the current position"""
        lie = shot_result["lie"]
        remaining = shot_result["remaining"]
        
        # Scoring positions
        if lie == "fairway":
            if remaining <= 100:
                quality = "Excellent - Short iron to green"
                score = 90
            elif remaining <= 150:
                quality = "Good - Mid iron opportunity"
                score = 75
            else:
                quality = "Fair - Long approach needed"
                score = 60
        elif lie in ["first cut", "rough"]:
            if remaining <= 120:
                quality = "Good - Manageable from rough"
                score = 65
            else:
                quality = "Challenging - Long shot from rough"
                score = 45
        else:  # bunker, trees, hazard
            quality = "Difficult - Recovery shot needed"
            score = 25
        
        return {
            "quality_score": score,
            "description": quality,
            "lie_type": lie,
            "distance_category": "Short" if remaining <= 100 else "Medium" if remaining <= 150 else "Long"
        }
    
    def _get_strategic_implications(self, shot_result: dict, game_state: GameState) -> list:
        """Get strategic implications and advice"""
        implications = []
        shot_quality = shot_result["shot_quality"]
        remaining = shot_result["remaining"]
        lie = shot_result["lie"]
        
        # Shot quality implications
        if shot_quality == "excellent":
            implications.append("🎯 This player is in excellent position - strong partnership candidate")
        elif shot_quality == "terrible":
            implications.append("⚠️ Poor position - consider other partnership options")
        
        # Distance implications
        if remaining <= 100:
            implications.append("🎯 Short approach shot - high birdie/par probability")
        elif remaining > 200:
            implications.append("📏 Long approach required - more challenging scoring")
        
        # Lie implications
        if lie == "fairway":
            implications.append("✅ Perfect lie - clean contact expected")
        elif lie in ["trees", "hazard"]:
            implications.append("🌲 Trouble lie - recovery shot needed")
        
        # Betting implications
        captain_id = game_state.captain_id
        if shot_result["player"]["id"] != captain_id:
            if shot_quality in ["excellent", "good"]:
                implications.append("💰 Good betting opportunity - consider partnership")
            else:
                implications.append("🤔 Wait for better partnership opportunity")
        
        return implications
    
    def _calculate_betting_implications(self, shot_result: dict, game_state: GameState) -> dict:
        """Calculate betting implications and recommendations"""
        shot_quality = shot_result["shot_quality"]
        player_id = shot_result["player"]["id"]
        captain_id = game_state.captain_id
        
        if player_id == captain_id:
            return {
                "recommendation": "N/A - Captain's own shot",
                "partnership_appeal": 0,
                "action": "continue"
            }
        
        # Calculate partnership appeal
        if shot_quality == "excellent":
            appeal = 90
            recommendation = "Strong partnership candidate - excellent position"
            action = "consider_partnership"
        elif shot_quality == "good":
            appeal = 75
            recommendation = "Good partnership option - solid position"
            action = "consider_partnership"
        elif shot_quality == "average":
            appeal = 50
            recommendation = "Moderate option - wait for better shots"
            action = "keep_watching"
        else:
            appeal = 25
            recommendation = "Poor position - look for other partners"
            action = "keep_watching"
        
        return {
            "partnership_appeal": appeal,
            "recommendation": recommendation,
            "action": action,
            "shot_quality_factor": shot_quality
        }
    
    def _create_detailed_shot_description(self, shot_result: dict, player: dict, game_state: GameState) -> str:
        """Create detailed, realistic shot description"""
        drive = shot_result["drive"]
        lie = shot_result["lie"]
        remaining = shot_result["remaining"]
        quality = shot_result["shot_quality"]
        
        # Player identifier
        player_icon = "🧑" if player["id"] == self._get_human_player_id(game_state) else "💻"
        
        # Quality descriptors
        quality_desc = {
            "excellent": "striped it",
            "good": "hit a solid drive",
            "average": "found the fairway",
            "poor": "struggled off the tee",
            "terrible": "got into trouble"
        }
        
        # Lie descriptors
        lie_desc = {
            "fairway": "sitting pretty in the fairway",
            "first cut": "in the first cut of rough",
            "rough": "nestled in the rough",
            "bunker": "caught the fairway bunker",
            "trees": "behind some trees",
            "hazard": "near the hazard",
            "deep rough": "buried in thick rough"
        }
        
        base_desc = f"{player_icon} **{player['name']}** {quality_desc.get(quality, 'hit their drive')} {drive} yards, {lie_desc.get(lie, f'in the {lie}')}, leaving {remaining} yards to the pin."
        
        # Add quality-specific reactions
        if quality == "excellent":
            base_desc += " 🎯 What a shot!"
        elif quality == "terrible":
            base_desc += " 😬 That's not what they were looking for."
        
        return base_desc
    
    def _generate_shot_reactions(self, shot_result: dict, player: dict, game_state: GameState) -> list:
        """Generate realistic reactions from other players"""
        reactions = []
        quality = shot_result["shot_quality"]
        
        if quality == "excellent":
            reactions.append("💬 \"Wow, great shot!\"")
            reactions.append("💬 \"That's how you do it!\"")
        elif quality == "terrible":
            reactions.append("💬 \"Ouch, tough break.\"")
            reactions.append("💬 \"Happens to the best of us.\"")
        
        return reactions
    
    def execute_betting_decision(self, game_state: GameState, decision: dict, betting_probs: dict) -> Tuple[GameState, dict]:
        """Execute a betting decision with probability context"""
        if decision.get("action") == "request_partner":
            partner_id = decision.get("partner_id")
            captain_id = game_state.captain_id
            
            # Execute partnership request
            game_state.dispatch_action("request_partner", {
                "captain_id": captain_id,
                "partner_id": partner_id
            })
            
            # Check if partner accepts (for computer players)
            if partner_id in [cp.player_id for cp in self.computer_players]:
                partner_player = self._get_computer_player(partner_id)
                captain_player = self._get_computer_player(captain_id) if captain_id in [cp.player_id for cp in self.computer_players] else None
                
                if captain_player:
                    accept = partner_player.should_accept_partnership(captain_player.handicap, game_state)
                else:
                    # Human captain
                    human_handicap = next(p["handicap"] for p in game_state.players if p["id"] == captain_id)
                    accept = partner_player.should_accept_partnership(human_handicap, game_state)
                
                if accept:
                    game_state.dispatch_action("accept_partner", {"partner_id": partner_id})
                    result_message = f"Partnership formed! {betting_probs.get('win_probability', 'Unknown')}% win probability."
                else:
                    game_state.dispatch_action("decline_partner", {"partner_id": partner_id})
                    result_message = "Partnership declined. Captain going solo by default."
            else:
                result_message = "Partnership request sent to human player."
            
            return game_state, {"message": result_message, "action_taken": "partnership_request"}
        
        elif decision.get("action") == "go_solo":
            captain_id = game_state.captain_id
            game_state.dispatch_action("go_solo", {"captain_id": captain_id})
            
            win_prob = betting_probs.get('win_probability', 'Unknown')
            return game_state, {
                "message": f"Going solo! {win_prob}% win probability vs. field.",
                "action_taken": "go_solo"
            }
        
        return game_state, {"message": "No action taken", "action_taken": "none"}

# Global simulation engine instance
simulation_engine = SimulationEngine()
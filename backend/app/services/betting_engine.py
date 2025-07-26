import random
from typing import List, Dict, Any, Optional, Tuple
from ..game_state import GameState
from ..domain.player import Player
from ..domain.shot_result import ShotResult
from .probability_calculator import ProbabilityCalculator

class BettingEngine:
    @staticmethod
    def check_betting_opportunity(game_state: GameState, shot_result: ShotResult, computer_players: List) -> Optional[dict]:
        """Check if there's a betting opportunity after this shot"""
        captain_id = game_state.player_manager.captain_id
        shot_player_id = shot_result.player.id
        shot_quality = shot_result.shot_quality
        
        # Only offer betting opportunities for human captain or after good shots
        if captain_id == BettingEngine._get_human_player_id(game_state):
            if shot_quality in ["excellent", "good"] and shot_player_id != captain_id:
                return {
                    "type": "partnership_opportunity",
                    "target_player": shot_result.player,
                    "shot_context": shot_result,
                    "betting_probabilities": ProbabilityCalculator.calculate_betting_probabilities(game_state, {
                        "action": "request_partner",
                        "partner_id": shot_player_id
                    })
                }
        
        return None

    @staticmethod
    def execute_betting_decision(game_state: GameState, decision: dict, betting_probs: dict, computer_players: List) -> Tuple[GameState, dict]:
        """Execute a betting decision with probability context"""
        if decision.get("action") == "request_partner":
            partner_id = decision.get("partner_id")
            captain_id = game_state.player_manager.captain_id
            
            # Execute partnership request
            game_state.dispatch_action("request_partner", {
                "captain_id": captain_id,
                "partner_id": partner_id
            })
            
            # Check if partner accepts (for computer players)
            if partner_id in [cp.player_id for cp in computer_players]:
                partner_player = BettingEngine._get_computer_player(partner_id, computer_players)
                captain_player = BettingEngine._get_computer_player(captain_id, computer_players) if captain_id in [cp.player_id for cp in computer_players] else None
                
                if captain_player:
                    accept = partner_player.should_accept_partnership(captain_player.handicap, game_state)
                else:
                    # Human captain
                    human_handicap = next(p.handicap for p in game_state.player_manager.players if p.id == captain_id)
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
            captain_id = game_state.player_manager.captain_id
            game_state.dispatch_action("go_solo", {"captain_id": captain_id})
            
            win_prob = betting_probs.get('win_probability', 'Unknown')
            return game_state, {
                "message": f"Going solo! {win_prob}% win probability vs. field.",
                "action_taken": "go_solo"
            }
        
        return game_state, {"message": "No action taken", "action_taken": "none"}

    @staticmethod
    def make_computer_partnership_decision(captain, game_state: GameState, computer_players: List) -> Optional[str]:
        """Computer captain decides on partnership"""
        other_players = [cp for cp in computer_players if cp.player_id != captain.player_id]
        
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

    @staticmethod
    def evaluate_shot_for_partnership(captain_id: str, shot_player_id: str, 
                                    tee_result: ShotResult, game_state: GameState, shot_index: int, computer_players: List) -> str:
        """Evaluate if captain should make partnership decision after seeing this shot"""
        if captain_id == shot_player_id:
            return "continue"  # Captain doesn't partner with themselves
        
        shot_quality = tee_result.shot_quality
        captain_player = BettingEngine._get_computer_player(captain_id, computer_players)
        
        # If captain is human (not in computer_players), return continue to let human decide
        if captain_player is None:
            return "continue"  # Human captain makes decisions interactively
        
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
            shot_player = next(p for p in game_state.player_manager.players if p.id == shot_player_id)
            handicap_diff = abs(captain_player.handicap - shot_player.handicap)
            
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

    @staticmethod
    def simulate_doubling_phase_chronological(game_state: GameState, human_decisions: dict, computer_players: List) -> Tuple[List[str], dict]:
        """Simulate the doubling/betting phase - INTERACTIVE for human training"""
        feedback = []
        interaction_needed = None
        
        # First check if human should be given opportunity to offer double
        if not game_state.betting_state.doubled_status:
            human_id = BettingEngine._get_human_player_id(game_state)
            
            # If human hasn't made their double decision yet, prompt them
            if "offer_double" not in human_decisions:
                # Give human the opportunity to offer a double
                current_position = BettingEngine._get_current_points(human_id, game_state)
                team_advantage = BettingEngine._assess_team_advantage(game_state)
                
                interaction_needed = {
                    "type": "doubling_decision",
                    "message": "Do you want to offer a double to increase the stakes?",
                    "current_wager": game_state.betting_state.base_wager,
                    "doubled_wager": game_state.betting_state.base_wager * 2,
                    "current_position": current_position,
                    "team_advantage": team_advantage,
                    "context": "You can offer to double the stakes before the hole is scored."
                }
                return feedback, interaction_needed
        
        # Process human double offer if provided
        if human_decisions.get("offer_double") and not game_state.betting_state.doubled_status:
            human_id = BettingEngine._get_human_player_id(game_state)
            target_team = BettingEngine._get_opposing_team_id(game_state, human_id)
            game_state.dispatch_action("offer_double", {
                "offering_team_id": BettingEngine._get_team_id_for_player(game_state, human_id),
                "target_team_id": target_team
            })
            
            feedback.append("🧑 **You:** \"I'd like to double the stakes!\"")
            
            # Computer response to double
            computer_response = BettingEngine._get_computer_double_response(game_state, target_team, computer_players)
            if computer_response == "accept":
                game_state.dispatch_action("accept_double", {"team_id": target_team})
                feedback.append("💻 **Computer team:** \"We accept your double! Stakes doubled!\"")
            else:
                game_state.dispatch_action("decline_double", {"team_id": target_team})
                feedback.append("💻 **Computer team:** \"We decline - you win the hole at current stakes!\"")
        
        # Check if computer wants to offer double (only if human didn't offer)
        elif not game_state.betting_state.doubled_status and not human_decisions.get("offer_double", False):
            for comp_player in computer_players:
                if comp_player.should_offer_double(game_state):
                    # Computer offers double
                    human_id = BettingEngine._get_human_player_id(game_state)
                    target_team = BettingEngine._get_team_id_for_player(game_state, human_id)
                    
                    game_state.dispatch_action("offer_double", {
                        "offering_team_id": BettingEngine._get_opposing_team_id(game_state, human_id),
                        "target_team_id": target_team
                    })
                    
                    comp_name = comp_player.name
                    feedback.append(f"💻 **{comp_name}:** \"I'd like to double the stakes!\"")
                    
                    # Human response to double
                    if "accept_double" in human_decisions:
                        if human_decisions.get("accept_double", False):
                            game_state.dispatch_action("accept_double", {"team_id": target_team})
                            feedback.append("🧑 **You:** \"I accept the double! Stakes doubled!\"")
                        else:
                            game_state.dispatch_action("decline_double", {"team_id": target_team})
                            feedback.append("🧑 **You:** \"I decline - you win the hole at current stakes!\"")
                    else:
                        # Need human decision
                        interaction_needed = {
                            "type": "double_response",
                            "message": f"{comp_name} wants to double the stakes. Do you accept?",
                            "offering_player": comp_name,
                            "current_wager": game_state.betting_state.base_wager,
                            "doubled_wager": game_state.betting_state.base_wager * 2
                        }
                        return feedback, interaction_needed
                    break
        
        return feedback, interaction_needed

    # --- Helper methods ---
    @staticmethod
    def _get_computer_player(player_id: str, computer_players: List):
        """Get computer player by ID"""
        for cp in computer_players:
            if cp.player_id == player_id:
                return cp
        return None

    @staticmethod
    def _get_human_player_id(game_state: GameState) -> str:
        """Get the human player ID consistently using GameState utility"""
        return game_state.get_human_player_id()

    @staticmethod
    def _get_current_points(player_id: str, game_state: GameState) -> int:
        """Get current points for a player"""
        return game_state.get_player_points().get(player_id, 0)

    @staticmethod
    def _assess_team_advantage(game_state: GameState) -> float:
        """Assess team advantage for betting decisions"""
        # Simple team advantage calculation
        if not hasattr(game_state, 'betting_state') or not game_state.betting_state.teams:
            return 0.0
        
        # Calculate average handicaps for each team
        team1_handicaps = []
        team2_handicaps = []
        
        for player in game_state.player_manager.players:
            # Always work with Player objects
            player_id = player.id
            player_handicap = player.handicap
            
            if player_id in game_state.betting_state.teams.get("team1", []):
                team1_handicaps.append(player_handicap)
            elif player_id in game_state.betting_state.teams.get("team2", []):
                team2_handicaps.append(player_handicap)
        
        if not team1_handicaps or not team2_handicaps:
            return 0.0
        
        avg_team1 = sum(team1_handicaps) / len(team1_handicaps)
        avg_team2 = sum(team2_handicaps) / len(team2_handicaps)
        
        # Lower handicap = better, so team1 advantage is (team2_avg - team1_avg)
        return avg_team2 - avg_team1

    @staticmethod
    def _get_team_id_for_player(game_state: GameState, player_id: str) -> str:
        """Get team ID for a player"""
        if not hasattr(game_state, 'betting_state') or not game_state.betting_state.teams:
            return "no_team"
        
        if player_id in game_state.betting_state.teams.get("team1", []):
            return "team1"
        elif player_id in game_state.betting_state.teams.get("team2", []):
            return "team2"
        else:
            return "no_team"

    @staticmethod
    def _get_opposing_team_id(game_state: GameState, player_id: str) -> str:
        """Get opposing team ID for a player"""
        player_team = BettingEngine._get_team_id_for_player(game_state, player_id)
        if player_team == "team1":
            return "team2"
        elif player_team == "team2":
            return "team1"
        else:
            return "no_team"

    @staticmethod
    def _get_computer_double_response(game_state: GameState, target_team_id: str, computer_players: List) -> str:
        """Get computer response to double offer"""
        # Find computer players on the target team
        team_players = []
        if target_team_id == "team1":
            team_players = game_state.betting_state.teams.get("team1", [])
        elif target_team_id == "team2":
            team_players = game_state.betting_state.teams.get("team2", [])
        
        # Get computer players on this team
        comp_team_players = [cp for cp in computer_players if cp.player_id in team_players]
        
        if not comp_team_players:
            return "decline"  # No computer players on team
        
        # Check if any computer player wants to accept
        for comp_player in comp_team_players:
            if comp_player.should_accept_double(game_state):
                return "accept"
        
        return "decline" 
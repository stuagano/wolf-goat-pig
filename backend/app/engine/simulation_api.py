"""Simulation-mode API for WolfGoatPigGame — human/computer decisions and shot simulation."""

import random
from typing import Any

from ..domain.game_types import Player, TeamFormation


class SimulationMixin:
    """Simulation-mode flows: human action wrappers, AI decision heuristics, shot simulation."""

    def human_requests_partner(self, human_player_id: str, partner_id: str) -> dict[str, Any]:
        """
        Human requests a specific player as partner (simulating "rolling the dice")
        """
        hole_state = self.hole_states[self.current_hole]

        # Check if partner is still eligible
        if not self._is_player_eligible_for_partnership(partner_id, hole_state):
            return {
                "status": "error",
                "message": f"{self._get_player_name(partner_id)} is no longer eligible for partnership",
            }

        # Check if partner is computer or human
        partner = next(p for p in self.players if p.id == partner_id)

        if partner_id in self.computer_players:
            # Computer partner - simulate their decision
            computer_player = self.computer_players[partner_id]
            accept = computer_player.should_accept_partnership(
                next(p for p in self.players if p.id == human_player_id),
                self.get_game_state(),
            )

            if accept:
                # Computer accepts partnership
                result = self._accept_partnership(human_player_id, partner_id, hole_state)
                result["computer_response"] = f"{partner.name} accepts your partnership request!"
                return result
            # Computer declines - human goes solo
            result = self._decline_partnership(human_player_id, partner_id, hole_state)
            result["computer_response"] = f"{partner.name} declines your partnership request."
            return result
        # Human partner - create pending request
        hole_state.teams.pending_request = {
            "type": "partnership",
            "captain": human_player_id,
            "requested": partner_id,
        }

        return {
            "status": "partnership_request_pending",
            "message": f"Partnership request sent to {partner.name}. Waiting for response...",
            "pending_request": hole_state.teams.pending_request,
            "hole_state": self._get_comprehensive_hole_state(),
        }

    def human_goes_solo(self, human_player_id: str, use_duncan: bool = False) -> dict[str, Any]:
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
            opponents=others,
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
            "next_action": "continue_with_other_players",
        }

    def captain_partnership_decision(
        self, human_player_id: str, action: str, target_player_id: str | None = None
    ) -> dict[str, Any]:
        """
        Captain (human) makes partnership decision after seeing a player's tee shot.
        Action can be: 'ask_partnership', 'wait_for_next', 'go_solo'
        """
        hole_state = self.hole_states[self.current_hole]

        if action == "ask_partnership":
            if not target_player_id:
                return {
                    "status": "error",
                    "message": "Must specify target_player_id when asking for partnership",
                }

            # Check if target player is still eligible
            if not self._is_player_eligible_for_partnership(target_player_id, hole_state):
                return {
                    "status": "error",
                    "message": f"{self._get_player_name(target_player_id)} is no longer eligible for partnership",
                }

            # Check if target player is computer or human
            if target_player_id in self.computer_players:
                # Computer partner - simulate their decision
                computer_player = self.computer_players[target_player_id]
                accept = computer_player.should_accept_partnership(
                    next(p for p in self.players if p.id == human_player_id),
                    self.get_game_state(),
                )

                if accept:
                    # Computer accepts partnership
                    result = self._accept_partnership(human_player_id, target_player_id, hole_state)
                    result["computer_response"] = (
                        f"{self._get_player_name(target_player_id)} accepts your partnership request!"
                    )
                    result["next_action"] = "partnership_formed_continue_hole"
                    return result
                # Computer declines - human goes solo
                result = self._decline_partnership(human_player_id, target_player_id, hole_state)
                result["computer_response"] = (
                    f"{self._get_player_name(target_player_id)} declines your partnership request."
                )
                result["next_action"] = "human_going_solo_continue_hole"
                return result
            # Human partner - create pending request
            hole_state.teams.pending_request = {
                "type": "partnership",
                "captain": human_player_id,
                "requested": target_player_id,
            }

            return {
                "status": "partnership_request_pending",
                "message": f"Partnership request sent to {self._get_player_name(target_player_id)}. Waiting for response...",
                "pending_request": hole_state.teams.pending_request,
                "hole_state": self._get_comprehensive_hole_state(),
                "next_action": "wait_for_partnership_response",
            }

        if action == "wait_for_next":
            # Check if there are more players to hit
            hitting_order = hole_state.hitting_order
            hitting_order.index(human_player_id)
            current_players_hit = len(hole_state.ball_positions)

            if current_players_hit < len(hitting_order):
                # More players to hit - continue
                return {
                    "status": "waiting_for_next_player",
                    "message": "Captain waits for next player to tee off...",
                    "hole_state": self._get_comprehensive_hole_state(),
                    "next_action": "next_player_tees_off",
                }
            # All players have hit - captain goes solo
            return self.human_goes_solo(human_player_id)

        if action == "go_solo":
            return self.human_goes_solo(human_player_id)

        return {
            "status": "error",
            "message": f"Invalid action: {action}. Must be 'ask_partnership', 'wait_for_next', or 'go_solo'",
        }

    # AI Decision Making Methods (moved from WGPComputerPlayer)

    def should_accept_partnership(self, captain: Player, game_state: dict) -> bool:
        """Decide whether to accept partnership request"""
        # For simulation purposes, use a simple decision based on handicap difference
        # In a real implementation, this would be called on a specific player
        handicap_diff = abs(captain.handicap - 12.0)  # Assume average handicap
        current_position = 2  # Assume middle position

        # Simple decision logic
        if handicap_diff < 8 or current_position > 2:
            return True
        return random.random() > 0.4

    def should_request_partner(self, target_player_id: str, game_state: dict) -> bool:
        """Determine if this computer player should request a specific player as partner"""
        # This would be used if computer players could request human as partner
        # For now, computer players don't actively request partners
        return False

    def should_go_solo(self, game_state: dict) -> bool:
        """Decide whether to go solo as captain"""
        # For simulation purposes, use simple decision logic
        current_position = 2  # Assume middle position
        individual_skill = 0.5  # Assume average skill

        # Simple decision logic
        if individual_skill > 0.4:
            return random.random() > 0.7
        return current_position > 3

    def should_use_float(self, game_state: dict) -> bool:
        """Decide whether to use float as captain"""
        # For simulation purposes, use simple decision logic
        current_position = 2  # Assume middle position
        hole_confidence = 0.6  # Assume moderate confidence

        # Simple decision logic
        if hole_confidence > 0.6:
            return random.random() > 0.5
        return current_position > 3

    def should_offer_double(self, game_state: dict) -> bool:
        """Decide whether to offer a double"""
        # For simulation purposes, use simple decision logic
        team_advantage = 0.5  # Assume moderate advantage
        current_position = 2  # Assume middle position

        # Simple decision logic
        if team_advantage > 0.5:
            return random.random() > 0.3
        return current_position > 2

    def should_accept_double(self, game_state: dict) -> bool:
        """Decide whether to accept a double"""
        # For simulation purposes, use simple decision logic
        current_points = 0  # Assume neutral position
        hole_advantage = 0.1  # Assume slight advantage

        # Simple decision logic
        if hole_advantage > 0:
            return random.random() > 0.4
        return current_points < 0

    # Compatibility methods for old simulation API
    def setup_simulation(self, human_player, computer_configs, course_name=None):
        """Compatibility method for old simulation API"""
        # Convert human player to Player (handle both dict and object)
        if isinstance(human_player, dict):
            wgp_human = Player(
                id=human_player["id"],
                name=human_player["name"],
                handicap=human_player["handicap"],
            )
        else:
            wgp_human = Player(
                id=human_player.id,
                name=human_player.name,
                handicap=human_player.handicap,
            )

        # Convert computer configs to Players
        wgp_players = [wgp_human]
        computer_player_ids = []
        personalities = []

        for config in computer_configs:
            wgp_player = Player(id=config["id"], name=config["name"], handicap=config["handicap"])
            wgp_players.append(wgp_player)
            computer_player_ids.append(config["id"])
            personalities.append(config.get("personality", "balanced"))

        # Create new simulation with these players
        new_sim = type(self)(player_count=len(wgp_players), players=wgp_players)

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
                self.hole_handicaps = list(range(1, 19))  # Default handicaps
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
            return self.respond_to_partnership(human_decisions["partner_id"], False)

        if "action" in human_decisions:
            if human_decisions["action"] == "go_solo":
                return self.captain_go_solo("human")
            if human_decisions["action"] == "request_partner":
                return self.request_partner("human", human_decisions["requested_partner"])

        # Default: advance hole
        return self.advance_to_next_hole()

    def play_next_shot(self, game_state, human_decisions):
        """Compatibility method for old simulation API"""
        # For now, just simulate a shot and return
        if hasattr(self, "shot_simulation_mode") and self.shot_simulation_mode:
            next_player = self._get_next_shot_player()
            if next_player:
                # Shot simulation removed - use manual shot recording instead

                shot_result = None  # self.simulate_shot(next_player)
                return shot_result, ["Shot simulated"], True, None

        # Default: advance hole
        self.advance_to_next_hole()
        return None, ["Hole advanced"], False, None

    def calculate_shot_probabilities(self, game_state):
        """Compatibility method for old simulation API"""
        # Return basic probabilities
        return {
            "excellent": 0.1,
            "good": 0.3,
            "average": 0.4,
            "poor": 0.15,
            "terrible": 0.05,
        }

    def calculate_betting_probabilities(self, game_state, decision):
        """Compatibility method for old simulation API"""
        # Return basic betting probabilities
        return {"partnership_success": 0.6, "solo_success": 0.4, "double_success": 0.5}

    def execute_betting_decision(self, game_state: Any, decision: Any, probabilities: Any) -> Any:
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
            "hole_number": self.current_hole,
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

    # ADVANCED ANALYTICS METHODS

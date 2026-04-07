"""
Integration tests for complete game scenarios
Test end-to-end flows with realistic data
"""
import os
import sys
import random
import pytest

sys.path.append(os.path.join(os.path.dirname(__file__), "../../backend"))

from app.wolf_goat_pig_simulation import WolfGoatPigSimulation
from app.domain.player import Player


class TestCompleteGameScenarios:
    """Test complete game scenarios from start to finish"""
    
    def setup_method(self):
        """Setup common test data"""
        random.seed(0)
        self.human_player = Player("human", "You", 12.0)
        self.computer_configs = [
            {"id": "comp1", "name": "Alice", "handicap": 8.0, "personality": "balanced"},
            {"id": "comp2", "name": "Bob", "handicap": 15.0, "personality": "aggressive"},
            {"id": "comp3", "name": "Charlie", "handicap": 20.0, "personality": "conservative"}
        ]

    def _create_simulation(self, computer_configs=None):
        configs = computer_configs or self.computer_configs
        base = WolfGoatPigSimulation(player_count=len(configs) + 1)
        game_state = base.setup_simulation(
            self.human_player,
            configs,
            'Wing Point Golf & Country Club'
        )
        return game_state, game_state.wgp_sim

    @staticmethod
    def _next_non_captain(hole_state, captain_id):
        for player_id in hole_state.hitting_order:
            if player_id != captain_id:
                return player_id
        raise AssertionError("No alternate player available for partnership test")
    
    def test_complete_hole_with_partnership_acceptance(self):
        """Test a complete hole where human accepts partnership"""
        game_state, simulation = self._create_simulation()
        hole_state = simulation.hole_states[simulation.current_hole]
        captain = hole_state.teams.captain
        partner = self._next_non_captain(hole_state, captain)

        simulation.request_partner(captain, partner)
        result = simulation.respond_to_partnership(partner, True)

        updated_hole = simulation.hole_states[simulation.current_hole]
        assert updated_hole.teams.type == "partners"
        assert sorted(result.get("team1", [])) == sorted(updated_hole.teams.team1)

        simulation.advance_to_next_hole()
        assert simulation.current_hole == 2
    
    def test_complete_hole_with_partnership_decline(self):
        """Test a complete hole where human declines partnership"""
        game_state, simulation = self._create_simulation()
        hole_state = simulation.hole_states[simulation.current_hole]
        captain = hole_state.teams.captain
        partner = self._next_non_captain(hole_state, captain)

        simulation.request_partner(captain, partner)
        decline = simulation.respond_to_partnership(partner, False)

        updated_hole = simulation.hole_states[simulation.current_hole]
        assert updated_hole.teams.type == "solo"
        assert updated_hole.teams.captain != partner
        assert updated_hole.betting.current_wager == decline.get("new_wager", updated_hole.betting.current_wager)

        simulation.advance_to_next_hole()
        assert simulation.current_hole == 2
    
    def test_human_captain_requests_partner(self):
        """Test when human is captain and requests a partner"""
        game_state, simulation = self._create_simulation()
        hole_state = simulation.hole_states[simulation.current_hole]
        assert hole_state.teams.captain == "human"

        partner = self._next_non_captain(hole_state, "human")
        pending = simulation.request_partner("human", partner)

        hole_state = simulation.hole_states[simulation.current_hole]
        assert hole_state.teams.pending_request is not None
        assert pending.get("status") == "pending"
    
    def test_human_captain_goes_solo(self):
        """Test when human captain goes solo"""
        game_state, simulation = self._create_simulation()
        captain = simulation.hole_states[simulation.current_hole].teams.captain
        result = simulation.captain_go_solo(captain)
        hole_state = simulation.hole_states[simulation.current_hole]

        assert hole_state.teams.type == "solo"
        assert hole_state.teams.captain == captain
        assert hole_state.betting.current_wager == result.get("new_wager", hole_state.betting.current_wager)


class TestEdgeCases:
    """Test edge cases and error conditions"""
    
    def setup_method(self):
        random.seed(0)
        self.human_player = Player("human", "You", 12.0)
        self.computer_configs = [
            {"id": "comp1", "name": "Alice", "handicap": 8.0, "personality": "balanced"},
            {"id": "comp2", "name": "Bob", "handicap": 15.0, "personality": "aggressive"},
            {"id": "comp3", "name": "Charlie", "handicap": 20.0, "personality": "conservative"}
        ]

    def _create_simulation(self):
        base = WolfGoatPigSimulation(player_count=4)
        game_state = base.setup_simulation(
            self.human_player,
            self.computer_configs,
            'Wing Point Golf & Country Club'
        )
        return game_state, game_state.wgp_sim
    
    def test_invalid_partnership_request(self):
        """Test handling of invalid partnership requests"""
        _, simulation = self._create_simulation()
        hole_state = simulation.hole_states[simulation.current_hole]
        partner = next(pid for pid in hole_state.hitting_order if pid != hole_state.teams.captain)
        with pytest.raises(ValueError):
            simulation.respond_to_partnership(partner, False)
    
    def test_multiple_partnership_requests(self):
        """Test handling of multiple partnership requests"""
        _, simulation = self._create_simulation()
        hole_state = simulation.hole_states[simulation.current_hole]
        captain = hole_state.teams.captain
        partner = next(pid for pid in hole_state.hitting_order if pid != captain)

        first = simulation.request_partner(captain, partner)
        second = simulation.request_partner(captain, partner)
        hole_state = simulation.hole_states[simulation.current_hole]
        assert hole_state.teams.pending_request is not None
        assert first["status"] == "pending"
        assert second["status"] == "pending"
        assert hole_state.teams.pending_request.get("requested") == partner


class TestGameStateConsistency:
    """Test that game state remains consistent throughout simulation"""
    
    def setup_method(self):
        random.seed(0)
        self.human_player = Player("human", "You", 12.0)
        self.computer_configs = [
            {"id": "comp1", "name": "Alice", "handicap": 8.0, "personality": "balanced"},
            {"id": "comp2", "name": "Bob", "handicap": 15.0, "personality": "aggressive"},
            {"id": "comp3", "name": "Charlie", "handicap": 20.0, "personality": "conservative"}
        ]

    def _create_simulation(self):
        base = WolfGoatPigSimulation(player_count=4)
        game_state = base.setup_simulation(
            self.human_player,
            self.computer_configs,
            'Wing Point Golf & Country Club'
        )
        return game_state, game_state.wgp_sim
    
    def test_player_order_consistency(self):
        """Test that player order remains consistent"""
        game_state, simulation = self._create_simulation()
        hole_state = simulation.hole_states[simulation.current_hole]
        initial_order = hole_state.hitting_order.copy()
        initial_captain = hole_state.teams.captain

        simulation.captain_go_solo(initial_captain)
        simulation.advance_to_next_hole()

        next_hole = simulation.hole_states[simulation.current_hole]
        assert set(next_hole.hitting_order) == set(initial_order)
        assert next_hole.hitting_order != initial_order
        assert next_hole.teams.captain != initial_captain
    
    def test_score_tracking_consistency(self):
        """Test that scores are tracked correctly"""
        game_state, simulation = self._create_simulation()
        hole_state = simulation.hole_states[simulation.current_hole]
        simulation.captain_go_solo(hole_state.teams.captain)
        hole_state = simulation.hole_states[simulation.current_hole]

        # Enter explicit scores for every player so the hole is fully evaluated
        score_card = {player.id: index + 3 for index, player in enumerate(simulation.players)}
        points_summary = simulation.enter_hole_scores(score_card)
        assert points_summary["points_changes"]  # ensure scoring logic executed

        summary = simulation.advance_to_next_hole()
        assert summary["status"] == "hole_advanced"

        previous_hole_scores = simulation.hole_states[simulation.current_hole - 1].scores
        for player_id, score in previous_hole_scores.items():
            assert player_id in score_card
            assert score == score_card[player_id]


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 

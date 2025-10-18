"""
Integration tests for complete game scenarios
Test end-to-end flows with realistic data
"""
import pytest
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

HELPERS_PATH = os.path.join(os.path.dirname(__file__), "helpers")
if HELPERS_PATH not in sys.path:
    sys.path.append(HELPERS_PATH)

from simulation_engine import SimulationEngine
from app.wolf_goat_pig_simulation import WolfGoatPigSimulation
from app.domain.player import Player


class TestCompleteGameScenarios:
    """Test complete game scenarios from start to finish"""
    
    def setup_method(self):
        """Setup common test data"""
        self.engine = SimulationEngine()
        self.human_player = Player("human", "You", 12.0)
        self.computer_configs = [
            {"id": "comp1", "name": "Alice", "handicap": 8.0, "personality": "balanced"},
            {"id": "comp2", "name": "Bob", "handicap": 15.0, "personality": "aggressive"},
            {"id": "comp3", "name": "Charlie", "handicap": 20.0, "personality": "conservative"}
        ]
    
    def test_complete_hole_with_partnership_acceptance(self):
        """Test a complete hole where human accepts partnership"""
        game_state = self.engine.setup_simulation(
            self.human_player, 
            self.computer_configs, 
            'Wing Point Golf & Country Club'
        )
        
        # Setup partnership request
        game_state.betting_state.request_partner("comp1", "human")
        
        # Human accepts partnership
        human_decisions = {"accept": True, "partner_id": "human"}
        
        # Run simulation
        result_state, feedback, interaction = self.engine.simulate_hole(game_state, human_decisions)
        
        # Verify partnership was formed
        assert result_state.betting_state.teams.get("type") == "partners"
        assert "human" in result_state.betting_state.teams.get("team1", [])
        assert "comp1" in result_state.betting_state.teams.get("team1", [])
        
        # Verify hole completed
        assert result_state.current_hole == 2  # Moved to next hole
    
    def test_complete_hole_with_partnership_decline(self):
        """Test a complete hole where human declines partnership"""
        game_state = self.engine.setup_simulation(
            self.human_player, 
            self.computer_configs, 
            'Wing Point Golf & Country Club'
        )
        
        # Setup partnership request
        game_state.betting_state.request_partner("comp1", "human")
        
        # Human declines partnership
        human_decisions = {"accept": False, "partner_id": "human"}
        
        # Run simulation
        result_state, feedback, interaction = self.engine.simulate_hole(game_state, human_decisions)
        
        # Verify captain went solo
        assert result_state.betting_state.teams.get("type") == "solo"
        assert result_state.betting_state.teams.get("captain") == "comp1"
        assert result_state.betting_state.base_wager == 2  # Doubled
        
        # Verify hole completed
        assert result_state.current_hole == 2  # Moved to next hole
    
    def test_human_captain_requests_partner(self):
        """Test when human is captain and requests a partner"""
        game_state = self.engine.setup_simulation(
            self.human_player, 
            self.computer_configs, 
            'Wing Point Golf & Country Club'
        )
        
        # Human is captain (first player in hitting order)
        assert game_state.player_manager.captain_id == "human"
        
        # Human requests partner
        human_decisions = {"action": "request_partner", "requested_partner": "comp1"}
        
        # Run simulation
        result_state, feedback, interaction = self.engine.simulate_hole(game_state, human_decisions)
        
        # Should need interaction for partner response
        assert interaction is not None
        assert interaction.get("type") == "partnership_response"
    
    def test_human_captain_goes_solo(self):
        """Test when human captain goes solo"""
        game_state = self.engine.setup_simulation(
            self.human_player, 
            self.computer_configs, 
            'Wing Point Golf & Country Club'
        )
        
        # Human captain goes solo
        human_decisions = {"action": "go_solo"}
        
        # Run simulation
        result_state, feedback, interaction = self.engine.simulate_hole(game_state, human_decisions)
        
        # Verify solo play
        assert result_state.betting_state.teams.get("type") == "solo"
        assert result_state.betting_state.teams.get("captain") == "human"
        assert result_state.betting_state.base_wager == 2  # Doubled


class TestEdgeCases:
    """Test edge cases and error conditions"""
    
    def setup_method(self):
        self.engine = SimulationEngine()
        self.human_player = Player("human", "You", 12.0)
        self.computer_configs = [
            {"id": "comp1", "name": "Alice", "handicap": 8.0, "personality": "balanced"}
        ]
    
    def test_invalid_partnership_request(self):
        """Test handling of invalid partnership requests"""
        game_state = self.engine.setup_simulation(
            self.human_player, 
            self.computer_configs, 
            'Wing Point Golf & Country Club'
        )
        
        # Try to decline without pending request
        human_decisions = {"accept": False, "partner_id": "human"}
        
        # Should handle gracefully
        result_state, feedback, interaction = self.engine.simulate_hole(game_state, human_decisions)
        
        # Should not crash and should complete hole
        assert result_state.current_hole == 2
    
    def test_multiple_partnership_requests(self):
        """Test handling of multiple partnership requests"""
        game_state = self.engine.setup_simulation(
            self.human_player, 
            self.computer_configs, 
            'Wing Point Golf & Country Club'
        )
        
        # Setup first request
        game_state.betting_state.request_partner("comp1", "human")
        
        # Try to setup second request (should fail gracefully)
        try:
            game_state.betting_state.request_partner("human", "comp1")
        except Exception:
            # Expected to fail - can't have multiple pending requests
            pass
        
        # Original request should still be valid
        assert game_state.betting_state.teams.get("type") == "pending"
        assert game_state.betting_state.teams.get("requested") == "human"


class TestGameStateConsistency:
    """Test that game state remains consistent throughout simulation"""
    
    def setup_method(self):
        self.engine = SimulationEngine()
        self.human_player = Player("human", "You", 12.0)
        self.computer_configs = [
            {"id": "comp1", "name": "Alice", "handicap": 8.0, "personality": "balanced"},
            {"id": "comp2", "name": "Bob", "handicap": 15.0, "personality": "aggressive"},
            {"id": "comp3", "name": "Charlie", "handicap": 20.0, "personality": "conservative"}
        ]
    
    def test_player_order_consistency(self):
        """Test that player order remains consistent"""
        game_state = self.engine.setup_simulation(
            self.human_player, 
            self.computer_configs, 
            'Wing Point Golf & Country Club'
        )
        
        initial_order = game_state.player_manager.hitting_order.copy()
        initial_captain = game_state.player_manager.captain_id
        
        # Run a hole
        human_decisions = {"action": "go_solo"}
        result_state, feedback, interaction = self.engine.simulate_hole(game_state, human_decisions)
        
        # Player order should remain the same
        assert result_state.player_manager.hitting_order == initial_order
        
        # Captain should rotate
        assert result_state.player_manager.captain_id != initial_captain
    
    def test_score_tracking_consistency(self):
        """Test that scores are tracked correctly"""
        game_state = self.engine.setup_simulation(
            self.human_player, 
            self.computer_configs, 
            'Wing Point Golf & Country Club'
        )
        
        # Run a hole
        human_decisions = {"action": "go_solo"}
        result_state, feedback, interaction = self.engine.simulate_hole(game_state, human_decisions)
        
        # All players should have scores for the completed hole
        for player in result_state.player_manager.players:
            assert player.id in result_state.hole_scores
            assert result_state.hole_scores[player.id] is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 

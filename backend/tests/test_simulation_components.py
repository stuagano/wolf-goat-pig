"""
Unit tests for simulation engine components
Focus on testing individual pieces in isolation
"""
import pytest
from unittest.mock import Mock, patch
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.simulation import SimulationEngine, ComputerPlayer
from app.domain.player import Player
from app.state.betting_state import BettingState
from app.game_state import GameState


class TestComputerPlayer:
    """Test computer player decision logic in isolation"""
    
    def test_should_accept_partnership_when_behind(self):
        player = ComputerPlayer("comp1", "Alice", 8.0, "balanced")
        game_state = Mock()
        
        # Mock the player_manager.players to be iterable
        mock_player = Mock()
        mock_player.id = "comp1"
        mock_player.points = -5  # Behind
        game_state.player_manager.players = [mock_player]
        
        result = player.should_accept_partnership(12.0, game_state)
        assert result == True  # Should accept when behind
    
    def test_should_go_solo_when_ahead(self):
        player = ComputerPlayer("comp1", "Alice", 8.0, "aggressive")
        game_state = Mock()
        
        # Mock the player_manager.players to be iterable
        mock_player = Mock()
        mock_player.id = "comp1"
        mock_player.points = 5  # Ahead
        game_state.player_manager.players = [mock_player]
        
        result = player.should_go_solo(game_state)
        assert result == True  # Aggressive player ahead should go solo


class TestBettingState:
    """Test betting state logic in isolation"""
    
    def test_partnership_acceptance(self):
        betting_state = BettingState()
        players = [
            Player("captain", "Captain", 10.0),
            Player("partner", "Partner", 12.0),
            Player("other1", "Other1", 15.0),
            Player("other2", "Other2", 18.0)
        ]
        
        # Setup pending request
        betting_state.request_partner("captain", "partner")
        
        # Accept partnership
        result = betting_state.accept_partner("partner", players)
        
        assert betting_state.teams["type"] == "partners"
        assert betting_state.teams["team1"] == ["captain", "partner"]
        assert betting_state.teams["team2"] == ["other1", "other2"]
    
    def test_partnership_decline_goes_solo(self):
        betting_state = BettingState()
        players = [
            Player("captain", "Captain", 10.0),
            Player("partner", "Partner", 12.0),
            Player("other1", "Other1", 15.0),
            Player("other2", "Other2", 18.0)
        ]
        
        # Setup pending request
        betting_state.request_partner("captain", "partner")
        
        # Decline partnership
        result = betting_state.decline_partner("partner", players)
        
        assert betting_state.teams["type"] == "solo"
        assert betting_state.teams["captain"] == "captain"
        assert betting_state.teams["opponents"] == ["partner", "other1", "other2"]
        assert betting_state.base_wager == 2  # Doubled


class TestShotSimulation:
    """Test shot simulation logic in isolation"""
    
    def test_approach_shot_simulation(self):
        from app.services.shot_simulator import ShotSimulator
        
        player = Player("test", "Test", 12.0)
        game_state = Mock()
        game_state.current_hole = 1
        
        result = ShotSimulator.simulate_approach_shot(player, 150, game_state)
        
        assert hasattr(result, 'remaining')
        assert hasattr(result, 'lie')
        assert hasattr(result, 'shot_quality')


class TestPartnershipAdvantage:
    """Test partnership advantage calculations"""
    
    def test_partnership_advantage_calculation(self):
        engine = SimulationEngine()
        game_state = Mock()
        
        # Mock the player_manager.players to be iterable
        mock_captain = Mock()
        mock_captain.id = "captain"
        mock_captain.handicap = 10.0
        
        mock_partner = Mock()
        mock_partner.id = "partner"
        mock_partner.handicap = 12.0
        
        mock_other1 = Mock()
        mock_other1.id = "other1"
        mock_other1.handicap = 15.0
        
        mock_other2 = Mock()
        mock_other2.id = "other2"
        mock_other2.handicap = 18.0
        
        game_state.player_manager.players = [mock_captain, mock_partner, mock_other1, mock_other2]
        
        advantage = engine._calculate_partnership_advantage("captain", "partner", game_state)
        
        # Team avg: (10 + 12) / 2 = 11
        # Others avg: (15 + 18) / 2 = 16.5
        # Advantage: 16.5 - 11 = 5.5
        assert advantage > 0  # Team should have advantage


class TestSimulationFlow:
    """Test simulation flow with mocked dependencies"""
    
    @patch('app.services.shot_simulator.ShotSimulator.simulate_remaining_shots_chronological')
    def test_simulation_with_mocked_shots(self, mock_shots):
        engine = SimulationEngine()
        human_player = Player("human", "You", 12.0)
        computer_configs = [
            {"id": "comp1", "name": "Alice", "handicap": 8.0, "personality": "balanced"},
            {"id": "comp2", "name": "Bob", "handicap": 15.0, "personality": "aggressive"},
            {"id": "comp3", "name": "Charlie", "handicap": 20.0, "personality": "conservative"}
        ]
        
        game_state = engine.setup_simulation(human_player, computer_configs)
        mock_shots.return_value = ["Mock shot feedback"]
        
        # Test partnership decline scenario
        human_decisions = {"accept": False, "partner_id": "human"}
        game_state.betting_state.request_partner("comp1", "human")
        
        result_state, feedback, interaction = engine.simulate_hole(game_state, human_decisions)
        
        # Verify partnership was declined and captain went solo
        assert result_state.betting_state.teams.get("type") == "solo"
        assert "decline" in str(feedback).lower() or "solo" in str(feedback).lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 
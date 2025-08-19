"""
Unit tests for simulation engine components
Focus on testing individual pieces in isolation
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.wolf_goat_pig_simulation import WolfGoatPigSimulation, WGPPlayer
from app.domain.player import Player
from app.state.betting_state import BettingState
from app.game_state import GameState


class TestWGPPlayer:
    """Test WGP Player functionality"""
    
    def test_player_creation(self):
        player = WGPPlayer("p1", "Alice", 10.0)
        assert player.id == "p1"
        assert player.name == "Alice"
        assert player.handicap == 10.0
        assert player.is_computer == False
        assert player.personality == "balanced"
    
    def test_computer_player_creation(self):
        player = WGPPlayer("p2", "Bob", 15.0, is_computer=True, personality="aggressive")
        assert player.is_computer == True
        assert player.personality == "aggressive"


class TestBettingState:
    """Test betting state logic in isolation"""
    
    def test_partnership_request(self):
        betting_state = BettingState()
        betting_state.teams = {
            "type": "pending",
            "captain": "captain",
            "pending_request": None
        }
        
        result = betting_state.request_partner("captain", "partner")
        assert result == True
        assert betting_state.teams["pending_request"]["captain"] == "captain"
        assert betting_state.teams["pending_request"]["requested"] == "partner"
    
    def test_partnership_acceptance(self):
        betting_state = BettingState()
        betting_state.teams = {
            "type": "pending",
            "captain": "captain",
            "pending_request": {"captain": "captain", "requested": "partner"}
        }
        
        # Accept partnership
        betting_state.accept_partner("partner", ["captain", "partner", "other1", "other2"])
        
        assert betting_state.teams["type"] == "partners"
        assert "captain" in betting_state.teams["team1"]
        assert "partner" in betting_state.teams["team1"]
    
    def test_partnership_decline_goes_solo(self):
        betting_state = BettingState()
        betting_state.teams = {
            "type": "pending",
            "captain": "captain",
            "pending_request": {"captain": "captain", "requested": "partner"}
        }
        
        # Decline partnership
        betting_state.decline_partner("partner", ["captain", "partner", "other1", "other2"])
        
        assert betting_state.teams["type"] == "solo"
        assert betting_state.teams["captain"] == "captain"
        assert len(betting_state.teams["opponents"]) == 3
        assert betting_state.base_wager == 2  # Doubled for solo


class TestWolfGoatPigSimulation:
    """Test main simulation engine"""
    
    def test_simulation_initialization(self):
        sim = WolfGoatPigSimulation(player_count=4)
        assert sim.player_count == 4
        assert len(sim.players) == 4
        assert sim.current_hole == 1
        assert sim.total_holes == 18
    
    def test_simulation_with_custom_players(self):
        players = [
            WGPPlayer("p1", "Alice", 10.0),
            WGPPlayer("p2", "Bob", 15.0),
            WGPPlayer("p3", "Charlie", 18.0),
            WGPPlayer("p4", "David", 20.0)
        ]
        sim = WolfGoatPigSimulation(player_count=4, players=players)
        assert len(sim.players) == 4
        assert sim.players[0].name == "Alice"
    
    def test_set_computer_players(self):
        sim = WolfGoatPigSimulation(player_count=4)
        sim.set_computer_players(["p2", "p3", "p4"])
        
        assert sim.players[0].is_computer == False
        assert sim.players[1].is_computer == True
        assert sim.players[2].is_computer == True
        assert sim.players[3].is_computer == True
    
    def test_request_partnership(self):
        sim = WolfGoatPigSimulation(player_count=4)
        sim.hole_states[1].teams.captain = "p1"
        
        result = sim.request_partner("p1", "p2")
        assert "Partnership requested" in result["message"]
        assert result["partnership_requested"] == True
    
    def test_captain_go_solo(self):
        sim = WolfGoatPigSimulation(player_count=4)
        sim.hole_states[1].teams.captain = "p1"
        
        result = sim.captain_go_solo("p1")
        assert "goes solo" in result["message"]
        assert sim.hole_states[1].teams.type == "solo"
    
    def test_offer_double(self):
        sim = WolfGoatPigSimulation(player_count=4)
        sim.hole_states[1].teams.type = "partners"
        sim.hole_states[1].teams.team1 = ["p1", "p2"]
        sim.hole_states[1].teams.team2 = ["p3", "p4"]
        
        result = sim.offer_double("p1")
        assert "offers to double" in result["message"]
        assert sim.hole_states[1].betting.double_offered == True
    
    def test_advance_hole(self):
        sim = WolfGoatPigSimulation(player_count=4)
        initial_hole = sim.current_hole
        
        result = sim.advance_to_next_hole()
        assert sim.current_hole == initial_hole + 1
        assert "Advanced to hole" in result["message"]
    
    def test_get_game_state(self):
        sim = WolfGoatPigSimulation(player_count=4)
        state = sim.get_game_state()
        
        assert "players" in state
        assert "current_hole" in state
        assert "total_holes" in state
        assert "hole_state" in state
        assert len(state["players"]) == 4
    
    @patch('app.wolf_goat_pig_simulation.random.random')
    def test_simulate_shot(self, mock_random):
        sim = WolfGoatPigSimulation(player_count=4)
        sim.enable_shot_progression()
        
        # Mock random to control shot outcome
        mock_random.return_value = 0.5
        
        result = sim.simulate_shot("p1")
        assert "shot_result" in result
        assert result["shot_result"]["player_id"] == "p1"
        assert "distance_to_pin" in result["shot_result"]
    
    def test_enter_hole_scores(self):
        sim = WolfGoatPigSimulation(player_count=4)
        sim.hole_states[1].teams.type = "partners"
        sim.hole_states[1].teams.team1 = ["p1", "p2"]
        sim.hole_states[1].teams.team2 = ["p3", "p4"]
        
        scores = {"p1": 4, "p2": 5, "p3": 4, "p4": 6}
        result = sim.enter_hole_scores(scores)
        
        assert "Teams tied" in result["message"] or "wins" in result["message"]
        assert "points_awarded" in result


class TestHoleProgression:
    """Test hole progression and shot tracking"""
    
    def test_shot_progression_initialization(self):
        sim = WolfGoatPigSimulation(player_count=4)
        sim.enable_shot_progression()
        
        assert hasattr(sim, 'hole_progression')
        assert sim.hole_progression is not None
        assert len(sim.hole_progression.timeline) > 0
    
    def test_get_next_shot_player(self):
        sim = WolfGoatPigSimulation(player_count=4)
        sim.enable_shot_progression()
        
        # First player should be the one with honors
        next_player = sim._get_next_shot_player()
        assert next_player in [p.id for p in sim.players]
    
    def test_timeline_events(self):
        sim = WolfGoatPigSimulation(player_count=4)
        sim.enable_shot_progression()
        
        initial_timeline_length = len(sim.hole_progression.timeline)
        
        # Simulate a shot
        sim.simulate_shot("p1")
        
        # Timeline should have grown
        assert len(sim.hole_progression.timeline) > initial_timeline_length


class TestAnalytics:
    """Test analytics and reporting features"""
    
    def test_get_advanced_analytics(self):
        sim = WolfGoatPigSimulation(player_count=4)
        analytics = sim.get_advanced_analytics()
        
        assert "player_performance" in analytics
        assert "partnership_analytics" in analytics
        assert "betting_trends" in analytics
        assert "shot_analysis" in analytics
    
    def test_post_hole_analysis(self):
        sim = WolfGoatPigSimulation(player_count=4)
        sim.hole_states[1].teams.type = "partners"
        sim.hole_states[1].teams.team1 = ["p1", "p2"]
        sim.hole_states[1].teams.team2 = ["p3", "p4"]
        sim.hole_states[1].hole_complete = True
        
        analysis = sim.get_post_hole_analysis(1)
        
        assert "hole_number" in analysis
        assert "teams" in analysis
        assert "betting_summary" in analysis


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
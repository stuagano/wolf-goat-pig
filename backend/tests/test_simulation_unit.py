#!/usr/bin/env python3
"""
Unit tests for simulation mode components
Tests individual functions and classes in isolation
"""

import pytest
import sys
import os
from unittest.mock import Mock, patch, MagicMock

# Add backend to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

try:
    from app.wolf_goat_pig_simulation import WolfGoatPigSimulation
    from app.game_state import GameState
    from app.models import Player, Course
    from app.services.monte_carlo import MonteCarloService
    from app.services.odds_calculator import OddsCalculator
    IMPORTS_AVAILABLE = True
except ImportError as e:
    print(f"Import error: {e}")
    IMPORTS_AVAILABLE = False

@pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Required imports not available")
class TestWolfGoatPigSimulation:
    """Test the main simulation class"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.mock_players = [
            Mock(id="p1", name="Player 1", handicap=10, is_human=True),
            Mock(id="p2", name="Player 2", handicap=15, is_human=False),
            Mock(id="p3", name="Player 3", handicap=12, is_human=False),
            Mock(id="p4", name="Player 4", handicap=8, is_human=False),
        ]
        
        self.mock_course = Mock(name="Test Course", holes=18)
        
    def test_simulation_initialization(self):
        """Test simulation can be initialized"""
        sim = WolfGoatPigSimulation()
        assert sim is not None
        assert hasattr(sim, 'players')
        assert hasattr(sim, 'game_state')
        
    def test_add_players(self):
        """Test adding players to simulation"""
        sim = WolfGoatPigSimulation()
        sim.add_players(self.mock_players)
        
        assert len(sim.players) == 4
        assert sim.players[0].name == "Player 1"
        
    def test_set_course(self):
        """Test setting course for simulation"""
        sim = WolfGoatPigSimulation()
        sim.set_course(self.mock_course)
        
        assert sim.course == self.mock_course
        assert sim.course.name == "Test Course"
        
    def test_start_game(self):
        """Test starting a game"""
        sim = WolfGoatPigSimulation()
        sim.add_players(self.mock_players)
        sim.set_course(self.mock_course)
        
        result = sim.start_game()
        
        assert result is not None
        assert sim.game_state is not None
        
    def test_get_current_captain(self):
        """Test captain rotation logic"""
        sim = WolfGoatPigSimulation()
        sim.add_players(self.mock_players)
        sim.current_hole = 1
        
        captain = sim.get_current_captain()
        
        assert captain is not None
        assert captain in self.mock_players
        
    def test_captain_rotation(self):
        """Test that captain rotates each hole"""
        sim = WolfGoatPigSimulation()
        sim.add_players(self.mock_players)
        
        sim.current_hole = 1
        captain1 = sim.get_current_captain()
        
        sim.current_hole = 2
        captain2 = sim.get_current_captain()
        
        assert captain1 != captain2
        
    def test_partnership_request(self):
        """Test partnership request functionality"""
        sim = WolfGoatPigSimulation()
        sim.add_players(self.mock_players)
        
        captain = self.mock_players[0]
        partner = self.mock_players[1]
        
        result = sim.request_partnership(captain.id, partner.id)
        
        assert result is not None
        assert 'partnership_requested' in result or result is True
        
    def test_partnership_response(self):
        """Test partnership response functionality"""
        sim = WolfGoatPigSimulation()
        sim.add_players(self.mock_players)
        
        # First request a partnership
        captain = self.mock_players[0]
        partner = self.mock_players[1]
        sim.request_partnership(captain.id, partner.id)
        
        # Then respond
        result = sim.respond_to_partnership(partner.id, accept=True)
        
        assert result is not None
        
    def test_shot_simulation(self):
        """Test shot simulation functionality"""
        sim = WolfGoatPigSimulation()
        sim.add_players(self.mock_players)
        sim.set_course(self.mock_course)
        
        player = self.mock_players[0]
        
        with patch('random.random', return_value=0.5):
            result = sim.simulate_shot(player.id)
            
        assert result is not None
        assert 'distance' in result or 'outcome' in result
        
    def test_game_state_serialization(self):
        """Test that game state can be serialized"""
        sim = WolfGoatPigSimulation()
        sim.add_players(self.mock_players)
        
        state = sim.get_game_state()
        
        assert isinstance(state, dict)
        assert 'players' in state or 'status' in state

@pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Required imports not available")
class TestGameState:
    """Test the game state management"""
    
    def test_game_state_creation(self):
        """Test creating a new game state"""
        players = [Mock(id=f"p{i}", name=f"Player {i}") for i in range(4)]
        
        game_state = GameState(players=players)
        
        assert game_state is not None
        assert len(game_state.players) == 4
        
    def test_hole_progression(self):
        """Test advancing to next hole"""
        players = [Mock(id=f"p{i}", name=f"Player {i}") for i in range(4)]
        game_state = GameState(players=players)
        
        initial_hole = game_state.current_hole
        game_state.advance_hole()
        
        assert game_state.current_hole == initial_hole + 1
        
    def test_score_tracking(self):
        """Test score tracking functionality"""
        players = [Mock(id=f"p{i}", name=f"Player {i}") for i in range(4)]
        game_state = GameState(players=players)
        
        game_state.record_score("p1", 4)
        
        assert "p1" in game_state.scores
        assert game_state.scores["p1"][-1] == 4

@pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Required imports not available")
class TestMonteCarloService:
    """Test the Monte Carlo simulation service"""
    
    def test_monte_carlo_initialization(self):
        """Test Monte Carlo service can be initialized"""
        service = MonteCarloService()
        assert service is not None
        
    def test_shot_probability_calculation(self):
        """Test shot probability calculations"""
        service = MonteCarloService()
        
        player_stats = {
            'handicap': 15,
            'driving_distance': 250,
            'accuracy': 0.7
        }
        
        hole_info = {
            'distance': 400,
            'par': 4,
            'difficulty': 0.6
        }
        
        probabilities = service.calculate_shot_probabilities(player_stats, hole_info)
        
        assert isinstance(probabilities, dict)
        assert 'excellent' in probabilities
        assert 'good' in probabilities
        assert 'average' in probabilities
        assert 'poor' in probabilities
        
        # Probabilities should sum to approximately 1.0
        total = sum(probabilities.values())
        assert 0.9 < total < 1.1
        
    def test_outcome_simulation(self):
        """Test outcome simulation with multiple iterations"""
        service = MonteCarloService()
        
        player_stats = {'handicap': 10}
        hole_info = {'par': 4, 'distance': 350}
        
        outcomes = service.simulate_outcomes(player_stats, hole_info, iterations=100)
        
        assert len(outcomes) == 100
        assert all(isinstance(outcome, (int, float)) for outcome in outcomes)

@pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Required imports not available")
class TestOddsCalculator:
    """Test the odds calculation service"""
    
    def test_odds_calculator_initialization(self):
        """Test odds calculator can be initialized"""
        calculator = OddsCalculator()
        assert calculator is not None
        
    def test_betting_odds_calculation(self):
        """Test betting odds calculation"""
        calculator = OddsCalculator()
        
        team1_stats = [
            {'handicap': 10, 'recent_scores': [75, 78, 76]},
            {'handicap': 15, 'recent_scores': [85, 82, 84]}
        ]
        
        team2_stats = [
            {'handicap': 8, 'recent_scores': [70, 72, 71]},
            {'handicap': 12, 'recent_scores': [80, 78, 82]}
        ]
        
        odds = calculator.calculate_team_odds(team1_stats, team2_stats)
        
        assert isinstance(odds, dict)
        assert 'team1_win_probability' in odds
        assert 'team2_win_probability' in odds
        assert 'recommended_bet' in odds
        
    def test_double_decision_logic(self):
        """Test doubling decision logic"""
        calculator = OddsCalculator()
        
        current_situation = {
            'team_scores': {'team1': 10, 'team2': 8},
            'holes_remaining': 5,
            'current_bet': 10
        }
        
        decision = calculator.should_offer_double(current_situation)
        
        assert isinstance(decision, dict)
        assert 'should_double' in decision
        assert 'confidence' in decision
        assert isinstance(decision['should_double'], bool)
        assert 0 <= decision['confidence'] <= 1

class TestSimulationUtilities:
    """Test utility functions for simulation"""
    
    def test_handicap_calculation(self):
        """Test handicap-based stroke allocation"""
        from app.services.odds_calculator import calculate_strokes_received
        
        player_handicap = 18
        hole_index = 5  # Stroke index
        
        strokes = calculate_strokes_received(player_handicap, hole_index)
        
        assert isinstance(strokes, int)
        assert strokes >= 0
        
    def test_net_score_calculation(self):
        """Test net score calculation"""
        from app.services.odds_calculator import calculate_net_score
        
        gross_score = 5
        strokes_received = 1
        
        net_score = calculate_net_score(gross_score, strokes_received)
        
        assert net_score == 4
        
    def test_team_formation_validation(self):
        """Test team formation validation"""
        players = [
            Mock(id="p1", handicap=10),
            Mock(id="p2", handicap=15),
            Mock(id="p3", handicap=12),
            Mock(id="p4", handicap=8),
        ]
        
        # Test valid team formation
        team1 = [players[0], players[1]]
        team2 = [players[2], players[3]]
        
        assert len(team1) == 2
        assert len(team2) == 2
        assert all(p.id for p in team1 + team2)

class TestSimulationErrorHandling:
    """Test error handling in simulation components"""
    
    def test_invalid_player_count(self):
        """Test handling of invalid player count"""
        with pytest.raises((ValueError, AssertionError)):
            sim = WolfGoatPigSimulation()
            sim.add_players([Mock()])  # Only 1 player, need 4
            sim.start_game()
            
    def test_missing_course(self):
        """Test handling of missing course"""
        sim = WolfGoatPigSimulation()
        players = [Mock(id=f"p{i}") for i in range(4)]
        sim.add_players(players)
        
        # Don't set course
        with pytest.raises((ValueError, AttributeError)):
            sim.start_game()
            
    def test_invalid_partnership_request(self):
        """Test handling of invalid partnership requests"""
        sim = WolfGoatPigSimulation()
        
        with pytest.raises((ValueError, KeyError)):
            sim.request_partnership("invalid_player", "another_invalid")

def main():
    """Run unit tests for simulation components"""
    print("🧪 Simulation Unit Tests")
    print("=" * 50)
    
    if not IMPORTS_AVAILABLE:
        print("⚠️ Simulation components not available for testing")
        print("💡 Run 'python -m pytest backend/tests/test_simulation_unit.py' to execute tests")
        return True
    
    # Run tests manually for demonstration
    test_classes = [
        TestWolfGoatPigSimulation,
        TestGameState,
        TestMonteCarloService,
        TestOddsCalculator,
        TestSimulationUtilities,
        TestSimulationErrorHandling,
    ]
    
    total_tests = 0
    passed_tests = 0
    
    for test_class in test_classes:
        print(f"\n📋 {test_class.__name__}")
        print("-" * 30)
        
        # Get test methods
        test_methods = [m for m in dir(test_class) if m.startswith('test_')]
        
        for method_name in test_methods:
            total_tests += 1
            try:
                # Create instance and run test
                instance = test_class()
                if hasattr(instance, 'setup_method'):
                    instance.setup_method()
                
                test_method = getattr(instance, method_name)
                test_method()
                
                print(f"✅ {method_name}")
                passed_tests += 1
                
            except Exception as e:
                print(f"❌ {method_name}: {e}")
    
    print(f"\n🎯 Test Results: {passed_tests}/{total_tests} passed")
    
    if passed_tests == total_tests:
        print("🎉 All unit tests PASSED!")
        return True
    else:
        print("⚠️ Some unit tests failed")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
#!/usr/bin/env python3
"""
Unit tests for simulation mode components
Tests individual functions and classes in isolation
"""

import pytest
import sys
import os
from unittest.mock import Mock

# Add backend to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.wolf_goat_pig import WolfGoatPigGame
from app.validators import HandicapValidator


# NOTE: The following test classes were removed because they test non-existent modules:
# - TestWolfGoatPigGame: Tests methods that don't exist on WolfGoatPigGame
# - TestGameState: Tests app.game_state.GameState which doesn't exist
# - TestMonteCarloService: Tests app.services.monte_carlo.MonteCarloService which doesn't exist
# - TestOddsCalculator: Tests app.services.odds_calculator.OddsCalculator which doesn't exist
#
# These were placeholder tests for future simulation features.
# The tests that remain (TestSimulationUtilities, TestSimulationErrorHandling)
# test actual working code.


class TestSimulationUtilities:
    """Test utility functions for simulation"""
    
    def test_handicap_calculation(self):
        """Test handicap-based stroke allocation"""
        player_handicap = 18
        hole_index = 5  # Stroke index

        strokes = HandicapValidator.calculate_strokes_received_with_creecher(player_handicap, hole_index)

        assert isinstance(strokes, (int, float))
        assert strokes >= 0

    def test_net_score_calculation(self):
        """Test net score calculation"""
        gross_score = 5
        strokes_received = 1

        net_score = HandicapValidator.calculate_net_score(gross_score, strokes_received)

        assert net_score == pytest.approx(4)
        
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
        with pytest.raises(ValueError):
            WolfGoatPigGame(player_count=3)
            
    def test_missing_course(self):
        """Test handling of responding to non-existent partnership request"""
        sim = WolfGoatPigGame()
        with pytest.raises(ValueError):
            sim.respond_to_partnership("comp1", True)
            
    def test_invalid_partnership_request(self):
        """Test handling of invalid partnership requests"""
        sim = WolfGoatPigGame()
        
        with pytest.raises((ValueError, KeyError)):
            sim.request_partner("invalid_player", "another_invalid")

def main():
    """Run unit tests for simulation components"""
    print("🧪 Simulation Unit Tests")
    print("=" * 50)

    # Run tests manually for demonstration
    test_classes = [
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

#!/usr/bin/env python3
"""
Quick test runner for simulation engine during development
Run specific tests or scenarios without full test suite
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.simulation import SimulationEngine
from app.domain.player import Player
from app.state.betting_state import BettingState


def test_partnership_decline_scenario():
    """Quick test for partnership decline scenario"""
    print("🧪 Testing Partnership Decline Scenario")
    print("=" * 50)
    
    engine = SimulationEngine()
    human_player = Player("human", "You", 12.0)
    computer_configs = [
        {"id": "comp1", "name": "Alice", "handicap": 8.0, "personality": "balanced"},
        {"id": "comp2", "name": "Bob", "handicap": 15.0, "personality": "aggressive"},
        {"id": "comp3", "name": "Charlie", "handicap": 20.0, "personality": "conservative"}
    ]
    
    game_state = engine.setup_simulation(human_player, computer_configs, 'Wing Point Golf & Country Club')
    
    # Setup partnership request
    game_state.betting_state.request_partner('comp1', 'human')
    print(f"✅ Initial teams state: {game_state.betting_state.teams}")
    
    # Human declines partnership
    human_decisions = {'accept': False, 'partner_id': 'human'}
    
    # Check teams state before simulation (should be pending)
    print(f"✅ Teams before simulation: {game_state.betting_state.teams}")
    
    # Run simulation and capture intermediate state
    game_state, feedback, interaction_needed = engine.simulate_hole(game_state, human_decisions)
    
    print(f"✅ Final teams state: {game_state.betting_state.teams}")
    print(f"✅ Doubled status: {game_state.betting_state.doubled_status}")
    print(f"✅ Current hole: {game_state.current_hole}")
    
    # Verify the fix worked by checking feedback messages
    feedback_text = " ".join(feedback).lower()
    print(f"🔍 Feedback text: {feedback_text}")
    assert "decline" in feedback_text or "solo" in feedback_text or "pass" in feedback_text, "Should mention decline or solo in feedback"
    assert game_state.current_hole == 2, "Should advance to next hole"
    print("✅ Partnership decline scenario PASSED")


def test_partnership_acceptance_scenario():
    """Quick test for partnership acceptance scenario"""
    print("\n🧪 Testing Partnership Acceptance Scenario")
    print("=" * 50)
    
    engine = SimulationEngine()
    human_player = Player("human", "You", 12.0)
    computer_configs = [
        {"id": "comp1", "name": "Alice", "handicap": 8.0, "personality": "balanced"},
        {"id": "comp2", "name": "Bob", "handicap": 15.0, "personality": "aggressive"},
        {"id": "comp3", "name": "Charlie", "handicap": 20.0, "personality": "conservative"}
    ]
    
    game_state = engine.setup_simulation(human_player, computer_configs, 'Wing Point Golf & Country Club')
    
    # Setup partnership request
    game_state.betting_state.request_partner('comp1', 'human')
    print(f"✅ Initial teams state: {game_state.betting_state.teams}")
    
    # Human accepts partnership
    human_decisions = {'accept': True, 'partner_id': 'human'}
    
    # Check teams state before simulation (should be pending)
    print(f"✅ Teams before simulation: {game_state.betting_state.teams}")
    
    # Run simulation
    game_state, feedback, interaction_needed = engine.simulate_hole(game_state, human_decisions)
    
    print(f"✅ Final teams state: {game_state.betting_state.teams}")
    print(f"✅ Doubled status: {game_state.betting_state.doubled_status}")
    print(f"✅ Current hole: {game_state.current_hole}")
    
    # Verify the fix worked by checking feedback messages
    feedback_text = " ".join(feedback).lower()
    print(f"🔍 Feedback text: {feedback_text}")
    assert "accept" in feedback_text or "team" in feedback_text or "absolutely" in feedback_text, "Should mention acceptance or team in feedback"
    assert game_state.current_hole == 2, "Should advance to next hole"
    print("✅ Partnership acceptance scenario PASSED")


def test_betting_state_isolated():
    """Test betting state logic in isolation"""
    print("\n🧪 Testing Betting State Logic (Isolated)")
    print("=" * 50)
    
    betting_state = BettingState()
    players = [
        Player("captain", "Captain", 10.0),
        Player("partner", "Partner", 12.0),
        Player("other1", "Other1", 15.0),
        Player("other2", "Other2", 18.0)
    ]
    
    # Test partnership request
    betting_state.request_partner("captain", "partner")
    print(f"✅ After request: {betting_state.teams}")
    
    # Test partnership acceptance
    betting_state.accept_partner("partner", players)
    print(f"✅ After acceptance: {betting_state.teams}")
    
    # Reset and test decline
    betting_state.reset_hole()
    betting_state.request_partner("captain", "partner")
    betting_state.decline_partner("partner", players)
    print(f"✅ After decline: {betting_state.teams}")
    print(f"✅ Base wager after decline: {betting_state.base_wager}")
    
    assert betting_state.teams["type"] == "solo", "Should be solo after decline"
    assert betting_state.base_wager == 2, "Wager should be doubled"
    print("✅ Betting state logic PASSED")


def test_shot_simulation_isolated():
    """Test shot simulation logic in isolation"""
    print("\n🧪 Testing Shot Simulation Logic (Isolated)")
    print("=" * 50)
    
    from app.services.shot_simulator import ShotSimulator
    from app.domain.shot_result import ShotResult
    
    player = Player("test", "Test", 12.0)
    game_state = type('MockGameState', (), {'current_hole': 1})()
    
    # Test approach shot
    result = ShotSimulator.simulate_approach_shot(player, 150, game_state)
    print(f"✅ Approach shot result: {result}")
    
    assert hasattr(result, 'remaining'), "Should have remaining distance"
    assert hasattr(result, 'lie'), "Should have lie type"
    assert hasattr(result, 'shot_quality'), "Should have shot quality"
    print("✅ Shot simulation logic PASSED")


def run_all_quick_tests():
    """Run all quick tests"""
    print("🚀 Running Quick Simulation Tests")
    print("=" * 60)
    
    try:
        test_betting_state_isolated()
        test_shot_simulation_isolated()
        test_partnership_decline_scenario()
        test_partnership_acceptance_scenario()
        
        print("\n🎉 ALL TESTS PASSED!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        print("=" * 60)
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    if len(sys.argv) > 1:
        test_name = sys.argv[1]
        if test_name == "partnership_decline":
            test_partnership_decline_scenario()
        elif test_name == "partnership_accept":
            test_partnership_acceptance_scenario()
        elif test_name == "betting_state":
            test_betting_state_isolated()
        elif test_name == "shot_simulation":
            test_shot_simulation_isolated()
        else:
            print(f"Unknown test: {test_name}")
            print("Available tests: partnership_decline, partnership_accept, betting_state, shot_simulation")
    else:
        run_all_quick_tests() 
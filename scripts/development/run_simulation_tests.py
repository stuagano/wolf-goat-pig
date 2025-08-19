#!/usr/bin/env python3
"""
Quick test runner for simulation engine during development
Run specific tests or scenarios without full test suite
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.wolf_goat_pig_simulation import WolfGoatPigSimulation
from app.domain.player import Player
from app.state.betting_state import BettingState


def test_partnership_decline_scenario():
    """Quick test for partnership decline scenario"""
    print("🧪 Testing Partnership Decline Scenario")
    print("=" * 50)
    
    from app.wolf_goat_pig_simulation import WolfGoatPigSimulation, WGPPlayer
    
    simulation = WolfGoatPigSimulation(player_count=4)
    players = [
        WGPPlayer("p1", "Player1", 12.0),  # Captain
        WGPPlayer("p2", "Player2", 15.0),  # Requested partner
        WGPPlayer("p3", "Player3", 8.0),
        WGPPlayer("p4", "Player4", 20.0)
    ]
    
    # Initialize simulation properly
    simulation.players = players
    simulation.current_hole = 1
    simulation._initialize_hole(1)
    
    # Check who the captain is
    hole_state = simulation.hole_states[simulation.current_hole]
    print(f"🔍 Captain: {hole_state.teams.captain}")
    print(f"🔍 Hitting order: {hole_state.hitting_order}")
    
    # Test partnership request and decline
    captain_id = hole_state.teams.captain
    result1 = simulation.request_partner(captain_id, "p2")  # Captain requests partner
    print(f"✅ Partnership requested: {result1.get('status')}")
    
    result2 = simulation.respond_to_partnership("p2", False)  # Partner declines
    print(f"✅ Partnership declined: {result2.get('status')}")
    
    # Check that captain went solo
    hole_state = simulation.hole_states[simulation.current_hole]
    print(f"✅ Teams type: {hole_state.teams.type}")
    print(f"✅ Base wager: {hole_state.betting.base_wager}")
    print(f"✅ Current wager: {hole_state.betting.current_wager}")
    
    assert hole_state.teams.type == "solo", "Should be solo after decline"
    assert hole_state.betting.current_wager == 2, "Current wager should double after decline"
    print("✅ Partnership decline scenario PASSED")


def test_partnership_acceptance_scenario():
    """Quick test for partnership acceptance scenario"""
    print("\n🧪 Testing Partnership Acceptance Scenario")
    print("=" * 50)
    
    from app.wolf_goat_pig_simulation import WolfGoatPigSimulation, WGPPlayer
    
    simulation = WolfGoatPigSimulation(player_count=4)
    players = [
        WGPPlayer("p1", "Player1", 12.0),  # Captain
        WGPPlayer("p2", "Player2", 15.0),  # Requested partner
        WGPPlayer("p3", "Player3", 8.0),
        WGPPlayer("p4", "Player4", 20.0)
    ]
    
    # Initialize simulation properly
    simulation.players = players
    simulation.current_hole = 1
    simulation._initialize_hole(1)
    
    # Check who the captain is
    hole_state = simulation.hole_states[simulation.current_hole]
    print(f"🔍 Captain: {hole_state.teams.captain}")
    print(f"🔍 Hitting order: {hole_state.hitting_order}")
    
    # Test partnership request and acceptance
    captain_id = hole_state.teams.captain
    result1 = simulation.request_partner(captain_id, "p2")  # Captain requests partner
    print(f"✅ Partnership requested: {result1.get('status')}")
    
    result2 = simulation.respond_to_partnership("p2", True)  # Partner accepts
    print(f"✅ Partnership accepted: {result2.get('status')}")
    
    # Check that partnership was formed
    hole_state = simulation.hole_states[simulation.current_hole]
    print(f"✅ Teams type: {hole_state.teams.type}")
    print(f"✅ Team 1: {hole_state.teams.team1}")
    print(f"✅ Team 2: {hole_state.teams.team2}")
    
    assert hole_state.teams.type == "partners", "Should be partners after acceptance"
    assert captain_id in hole_state.teams.team1 and "p2" in hole_state.teams.team1, "Captain and partner should be on team1"
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
    
    from app.wolf_goat_pig_simulation import WolfGoatPigSimulation
    from app.domain.player import Player
    
    # Test shot simulation via WGP simulation
    simulation = WolfGoatPigSimulation(player_count=4)
    human_player = Player("p1", "Test1", 12.0)
    computer_configs = [
        {"id": "p2", "name": "Test2", "handicap": 15.0, "personality": "balanced"},
        {"id": "p3", "name": "Test3", "handicap": 8.0, "personality": "aggressive"},
        {"id": "p4", "name": "Test4", "handicap": 20.0, "personality": "conservative"}
    ]
    
    game_state = simulation.setup_simulation(human_player, computer_configs, "default_course")
    
    # Enable shot progression mode
    simulation.enable_shot_progression()
    result = simulation.simulate_shot("p1")
    
    shot_result = result.get('shot_result', {})
    print(f"✅ Shot simulation result: distance={shot_result.get('distance_to_pin')}, lie={shot_result.get('lie_type')}")
    
    assert 'shot_result' in result, "Should have shot result"
    assert 'distance_to_pin' in shot_result, "Should have distance to pin"
    assert 'lie_type' in shot_result, "Should have lie type"
    assert 'shot_quality' in shot_result, "Should have shot quality"
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
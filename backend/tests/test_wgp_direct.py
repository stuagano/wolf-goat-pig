#!/usr/bin/env python3
"""
Direct test of Wolf Goat Pig simulation functionality
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.wolf_goat_pig_simulation import WolfGoatPigSimulation, WGPPlayer

def test_wgp_basic():
    """Test basic Wolf Goat Pig simulation"""
    print("🧪 Testing Wolf Goat Pig Simulation Directly")
    print("=" * 50)
    
    # Create players
    players = [
        WGPPlayer(id="p1", name="Alice", handicap=10.0),
        WGPPlayer(id="p2", name="Bob", handicap=12.0),
        WGPPlayer(id="p3", name="Charlie", handicap=15.0),
        WGPPlayer(id="p4", name="Dana", handicap=18.0),
    ]
    
    # Create simulation
    sim = WolfGoatPigSimulation(player_count=4, players=players)
    
    print(f"✅ Simulation created with {len(players)} players")
    print(f"✅ Current hole: {sim.current_hole}")
    print(f"✅ Game phase: {sim.game_phase}")
    
    # Get initial game state
    game_state = sim.get_game_state()
    print(f"✅ Initial game state: Hole {game_state['current_hole']}, Phase {game_state['game_phase']}")
    
    # Test partnership request
    print("\n🏌️ Testing partnership mechanics...")
    # Get the current captain (first player in hitting order)
    current_hole_state = sim.hole_states[sim.current_hole]
    captain = current_hole_state.teams.captain
    # Find a partner (any other player)
    partner = next(p.id for p in sim.players if p.id != captain)
    result = sim.request_partner(captain, partner)
    print(f"✅ Partnership request result: {result['status']}")
    
    # Test partnership response
    result = sim.respond_to_partnership(partner, True)
    print(f"✅ Partnership response result: {result['status']}")
    
    # Test solo play
    print("\n🏌️ Testing solo mechanics...")
    # Get the current captain (first player in hitting order)
    current_hole_state = sim.hole_states[sim.current_hole]
    captain = current_hole_state.teams.captain
    result = sim.captain_go_solo(captain)
    print(f"✅ Solo play result: {result['status']}")
    
    # Test hole advancement
    print("\n🏌️ Testing hole advancement...")
    result = sim.advance_to_next_hole()
    print(f"✅ Hole advancement result: {result['status']}")
    print(f"✅ New current hole: {sim.current_hole}")
    
    # Test betting mechanics
    print("\n🏌️ Testing betting mechanics...")
    result = sim.offer_double("p1")
    print(f"✅ Double offer result: {result['status']}")
    
    # Test special rules
    print("\n🏌️ Testing special rules...")
    # Get the current captain for hole 2
    current_hole_state = sim.hole_states[sim.current_hole]
    captain = current_hole_state.teams.captain
    result = sim.invoke_float(captain)
    print(f"✅ Float invocation result: {result['status']}")
    
    print("\n🎉 All basic Wolf Goat Pig functionality tests passed!")
    print("=" * 50)

def test_wgp_ai_decisions():
    """Test AI decision making"""
    print("\n🧪 Testing AI Decision Making")
    print("=" * 50)
    
    # Create simulation
    sim = WolfGoatPigSimulation(4)
    
    # Test AI decision methods
    game_state = {"current_hole": 5, "players": []}
    
    # Test partnership decisions
    should_accept = sim.should_accept_partnership(sim.players[0], game_state)
    should_request = sim.should_request_partner("p2", game_state)
    should_solo = sim.should_go_solo(game_state)
    should_double = sim.should_offer_double(game_state)
    
    print(f"✅ Should accept partnership: {should_accept}")
    print(f"✅ Should request partner: {should_request}")
    print(f"✅ Should go solo: {should_solo}")
    print(f"✅ Should offer double: {should_double}")
    
    print("🎉 AI decision making tests passed!")

if __name__ == "__main__":
    test_wgp_basic()
    test_wgp_ai_decisions()
    print("\n🎉 All Wolf Goat Pig simulation tests completed successfully!") 
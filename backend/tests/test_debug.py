#!/usr/bin/env python3
"""
Debug script to test Wolf Goat Pig simulation
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.wolf_goat_pig_simulation import WolfGoatPigSimulation, WGPPlayer

def test_basic():
    """Test basic functionality"""
    print("🧪 Testing Wolf Goat Pig Simulation")
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
    
    print(f"✅ Simulation created")
    print(f"✅ Current hole: {sim.current_hole}")
    print(f"✅ Hole states type: {type(sim.hole_states)}")
    print(f"✅ Hole states keys: {list(sim.hole_states.keys())}")
    
    # Test get_game_state
    try:
        game_state = sim.get_game_state()
        print(f"✅ get_game_state() works")
    except Exception as e:
        print(f"❌ get_game_state() failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Test enable_shot_progression
    try:
        result = sim.enable_shot_progression()
        print(f"✅ enable_shot_progression() works")
    except Exception as e:
        print(f"❌ enable_shot_progression() failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Test simulate_shot
    try:
        shot_result = sim.simulate_shot("p1")
        print(f"✅ simulate_shot() works")
    except Exception as e:
        print(f"❌ simulate_shot() failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_basic() 
#!/usr/bin/env python3
"""Test script for golf accuracy fixes"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.wolf_goat_pig_simulation import WolfGoatPigSimulation, WGPPlayer

def test_shot_progression():
    """Test that shot progression is realistic"""
    
    # Create simulation with test players (need 4 for Wolf Goat Pig)
    players = [
        WGPPlayer(id="test1", name="Test Player 1", handicap=18),
        WGPPlayer(id="test2", name="Test Player 2", handicap=5),
        WGPPlayer(id="test3", name="Test Player 3", handicap=12),
        WGPPlayer(id="test4", name="Test Player 4", handicap=8)
    ]
    
    sim = WolfGoatPigSimulation(player_count=4, players=players)
    sim.enable_shot_progression()
    
    print("Testing shot progression fixes...")
    print("=" * 50)
    
    # Test multiple shots for each player
    for i in range(10):  # Try 10 shots max
        try:
            # Get next player
            hole_state = sim.hole_states.get(sim.current_hole)
            if not hole_state:
                print("No hole state found")
                break
            next_player = hole_state.next_player_to_hit
            if not next_player:
                print("No more players to hit")
                break
                
            print(f"\nShot {i+1}: {next_player}")
            
            # Get previous distance before the shot
            prev_distance = None
            prev_ball = hole_state.ball_positions.get(next_player)
            if prev_ball:
                prev_distance = prev_ball.distance_to_pin
            
            # Simulate shot
            result = sim.simulate_shot(next_player)
            
            if result.get("hole_complete"):
                print("Hole completed!")
                break
                
            shot_result = result["shot_result"]
            print(f"  Quality: {shot_result['shot_quality']}")
            print(f"  Distance: {shot_result['distance_to_pin']:.1f} yards")
            print(f"  Shot count: {shot_result['shot_number']}")
            
            # Check for progression issues
            if prev_distance is not None:
                current_distance = shot_result['distance_to_pin']
                if current_distance > prev_distance and shot_result['shot_quality'] in ['poor', 'terrible']:
                    print(f"  ⚠️  WARNING: {shot_result['shot_quality']} shot went BACKWARDS: {prev_distance:.1f} → {current_distance:.1f}")
                elif current_distance < prev_distance:
                    print(f"  ✅ Progress: {prev_distance:.1f} → {current_distance:.1f} ({prev_distance - current_distance:.1f} yards closer)")
            
            # Check for unrealistic patterns
            if shot_result['shot_number'] > 8:
                print(f"  ⚠️  WARNING: Shot count exceeds limit!")
                
        except Exception as e:
            print(f"Error on shot {i+1}: {e}")
            break
    
    print("\n" + "=" * 50)
    print("Test completed")

if __name__ == "__main__":
    test_shot_progression()
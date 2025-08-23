#!/usr/bin/env python3
"""
Test shot progression logic directly
"""

import sys
import os

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(__file__))

try:
    from app.wolf_goat_pig_simulation import WolfGoatPigSimulation
    
    def test_progression_logic():
        """Test shot progression from different starting distances"""
        print("🧪 Testing Shot Progression Logic")
        print("=" * 40)
        
        sim = WolfGoatPigSimulation()
        
        # Test approach shot progression
        print("\n🏌️ Full Shot Progression (>100 yards)")
        starting_distances = [300, 250, 200, 150, 120]
        handicap = 12  # Mid handicap
        
        for start_dist in starting_distances:
            new_dist = sim._simulate_approach_shot(handicap, start_dist, "fairway")
            advancement = start_dist - new_dist
            print(f"  {start_dist}yd -> {new_dist:.1f}yd (advanced {advancement:.1f}yd)")
            
            if new_dist >= start_dist:
                print(f"  ⚠️ WARNING: No advancement from {start_dist}yd!")
            elif advancement < 10:
                print(f"  ⚠️ WARNING: Only {advancement:.1f}yd advancement!")
        
        print("\n⛳ Short Game Progression (<100 yards)")
        short_distances = [90, 70, 50, 30, 15, 8, 3, 1]
        
        for start_dist in short_distances:
            new_dist = sim._simulate_short_game_shot(handicap, start_dist, "fairway")
            advancement = start_dist - new_dist
            print(f"  {start_dist}yd -> {new_dist:.1f}yd", end="")
            
            if new_dist == 0:
                print(" ⛳ HOLED OUT!")
            elif new_dist < start_dist:
                print(f" (advanced {advancement:.1f}yd)")
            else:
                print(f" ⚠️ WENT BACKWARDS {abs(advancement):.1f}yd!")
        
        print("\n🎯 Testing Hole Completion Simulation")
        # Simulate multiple shots from different handicaps to see progression
        test_cases = [
            {"handicap": 5, "name": "Low handicap"},
            {"handicap": 12, "name": "Mid handicap"}, 
            {"handicap": 20, "name": "High handicap"}
        ]
        
        for case in test_cases:
            print(f"\n📊 {case['name']} (handicap {case['handicap']})")
            distance = 400  # Start from 400 yards
            shots = 0
            max_shots = 15
            
            while distance > 0 and shots < max_shots:
                shots += 1
                if distance > 100:
                    new_distance = sim._simulate_approach_shot(case['handicap'], distance, "fairway")
                else:
                    new_distance = sim._simulate_short_game_shot(case['handicap'], distance, "fairway")
                
                advancement = distance - new_distance
                print(f"  Shot {shots}: {distance:.0f}yd -> {new_distance:.1f}yd (advanced {advancement:.1f}yd)")
                
                if new_distance == 0:
                    print(f"  🎯 COMPLETED HOLE in {shots} shots!")
                    break
                elif new_distance >= distance:
                    print(f"  ⚠️ No progress on shot {shots}, stopping test")
                    break
                    
                distance = new_distance
            
            if distance > 0:
                print(f"  ❌ Did not complete hole after {shots} shots ({distance:.1f}yd remaining)")
        
        return True
        
    if __name__ == "__main__":
        success = test_progression_logic()
        exit(0 if success else 1)
        
except ImportError as e:
    print(f"❌ Import error: {e}")
    exit(1)
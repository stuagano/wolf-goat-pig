#!/usr/bin/env python3
"""
Test script to verify simulation uses course data properly
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.wolf_goat_pig_simulation import WolfGoatPigSimulation
from app.game_state import GameState

def test_simulation_with_courses():
    """Test that simulation properly uses course data"""
    print("🧪 Testing Simulation with Course Data")
    print("=" * 50)
    
    # Create simulation engine
    engine = WolfGoatPigSimulation()
    
    # Test human player
    human_player = {
        "id": "human",
        "name": "Test Player",
        "handicap": 15.0,
        "strength": "Average"
    }
    
    # Test computer players
    computer_configs = [
        {"id": "comp1", "name": "Alice", "handicap": 12.0, "personality": "balanced"},
        {"id": "comp2", "name": "Bob", "handicap": 18.0, "personality": "aggressive"},
        {"id": "comp3", "name": "Charlie", "handicap": 8.0, "personality": "conservative"}
    ]
    
    # Test with different courses
    courses_to_test = ["Wing Point", "Championship Links", "Executive Course"]
    
    for course_name in courses_to_test:
        print(f"\n🏌️ Testing with course: {course_name}")
        print("-" * 30)
        
        # Setup simulation with course
        game_state = engine.setup_simulation(human_player, computer_configs, course_name)
        
        # Verify course data is set
        print(f"✅ Selected course: {game_state.selected_course}")
        print(f"✅ Hole pars: {game_state.hole_pars[:5]}... (showing first 5)")
        print(f"✅ Hole yards: {game_state.hole_yards[:5]}... (showing first 5)")
        print(f"✅ Stroke indexes: {game_state.hole_stroke_indexes[:5]}... (showing first 5)")
        print(f"✅ Descriptions: {len(game_state.hole_descriptions)} descriptions loaded")
        
        # Test hole difficulty calculation
        hole_1_difficulty = engine._assess_hole_difficulty(game_state)
        print(f"✅ Hole 1 difficulty factor: {hole_1_difficulty:.3f}")
        
        # Test player score simulation with distance factor
        hole_1_par = game_state.hole_pars[0]
        hole_1_yards = game_state.hole_yards[0]
        print(f"✅ Hole 1: Par {hole_1_par}, {hole_1_yards} yards")
        
        # Simulate a few scores to see distance factor in action
        scores = []
        for _ in range(5):
            score = engine._simulate_player_score(15.0, hole_1_par, 1, game_state)
            scores.append(score)
        print(f"✅ Sample scores for 15 handicap: {scores}")
        
        # Test Monte Carlo with course
        print(f"\n📊 Running Monte Carlo simulation (10 games)...")
        results = engine.run_monte_carlo_simulation(
            human_player, 
            computer_configs, 
            num_simulations=10, 
            course_name=course_name
        )
        
        summary = results.get_summary()
        human_stats = summary["player_statistics"]["human"]
        print(f"✅ Human player results:")
        print(f"   - Win rate: {human_stats['win_percentage']:.1f}%")
        print(f"   - Average score: {human_stats['average_score']:.1f}")
        print(f"   - Best score: {human_stats['best_score']}")
        print(f"   - Worst score: {human_stats['worst_score']}")
    
    print(f"\n🎉 All course tests completed successfully!")
    print("=" * 50)

if __name__ == "__main__":
    test_simulation_with_courses() 
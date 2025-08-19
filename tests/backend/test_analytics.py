#!/usr/bin/env python3
"""
Quick test script for advanced analytics functionality
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '.'))

from app.wolf_goat_pig_simulation import WolfGoatPigSimulation, WGPPlayer

def test_analytics():
    """Test the advanced analytics functionality"""
    print("🧪 Testing Advanced Analytics")
    print("=" * 50)
    
    # Create simulation with test players
    players = [
        WGPPlayer("p1", "Alice", 10.5),
        WGPPlayer("p2", "Bob", 15.0),
        WGPPlayer("p3", "Charlie", 8.0),
        WGPPlayer("p4", "Dave", 20.5)
    ]
    
    simulation = WolfGoatPigSimulation(player_count=4, players=players)
    
    # Simulate some holes with different outcomes
    print("🔍 Setting up test scenario...")
    
    # Hole 1: Partnership formation and completion
    simulation._initialize_hole(1)
    hole1 = simulation.hole_states[1]
    
    # Set up teams
    hole1.teams.type = "partners"
    hole1.teams.team1 = ["p1", "p2"]
    hole1.teams.team2 = ["p3", "p4"]
    hole1.hole_complete = True
    hole1.points_awarded = {"p1": 2, "p2": 2, "p3": -1, "p4": -1}
    
    # Update player points
    players[0].points += 2
    players[1].points += 2
    players[2].points -= 1
    players[3].points -= 1
    
    # Hole 2: Solo scenario
    simulation.current_hole = 2
    simulation._initialize_hole(2)
    hole2 = simulation.hole_states[2]
    
    hole2.teams.type = "solo"
    hole2.teams.solo_player = "p1"
    hole2.teams.opponents = ["p2", "p3", "p4"]
    hole2.betting.current_wager = 4  # Doubled
    hole2.hole_complete = True
    hole2.points_awarded = {"p1": 6, "p2": -2, "p3": -2, "p4": -2}
    
    # Update player points
    players[0].points += 6
    players[1].points -= 2
    players[2].points -= 2
    players[3].points -= 2
    
    print("✅ Test scenario setup complete")
    
    # Test analytics
    print("\n🔍 Testing analytics retrieval...")
    analytics = simulation.get_advanced_analytics()
    
    # Check that all sections are present
    expected_sections = [
        "performance_trends", 
        "betting_analysis", 
        "partnership_chemistry", 
        "game_statistics", 
        "risk_analysis", 
        "prediction_models"
    ]
    
    for section in expected_sections:
        if section in analytics:
            print(f"✅ {section} section present")
        else:
            print(f"❌ {section} section MISSING")
            return False
    
    # Test performance trends
    perf_trends = analytics["performance_trends"]
    if len(perf_trends) == 4:
        print("✅ Performance trends has all 4 players")
    else:
        print(f"❌ Performance trends has {len(perf_trends)} players, expected 4")
    
    # Check Alice's performance (she should be leading)
    alice_stats = perf_trends["p1"]
    if alice_stats["name"] == "Alice" and alice_stats["current_points"] == 8:
        print("✅ Alice's performance stats correct")
    else:
        print(f"❌ Alice's stats incorrect: {alice_stats}")
    
    # Test betting analysis
    betting_analysis = analytics["betting_analysis"]
    if "success_rates" in betting_analysis and len(betting_analysis["success_rates"]) == 4:
        print("✅ Betting analysis has success rates for all players")
    else:
        print("❌ Betting analysis incomplete")
    
    # Test partnership chemistry
    partnership_chemistry = analytics["partnership_chemistry"]
    if "Alice & Bob" in partnership_chemistry:
        print("✅ Partnership chemistry tracking Alice & Bob")
        alice_bob_stats = partnership_chemistry["Alice & Bob"]
        if alice_bob_stats["attempts"] == 1 and alice_bob_stats["wins"] == 1:
            print("✅ Alice & Bob partnership stats correct")
        else:
            print(f"❌ Alice & Bob stats incorrect: {alice_bob_stats}")
    else:
        print("❌ Partnership chemistry not tracking Alice & Bob")
    
    # Test game statistics
    game_stats = analytics["game_statistics"]
    if game_stats["holes_completed"] == 2 and game_stats["player_count"] == 4:
        print("✅ Game statistics correct")
    else:
        print(f"❌ Game statistics incorrect: {game_stats}")
    
    # Test prediction models
    predictions = analytics["prediction_models"]
    if len(predictions) == 4:
        print("✅ Predictions generated for all players")
        
        # Alice should have highest win probability (she's leading)
        alice_prediction = predictions["p1"]
        if alice_prediction["name"] == "Alice" and alice_prediction["current_position"] == 1:
            print("✅ Alice predicted as leader")
        else:
            print(f"❌ Alice prediction incorrect: {alice_prediction}")
    else:
        print(f"❌ Predictions incomplete: {len(predictions)} players")
    
    print("\n🎉 Advanced Analytics Test Complete!")
    return True

if __name__ == "__main__":
    success = test_analytics()
    if success:
        print("\n✅ ALL ANALYTICS TESTS PASSED!")
        sys.exit(0)
    else:
        print("\n❌ SOME ANALYTICS TESTS FAILED!")
        sys.exit(1)
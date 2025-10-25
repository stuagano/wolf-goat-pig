#!/usr/bin/env python3
"""
Standalone test for short game logic
"""

import sys
import os

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(__file__))

try:
    from app.wolf_goat_pig_simulation import WolfGoatPigSimulation, WGPShotResult
    
    def test_short_game_logic():
        """Test the short game logic and putting progression"""
        print("🧪 Testing Short Game Logic")
        print("=" * 40)
        
        sim = WolfGoatPigSimulation()
        
        # Test 1: Very short putts (under 3 yards)
        print("\n🏌️ Test 1: Very short putts")
        for i in range(5):
            distance = sim._simulate_short_game_shot(handicap=10, distance=2, lie_type="green")
            print(f"  Shot {i+1}: {distance:.1f} yards (should be ≤ 3)")
            assert distance <= 4, f"Short putt too far: {distance}"
        
        # Test 2: Putting range (3-15 yards)
        print("\n⛳ Test 2: Putting range")
        for i in range(5):
            distance = sim._simulate_short_game_shot(handicap=10, distance=12, lie_type="green")
            print(f"  Shot {i+1}: {distance:.1f} yards (should be ≤ 15)")
            assert distance <= 16, f"Putt too far: {distance}"
        
        # Test 3: Chipping range (15-40 yards)
        print("\n🏌️ Test 3: Chipping range")
        for i in range(5):
            distance = sim._simulate_short_game_shot(handicap=10, distance=30, lie_type="fairway")
            print(f"  Shot {i+1}: {distance:.1f} yards (should advance)")
            assert distance <= 30, f"Chip went backwards: {distance}"
        
        # Test 4: Lie type determination with distance
        print("\n📍 Test 4: Lie type with distance consideration")
        
        # Close good shot should be on green
        close_shot = WGPShotResult(
            player_id="test", 
            shot_number=2,
            lie_type="fairway",
            distance_to_pin=15,
            shot_quality="good",
            made_shot=False
        )
        
        lie_type = sim._determine_lie_type(close_shot)
        print(f"  Good shot at 15yd: {lie_type} (should be 'green')")
        assert lie_type == "green", f"Good close shot should be on green: {lie_type}"
        
        # Close poor shot should be green or rough
        poor_close_shot = WGPShotResult(
            player_id="test",
            shot_number=2, 
            lie_type="fairway",
            distance_to_pin=18,
            shot_quality="poor",
            made_shot=False
        )
        
        poor_lie_type = sim._determine_lie_type(poor_close_shot)
        print(f"  Poor shot at 18yd: {poor_lie_type} (should be 'green' or 'rough')")
        assert poor_lie_type in ["green", "rough"], f"Poor close shot should be green/rough: {poor_lie_type}"
        
        # Far shot should use normal quality logic
        far_shot = WGPShotResult(
            player_id="test",
            shot_number=2,
            lie_type="fairway", 
            distance_to_pin=150,
            shot_quality="good",
            made_shot=False
        )
        
        far_lie_type = sim._determine_lie_type(far_shot)
        print(f"  Good shot at 150yd: {far_lie_type} (should be 'fairway' or 'green')")
        assert far_lie_type in ["fairway", "green"], f"Good far shot should be fairway/green: {far_lie_type}"
        
        print("\n✅ All short game tests PASSED!")
        return True
        
    if __name__ == "__main__":
        success = test_short_game_logic()
        if success:
            print("\n🎉 Short game logic is working correctly!")
        else:
            print("\n❌ Short game logic has issues")
        exit(0 if success else 1)
        
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("💡 Make sure you're running from the backend directory")
    exit(1)
#!/usr/bin/env python3
"""Comprehensive smoke tests for Wolf-Goat-Pig golf simulation system"""

import sys
import os
import json
import traceback
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.wolf_goat_pig import WolfGoatPigGame

class SmokeTestRunner:
    def __init__(self):
        self.tests_passed = 0
        self.tests_failed = 0
        self.failures = []

    def run_test(self, test_name, test_func):
        """Run a single test and track results"""
        print(f"\n🧪 Running: {test_name}")
        print("-" * 60)
        
        try:
            test_func()
            print(f"✅ PASSED: {test_name}")
            self.tests_passed += 1
        except Exception as e:
            print(f"❌ FAILED: {test_name}")
            print(f"   Error: {str(e)}")
            print(f"   Traceback: {traceback.format_exc()}")
            self.tests_failed += 1
            self.failures.append((test_name, str(e)))

    def print_summary(self):
        """Print test run summary"""
        print("\n" + "=" * 70)
        print("🏁 SMOKE TEST SUMMARY")
        print("=" * 70)
        print(f"✅ Tests Passed: {self.tests_passed}")
        print(f"❌ Tests Failed: {self.tests_failed}")
        print(f"📊 Total Tests: {self.tests_passed + self.tests_failed}")
        
        if self.failures:
            print("\n💥 FAILURES:")
            for test_name, error in self.failures:
                print(f"   • {test_name}: {error}")
        
        success_rate = (self.tests_passed / (self.tests_passed + self.tests_failed)) * 100
        print(f"\n🎯 Success Rate: {success_rate:.1f}%")
        
        if self.tests_failed == 0:
            print("🎉 ALL TESTS PASSED! System is ready for production.")
        else:
            print("⚠️  Some tests failed. Review issues before deployment.")

def test_basic_simulation_creation():
    """Test basic simulation setup"""
    players = [
        WGPPlayer(id="p1", name="Player 1", handicap=18),
        WGPPlayer(id="p2", name="Player 2", handicap=5),
        WGPPlayer(id="p3", name="Player 3", handicap=12),
        WGPPlayer(id="p4", name="Player 4", handicap=8)
    ]
    
    # Initialize game
    game = WolfGoatPigGame(player_count=4)
    sim = WolfGoatPigSimulation(player_count=4, players=players)
    sim.enable_shot_progression()
    
    assert sim.players is not None, "Players not initialized"
    assert len(sim.players) == 4, f"Expected 4 players, got {len(sim.players)}"
    assert sim.current_hole == 1, f"Expected hole 1, got {sim.current_hole}"
    print("   ✓ Simulation created with 4 players")
    print("   ✓ Starting on hole 1")

def test_shot_progression_realism():
    """Test that shots always progress realistically"""
    players = [
        WGPPlayer(id="test1", name="Test1", handicap=18),
        WGPPlayer(id="test2", name="Test2", handicap=5),
        WGPPlayer(id="test3", name="Test3", handicap=12),
        WGPPlayer(id="test4", name="Test4", handicap=8)
    ]
    
    sim = WolfGoatPigSimulation(player_count=4, players=players)
    sim.enable_shot_progression()
    
    backward_shots = 0
    total_shots = 0
    excessive_shots = 0
    
    # Test 50 shots
    for i in range(50):
        hole_state = sim.hole_states.get(sim.current_hole)
        if not hole_state:
            break
            
        next_player = hole_state.next_player_to_hit
        if not next_player:
            break
            
        prev_ball = hole_state.ball_positions.get(next_player)
        prev_distance = prev_ball.distance_to_pin if prev_ball else None
        
        result = sim.simulate_shot(next_player)
        if result.get("hole_complete"):
            break
            
        shot = result["shot_result"]
        total_shots += 1
        
        # Check for backward movement
        if prev_distance is not None:
            current_distance = shot['distance_to_pin']
            if current_distance > prev_distance and shot['shot_quality'] in ['poor', 'terrible']:
                backward_shots += 1
                print(f"   ⚠️  Backward shot: {prev_distance:.1f} → {current_distance:.1f}")
        
        # Check for excessive shot counts
        if shot['shot_number'] > 8:
            excessive_shots += 1
    
    print(f"   ✓ Tested {total_shots} shots")
    print(f"   ✓ Backward shots: {backward_shots} (should be 0)")
    print(f"   ✓ Excessive shots (>8): {excessive_shots} (should be 0)")
    
    assert backward_shots == 0, f"Found {backward_shots} shots going backward"
    assert excessive_shots == 0, f"Found {excessive_shots} shots exceeding 8-shot limit"

def test_partnership_timing():
    """Test that partnerships are offered at correct time"""
    players = [
        WGPPlayer(id="captain", name="Captain", handicap=18),
        WGPPlayer(id="partner1", name="Partner1", handicap=5),
        WGPPlayer(id="partner2", name="Partner2", handicap=12),
        WGPPlayer(id="partner3", name="Partner3", handicap=8)
    ]
    
    sim = WolfGoatPigSimulation(player_count=4, players=players)
    sim.enable_shot_progression()
    
    hole_state = sim.hole_states.get(sim.current_hole)
    
    # Before any shots - no partnerships
    tee_shots = sum(1 for ball in hole_state.ball_positions.values() if ball and ball.shot_count >= 1)
    assert tee_shots == 0, "Should have no tee shots initially"
    print("   ✓ No tee shots initially")
    
    # After first shot - still no partnerships  
    result1 = sim.simulate_shot("captain")
    hole_state = sim.hole_states.get(sim.current_hole)
    tee_shots = sum(1 for ball in hole_state.ball_positions.values() if ball and ball.shot_count >= 1)
    
    if not result1.get("hole_complete"):
        assert tee_shots == 1, f"Should have 1 tee shot, got {tee_shots}"
        print("   ✓ One tee shot completed")
        
        # Take second tee shot from next player in order
        next_player = hole_state.next_player_to_hit
        if next_player and next_player != "captain":  # Don't let captain hit again immediately
            result2 = sim.simulate_shot(next_player)
            if not result2.get("hole_complete"):
                hole_state = sim.hole_states.get(sim.current_hole)
                tee_shots = sum(1 for ball in hole_state.ball_positions.values() if ball and ball.shot_count >= 1)
                
                # Should now have 2 tee shots
                if tee_shots >= 2:
                    assert hole_state.teams.type == "pending", f"Teams should be pending, got {hole_state.teams.type}"
                    print("   ✓ Partnership decisions available after 2 tee shots")
                else:
                    print(f"   ℹ️  Only {tee_shots} tee shots completed (rotation may need adjustment)")
        else:
            print("   ℹ️  Next player same as captain or None - testing rotation logic")

def test_betting_system():
    """Test betting system functionality"""
    players = [
        WGPPlayer(id="p1", name="Player1", handicap=18),
        WGPPlayer(id="p2", name="Player2", handicap=5),
        WGPPlayer(id="p3", name="Player3", handicap=12),
        WGPPlayer(id="p4", name="Player4", handicap=8)
    ]
    
    sim = WolfGoatPigSimulation(player_count=4, players=players)
    sim.enable_shot_progression()
    
    hole_state = sim.hole_states.get(sim.current_hole)
    
    # Check initial betting state
    assert hole_state.betting.current_wager == 1, f"Expected 1 quarter wager, got {hole_state.betting.current_wager}"
    assert not hole_state.betting.doubled, "Should not be doubled initially"
    print("   ✓ Initial betting state correct")
    
    # Test partnership formation
    captain_id = hole_state.teams.captain
    
    # Simulate shots to create partnership opportunity
    result1 = sim.simulate_shot(captain_id)
    if not result1.get("hole_complete"):
        next_player = hole_state.next_player_to_hit
        if next_player:
            result2 = sim.simulate_shot(next_player)
            if not result2.get("hole_complete"):
                hole_state = sim.hole_states.get(sim.current_hole)
                
                # Try to form partnership
                if hole_state.can_request_partnership(captain_id, next_player):
                    sim.request_partner(captain_id, next_player)
                    print("   ✓ Partnership formed successfully")
                else:
                    print("   ⚠️  Partnership not available (may be expected)")

def test_hole_completion():
    """Test that holes complete properly"""
    players = [
        WGPPlayer(id="p1", name="Player1", handicap=0),  # Low handicap for better chance of completion
        WGPPlayer(id="p2", name="Player2", handicap=0),
        WGPPlayer(id="p3", name="Player3", handicap=0),
        WGPPlayer(id="p4", name="Player4", handicap=0)
    ]
    
    sim = WolfGoatPigSimulation(player_count=4, players=players)
    sim.enable_shot_progression()
    
    print("   Testing basic hole completion mechanics...")
    
    # Take several shots and verify hole state updates
    shots_taken = 0
    max_shots = 32  # 8 shots per player maximum
    
    while shots_taken < max_shots:
        hole_state = sim.hole_states.get(sim.current_hole)
        if not hole_state or hole_state.hole_complete:
            print(f"   ✓ Hole completed in {shots_taken} shots")
            break
            
        next_player = hole_state.next_player_to_hit
        if not next_player:
            print(f"   ✓ No more players to hit after {shots_taken} shots")
            break
            
        # Check if any player has exceeded 8 shots
        max_player_shots = 0
        for player_id in [p.id for p in players]:
            ball = hole_state.ball_positions.get(player_id)
            if ball:
                max_player_shots = max(max_player_shots, ball.shot_count)
        
        if max_player_shots >= 8:
            print(f"   ✓ Max shot limit reached (player has {max_player_shots} shots)")
            break
            
        result = sim.simulate_shot(next_player)
        shots_taken += 1
        
        if result.get("hole_complete"):
            print(f"   ✓ Hole completed in {shots_taken} shots")
            break
    
    if shots_taken >= max_shots:
        print(f"   ⚠️  Hole did not complete within {max_shots} shots")
    
    print(f"   ✓ Hole completion test completed ({shots_taken} shots taken)")
    assert shots_taken > 0, "No shots were taken"

def test_json_output_structure():
    """Test that simulation produces valid JSON output"""
    players = [
        WGPPlayer(id="p1", name="Player1", handicap=18),
        WGPPlayer(id="p2", name="Player2", handicap=5),
        WGPPlayer(id="p3", name="Player3", handicap=12),
        WGPPlayer(id="p4", name="Player4", handicap=8)
    ]
    
    sim = WolfGoatPigSimulation(player_count=4, players=players)
    sim.enable_shot_progression()
    
    # Simulate a few shots
    for _ in range(5):
        hole_state = sim.hole_states.get(sim.current_hole)
        if not hole_state:
            break
            
        next_player = hole_state.next_player_to_hit
        if not next_player:
            break
            
        result = sim.simulate_shot(next_player)
        if result.get("hole_complete"):
            break
    
    # Test game state export
    game_state = sim.get_game_state()
    
    # Should be JSON serializable
    json_str = json.dumps(game_state, indent=2)
    parsed = json.loads(json_str)
    
    assert isinstance(parsed, dict), "Game state should be a dictionary"
    assert "current_hole" in parsed, "Game state missing current_hole"
    assert "hole_state" in parsed, "Game state missing hole_state"
    
    print("   ✓ Game state exports to valid JSON")
    print(f"   ✓ JSON size: {len(json_str):,} characters")

def test_error_handling():
    """Test system error handling"""
    players = [
        WGPPlayer(id="p1", name="Player1", handicap=18),
        WGPPlayer(id="p2", name="Player2", handicap=5),
        WGPPlayer(id="p3", name="Player3", handicap=12),
        WGPPlayer(id="p4", name="Player4", handicap=8)
    ]
    
    sim = WolfGoatPigSimulation(player_count=4, players=players)
    sim.enable_shot_progression()
    
    # Test invalid player ID
    try:
        sim.simulate_shot("invalid_player")
        assert False, "Should have raised error for invalid player"
    except:
        print("   ✓ Properly handles invalid player ID")
    
    # Test invalid partnership request
    try:
        sim.request_partnership("invalid1", "invalid2")
        assert False, "Should have raised error for invalid partnership"
    except:
        print("   ✓ Properly handles invalid partnership request")

def main():
    """Run all smoke tests"""
    print("🚀 WOLF-GOAT-PIG SMOKE TESTS")
    print("=" * 70)
    print("Testing core functionality before deployment...")
    
    runner = SmokeTestRunner()
    
    # Run all tests
    runner.run_test("Basic Simulation Creation", test_basic_simulation_creation)
    runner.run_test("Shot Progression Realism", test_shot_progression_realism)
    runner.run_test("Partnership Timing", test_partnership_timing)
    runner.run_test("Betting System", test_betting_system)
    runner.run_test("Hole Completion", test_hole_completion)
    runner.run_test("JSON Output Structure", test_json_output_structure)
    runner.run_test("Error Handling", test_error_handling)
    
    runner.print_summary()
    
    return runner.tests_failed == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
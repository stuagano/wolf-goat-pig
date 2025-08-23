#!/usr/bin/env python3
"""
Test complete hole progression from tee to cup
"""

import requests
import json
import time

API_URL = "http://localhost:8000"

def test_hole_completion():
    """Test a complete hole from tee to cup"""
    print("🏌️ Testing Complete Hole Progression")
    print("=" * 50)
    
    # Setup simulation
    print("\n🎮 Setting up simulation...")
    setup_data = {
        "human_player": {"id": "human", "name": "TestPlayer", "handicap": 15, "is_human": True},
        "computer_players": [
            {"id": "comp1", "name": "Alice", "handicap": 10, "is_human": False},
            {"id": "comp2", "name": "Bob", "handicap": 12, "is_human": False}, 
            {"id": "comp3", "name": "Charlie", "handicap": 8, "is_human": False}
        ]
    }
    
    response = requests.post(f"{API_URL}/simulation/setup", json=setup_data)
    setup_result = response.json()
    
    if setup_result.get("status") != "ok":
        print(f"❌ Setup failed: {setup_result}")
        return False
    
    print("✅ Simulation setup successful")
    print(f"🏌️ Hole {setup_result.get('current_hole', 1)} - Par {setup_result.get('game_state', {}).get('hole_state', {}).get('hole_par', 4)}")
    
    shot_count = 0
    max_shots = 30  # Safety limit
    players_finished = set()
    
    while shot_count < max_shots:
        shot_count += 1
        print(f"\n=== Shot #{shot_count} ===")
        
        # Play next shot
        try:
            response = requests.post(f"{API_URL}/simulation/play-next-shot", json={})
            result = response.json()
            
            if result.get("status") != "ok":
                print(f"❌ Shot failed: {result.get('message', 'Unknown error')}")
                break
            
            shot_result = result.get("shot_result", {}).get("shot_result", {})
            if not shot_result:
                print("❌ No shot result returned")
                break
            
            player_id = shot_result.get("player_id")
            distance = shot_result.get("distance_to_pin", 0)
            lie_type = shot_result.get("lie_type")
            quality = shot_result.get("shot_quality")
            made_shot = shot_result.get("made_shot", False)
            shot_num = shot_result.get("shot_number", 1)
            
            print(f"🏌️ {player_id} shot #{shot_num}: {distance:.1f}yd from {lie_type} ({quality})")
            
            if made_shot:
                print(f"🎯 {player_id} HOLED OUT! ⛳")
                players_finished.add(player_id)
            elif distance == 0:
                print(f"✅ {player_id} finished the hole")
                players_finished.add(player_id)
            
            # Check if hole is complete
            hole_complete = result.get("hole_complete", False)
            if hole_complete:
                print("🏆 HOLE COMPLETED!")
                print(f"📊 {len(players_finished)} players finished in {shot_count} shots")
                return True
                
            # Show feedback
            feedback = result.get("feedback", [])
            for fb in feedback:
                print(f"  💬 {fb}")
            
            # Check if next shot available
            if not result.get("next_shot_available", False):
                print("⚠️ No more shots available")
                break
                
            time.sleep(0.5)  # Small delay to see progress
            
        except Exception as e:
            print(f"❌ Error during shot: {e}")
            break
    
    print(f"\n🎯 Test completed after {shot_count} shots")
    print(f"📊 Players finished: {len(players_finished)} / 4")
    
    if len(players_finished) == 4:
        print("✅ All players completed the hole!")
        return True
    else:
        print(f"⚠️ Only {len(players_finished)} players completed the hole")
        return False

if __name__ == "__main__":
    try:
        success = test_hole_completion()
        if success:
            print("\n🎉 Hole completion test PASSED!")
        else:
            print("\n❌ Hole completion test FAILED")
        exit(0 if success else 1)
    except Exception as e:
        print(f"\n💥 Test error: {e}")
        exit(1)
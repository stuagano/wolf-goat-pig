#!/usr/bin/env python3
"""
Quick test script for 5/6-man Aardvark functionality
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '.'))

from app.wolf_goat_pig_simulation import WolfGoatPigSimulation, WGPPlayer

def test_5_man_aardvark():
    """Test 5-man game with Aardvark functionality"""
    print("🧪 Testing 5-Man Aardvark Game")
    print("=" * 50)
    
    # Create 5-man simulation
    players = [
        WGPPlayer("p1", "Alice", 10.5),
        WGPPlayer("p2", "Bob", 15.0),
        WGPPlayer("p3", "Charlie", 8.0),
        WGPPlayer("p4", "Dave", 20.5),
        WGPPlayer("p5", "Eve", 12.0)  # Aardvark
    ]
    
    simulation = WolfGoatPigSimulation(player_count=5, players=players)
    
    print(f"✅ 5-man simulation created with {len(simulation.players)} players")
    print(f"✅ Hoepfinger starts at hole {simulation.hoepfinger_start_hole}")
    
    # Test Aardvark functionality
    simulation._initialize_hole(1)
    hole_state = simulation.hole_states[1]
    
    print(f"🔍 Captain: {simulation._get_player_name(hole_state.teams.captain)}")
    print(f"🔍 Hitting order: {[simulation._get_player_name(p) for p in hole_state.hitting_order]}")
    
    # Test if player 5 is identified as Aardvark
    aardvark_id = hole_state.hitting_order[4]  # 5th player
    is_aardvark = simulation._is_aardvark(aardvark_id, hole_state)
    
    if is_aardvark:
        print(f"✅ {simulation._get_player_name(aardvark_id)} correctly identified as Aardvark")
    else:
        print(f"❌ {simulation._get_player_name(aardvark_id)} not identified as Aardvark")
        return False
    
    # Test Aardvark requesting to join a team
    print("\n🔍 Testing Aardvark team request...")
    
    # First, form teams among first 4 players
    captain_id = hole_state.teams.captain
    other_players = [p for p in hole_state.hitting_order[:4] if p != captain_id]
    partner_id = other_players[0]
    
    # Captain requests partnership
    result = simulation.request_partner(captain_id, partner_id)
    print(f"✅ Partnership requested: {result['status']}")
    
    # Partner accepts
    result = simulation.respond_to_partnership(partner_id, True)
    print(f"✅ Partnership formed: {result['status']}")
    
    # Now Aardvark can request to join team1
    result = simulation.aardvark_request_team(aardvark_id, "team1")
    print(f"✅ Aardvark request result: {result['status']}")
    
    # Test accepting Aardvark
    result = simulation.respond_to_aardvark("team1", True)
    print(f"✅ Aardvark acceptance result: {result['status']}")
    
    # Verify team composition
    if len(hole_state.teams.team1) == 3:
        print(f"✅ Team1 now has 3 players: {[simulation._get_player_name(p) for p in hole_state.teams.team1]}")
    else:
        print(f"❌ Team1 has {len(hole_state.teams.team1)} players, expected 3")
        return False
    
    return True

def test_aardvark_solo():
    """Test Aardvark going solo (Tunkarri)"""
    print("\n🧪 Testing Aardvark Solo (Tunkarri)")
    print("=" * 50)
    
    # Create 5-man simulation
    players = [
        WGPPlayer("p1", "Alice", 10.5),
        WGPPlayer("p2", "Bob", 15.0),
        WGPPlayer("p3", "Charlie", 8.0),
        WGPPlayer("p4", "Dave", 20.5),
        WGPPlayer("p5", "Eve", 12.0)  # Aardvark
    ]
    
    simulation = WolfGoatPigSimulation(player_count=5, players=players)
    simulation.current_hole = 2  # Set current hole before initializing
    simulation._initialize_hole(2)
    hole_state = simulation.hole_states[2]
    
    # Find the actual Aardvark (5th in hitting order for 5-man game)
    aardvark_id = hole_state.hitting_order[4]  # 5th player in hitting order
    print(f"🔍 Testing Aardvark: {simulation._get_player_name(aardvark_id)}")
    print(f"🔍 Is Aardvark: {simulation._is_aardvark(aardvark_id, hole_state)}")
    print(f"🔍 Player count: {simulation.player_count}")
    print(f"🔍 Aardvark index in hitting order: {hole_state.hitting_order.index(aardvark_id)}")
    print(f"🔍 Current hole: {simulation.current_hole}")
    print(f"🔍 Hole state exists: {simulation.current_hole in simulation.hole_states}")
    
    # Test Aardvark going solo with Tunkarri
    result = simulation.aardvark_go_solo(aardvark_id, use_tunkarri=True)
    
    if result["status"] == "solo":
        print(f"✅ Aardvark solo successful: {result['message']}")
        
        if hole_state.betting.tunkarri_invoked:
            print("✅ Tunkarri rule invoked")
        else:
            print("❌ Tunkarri rule not invoked")
            return False
            
        if hole_state.teams.type == "solo" and hole_state.teams.solo_player == aardvark_id:
            print("✅ Teams correctly set to solo")
        else:
            print("❌ Teams not correctly set")
            return False
    else:
        print(f"❌ Aardvark solo failed: {result}")
        return False
    
    return True

def test_6_man_game():
    """Test 6-man game basics"""
    print("\n🧪 Testing 6-Man Game Setup")
    print("=" * 50)
    
    # Create 6-man simulation
    players = [
        WGPPlayer("p1", "Alice", 10.5),
        WGPPlayer("p2", "Bob", 15.0),
        WGPPlayer("p3", "Charlie", 8.0),
        WGPPlayer("p4", "Dave", 20.5),
        WGPPlayer("p5", "Eve", 12.0),   # First Aardvark
        WGPPlayer("p6", "Frank", 18.0)  # Second Aardvark
    ]
    
    simulation = WolfGoatPigSimulation(player_count=6, players=players)
    
    print(f"✅ 6-man simulation created with {len(simulation.players)} players")
    print(f"✅ Hoepfinger starts at hole {simulation.hoepfinger_start_hole}")
    print(f"✅ Vinnie's Variation: {simulation.vinnie_variation_start}")
    
    # Test that both 5th and 6th players are Aardvarks
    simulation._initialize_hole(1)
    hole_state = simulation.hole_states[1]
    
    aardvark1_id = hole_state.hitting_order[4]  # 5th player
    aardvark2_id = hole_state.hitting_order[5]  # 6th player
    
    is_aardvark1 = simulation._is_aardvark(aardvark1_id, hole_state)
    is_aardvark2 = simulation._is_aardvark(aardvark2_id, hole_state)
    
    if is_aardvark1 and is_aardvark2:
        print(f"✅ Both {simulation._get_player_name(aardvark1_id)} and {simulation._get_player_name(aardvark2_id)} are Aardvarks")
    else:
        print(f"❌ Aardvark identification failed: {is_aardvark1}, {is_aardvark2}")
        return False
    
    return True

if __name__ == "__main__":
    success = True
    
    success &= test_5_man_aardvark()
    success &= test_aardvark_solo()
    success &= test_6_man_game()
    
    if success:
        print("\n🎉 ALL AARDVARK TESTS PASSED!")
        sys.exit(0)
    else:
        print("\n❌ SOME AARDVARK TESTS FAILED!")
        sys.exit(1)
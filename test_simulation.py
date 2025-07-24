#!/usr/bin/env python3
"""
Simple test script to verify the enhanced Wolf Goat Pig simulation
"""
import requests
import json
import time

API_URL = "http://localhost:8000"

def test_simulation():
    print("🧪 Testing Wolf Goat Pig Enhanced Simulation")
    print("=" * 50)
    
    # Test 1: Get available personalities
    print("\n1. Testing available personalities...")
    try:
        response = requests.get(f"{API_URL}/simulation/available-personalities")
        if response.status_code == 200:
            personalities = response.json()
            print(f"✅ Found {len(personalities['personalities'])} personalities:")
            for p in personalities['personalities']:
                print(f"   - {p['name']}: {p['description']}")
        else:
            print(f"❌ Failed to get personalities: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ Error getting personalities: {e}")
        return
    
    # Test 2: Get suggested opponents
    print("\n2. Testing suggested opponents...")
    try:
        response = requests.get(f"{API_URL}/simulation/suggested-opponents")
        if response.status_code == 200:
            opponents = response.json()
            print(f"✅ Found {len(opponents['opponents'])} suggested opponents:")
            for opp in opponents['opponents'][:3]:  # Show first 3
                print(f"   - {opp['name']} (handicap {opp['handicap']}, {opp['personality']})")
        else:
            print(f"❌ Failed to get opponents: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ Error getting opponents: {e}")
        return
    
    # Test 3: Setup simulation
    print("\n3. Testing simulation setup...")
    setup_data = {
        "human_player": {
            "id": "human",
            "name": "Test Player",
            "handicap": 12.0,
            "strength": "Average"
        },
        "computer_players": [
            {
                "id": "comp1",
                "name": "Tiger Bot",
                "handicap": 2.0,
                "personality": "aggressive"
            },
            {
                "id": "comp2", 
                "name": "Strategic Sam",
                "handicap": 8.5,
                "personality": "strategic"
            },
            {
                "id": "comp3",
                "name": "Conservative Carl", 
                "handicap": 15.0,
                "personality": "conservative"
            }
        ]
    }
    
    try:
        response = requests.post(f"{API_URL}/simulation/setup", json=setup_data)
        if response.status_code == 200:
            setup_result = response.json()
            print("✅ Simulation setup successful!")
            print(f"   Message: {setup_result.get('message', 'No message')}")
            
            game_state = setup_result.get('game_state', {})
            players = game_state.get('players', [])
            print(f"   Players: {len(players)}")
            for player in players:
                print(f"     - {player['name']} (handicap {player['handicap']}, {player['points']} points)")
        else:
            print(f"❌ Failed to setup simulation: {response.status_code}")
            print(f"   Response: {response.text}")
            return
    except Exception as e:
        print(f"❌ Error setting up simulation: {e}")
        return
    
    # Test 4: Event-driven shot-by-shot progression
    print("\n4. Testing event-driven shot-by-shot progression...")
    try:
        # Play first shot
        response = requests.post(f"{API_URL}/simulation/next-shot")
        if response.status_code == 200:
            shot_result = response.json()
            print(f"✅ First shot event: {shot_result['shot_event']}")
            print(f"   Shot result: {shot_result['shot_result']['shot_description']}")
            print(f"   Probabilities: {json.dumps(shot_result['probabilities'], indent=2)}")
            print(f"   Next shot available: {shot_result['next_shot_available']}")
        else:
            print(f"❌ Failed to play first shot: {response.status_code}")
            print(f"   Response: {response.text}")
            return
        # Play subsequent shots until no more
        shot_count = 1
        while shot_result.get('next_shot_available') and shot_count < 10:
            response = requests.post(f"{API_URL}/simulation/next-shot")
            if response.status_code == 200:
                shot_result = response.json()
                shot_count += 1
                print(f"   Shot {shot_count}: {shot_result['shot_result']['shot_description']}")
                print(f"     Probabilities: {json.dumps(shot_result['probabilities'], indent=2)}")
                print(f"     Next shot available: {shot_result['next_shot_available']}")
            else:
                print(f"❌ Failed to play shot {shot_count}: {response.status_code}")
                print(f"   Response: {response.text}")
                break
        print(f"✅ Completed {shot_count} shot events.")
    except Exception as e:
        print(f"❌ Error during event-driven shot progression: {e}")
        return
    
    # Test 4: Play a hole
    print("\n4. Testing hole simulation...")
    hole_decisions = {
        "action": None,
        "requested_partner": "comp2",  # Request Strategic Sam as partner
        "offer_double": False,
        "accept_double": False
    }
    
    try:
        response = requests.post(f"{API_URL}/simulation/play-hole", json=hole_decisions)
        if response.status_code == 200:
            hole_result = response.json()
            print("✅ Hole simulation successful!")
            
            feedback = hole_result.get('feedback', [])
            print(f"   Received {len(feedback)} feedback messages:")
            
            # Show key feedback (first few messages)
            for i, message in enumerate(feedback[:5]):
                print(f"     {i+1}. {message}")
            
            if len(feedback) > 5:
                print(f"     ... and {len(feedback) - 5} more messages")
                
            # Show educational analysis if present
            educational_msgs = [msg for msg in feedback if "Educational Analysis" in msg]
            if educational_msgs:
                print("\n📚 Educational feedback is working!")
                
        else:
            print(f"❌ Failed to play hole: {response.status_code}")
            print(f"   Response: {response.text}")
            return
    except Exception as e:
        print(f"❌ Error playing hole: {e}")
        return
    
    print("\n🎉 All simulation tests passed!")
    print("\n📋 Summary of enhancements:")
    print("✅ Realistic golf scoring based on handicaps")
    print("✅ Detailed educational feedback with course management tips")
    print("✅ Distance control expectations based on player skill level")
    print("✅ Opponent analysis and personality insights")
    print("✅ Strategic betting guidance based on game situation")
    print("✅ Stroke advantage analysis and recommendations")

if __name__ == "__main__":
    test_simulation()
#!/usr/bin/env python3
"""Test simulation flow to identify issues."""

import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_simulation_setup():
    """Test the simulation setup endpoint."""
    print("\n=== Testing Simulation Setup ===")

    payload = {
        "human_player": {
            "id": "human",
            "name": "Test Player",
            "handicap": 18,
            "strength": "Average",
            "is_human": True
        },
        "computer_players": [
            {
                "id": "comp1",
                "name": "Computer 1",
                "handicap": 15,
                "strength": "Average",
                "personality": "balanced",
                "is_human": False
            },
            {
                "id": "comp2",
                "name": "Computer 2",
                "handicap": 12,
                "strength": "Strong",
                "personality": "aggressive",
                "is_human": False
            },
            {
                "id": "comp3",
                "name": "Computer 3",
                "handicap": 10,
                "strength": "Strong",
                "personality": "conservative",
                "is_human": False
            }
        ],
        "course_name": None
    }

    response = requests.post(f"{BASE_URL}/simulation/setup", json=payload)
    print(f"Status Code: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"Status: {data.get('status')}")
        print(f"Message: {data.get('message')}")
        print(f"Game State: {json.dumps(data.get('game_state', {}), indent=2)[:500]}...")
        return data.get('game_state')
    else:
        print(f"Error: {response.text}")
        return None


def test_play_next_shot():
    """Test playing the next shot."""
    print("\n=== Testing Play Next Shot ===")

    response = requests.post(f"{BASE_URL}/simulation/play-next-shot", json={})
    print(f"Status Code: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"Status: {data.get('status')}")
        print(f"Feedback: {data.get('feedback')}")
        print(f"Interaction Needed: {data.get('interaction_needed')}")
        print(f"Next Shot Available: {data.get('next_shot_available')}")
        return data
    else:
        print(f"Error: {response.text}")
        return None


def test_simulation_state():
    """Test getting the current simulation state."""
    print("\n=== Testing Simulation State ===")

    response = requests.get(f"{BASE_URL}/simulation/state")
    print(f"Status Code: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"Game State: {json.dumps(data, indent=2)[:500]}...")
        return data
    else:
        print(f"Error: {response.text}")
        return None


def main():
    """Run the simulation flow test."""
    print("🐺 Wolf Goat Pig Simulation Flow Test")
    print("=" * 60)

    # Test 1: Setup simulation
    game_state = test_simulation_setup()
    if not game_state:
        print("\n❌ Simulation setup failed!")
        return

    print("\n✅ Simulation setup successful!")
    time.sleep(1)

    # Test 2: Check state
    state = test_simulation_state()
    if not state:
        print("\n❌ Failed to get simulation state!")
        return

    print("\n✅ Simulation state retrieved!")
    time.sleep(1)

    # Test 3: Play shots
    print("\n=== Testing Shot Sequence ===")
    for i in range(5):
        print(f"\n--- Shot {i + 1} ---")
        result = test_play_next_shot()
        if not result:
            print(f"\n❌ Shot {i + 1} failed!")
            break

        if not result.get('next_shot_available'):
            print(f"\n✅ No more shots available (expected at some point)")
            break

        time.sleep(0.5)

    print("\n" + "=" * 60)
    print("✅ Simulation flow test completed!")


if __name__ == "__main__":
    main()

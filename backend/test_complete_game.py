#!/usr/bin/env python3
"""
Test script to complete a full 18-hole game using the simplified API.
Tests implicit team assignment where Team 2 is automatically calculated.
"""

import requests
import json
import random
from typing import List, Dict

API_URL = "http://localhost:8000"

def create_test_game() -> Dict:
    """Create a new game with 4 test players."""
    response = requests.post(
        f"{API_URL}/wgp/simplified/start-game",
        json={
            "player_names": ["Alice", "Bob", "Charlie", "Diana"],
            "base_wager": 1
        }
    )
    response.raise_for_status()
    return response.json()

def complete_hole(game_id: str, hole_number: int, use_implicit_team2: bool = True) -> Dict:
    """
    Complete a single hole.

    Args:
        game_id: The game ID
        hole_number: Current hole number (1-18)
        use_implicit_team2: If True, only send team1 (tests implicit assignment)
    """
    # Get player IDs
    game_info = requests.get(f"{API_URL}/wgp/simplified/games/{game_id}").json()
    players = game_info["players"]
    player_ids = [p["id"] for p in players]

    # Alternate between partners and solo mode
    use_solo = hole_number % 3 == 0  # Every 3rd hole is solo

    # Generate random scores (4-7 strokes)
    scores = {pid: random.randint(4, 7) for pid in player_ids}

    if use_solo:
        # Solo mode: one player vs the rest
        captain_id = player_ids[hole_number % len(player_ids)]
        teams = {
            "type": "solo",
            "captain": captain_id,
            "opponents": [pid for pid in player_ids if pid != captain_id]
        }
        # Determine winner based on scores
        captain_score = scores[captain_id]
        opponent_scores = [scores[pid] for pid in teams["opponents"]]
        best_opponent = min(opponent_scores)

        if captain_score < best_opponent:
            winner = "captain"
        elif captain_score > best_opponent:
            winner = "opponents"
        else:
            winner = "push"
    else:
        # Partners mode: split into two teams
        team1 = player_ids[:2]

        if use_implicit_team2:
            # Test implicit team assignment - don't send team2
            teams = {
                "type": "partners",
                "team1": team1
                # team2 will be calculated automatically by the backend
            }
        else:
            # Explicit team assignment
            team2 = player_ids[2:]
            teams = {
                "type": "partners",
                "team1": team1,
                "team2": team2
            }

        # Determine winner based on best ball scoring
        team1_score = min(scores[pid] for pid in team1)
        team2_ids = [pid for pid in player_ids if pid not in team1]
        team2_score = min(scores[pid] for pid in team2_ids)

        if team1_score < team2_score:
            winner = "team1"
        elif team1_score > team2_score:
            winner = "team2"
        else:
            winner = "push"

    # Submit the hole
    payload = {
        "hole_number": hole_number,
        "teams": teams,
        "final_wager": 1,
        "winner": winner,
        "scores": scores,
        "hole_par": 4
    }

    print(f"Hole {hole_number}: {teams['type']} mode, winner: {winner}")
    if use_implicit_team2 and teams["type"] == "partners":
        print(f"  ✓ Testing implicit team2 assignment (only sent team1: {team1})")

    response = requests.post(
        f"{API_URL}/games/{game_id}/holes/complete",
        json=payload
    )
    response.raise_for_status()
    return response.json()

def complete_full_game(use_implicit_team2: bool = True):
    """Complete a full 18-hole game."""
    print("=" * 60)
    print("COMPLETING FULL 18-HOLE GAME")
    print(f"Implicit Team 2 Assignment: {'ENABLED' if use_implicit_team2 else 'DISABLED'}")
    print("=" * 60)

    # Create game
    print("\n1. Creating game...")
    game_data = create_test_game()
    game_id = game_data["game_id"]
    print(f"   Game ID: {game_id}")
    print(f"   Players: {', '.join([p['name'] for p in game_data['players']])}")

    # Complete all 18 holes
    print("\n2. Completing 18 holes...")
    for hole in range(1, 19):
        complete_hole(game_id, hole, use_implicit_team2)

    # Fetch final game state
    print("\n3. Fetching final game state...")
    final_game = requests.get(f"{API_URL}/wgp/simplified/games/{game_id}").json()

    print("\n" + "=" * 60)
    print("GAME COMPLETE!")
    print("=" * 60)
    print(f"\nFinal Standings:")
    for player in final_game["players"]:
        quarters = final_game["standings"].get(player["id"], {}).get("quarters", 0)
        print(f"  {player['name']}: {quarters:+d} quarters")

    print(f"\nTotal Holes Completed: {len(final_game['hole_history'])}")
    print(f"Game Status: {'COMPLETE' if len(final_game['hole_history']) == 18 else 'INCOMPLETE'}")

    return game_id, final_game

if __name__ == "__main__":
    try:
        game_id, final_game = complete_full_game(use_implicit_team2=True)
        print("\n✅ Test completed successfully!")
        print(f"\nYou can view this game at: http://localhost:3000/wgp/game/{game_id}")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

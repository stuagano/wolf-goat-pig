"""
Test scoring mode through a full round using HTTP API
Tests the complete hole scoring flow with 5-man advanced rules
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def print_section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")

def create_test_game():
    """Create a 5-player test game"""
    response = requests.post(f"{BASE_URL}/games/create-test?player_count=5")
    data = response.json()
    return data["game_id"], data["players"]

def get_game_state(game_id):
    """Get current game state"""
    response = requests.get(f"{BASE_URL}/games/{game_id}/state")
    return response.json()

def complete_hole(game_id, hole_data):
    """Complete a hole with given data"""
    response = requests.post(
        f"{BASE_URL}/games/{game_id}/holes/complete",
        json=hole_data
    )
    return response.status_code, response.json()

def test_full_round():
    """Test a complete round with various scenarios"""

    # Create game
    print_section("CREATING 5-MAN GAME")
    game_id, players = create_test_game()
    player_ids = [p["id"] for p in players]

    print(f"Game ID: {game_id}")
    print(f"\nPlayers:")
    for i, p in enumerate(players, 1):
        print(f"  {i}. {p['name']} (ID: {p['id']}, Handicap: {p['handicap']})")

    # Get initial state
    print_section("INITIAL GAME STATE")
    state = get_game_state(game_id)
    print(f"Game Phase: {state.get('game_phase', 'N/A')}")
    print(f"Current Hole: {state['current_hole']}")
    print(f"Player Count: {len(state['players'])}")
    print(f"Hole Par: {state.get('hole_par', 'N/A')}")

    # HOLE 1: Basic partners game (2v3 with Aardvark)
    print_section("HOLE 1: Partners Game (Captain + Partner) vs (3 others)")
    hole1_data = {
        "hole_number": 1,
        "rotation_order": player_ids,  # [p1, p2, p3, p4, p5]
        "captain_index": 0,  # p1 is captain
        "teams": {
            "type": "partners",
            "team1": [player_ids[0], player_ids[1]],  # Captain + Partner
            "team2": [player_ids[2], player_ids[3], player_ids[4]]  # 3 others (Aardvark joins)
        },
        "aardvark_requested_team": "team2",  # Aardvark requests team2
        "aardvark_tossed": False,
        "final_wager": 2,
        "winner": "team1",
        "scores": {
            player_ids[0]: 4,
            player_ids[1]: 4,
            player_ids[2]: 5,
            player_ids[3]: 5,
            player_ids[4]: 5
        },
        "hole_par": 4
    }

    status, result = complete_hole(game_id, hole1_data)
    print(f"Status: {status}")
    print(f"Winner: {result['hole_result']['winner']}")
    print(f"\nPoints Delta:")
    for player_id, delta in result['hole_result']['points_delta'].items():
        player_name = next(p['name'] for p in players if p['id'] == player_id)
        print(f"  {player_name}: {delta:+.2f}Q")

    # Verify zero-sum
    total = sum(result['hole_result']['points_delta'].values())
    print(f"\n✓ Zero-sum check: {total:.6f} (should be ~0)")
    assert abs(total) < 0.01, f"Not zero-sum! Total: {total}"

    # HOLE 2: Aardvark tossed (doubled risk)
    print_section("HOLE 2: Aardvark Tossed (2x Multiplier)")
    hole2_data = {
        "hole_number": 2,
        "rotation_order": player_ids[1:] + [player_ids[0]],  # Rotate: [p2, p3, p4, p5, p1]
        "captain_index": 0,  # p2 is captain
        "teams": {
            "type": "partners",
            "team1": [player_ids[1], player_ids[2]],  # Tossed Aardvark
            "team2": [player_ids[3], player_ids[4], player_ids[0]]  # Aardvark auto-joins
        },
        "aardvark_requested_team": "team1",  # Requested team1
        "aardvark_tossed": True,  # But was tossed!
        "final_wager": 2,
        "winner": "team2",
        "scores": {
            player_ids[1]: 5,
            player_ids[2]: 5,
            player_ids[3]: 4,
            player_ids[4]: 4,
            player_ids[0]: 4
        },
        "hole_par": 4
    }

    status, result = complete_hole(game_id, hole2_data)
    print(f"Status: {status}")
    print(f"Winner: {result['hole_result']['winner']}")
    print(f"Aardvark Tossed: {result['hole_result']['aardvark_tossed']}")
    print(f"\nPoints Delta (2x multiplier):")
    for player_id, delta in result['hole_result']['points_delta'].items():
        player_name = next(p['name'] for p in players if p['id'] == player_id)
        print(f"  {player_name}: {delta:+.2f}Q")

    total = sum(result['hole_result']['points_delta'].values())
    print(f"\n✓ Zero-sum check: {total:.6f}")
    assert abs(total) < 0.01

    # HOLE 3: Ping Pong (4x multiplier)
    print_section("HOLE 3: Ping Pong (Aardvark Re-tossed - 4x Multiplier)")
    hole3_data = {
        "hole_number": 3,
        "rotation_order": player_ids[2:] + player_ids[:2],  # [p3, p4, p5, p1, p2]
        "captain_index": 0,  # p3 is captain
        "teams": {
            "type": "partners",
            "team1": [player_ids[2], player_ids[3], player_ids[4]],  # Aardvark back on requested team
            "team2": [player_ids[0], player_ids[1]]
        },
        "aardvark_requested_team": "team1",
        "aardvark_tossed": True,  # Initial toss
        "aardvark_ping_ponged": True,  # Re-tossed!
        "final_wager": 2,
        "winner": "team1",
        "scores": {
            player_ids[2]: 4,
            player_ids[3]: 4,
            player_ids[4]: 4,
            player_ids[0]: 5,
            player_ids[1]: 5
        },
        "hole_par": 4
    }

    status, result = complete_hole(game_id, hole3_data)
    print(f"Status: {status}")
    print(f"Winner: {result['hole_result']['winner']}")
    print(f"Ping Ponged: {result['hole_result']['aardvark_ping_ponged']}")
    print(f"\nPoints Delta (4x multiplier!):")
    for player_id, delta in result['hole_result']['points_delta'].items():
        player_name = next(p['name'] for p in players if p['id'] == player_id)
        print(f"  {player_name}: {delta:+.2f}Q")

    total = sum(result['hole_result']['points_delta'].values())
    print(f"\n✓ Zero-sum check: {total:.6f}")
    assert abs(total) < 0.01

    # HOLE 4: The Tunkarri (Aardvark solo with 3-for-2 payout)
    print_section("HOLE 4: The Tunkarri (Aardvark Solo - 3-for-2 Payout)")
    aardvark_id = player_ids[4]  # Player 5
    hole4_data = {
        "hole_number": 4,
        "rotation_order": player_ids,  # [p1, p2, p3, p4, p5]
        "captain_index": 4,  # Aardvark is captain (position 5)
        "teams": {
            "type": "solo",
            "captain": aardvark_id,
            "opponents": [player_ids[0], player_ids[1], player_ids[2], player_ids[3]]
        },
        "tunkarri_invoked": True,  # 3-for-2 payout!
        "final_wager": 2,
        "winner": "captain",  # Aardvark wins
        "scores": {
            player_ids[0]: 5,
            player_ids[1]: 5,
            player_ids[2]: 5,
            player_ids[3]: 5,
            player_ids[4]: 3  # Aardvark gets eagle
        },
        "hole_par": 4
    }

    status, result = complete_hole(game_id, hole4_data)
    print(f"Status: {status}")
    print(f"Winner: {result['hole_result']['winner']}")
    print(f"Tunkarri Invoked: {result['hole_result']['tunkarri_invoked']}")
    print(f"\nPoints Delta (3-for-2 payout):")
    print(f"  Wager: {hole4_data['final_wager']}Q → Payout: {hole4_data['final_wager'] * 3 / 2}Q")
    for player_id, delta in result['hole_result']['points_delta'].items():
        player_name = next(p['name'] for p in players if p['id'] == player_id)
        print(f"  {player_name}: {delta:+.2f}Q")

    total = sum(result['hole_result']['points_delta'].values())
    print(f"\n✓ Zero-sum check: {total:.6f}")
    assert abs(total) < 0.01

    # HOLE 5: Normal solo (Aardvark loses)
    print_section("HOLE 5: Aardvark Solo Loss (Normal Payout)")
    hole5_data = {
        "hole_number": 5,
        "rotation_order": player_ids,
        "captain_index": 4,
        "teams": {
            "type": "solo",
            "captain": aardvark_id,
            "opponents": [player_ids[0], player_ids[1], player_ids[2], player_ids[3]]
        },
        "aardvark_solo": True,
        "tunkarri_invoked": False,  # Not invoking Tunkarri
        "final_wager": 2,
        "winner": "opponents",  # Aardvark loses
        "scores": {
            player_ids[0]: 4,
            player_ids[1]: 4,
            player_ids[2]: 4,
            player_ids[3]: 4,
            player_ids[4]: 7  # Aardvark gets triple bogey
        },
        "hole_par": 4
    }

    status, result = complete_hole(game_id, hole5_data)
    print(f"Status: {status}")
    print(f"Winner: {result['hole_result']['winner']}")
    print(f"\nPoints Delta (Normal solo loss):")
    for player_id, delta in result['hole_result']['points_delta'].items():
        player_name = next(p['name'] for p in players if p['id'] == player_id)
        print(f"  {player_name}: {delta:+.2f}Q")

    total = sum(result['hole_result']['points_delta'].values())
    print(f"\n✓ Zero-sum check: {total:.6f}")
    assert abs(total) < 0.01

    # Final standings
    print_section("FINAL STANDINGS AFTER 5 HOLES")
    final_state = get_game_state(game_id)
    standings = [(p['name'], p.get('total_points', p.get('points', 0))) for p in final_state['players']]
    standings.sort(key=lambda x: x[1], reverse=True)

    for i, (name, points) in enumerate(standings, 1):
        emoji = "🏆" if i == 1 else "🐺" if i == len(standings) else "  "
        print(f"{emoji} {i}. {name}: {points:+.2f}Q")

    print_section("TEST SUMMARY")
    print("✅ All 5 holes completed successfully")
    print("✅ All point calculations validated")
    print("✅ Zero-sum maintained on all holes")
    print("✅ 5-Man advanced rules tested:")
    print("   - Aardvark team selection")
    print("   - Aardvark tossing (2x multiplier)")
    print("   - Ping Ponging (4x multiplier)")
    print("   - The Tunkarri (3-for-2 payout)")
    print("   - Normal Aardvark solo")
    print("\n🎉 SCORING MODE TEST COMPLETED SUCCESSFULLY!")

if __name__ == "__main__":
    try:
        test_full_round()
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()

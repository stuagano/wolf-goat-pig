"""Debug carry-over state"""
import requests
import json

# Create test game
resp = requests.post("http://localhost:8000/games/create-test?player_count=4")
data = resp.json()
game_id = data["game_id"]
player_ids = [p["id"] for p in data["players"]]

print(f"Game ID: {game_id}")
print(f"Players: {player_ids}")

# Complete hole 1 with push
resp = requests.post(
    f"http://localhost:8000/games/{game_id}/holes/complete",
    json={
        "hole_number": 1,
        "rotation_order": player_ids,
        "captain_index": 0,
        "teams": {
            "type": "partners",
            "team1": [player_ids[0], player_ids[1]],
            "team2": [player_ids[2], player_ids[3]]
        },
        "final_wager": 2,
        "winner": "push",
        "scores": {player_ids[0]: 4, player_ids[1]: 4, player_ids[2]: 4, player_ids[3]: 4},
        "hole_par": 4
    }
)

print("\nComplete hole response:")
result = resp.json()
print(json.dumps(result, indent=2))

# Check game state
resp = requests.get(f"http://localhost:8000/games/{game_id}/state")
state = resp.json()
print("\nGame state after push:")
print(f"  carry_over_wager: {state.get('carry_over_wager', 'NOT FOUND')}")
print(f"  carry_over_from_hole: {state.get('carry_over_from_hole', 'NOT FOUND')}")
print(f"  consecutive_push_block: {state.get('consecutive_push_block', 'NOT FOUND')}")

# Check next hole wager
resp = requests.get(f"http://localhost:8000/games/{game_id}/next-hole-wager")
wager = resp.json()
print("\nNext hole wager:")
print(json.dumps(wager, indent=2))

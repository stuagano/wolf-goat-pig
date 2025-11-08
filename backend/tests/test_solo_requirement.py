"""Test Solo Requirement - once per player in first 16 holes (4-man only)"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_solo_usage_tracked():
    """Test solo usage is tracked in player standings"""
    game_response = client.post("/games/create-test?player_count=4")
    game_id = game_response.json()["game_id"]
    players = game_response.json()["players"]
    player_ids = [p["id"] for p in players]

    # Hole 1: p1 goes solo
    response = client.post(f"/games/{game_id}/holes/complete", json={
        "hole_number": 1,
        "rotation_order": player_ids,
        "captain_index": 0,
        "teams": {"type": "solo", "captain": player_ids[0], "opponents": [player_ids[1], player_ids[2], player_ids[3]]},
        "final_wager": 2,
        "winner": "captain",
        "scores": {player_ids[0]: 4, player_ids[1]: 5, player_ids[2]: 5, player_ids[3]: 6},
        "hole_par": 4
    })

    assert response.status_code == 200

    # Get game state to verify solo count
    state_response = client.get(f"/games/{game_id}/state")
    game_state = state_response.json()

    # Check p1 has used solo (via hole history)
    hole_history = game_state.get("hole_history", [])
    assert len(hole_history) > 0
    assert hole_history[0]["teams"]["type"] == "solo"
    assert hole_history[0]["teams"]["captain"] == player_ids[0]


def test_all_players_must_go_solo_before_hoepfinger():
    """Test all players should go solo at least once before hole 17"""
    game_response = client.post("/games/create-test?player_count=4")
    game_id = game_response.json()["game_id"]
    players = game_response.json()["players"]
    player_ids = [p["id"] for p in players]

    # Play through 16 holes - p1, p2, p3 go solo, but NOT p4
    for hole_num in range(1, 17):
        captain_idx = (hole_num - 1) % 4
        rotation = player_ids[captain_idx:] + player_ids[:captain_idx]
        captain_id = rotation[0]

        # p1, p2, p3 go solo once each, p4 always plays partners
        if captain_id == player_ids[3]:  # p4 never goes solo
            response = client.post(f"/games/{game_id}/holes/complete", json={
                "hole_number": hole_num,
                "rotation_order": rotation,
                "captain_index": 0,
                "teams": {"type": "partners", "team1": [rotation[0], rotation[1]], "team2": [rotation[2], rotation[3]]},
                "final_wager": 1,
                "winner": "team1",
                "scores": {rotation[0]: 4, rotation[1]: 4, rotation[2]: 5, rotation[3]: 5},
                "hole_par": 4
            })
        else:
            response = client.post(f"/games/{game_id}/holes/complete", json={
                "hole_number": hole_num,
                "rotation_order": rotation,
                "captain_index": 0,
                "teams": {"type": "solo", "captain": captain_id, "opponents": [pid for pid in rotation[1:]]},
                "final_wager": 1,
                "winner": "captain",
                "scores": {captain_id: 4, rotation[1]: 5, rotation[2]: 5, rotation[3]: 5},
                "hole_par": 4
            })

        assert response.status_code == 200

    # Check game state - should have a warning about p4
    state_response = client.get(f"/games/{game_id}/state")
    game_state = state_response.json()

    # Count solo usage from hole history
    solo_counts = {pid: 0 for pid in player_ids}
    for hole in game_state.get("hole_history", []):
        if hole["teams"]["type"] == "solo":
            solo_counts[hole["teams"]["captain"]] += 1

    assert solo_counts[player_ids[0]] >= 1
    assert solo_counts[player_ids[1]] >= 1
    assert solo_counts[player_ids[2]] >= 1
    assert solo_counts[player_ids[3]] == 0  # p4 never went solo

"""Test captain rotation tracking functionality."""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_complete_hole_stores_rotation_order():
    """Test that rotation order is stored with hole data"""
    # Create test game with 4 players
    game_response = client.post("/games/create-test?player_count=4")
    assert game_response.status_code == 200
    game_id = game_response.json()["game_id"]
    players = game_response.json()["players"]
    player_ids = [p["id"] for p in players]

    # Complete hole 1 with rotation order
    response = client.post(f"/games/{game_id}/holes/complete", json={
        "hole_number": 1,
        "rotation_order": player_ids,  # NEW FIELD
        "captain_index": 0,             # NEW FIELD
        "teams": {
            "type": "partners",
            "team1": [player_ids[0], player_ids[1]],
            "team2": [player_ids[2], player_ids[3]]
        },
        "final_wager": 1,
        "winner": "team1",
        "scores": {player_ids[0]: 4, player_ids[1]: 5, player_ids[2]: 5, player_ids[3]: 6},
        "hole_par": 4
    })

    assert response.status_code == 200
    hole_result = response.json()["hole_result"]
    assert hole_result["rotation_order"] == player_ids
    assert hole_result["captain_index"] == 0


def test_rotation_advances_each_hole():
    """Test that captain rotation advances properly"""
    # Create test game
    game_response = client.post("/games/create-test?player_count=4")
    assert game_response.status_code == 200
    game_id = game_response.json()["game_id"]
    players = game_response.json()["players"]
    player_ids = [p["id"] for p in players]

    # Hole 1: First player is captain (index 0)
    client.post(f"/games/{game_id}/holes/complete", json={
        "hole_number": 1,
        "rotation_order": player_ids,
        "captain_index": 0,
        "teams": {"type": "partners", "team1": [player_ids[0], player_ids[1]], "team2": [player_ids[2], player_ids[3]]},
        "final_wager": 1,
        "winner": "team1",
        "scores": {player_ids[0]: 4, player_ids[1]: 5, player_ids[2]: 5, player_ids[3]: 6},
        "hole_par": 4
    })

    # Get next rotation - should shift left by 1
    state_response = client.get(f"/games/{game_id}/next-rotation")
    assert state_response.status_code == 200
    next_rotation = state_response.json()

    # Rotation should shift: [p2, p3, p4, p1]
    expected_rotation = player_ids[1:] + [player_ids[0]]
    assert next_rotation["rotation_order"] == expected_rotation
    assert next_rotation["captain_index"] == 0  # Captain is always first in rotation
    assert next_rotation["captain_id"] == player_ids[1]

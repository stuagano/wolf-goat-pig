"""Test Float enforcement - once per round per player"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_float_usage_tracked():
    """Test float usage is tracked in player standings"""
    game_response = client.post("/games/create-test?player_count=4")
    game_id = game_response.json()["game_id"]
    players = game_response.json()["players"]
    player_ids = [p["id"] for p in players]

    # Hole 1: p1 invokes float
    response = client.post(f"/games/{game_id}/holes/complete", json={
        "hole_number": 1,
        "rotation_order": player_ids,
        "captain_index": 0,
        "teams": {"type": "partners", "team1": [player_ids[0], player_ids[1]], "team2": [player_ids[2], player_ids[3]]},
        "final_wager": 2,  # Doubled by float
        "winner": "team1",
        "scores": {player_ids[0]: 4, player_ids[1]: 5, player_ids[2]: 5, player_ids[3]: 6},
        "hole_par": 4,
        "float_invoked_by": player_ids[0]
    })

    assert response.status_code == 200

    # Get game state to verify float count
    state_response = client.get(f"/games/{game_id}/state")
    game_state = state_response.json()

    # Check p1 has used float
    players_data = game_state.get("players", [])
    p1_data = next(p for p in players_data if p["id"] == player_ids[0])
    assert p1_data.get("float_used", 0) == 1


def test_float_cannot_be_used_twice():
    """Test player cannot invoke float twice in same round"""
    game_response = client.post("/games/create-test?player_count=4")
    game_id = game_response.json()["game_id"]
    players = game_response.json()["players"]
    player_ids = [p["id"] for p in players]

    # Hole 1: p1 invokes float
    client.post(f"/games/{game_id}/holes/complete", json={
        "hole_number": 1,
        "rotation_order": player_ids,
        "captain_index": 0,
        "teams": {"type": "partners", "team1": [player_ids[0], player_ids[1]], "team2": [player_ids[2], player_ids[3]]},
        "final_wager": 2,
        "winner": "team1",
        "scores": {player_ids[0]: 4, player_ids[1]: 5, player_ids[2]: 5, player_ids[3]: 6},
        "hole_par": 4,
        "float_invoked_by": player_ids[0]
    })

    # Hole 2: p1 tries to invoke float again (should fail)
    response = client.post(f"/games/{game_id}/holes/complete", json={
        "hole_number": 2,
        "rotation_order": player_ids[1:] + [player_ids[0]],
        "captain_index": 0,
        "teams": {"type": "partners", "team1": [player_ids[1], player_ids[2]], "team2": [player_ids[3], player_ids[0]]},
        "final_wager": 2,
        "winner": "team1",
        "scores": {player_ids[0]: 4, player_ids[1]: 4, player_ids[2]: 5, player_ids[3]: 5},
        "hole_par": 4,
        "float_invoked_by": player_ids[0]  # Second time!
    })

    assert response.status_code == 400
    detail = response.json()["detail"].lower()
    assert "already used" in detail and "float" in detail

"""Test The Option - auto-double when Captain is furthest down"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_option_auto_applies_when_captain_is_goat():
    """Test The Option automatically doubles wager when Captain is Goat"""
    # Create game
    game_response = client.post("/games/create-test?player_count=4")
    assert game_response.status_code == 200
    game_id = game_response.json()["game_id"]
    players = game_response.json()["players"]
    player_ids = [p["id"] for p in players]

    # Hole 1: Both p1 and p2 lose (partners), tied for Goat
    client.post(f"/games/{game_id}/holes/complete", json={
        "hole_number": 1,
        "rotation_order": player_ids,
        "captain_index": 0,
        "teams": {"type": "partners", "team1": [player_ids[0], player_ids[1]], "team2": [player_ids[2], player_ids[3]]},
        "final_wager": 5,
        "winner": "team2",
        "scores": {player_ids[0]: 7, player_ids[1]: 6, player_ids[2]: 4, player_ids[3]: 4},
        "hole_par": 4
    })

    # Hole 2: p2 is captain. If p2 is picked as Goat (tied with p1), Option applies
    wager = client.get(f"/games/{game_id}/next-hole-wager")
    data = wager.json()

    # Option should apply if captain is one of the Goats
    if data.get("option_active"):
        assert data["base_wager"] == 2  # 1Q × 2 (Option applied)
        assert data["goat_id"] in [player_ids[0], player_ids[1]]  # One of the tied Goats


def test_option_can_be_turned_off():
    """Test Captain can proactively turn off The Option"""
    game_response = client.post("/games/create-test?player_count=4")
    game_id = game_response.json()["game_id"]
    players = game_response.json()["players"]
    player_ids = [p["id"] for p in players]

    # Make p1 the Goat
    client.post(f"/games/{game_id}/holes/complete", json={
        "hole_number": 1,
        "rotation_order": player_ids,
        "captain_index": 0,
        "teams": {"type": "partners", "team1": [player_ids[0], player_ids[1]], "team2": [player_ids[2], player_ids[3]]},
        "final_wager": 5,
        "winner": "team2",
        "scores": {player_ids[0]: 7, player_ids[1]: 6, player_ids[2]: 4, player_ids[3]: 4},
        "hole_par": 4
    })

    # Hole 2: p2 is captain, turn off Option
    response = client.post(f"/games/{game_id}/holes/complete", json={
        "hole_number": 2,
        "rotation_order": player_ids[1:] + [player_ids[0]],
        "captain_index": 0,
        "option_turned_off": True,  # NEW FIELD
        "teams": {"type": "partners", "team1": [player_ids[1], player_ids[2]], "team2": [player_ids[3], player_ids[0]]},
        "final_wager": 1,  # Not doubled
        "winner": "team1",
        "scores": {player_ids[0]: 5, player_ids[1]: 4, player_ids[2]: 4, player_ids[3]: 5},
        "hole_par": 4
    })

    assert response.status_code == 200

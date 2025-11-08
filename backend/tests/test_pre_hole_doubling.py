"""Test Pre-hole Doubling Mechanics - Phase 4, Task 3"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_hole_with_no_doubles():
    """Test normal hole without any doubles"""
    game_response = client.post("/games/create-test?player_count=4")
    game_id = game_response.json()["game_id"]
    players = game_response.json()["players"]
    player_ids = [p["id"] for p in players]

    # Complete hole with base wager, no doubles
    response = client.post(f"/games/{game_id}/holes/complete", json={
        "hole_number": 1,
        "rotation_order": player_ids,
        "captain_index": 0,
        "teams": {"type": "partners", "team1": [player_ids[0], player_ids[1]], "team2": [player_ids[2], player_ids[3]]},
        "final_wager": 1,
        "winner": "team1",
        "scores": {player_ids[0]: 4, player_ids[1]: 4, player_ids[2]: 5, player_ids[3]: 5},
        "hole_par": 4
    })

    assert response.status_code == 200
    result = response.json()["hole_result"]

    # Verify no doubles history
    assert result.get("doubles_history") is None or result["doubles_history"] == []

    # Verify wager is base wager
    assert result["final_wager"] == 1


def test_hole_with_single_double():
    """Test hole with one double offered and accepted"""
    game_response = client.post("/games/create-test?player_count=4")
    game_id = game_response.json()["game_id"]
    players = game_response.json()["players"]
    player_ids = [p["id"] for p in players]

    # Complete hole with double
    response = client.post(f"/games/{game_id}/holes/complete", json={
        "hole_number": 1,
        "rotation_order": player_ids,
        "captain_index": 0,
        "teams": {"type": "partners", "team1": [player_ids[0], player_ids[1]], "team2": [player_ids[2], player_ids[3]]},
        "final_wager": 2,  # Base 1, doubled to 2
        "doubles_history": [
            {
                "offered_by": player_ids[0],
                "accepted_by_team": "team2",
                "multiplier": 2
            }
        ],
        "winner": "team1",
        "scores": {player_ids[0]: 4, player_ids[1]: 4, player_ids[2]: 5, player_ids[3]: 5},
        "hole_par": 4
    })

    assert response.status_code == 200
    result = response.json()["hole_result"]

    # Verify doubles history recorded
    assert "doubles_history" in result
    assert len(result["doubles_history"]) == 1
    assert result["doubles_history"][0]["offered_by"] == player_ids[0]
    assert result["doubles_history"][0]["accepted_by_team"] == "team2"

    # Verify wager is doubled
    assert result["final_wager"] == 2


def test_hole_with_multiple_doubles():
    """Test hole with multiple doubles offered and accepted"""
    game_response = client.post("/games/create-test?player_count=4")
    game_id = game_response.json()["game_id"]
    players = game_response.json()["players"]
    player_ids = [p["id"] for p in players]

    # Complete hole with 2 doubles (base 1 → 2 → 4)
    response = client.post(f"/games/{game_id}/holes/complete", json={
        "hole_number": 1,
        "rotation_order": player_ids,
        "captain_index": 0,
        "teams": {"type": "partners", "team1": [player_ids[0], player_ids[1]], "team2": [player_ids[2], player_ids[3]]},
        "final_wager": 4,  # Base 1, doubled twice to 4
        "doubles_history": [
            {
                "offered_by": player_ids[0],
                "accepted_by_team": "team2",
                "multiplier": 2
            },
            {
                "offered_by": player_ids[2],
                "accepted_by_team": "team1",
                "multiplier": 2
            }
        ],
        "winner": "team1",
        "scores": {player_ids[0]: 4, player_ids[1]: 4, player_ids[2]: 5, player_ids[3]: 5},
        "hole_par": 4
    })

    assert response.status_code == 200
    result = response.json()["hole_result"]

    # Verify doubles history recorded
    assert len(result["doubles_history"]) == 2
    assert result["final_wager"] == 4


def test_declined_double_not_recorded():
    """Test that declined doubles are not included in history"""
    game_response = client.post("/games/create-test?player_count=4")
    game_id = game_response.json()["game_id"]
    players = game_response.json()["players"]
    player_ids = [p["id"] for p in players]

    # Complete hole with no accepted doubles (double was declined)
    response = client.post(f"/games/{game_id}/holes/complete", json={
        "hole_number": 1,
        "rotation_order": player_ids,
        "captain_index": 0,
        "teams": {"type": "partners", "team1": [player_ids[0], player_ids[1]], "team2": [player_ids[2], player_ids[3]]},
        "final_wager": 1,  # Base wager, double was declined
        "doubles_history": [],  # Empty because declined
        "winner": "team1",
        "scores": {player_ids[0]: 4, player_ids[1]: 4, player_ids[2]: 5, player_ids[3]: 5},
        "hole_par": 4
    })

    assert response.status_code == 200
    result = response.json()["hole_result"]

    # Verify no doubles history
    assert result.get("doubles_history") == [] or result.get("doubles_history") is None
    assert result["final_wager"] == 1


def test_doubles_history_in_hole_record():
    """Test that doubles history is saved in hole_history"""
    game_response = client.post("/games/create-test?player_count=4")
    game_id = game_response.json()["game_id"]
    players = game_response.json()["players"]
    player_ids = [p["id"] for p in players]

    # Complete hole with double
    response = client.post(f"/games/{game_id}/holes/complete", json={
        "hole_number": 1,
        "rotation_order": player_ids,
        "captain_index": 0,
        "teams": {"type": "partners", "team1": [player_ids[0], player_ids[1]], "team2": [player_ids[2], player_ids[3]]},
        "final_wager": 2,
        "doubles_history": [
            {
                "offered_by": player_ids[0],
                "accepted_by_team": "team2",
                "multiplier": 2
            }
        ],
        "winner": "team1",
        "scores": {player_ids[0]: 4, player_ids[1]: 4, player_ids[2]: 5, player_ids[3]: 5},
        "hole_par": 4
    })

    assert response.status_code == 200

    # Get game state and verify doubles_history in hole_history
    game_response = client.get(f"/games/{game_id}/state")
    game_state = game_response.json()

    hole_history = game_state.get("hole_history", [])
    assert len(hole_history) > 0

    # Find hole 1
    hole_1 = hole_history[0]
    assert hole_1["hole_number"] == 1
    assert "doubles_history" in hole_1
    assert len(hole_1["doubles_history"]) == 1
    assert hole_1["doubles_history"][0]["offered_by"] == player_ids[0]


def test_points_calculated_with_doubled_wager():
    """Test that points are calculated using the doubled wager"""
    game_response = client.post("/games/create-test?player_count=4")
    game_id = game_response.json()["game_id"]
    players = game_response.json()["players"]
    player_ids = [p["id"] for p in players]

    # Complete hole with double (wager 2)
    response = client.post(f"/games/{game_id}/holes/complete", json={
        "hole_number": 1,
        "rotation_order": player_ids,
        "captain_index": 0,
        "teams": {"type": "partners", "team1": [player_ids[0], player_ids[1]], "team2": [player_ids[2], player_ids[3]]},
        "final_wager": 2,  # Doubled from 1 to 2
        "doubles_history": [
            {
                "offered_by": player_ids[0],
                "accepted_by_team": "team2",
                "multiplier": 2
            }
        ],
        "winner": "team1",
        "scores": {player_ids[0]: 4, player_ids[1]: 4, player_ids[2]: 5, player_ids[3]: 5},
        "hole_par": 4
    })

    assert response.status_code == 200
    result = response.json()["hole_result"]
    points_delta = result["points_delta"]

    # With wager 2, team1 wins +2 each, team2 loses -2 each
    assert points_delta[player_ids[0]] == 2
    assert points_delta[player_ids[1]] == 2
    assert points_delta[player_ids[2]] == -2
    assert points_delta[player_ids[3]] == -2

    # Verify balance
    assert sum(points_delta.values()) == 0

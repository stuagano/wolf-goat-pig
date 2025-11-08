"""Test Double Points - holes 17-18 worth double points"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_normal_hole_no_doubling():
    """Test regular holes don't double points"""
    game_response = client.post("/games/create-test?player_count=4")
    game_id = game_response.json()["game_id"]
    players = game_response.json()["players"]
    player_ids = [p["id"] for p in players]

    # Hole 1: 2Q wager, partners mode
    response = client.post(f"/games/{game_id}/holes/complete", json={
        "hole_number": 1,
        "rotation_order": player_ids,
        "captain_index": 0,
        "teams": {"type": "partners", "team1": [player_ids[0], player_ids[1]], "team2": [player_ids[2], player_ids[3]]},
        "final_wager": 2,
        "winner": "team1",
        "scores": {player_ids[0]: 4, player_ids[1]: 4, player_ids[2]: 5, player_ids[3]: 5},
        "hole_par": 4
    })

    assert response.status_code == 200
    result = response.json()["hole_result"]

    # Each winner gets 2Q, each loser loses 2Q (not doubled)
    assert result["points_delta"][player_ids[0]] == 2
    assert result["points_delta"][player_ids[1]] == 2
    assert result["points_delta"][player_ids[2]] == -2
    assert result["points_delta"][player_ids[3]] == -2


def test_hole_17_doubles_points():
    """Test hole 17 doubles points"""
    game_response = client.post("/games/create-test?player_count=4")
    game_id = game_response.json()["game_id"]
    players = game_response.json()["players"]
    player_ids = [p["id"] for p in players]

    # Play through 16 holes quickly
    for hole_num in range(1, 17):
        captain_idx = (hole_num - 1) % 4
        rotation = player_ids[captain_idx:] + player_ids[:captain_idx]

        client.post(f"/games/{game_id}/holes/complete", json={
            "hole_number": hole_num,
            "rotation_order": rotation,
            "captain_index": 0,
            "teams": {"type": "partners", "team1": [rotation[0], rotation[1]], "team2": [rotation[2], rotation[3]]},
            "final_wager": 1,
            "winner": "team1",
            "scores": {rotation[0]: 4, rotation[1]: 4, rotation[2]: 5, rotation[3]: 5},
            "hole_par": 4
        })

    # Hole 17: 2Q base wager, should double to 4Q per player
    rotation = player_ids  # Start fresh rotation for hole 17
    response = client.post(f"/games/{game_id}/holes/complete", json={
        "hole_number": 17,
        "rotation_order": rotation,
        "captain_index": 0,
        "teams": {"type": "partners", "team1": [rotation[0], rotation[1]], "team2": [rotation[2], rotation[3]]},
        "final_wager": 2,
        "winner": "team1",
        "scores": {rotation[0]: 4, rotation[1]: 4, rotation[2]: 5, rotation[3]: 5},
        "hole_par": 4
    })

    assert response.status_code == 200
    result = response.json()["hole_result"]

    # Each winner gets 4Q (2Q × 2), each loser loses 4Q
    assert result["points_delta"][rotation[0]] == 4
    assert result["points_delta"][rotation[1]] == 4
    assert result["points_delta"][rotation[2]] == -4
    assert result["points_delta"][rotation[3]] == -4


def test_hole_18_doubles_points():
    """Test hole 18 doubles points"""
    game_response = client.post("/games/create-test?player_count=4")
    game_id = game_response.json()["game_id"]
    players = game_response.json()["players"]
    player_ids = [p["id"] for p in players]

    # Play through 17 holes quickly
    for hole_num in range(1, 18):
        captain_idx = (hole_num - 1) % 4
        rotation = player_ids[captain_idx:] + player_ids[:captain_idx]

        client.post(f"/games/{game_id}/holes/complete", json={
            "hole_number": hole_num,
            "rotation_order": rotation,
            "captain_index": 0,
            "teams": {"type": "partners", "team1": [rotation[0], rotation[1]], "team2": [rotation[2], rotation[3]]},
            "final_wager": 1,
            "winner": "team1",
            "scores": {rotation[0]: 4, rotation[1]: 4, rotation[2]: 5, rotation[3]: 5},
            "hole_par": 4
        })

    # Hole 18: 2Q base wager, should double to 4Q per player
    rotation = player_ids  # Start fresh rotation for hole 18
    response = client.post(f"/games/{game_id}/holes/complete", json={
        "hole_number": 18,
        "rotation_order": rotation,
        "captain_index": 0,
        "teams": {"type": "partners", "team1": [rotation[0], rotation[1]], "team2": [rotation[2], rotation[3]]},
        "final_wager": 2,
        "winner": "team1",
        "scores": {rotation[0]: 4, rotation[1]: 4, rotation[2]: 5, rotation[3]: 5},
        "hole_par": 4
    })

    assert response.status_code == 200
    result = response.json()["hole_result"]

    # Each winner gets 4Q (2Q × 2), each loser loses 4Q
    assert result["points_delta"][rotation[0]] == 4
    assert result["points_delta"][rotation[1]] == 4
    assert result["points_delta"][rotation[2]] == -4
    assert result["points_delta"][rotation[3]] == -4


def test_hoepfinger_no_additional_doubling():
    """Test Hoepfinger phase doesn't get additional doubling (already has Joe's Special)"""
    game_response = client.post("/games/create-test?player_count=4")
    game_id = game_response.json()["game_id"]
    players = game_response.json()["players"]
    player_ids = [p["id"] for p in players]

    # Play through 16 holes quickly to reach Hoepfinger
    for hole_num in range(1, 17):
        captain_idx = (hole_num - 1) % 4
        rotation = player_ids[captain_idx:] + player_ids[:captain_idx]

        client.post(f"/games/{game_id}/holes/complete", json={
            "hole_number": hole_num,
            "rotation_order": rotation,
            "captain_index": 0,
            "teams": {"type": "partners", "team1": [rotation[0], rotation[1]], "team2": [rotation[2], rotation[3]]},
            "final_wager": 1,
            "winner": "team1",
            "scores": {rotation[0]: 4, rotation[1]: 4, rotation[2]: 5, rotation[3]: 5},
            "hole_par": 4
        })

    # Hole 17: Start Hoepfinger with 4Q Joe's Special wager
    rotation = player_ids
    response = client.post(f"/games/{game_id}/holes/complete", json={
        "hole_number": 17,
        "phase": "hoepfinger",
        "joes_special_wager": 4,
        "rotation_order": rotation,
        "captain_index": 0,
        "teams": {"type": "partners", "team1": [rotation[0], rotation[1]], "team2": [rotation[2], rotation[3]]},
        "final_wager": 4,
        "winner": "team1",
        "scores": {rotation[0]: 4, rotation[1]: 4, rotation[2]: 5, rotation[3]: 5},
        "hole_par": 4
    })

    assert response.status_code == 200
    result = response.json()["hole_result"]

    # Each winner gets 4Q (Joe's Special), NOT 8Q (no double doubling)
    assert result["points_delta"][rotation[0]] == 4
    assert result["points_delta"][rotation[1]] == 4
    assert result["points_delta"][rotation[2]] == -4
    assert result["points_delta"][rotation[3]] == -4

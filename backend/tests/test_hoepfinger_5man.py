"""Test Hoepfinger Phase for 5-Man Games - Phase 5, Task 3"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_joes_special_available_hole_16_5man():
    """Test that Joe's Special (Hoepfinger) works on hole 16 for 5-man games"""
    game_response = client.post("/games/create-test?player_count=5")
    game_id = game_response.json()["game_id"]
    players = game_response.json()["players"]
    player_ids = [p["id"] for p in players]

    # Complete hole 16 with Joe's Special (Hoepfinger)
    response = client.post(f"/games/{game_id}/holes/complete", json={
        "hole_number": 16,
        "rotation_order": player_ids,
        "captain_index": 0,
        "phase": "hoepfinger",
        "joes_special_wager": 4,  # Goat selects 4Q
        "teams": {
            "type": "partners",
            "team1": [player_ids[0], player_ids[1]],
            "team2": [player_ids[2], player_ids[3], player_ids[4]]
        },
        "final_wager": 4,
        "winner": "team1",
        "scores": {player_ids[0]: 4, player_ids[1]: 4, player_ids[2]: 5, player_ids[3]: 5, player_ids[4]: 6},
        "hole_par": 4
    })

    assert response.status_code == 200
    result = response.json()["hole_result"]

    # Verify Joe's Special wager recorded
    assert result["joes_special_wager"] == 4
    assert result["phase"] == "hoepfinger"


def test_joes_special_hole_17_5man():
    """Test that Hoepfinger continues on hole 17 for 5-man games"""
    game_response = client.post("/games/create-test?player_count=5")
    game_id = game_response.json()["game_id"]
    players = game_response.json()["players"]
    player_ids = [p["id"] for p in players]

    # Complete hole 17 with Joe's Special (Hoepfinger)
    response = client.post(f"/games/{game_id}/holes/complete", json={
        "hole_number": 17,
        "rotation_order": player_ids,
        "captain_index": 0,
        "phase": "hoepfinger",
        "joes_special_wager": 2,
        "teams": {
            "type": "partners",
            "team1": [player_ids[0], player_ids[1]],
            "team2": [player_ids[2], player_ids[3], player_ids[4]]
        },
        "final_wager": 2,
        "winner": "team1",
        "scores": {player_ids[0]: 4, player_ids[1]: 4, player_ids[2]: 5, player_ids[3]: 5, player_ids[4]: 6},
        "hole_par": 4
    })

    assert response.status_code == 200
    result = response.json()["hole_result"]

    # Verify Hoepfinger still active
    assert result["phase"] == "hoepfinger"


def test_joes_special_hole_18_5man():
    """Test that Hoepfinger continues on hole 18 for 5-man games"""
    game_response = client.post("/games/create-test?player_count=5")
    game_id = game_response.json()["game_id"]
    players = game_response.json()["players"]
    player_ids = [p["id"] for p in players]

    # Complete hole 18 with Joe's Special (Hoepfinger)
    response = client.post(f"/games/{game_id}/holes/complete", json={
        "hole_number": 18,
        "rotation_order": player_ids,
        "captain_index": 0,
        "phase": "hoepfinger",
        "joes_special_wager": 8,
        "teams": {
            "type": "partners",
            "team1": [player_ids[0], player_ids[1]],
            "team2": [player_ids[2], player_ids[3], player_ids[4]]
        },
        "final_wager": 8,
        "winner": "team1",
        "scores": {player_ids[0]: 4, player_ids[1]: 4, player_ids[2]: 5, player_ids[3]: 5, player_ids[4]: 6},
        "hole_par": 4
    })

    assert response.status_code == 200
    result = response.json()["hole_result"]

    # Verify Hoepfinger still active
    assert result["phase"] == "hoepfinger"


def test_hoepfinger_4man_still_starts_hole_17():
    """Test that 4-man Hoepfinger still starts on hole 17"""
    game_response = client.post("/games/create-test?player_count=4")
    game_id = game_response.json()["game_id"]
    players = game_response.json()["players"]
    player_ids = [p["id"] for p in players]

    # Complete hole 17 with Joe's Special (Hoepfinger)
    response = client.post(f"/games/{game_id}/holes/complete", json={
        "hole_number": 17,
        "rotation_order": player_ids,
        "captain_index": 0,
        "phase": "hoepfinger",
        "joes_special_wager": 4,
        "teams": {
            "type": "partners",
            "team1": [player_ids[0], player_ids[1]],
            "team2": [player_ids[2], player_ids[3]]
        },
        "final_wager": 4,
        "winner": "team1",
        "scores": {player_ids[0]: 4, player_ids[1]: 4, player_ids[2]: 5, player_ids[3]: 5},
        "hole_par": 4
    })

    assert response.status_code == 200
    result = response.json()["hole_result"]

    # Verify Hoepfinger works on hole 17 for 4-man
    assert result["phase"] == "hoepfinger"
    assert result["joes_special_wager"] == 4

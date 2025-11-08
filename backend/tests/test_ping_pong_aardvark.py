"""Test Ping Ponging the Aardvark - Phase 5 Advanced Rule"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_ping_pong_quadruples_risk():
    """Test that ping-ponging Aardvark quadruples the points (4x)"""
    game_response = client.post("/games/create-test?player_count=5")
    game_id = game_response.json()["game_id"]
    players = game_response.json()["players"]
    player_ids = [p["id"] for p in players]

    # Aardvark requests team1, team1 tosses, team2 ALSO tosses (ping-pong)
    # Aardvark ends up back on team1 (originally requested team)
    response = client.post(f"/games/{game_id}/holes/complete", json={
        "hole_number": 5,
        "rotation_order": player_ids,
        "captain_index": 0,
        "teams": {
            "type": "partners",
            "team1": [player_ids[0], player_ids[1], player_ids[4]],  # Captain, Partner, Aardvark
            "team2": [player_ids[2], player_ids[3]]
        },
        "aardvark_requested_team": "team1",  # Requested team1
        "aardvark_tossed": True,  # Team1 tossed
        "aardvark_ping_ponged": True,  # Team2 ALSO tossed (ping-pong)
        "final_wager": 2,
        "winner": "team1",
        "scores": {player_ids[0]: 4, player_ids[1]: 4, player_ids[2]: 5, player_ids[3]: 5, player_ids[4]: 4},
        "hole_par": 4
    })

    assert response.status_code == 200
    result = response.json()["hole_result"]
    points_delta = result["points_delta"]

    # Correct formula: pot = wager × winning_team_size
    # Normal: pot = 2Q × 3 winners = 6Q
    # Tossed (2x): 12Q
    # Ping-ponged (4x): 24Q
    # Each winner: 24Q / 3 = 8Q
    # Each loser: -24Q / 2 = -12Q

    assert points_delta[player_ids[0]] == 8  # Team1 winner
    assert points_delta[player_ids[1]] == 8  # Team1 winner
    assert points_delta[player_ids[4]] == 8  # Aardvark winner
    assert points_delta[player_ids[2]] == -12  # Team2 loser
    assert points_delta[player_ids[3]] == -12  # Team2 loser

    # Verify zero-sum
    total = sum(points_delta.values())
    assert abs(total) < 0.01

    # Verify fields in result
    assert result["aardvark_requested_team"] == "team1"
    assert result["aardvark_tossed"] is True
    assert result["aardvark_ping_ponged"] is True


def test_ping_pong_validation_requires_toss():
    """Test that ping-pong can only happen if Aardvark was initially tossed"""
    game_response = client.post("/games/create-test?player_count=5")
    game_id = game_response.json()["game_id"]
    players = game_response.json()["players"]
    player_ids = [p["id"] for p in players]

    # Try to ping-pong without initial toss (should fail)
    response = client.post(f"/games/{game_id}/holes/complete", json={
        "hole_number": 5,
        "rotation_order": player_ids,
        "captain_index": 0,
        "teams": {
            "type": "partners",
            "team1": [player_ids[0], player_ids[1], player_ids[4]],
            "team2": [player_ids[2], player_ids[3]]
        },
        "aardvark_requested_team": "team1",
        "aardvark_tossed": False,  # NOT tossed
        "aardvark_ping_ponged": True,  # But trying to ping-pong (INVALID)
        "final_wager": 2,
        "winner": "team1",
        "scores": {player_ids[0]: 4, player_ids[1]: 4, player_ids[2]: 5, player_ids[3]: 5, player_ids[4]: 4},
        "hole_par": 4
    })

    assert response.status_code == 400
    assert "ping-ponged unless initially tossed" in response.json()["detail"].lower()


def test_toss_without_ping_pong_doubles():
    """Test that simple toss (no ping-pong) still doubles correctly (2x)"""
    game_response = client.post("/games/create-test?player_count=5")
    game_id = game_response.json()["game_id"]
    players = game_response.json()["players"]
    player_ids = [p["id"] for p in players]

    # Aardvark tossed but NOT ping-ponged (regular 2x doubling)
    response = client.post(f"/games/{game_id}/holes/complete", json={
        "hole_number": 5,
        "rotation_order": player_ids,
        "captain_index": 0,
        "teams": {
            "type": "partners",
            "team1": [player_ids[0], player_ids[1]],  # Tossed Aardvark
            "team2": [player_ids[2], player_ids[3], player_ids[4]]  # Aardvark auto-joins
        },
        "aardvark_requested_team": "team1",
        "aardvark_tossed": True,
        "aardvark_ping_ponged": False,  # NOT ping-ponged
        "final_wager": 2,
        "winner": "team2",
        "scores": {player_ids[0]: 5, player_ids[1]: 5, player_ids[2]: 4, player_ids[3]: 4, player_ids[4]: 4},
        "hole_par": 4
    })

    assert response.status_code == 200
    result = response.json()["hole_result"]
    points_delta = result["points_delta"]

    # Normal: pot = 2Q × 3 winners = 6Q
    # Tossed (2x): 12Q
    # Each winner: 12Q / 3 = 4Q
    # Each loser: -12Q / 2 = -6Q

    assert points_delta[player_ids[0]] == -6  # Team1 loser
    assert points_delta[player_ids[1]] == -6  # Team1 loser
    assert points_delta[player_ids[2]] == 4  # Team2 winner
    assert points_delta[player_ids[3]] == 4  # Team2 winner
    assert points_delta[player_ids[4]] == 4  # Aardvark winner

    assert result["aardvark_ping_ponged"] is False


def test_ping_pong_only_5man():
    """Test that ping-pong fields are ignored in non-5-man games"""
    game_response = client.post("/games/create-test?player_count=4")
    game_id = game_response.json()["game_id"]
    players = game_response.json()["players"]
    player_ids = [p["id"] for p in players]

    response = client.post(f"/games/{game_id}/holes/complete", json={
        "hole_number": 5,
        "rotation_order": player_ids,
        "captain_index": 0,
        "teams": {
            "type": "partners",
            "team1": [player_ids[0], player_ids[1]],
            "team2": [player_ids[2], player_ids[3]]
        },
        "aardvark_ping_ponged": True,  # Should be ignored in 4-man
        "final_wager": 2,
        "winner": "team1",
        "scores": {player_ids[0]: 4, player_ids[1]: 4, player_ids[2]: 5, player_ids[3]: 5},
        "hole_par": 4
    })

    assert response.status_code == 200
    result = response.json()["hole_result"]

    # Should be sanitized to False for non-5-man
    assert result.get("aardvark_ping_ponged") is False

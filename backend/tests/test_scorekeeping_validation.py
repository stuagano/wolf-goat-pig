"""Test Scorekeeping Validation - points must balance to zero"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_partners_points_balance_to_zero():
    """Test partners mode points balance"""
    game_response = client.post("/games/create-test?player_count=4")
    game_id = game_response.json()["game_id"]
    players = game_response.json()["players"]
    player_ids = [p["id"] for p in players]

    # Hole 1: partners 2v2
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
    points_delta = result["points_delta"]

    # Verify points balance to zero
    total = sum(points_delta.values())
    assert total == 0, f"Points should balance to zero, got {total}"


def test_solo_points_balance_to_zero():
    """Test solo mode points balance"""
    game_response = client.post("/games/create-test?player_count=4")
    game_id = game_response.json()["game_id"]
    players = game_response.json()["players"]
    player_ids = [p["id"] for p in players]

    # Hole 1: solo (1v3)
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
    result = response.json()["hole_result"]
    points_delta = result["points_delta"]

    # Verify points balance to zero
    total = sum(points_delta.values())
    assert total == 0, f"Points should balance to zero, got {total}"


def test_duncan_points_balance_to_zero():
    """Test Duncan 3-for-2 payout still balances"""
    game_response = client.post("/games/create-test?player_count=4")
    game_id = game_response.json()["game_id"]
    players = game_response.json()["players"]
    player_ids = [p["id"] for p in players]

    # Hole 1: solo with Duncan (3-for-2)
    response = client.post(f"/games/{game_id}/holes/complete", json={
        "hole_number": 1,
        "rotation_order": player_ids,
        "captain_index": 0,
        "duncan_invoked": True,
        "teams": {"type": "solo", "captain": player_ids[0], "opponents": [player_ids[1], player_ids[2], player_ids[3]]},
        "final_wager": 2,
        "winner": "captain",
        "scores": {player_ids[0]: 4, player_ids[1]: 5, player_ids[2]: 5, player_ids[3]: 6},
        "hole_par": 4
    })

    assert response.status_code == 200
    result = response.json()["hole_result"]
    points_delta = result["points_delta"]

    # Verify points balance to zero
    total = sum(points_delta.values())
    assert total == 0, f"Points should balance to zero, got {total}"


def test_double_points_still_balance_to_zero():
    """Test double points on holes 17-18 still balance"""
    game_response = client.post("/games/create-test?player_count=4")
    game_id = game_response.json()["game_id"]
    players = game_response.json()["players"]
    player_ids = [p["id"] for p in players]

    # Play through to hole 17
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

    # Hole 17: double points
    rotation = player_ids
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
    points_delta = result["points_delta"]

    # Verify points balance to zero (even with 2x multiplier)
    total = sum(points_delta.values())
    assert total == 0, f"Points should balance to zero, got {total}"


def test_5man_karl_marx_points_balance():
    """Test 5-man Karl Marx uneven distribution still balances"""
    game_response = client.post("/games/create-test?player_count=5")
    game_id = game_response.json()["game_id"]
    players = game_response.json()["players"]
    player_ids = [p["id"] for p in players]

    # Hole 1: 2v3 teams (triggers Karl Marx)
    response = client.post(f"/games/{game_id}/holes/complete", json={
        "hole_number": 1,
        "rotation_order": player_ids,
        "captain_index": 0,
        "teams": {"type": "partners", "team1": [player_ids[0], player_ids[1]], "team2": [player_ids[2], player_ids[3], player_ids[4]]},
        "final_wager": 1,
        "winner": "team1",
        "scores": {player_ids[0]: 4, player_ids[1]: 4, player_ids[2]: 5, player_ids[3]: 6, player_ids[4]: 6},
        "hole_par": 4
    })

    assert response.status_code == 200
    result = response.json()["hole_result"]
    points_delta = result["points_delta"]

    # Verify points balance to zero (Karl Marx should maintain balance)
    total = sum(points_delta.values())
    assert abs(total) < 0.01, f"Points should balance to zero, got {total}"  # Allow for floating point error


def test_push_points_balance_to_zero():
    """Test push (tie) results in zero points for everyone"""
    game_response = client.post("/games/create-test?player_count=4")
    game_id = game_response.json()["game_id"]
    players = game_response.json()["players"]
    player_ids = [p["id"] for p in players]

    # Hole 1: push
    response = client.post(f"/games/{game_id}/holes/complete", json={
        "hole_number": 1,
        "rotation_order": player_ids,
        "captain_index": 0,
        "teams": {"type": "partners", "team1": [player_ids[0], player_ids[1]], "team2": [player_ids[2], player_ids[3]]},
        "final_wager": 2,
        "winner": "push",
        "scores": {player_ids[0]: 4, player_ids[1]: 4, player_ids[2]: 4, player_ids[3]: 4},
        "hole_par": 4
    })

    assert response.status_code == 200
    result = response.json()["hole_result"]
    points_delta = result["points_delta"]

    # Verify all points are zero
    total = sum(points_delta.values())
    assert total == 0, f"Points should balance to zero, got {total}"

    # Also verify each player got 0
    for player_id in player_ids:
        assert points_delta[player_id] == 0, f"Player {player_id} should have 0 points in a push"

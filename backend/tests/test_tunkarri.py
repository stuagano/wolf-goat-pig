"""Test The Tunkarri - Phase 5 Advanced Rule"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_tunkarri_win_3_for_2_payout():
    """Test that Aardvark wins 3-for-2 when invoking Tunkarri and winning"""
    game_response = client.post("/games/create-test?player_count=5")
    game_id = game_response.json()["game_id"]
    players = game_response.json()["players"]
    player_ids = [p["id"] for p in players]

    # Aardvark (player 5) goes solo with Tunkarri and wins
    aardvark_id = player_ids[4]  # Position 5 (index 4)

    response = client.post(f"/games/{game_id}/holes/complete", json={
        "hole_number": 5,
        "rotation_order": player_ids,
        "captain_index": 4,  # Aardvark is at index 4
        "teams": {
            "type": "solo",
            "captain": aardvark_id,  # Aardvark goes solo
            "opponents": [player_ids[0], player_ids[1], player_ids[2], player_ids[3]]
        },
        "tunkarri_invoked": True,  # Aardvark declares before Captain hits
        "final_wager": 2,
        "winner": "captain",  # Aardvark wins
        "scores": {player_ids[0]: 5, player_ids[1]: 5, player_ids[2]: 5, player_ids[3]: 5, player_ids[4]: 3},
        "hole_par": 4
    })

    assert response.status_code == 200
    result = response.json()["hole_result"]
    points_delta = result["points_delta"]

    # The Tunkarri: 3Q for every 2Q wagered
    # Wager: 2Q
    # Total payout: (2 × 3) / 2 = 3Q
    # Aardvark wins: 3Q
    # Each opponent loses: 3Q / 4 = 0.75Q

    assert points_delta[aardvark_id] == 3  # Aardvark wins 3Q
    assert points_delta[player_ids[0]] == -0.75  # Each opponent loses 0.75Q
    assert points_delta[player_ids[1]] == -0.75
    assert points_delta[player_ids[2]] == -0.75
    assert points_delta[player_ids[3]] == -0.75

    # Verify zero-sum
    total = sum(points_delta.values())
    assert abs(total) < 0.01

    # Verify field in result
    assert result["tunkarri_invoked"] is True


def test_tunkarri_loss_normal_payout():
    """Test that when Tunkarri fails, normal solo payout applies"""
    game_response = client.post("/games/create-test?player_count=5")
    game_id = game_response.json()["game_id"]
    players = game_response.json()["players"]
    player_ids = [p["id"] for p in players]

    aardvark_id = player_ids[4]

    response = client.post(f"/games/{game_id}/holes/complete", json={
        "hole_number": 5,
        "rotation_order": player_ids,
        "captain_index": 4,  # Aardvark is at index 4
        "teams": {
            "type": "solo",
            "captain": aardvark_id,
            "opponents": [player_ids[0], player_ids[1], player_ids[2], player_ids[3]]
        },
        "tunkarri_invoked": True,
        "final_wager": 2,
        "winner": "opponents",  # Aardvark loses
        "scores": {player_ids[0]: 4, player_ids[1]: 4, player_ids[2]: 4, player_ids[3]: 4, player_ids[4]: 7},
        "hole_par": 4
    })

    assert response.status_code == 200
    result = response.json()["hole_result"]
    points_delta = result["points_delta"]

    # When Tunkarri fails: Normal solo loss
    # Aardvark loses: 2Q × 4 opponents = 8Q
    # Each opponent wins: 2Q

    assert points_delta[aardvark_id] == -8
    assert points_delta[player_ids[0]] == 2
    assert points_delta[player_ids[1]] == 2
    assert points_delta[player_ids[2]] == 2
    assert points_delta[player_ids[3]] == 2

    # Verify zero-sum
    total = sum(points_delta.values())
    assert abs(total) < 0.01


def test_tunkarri_validation_only_aardvark():
    """Test that only Aardvark can invoke Tunkarri"""
    game_response = client.post("/games/create-test?player_count=5")
    game_id = game_response.json()["game_id"]
    players = game_response.json()["players"]
    player_ids = [p["id"] for p in players]

    # Try to have non-Aardvark player invoke Tunkarri (should fail)
    response = client.post(f"/games/{game_id}/holes/complete", json={
        "hole_number": 5,
        "rotation_order": player_ids,
        "captain_index": 0,
        "teams": {
            "type": "solo",
            "captain": player_ids[0],  # Player 1 (NOT Aardvark)
            "opponents": [player_ids[1], player_ids[2], player_ids[3], player_ids[4]]
        },
        "tunkarri_invoked": True,  # INVALID - not Aardvark
        "final_wager": 2,
        "winner": "captain",
        "scores": {player_ids[0]: 3, player_ids[1]: 5, player_ids[2]: 5, player_ids[3]: 5, player_ids[4]: 5},
        "hole_par": 4
    })

    assert response.status_code == 400
    assert "aardvark" in response.json()["detail"].lower()


def test_tunkarri_validation_only_solo():
    """Test that Tunkarri can only be invoked in solo mode"""
    game_response = client.post("/games/create-test?player_count=5")
    game_id = game_response.json()["game_id"]
    players = game_response.json()["players"]
    player_ids = [p["id"] for p in players]

    # Try to invoke Tunkarri in partners mode (should fail)
    response = client.post(f"/games/{game_id}/holes/complete", json={
        "hole_number": 5,
        "rotation_order": player_ids,
        "captain_index": 0,
        "teams": {
            "type": "partners",
            "team1": [player_ids[0], player_ids[1]],
            "team2": [player_ids[2], player_ids[3], player_ids[4]]
        },
        "tunkarri_invoked": True,  # INVALID - not solo mode
        "final_wager": 2,
        "winner": "team1",
        "scores": {player_ids[0]: 4, player_ids[1]: 4, player_ids[2]: 5, player_ids[3]: 5, player_ids[4]: 5},
        "hole_par": 4
    })

    assert response.status_code == 400
    assert "solo mode" in response.json()["detail"].lower()


def test_tunkarri_validation_only_5man():
    """Test that Tunkarri is only available in 5-man+ games"""
    game_response = client.post("/games/create-test?player_count=4")
    game_id = game_response.json()["game_id"]
    players = game_response.json()["players"]
    player_ids = [p["id"] for p in players]

    response = client.post(f"/games/{game_id}/holes/complete", json={
        "hole_number": 5,
        "rotation_order": player_ids,
        "captain_index": 0,
        "teams": {
            "type": "solo",
            "captain": player_ids[0],
            "opponents": [player_ids[1], player_ids[2], player_ids[3]]
        },
        "tunkarri_invoked": True,  # INVALID - 4-man game
        "final_wager": 2,
        "winner": "captain",
        "scores": {player_ids[0]: 3, player_ids[1]: 5, player_ids[2]: 5, player_ids[3]: 5},
        "hole_par": 4
    })

    assert response.status_code == 400
    assert "5-man" in response.json()["detail"].lower() or "6-man" in response.json()["detail"].lower()


def test_normal_aardvark_solo_without_tunkarri():
    """Test that Aardvark can go solo without Tunkarri (normal payout)"""
    game_response = client.post("/games/create-test?player_count=5")
    game_id = game_response.json()["game_id"]
    players = game_response.json()["players"]
    player_ids = [p["id"] for p in players]

    aardvark_id = player_ids[4]

    response = client.post(f"/games/{game_id}/holes/complete", json={
        "hole_number": 5,
        "rotation_order": player_ids,
        "captain_index": 4,  # Aardvark is at index 4
        "teams": {
            "type": "solo",
            "captain": aardvark_id,
            "opponents": [player_ids[0], player_ids[1], player_ids[2], player_ids[3]]
        },
        "tunkarri_invoked": False,  # Normal solo
        "aardvark_solo": True,
        "final_wager": 2,
        "winner": "captain",
        "scores": {player_ids[0]: 5, player_ids[1]: 5, player_ids[2]: 5, player_ids[3]: 5, player_ids[4]: 3},
        "hole_par": 4
    })

    assert response.status_code == 200
    result = response.json()["hole_result"]
    points_delta = result["points_delta"]

    # Normal solo win: 2Q × 4 opponents = 8Q
    assert points_delta[aardvark_id] == 8
    assert points_delta[player_ids[0]] == -2
    assert points_delta[player_ids[1]] == -2
    assert points_delta[player_ids[2]] == -2
    assert points_delta[player_ids[3]] == -2

    assert result["tunkarri_invoked"] is False
    assert result["aardvark_solo"] is True

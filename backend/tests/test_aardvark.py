"""Test The Aardvark - 5th Player Special Mechanics - Phase 5, Task 1"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_aardvark_joins_team1():
    """Test that Aardvark can request to join team1 and be accepted"""
    game_response = client.post("/games/create-test?player_count=5")
    game_id = game_response.json()["game_id"]
    players = game_response.json()["players"]
    player_ids = [p["id"] for p in players]

    # Captain (player 0) partners with player 1
    # Aardvark (player 4) requests to join team1
    response = client.post(f"/games/{game_id}/holes/complete", json={
        "hole_number": 5,
        "rotation_order": player_ids,
        "captain_index": 0,
        "teams": {
            "type": "partners",
            "team1": [player_ids[0], player_ids[1], player_ids[4]],  # Captain, Partner, Aardvark
            "team2": [player_ids[2], player_ids[3]]
        },
        "aardvark_requested_team": "team1",
        "aardvark_tossed": False,
        "final_wager": 2,
        "winner": "team1",
        "scores": {player_ids[0]: 4, player_ids[1]: 4, player_ids[2]: 5, player_ids[3]: 5, player_ids[4]: 4},
        "hole_par": 4
    })

    assert response.status_code == 200
    result = response.json()["hole_result"]

    # Verify Aardvark is on team1
    assert player_ids[4] in result["teams"]["team1"]
    assert result.get("aardvark_requested_team") == "team1"
    assert result.get("aardvark_tossed") == False


def test_aardvark_joins_team2():
    """Test that Aardvark can request to join team2 and be accepted"""
    game_response = client.post("/games/create-test?player_count=5")
    game_id = game_response.json()["game_id"]
    players = game_response.json()["players"]
    player_ids = [p["id"] for p in players]

    # Captain (player 0) partners with player 1
    # Aardvark (player 4) requests to join team2
    response = client.post(f"/games/{game_id}/holes/complete", json={
        "hole_number": 5,
        "rotation_order": player_ids,
        "captain_index": 0,
        "teams": {
            "type": "partners",
            "team1": [player_ids[0], player_ids[1]],
            "team2": [player_ids[2], player_ids[3], player_ids[4]]  # Aardvark joins team2
        },
        "aardvark_requested_team": "team2",
        "aardvark_tossed": False,
        "final_wager": 2,
        "winner": "team2",
        "scores": {player_ids[0]: 5, player_ids[1]: 5, player_ids[2]: 4, player_ids[3]: 4, player_ids[4]: 4},
        "hole_par": 4
    })

    assert response.status_code == 200
    result = response.json()["hole_result"]

    # Verify Aardvark is on team2
    assert player_ids[4] in result["teams"]["team2"]
    assert result.get("aardvark_requested_team") == "team2"


def test_aardvark_tossed_joins_opposite_team():
    """Test that when Aardvark is tossed by team1, they auto-join team2"""
    game_response = client.post("/games/create-test?player_count=5")
    game_id = game_response.json()["game_id"]
    players = game_response.json()["players"]
    player_ids = [p["id"] for p in players]

    # Aardvark requests team1, gets tossed, auto-joins team2
    response = client.post(f"/games/{game_id}/holes/complete", json={
        "hole_number": 5,
        "rotation_order": player_ids,
        "captain_index": 0,
        "teams": {
            "type": "partners",
            "team1": [player_ids[0], player_ids[1]],
            "team2": [player_ids[2], player_ids[3], player_ids[4]]  # Aardvark auto-joins team2
        },
        "aardvark_requested_team": "team1",  # Requested team1
        "aardvark_tossed": True,  # But was tossed
        "final_wager": 2,
        "winner": "team2",
        "scores": {player_ids[0]: 5, player_ids[1]: 5, player_ids[2]: 4, player_ids[3]: 4, player_ids[4]: 4},
        "hole_par": 4
    })

    assert response.status_code == 200
    result = response.json()["hole_result"]

    # Verify Aardvark is on team2 (opposite of requested)
    assert player_ids[4] in result["teams"]["team2"]
    assert player_ids[4] not in result["teams"]["team1"]
    assert result.get("aardvark_requested_team") == "team1"
    assert result.get("aardvark_tossed") == True


def test_aardvark_tossed_doubles_risk():
    """Test that when Aardvark is tossed, the team that tossed has doubled risk"""
    game_response = client.post("/games/create-test?player_count=5")
    game_id = game_response.json()["game_id"]
    players = game_response.json()["players"]
    player_ids = [p["id"] for p in players]

    # Aardvark tossed by team1, team1 loses, should lose 2x points
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
        "final_wager": 2,
        "winner": "team2",
        "scores": {player_ids[0]: 5, player_ids[1]: 5, player_ids[2]: 4, player_ids[3]: 4, player_ids[4]: 4},
        "hole_par": 4
    })

    assert response.status_code == 200
    result = response.json()["hole_result"]
    points_delta = result["points_delta"]

    # Team1 (tossed Aardvark) should have doubled losses
    # Normal: each loses 2 points (wager 2, 2 vs 3)
    # Doubled: each loses 4 points
    assert points_delta[player_ids[0]] == -4  # Team1 doubled loss
    assert points_delta[player_ids[1]] == -4  # Team1 doubled loss

    # Team2 (with Aardvark) should win points
    # Total won: 8 (4+4 from team1), split among 3 players
    # But uneven distribution (Karl Marx if applicable)
    total_team2_win = (
        points_delta[player_ids[2]] +
        points_delta[player_ids[3]] +
        points_delta[player_ids[4]]
    )
    assert total_team2_win == 8  # Total winnings from doubled risk


def test_aardvark_solo():
    """Test that Aardvark can go solo creating 1v1v3 scenario"""
    game_response = client.post("/games/create-test?player_count=5")
    game_id = game_response.json()["game_id"]
    players = game_response.json()["players"]
    player_ids = [p["id"] for p in players]

    # Aardvark goes solo
    response = client.post(f"/games/{game_id}/holes/complete", json={
        "hole_number": 5,
        "rotation_order": player_ids,
        "captain_index": 4,  # Aardvark is captain
        "teams": {
            "type": "solo",
            "captain": player_ids[4],  # Aardvark solo
            "opponents": [player_ids[0], player_ids[1], player_ids[2], player_ids[3]]
        },
        "aardvark_solo": True,
        "final_wager": 2,
        "winner": "captain",
        "scores": {player_ids[0]: 5, player_ids[1]: 5, player_ids[2]: 5, player_ids[3]: 5, player_ids[4]: 3},
        "hole_par": 4
    })

    assert response.status_code == 200
    result = response.json()["hole_result"]

    # Verify 1v4 formation
    assert result["teams"]["type"] == "solo"
    assert result["teams"]["captain"] == player_ids[4]
    assert len(result["teams"]["opponents"]) == 4
    assert result.get("aardvark_solo") == True


def test_captain_cannot_partner_aardvark():
    """Test that Captain cannot directly partner with Aardvark (player 5)"""
    game_response = client.post("/games/create-test?player_count=5")
    game_id = game_response.json()["game_id"]
    players = game_response.json()["players"]
    player_ids = [p["id"] for p in players]

    # Try to have captain partner with Aardvark (should fail)
    response = client.post(f"/games/{game_id}/holes/complete", json={
        "hole_number": 5,
        "rotation_order": player_ids,
        "captain_index": 0,
        "teams": {
            "type": "partners",
            "team1": [player_ids[0], player_ids[4]],  # Captain + Aardvark (INVALID)
            "team2": [player_ids[1], player_ids[2], player_ids[3]]
        },
        "final_wager": 2,
        "winner": "team1",
        "scores": {player_ids[0]: 4, player_ids[1]: 5, player_ids[2]: 5, player_ids[3]: 5, player_ids[4]: 4},
        "hole_par": 4
    })

    assert response.status_code == 400
    assert "captain" in response.json()["detail"].lower() and "aardvark" in response.json()["detail"].lower()


def test_aardvark_validation_only_5man():
    """Test that Aardvark mechanics only apply to 5-man games"""
    game_response = client.post("/games/create-test?player_count=4")
    game_id = game_response.json()["game_id"]
    players = game_response.json()["players"]
    player_ids = [p["id"] for p in players]

    # Try to use Aardvark fields in 4-man game (should be ignored or rejected)
    response = client.post(f"/games/{game_id}/holes/complete", json={
        "hole_number": 5,
        "rotation_order": player_ids,
        "captain_index": 0,
        "teams": {
            "type": "partners",
            "team1": [player_ids[0], player_ids[1]],
            "team2": [player_ids[2], player_ids[3]]
        },
        "aardvark_requested_team": "team1",  # Should be ignored/rejected
        "final_wager": 2,
        "winner": "team1",
        "scores": {player_ids[0]: 4, player_ids[1]: 4, player_ids[2]: 5, player_ids[3]: 5},
        "hole_par": 4
    })

    # Either accept but ignore Aardvark fields, or reject
    # For now, expect it to succeed but ignore Aardvark fields
    assert response.status_code in [200, 400]
    if response.status_code == 200:
        result = response.json()["hole_result"]
        # Aardvark fields should be ignored
        assert result.get("aardvark_requested_team") is None

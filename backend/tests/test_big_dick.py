"""Test The Big Dick - 18th Hole Special - Phase 4, Task 5"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_big_dick_on_hole_18():
    """Test that any player can declare Big Dick on hole 18"""
    game_response = client.post("/games/create-test?player_count=4")
    game_id = game_response.json()["game_id"]
    players = game_response.json()["players"]
    player_ids = [p["id"] for p in players]

    # Hole 18: Player 2 (not captain) declares Big Dick
    response = client.post(f"/games/{game_id}/holes/complete", json={
        "hole_number": 18,
        "rotation_order": player_ids,
        "captain_index": 0,  # Captain is player_ids[0]
        "big_dick_invoked_by": player_ids[1],  # Player 2 declares Big Dick
        "teams": {
            "type": "solo",
            "captain": player_ids[1],  # Player 2 vs everyone else
            "opponents": [player_ids[0], player_ids[2], player_ids[3]]
        },
        "final_wager": 2,
        "winner": "captain",
        "scores": {player_ids[0]: 5, player_ids[1]: 4, player_ids[2]: 5, player_ids[3]: 6},
        "hole_par": 4
    })

    assert response.status_code == 200
    result = response.json()["hole_result"]

    # Verify Big Dick was invoked
    assert result.get("big_dick_invoked_by") == player_ids[1]
    assert result["teams"]["type"] == "solo"
    assert result["teams"]["captain"] == player_ids[1]


def test_big_dick_only_on_hole_18():
    """Test that Big Dick can only be invoked on hole 18"""
    game_response = client.post("/games/create-test?player_count=4")
    game_id = game_response.json()["game_id"]
    players = game_response.json()["players"]
    player_ids = [p["id"] for p in players]

    # Try to invoke Big Dick on hole 17 (should fail)
    response = client.post(f"/games/{game_id}/holes/complete", json={
        "hole_number": 17,
        "rotation_order": player_ids,
        "captain_index": 0,
        "big_dick_invoked_by": player_ids[1],
        "teams": {
            "type": "solo",
            "captain": player_ids[1],
            "opponents": [player_ids[0], player_ids[2], player_ids[3]]
        },
        "final_wager": 2,
        "winner": "captain",
        "scores": {player_ids[0]: 5, player_ids[1]: 4, player_ids[2]: 5, player_ids[3]: 6},
        "hole_par": 4
    })

    assert response.status_code == 400
    assert "18" in response.json()["detail"].lower() or "big dick" in response.json()["detail"].lower()


def test_big_dick_1_vs_all():
    """Test that Big Dick creates 1 vs all team formation"""
    game_response = client.post("/games/create-test?player_count=4")
    game_id = game_response.json()["game_id"]
    players = game_response.json()["players"]
    player_ids = [p["id"] for p in players]

    # Hole 18: Player 3 declares Big Dick
    response = client.post(f"/games/{game_id}/holes/complete", json={
        "hole_number": 18,
        "rotation_order": player_ids,
        "captain_index": 0,
        "big_dick_invoked_by": player_ids[2],
        "teams": {
            "type": "solo",
            "captain": player_ids[2],
            "opponents": [player_ids[0], player_ids[1], player_ids[3]]
        },
        "final_wager": 2,
        "winner": "captain",
        "scores": {player_ids[0]: 5, player_ids[1]: 5, player_ids[2]: 3, player_ids[3]: 6},
        "hole_par": 4
    })

    assert response.status_code == 200
    result = response.json()["hole_result"]

    # Verify 1 vs 3 formation
    assert result["teams"]["type"] == "solo"
    assert result["teams"]["captain"] == player_ids[2]
    assert len(result["teams"]["opponents"]) == 3
    assert set(result["teams"]["opponents"]) == {player_ids[0], player_ids[1], player_ids[3]}


def test_big_dick_captain_vs_opponents_payout():
    """Test that Big Dick pays out correctly (1 vs 3)"""
    game_response = client.post("/games/create-test?player_count=4")
    game_id = game_response.json()["game_id"]
    players = game_response.json()["players"]
    player_ids = [p["id"] for p in players]

    # Hole 18: Big Dick declared, captain wins
    response = client.post(f"/games/{game_id}/holes/complete", json={
        "hole_number": 18,
        "rotation_order": player_ids,
        "captain_index": 0,
        "big_dick_invoked_by": player_ids[0],
        "teams": {
            "type": "solo",
            "captain": player_ids[0],
            "opponents": [player_ids[1], player_ids[2], player_ids[3]]
        },
        "final_wager": 2,
        "winner": "captain",
        "scores": {player_ids[0]: 3, player_ids[1]: 5, player_ids[2]: 5, player_ids[3]: 6},
        "hole_par": 4
    })

    assert response.status_code == 200
    result = response.json()["hole_result"]
    points_delta = result["points_delta"]

    # Solo payout: captain wins 3x wager, opponents lose 1x wager each
    # NOTE: Hole 18 has automatic 2x multiplier (Phase 3 feature)
    # So: (2 * 3) * 2 = 12 for captain, (2 * 1) * 2 = 4 for each opponent
    assert points_delta[player_ids[0]] == 12  # Wins (2*3)*2 = 12 (double points on hole 18)
    assert points_delta[player_ids[1]] == -4  # Loses (2*1)*2 = 4
    assert points_delta[player_ids[2]] == -4  # Loses (2*1)*2 = 4
    assert points_delta[player_ids[3]] == -4  # Loses (2*1)*2 = 4

    # Verify balance
    assert sum(points_delta.values()) == 0


def test_big_dick_saved_in_hole_history():
    """Test that Big Dick invocation is saved in hole history"""
    game_response = client.post("/games/create-test?player_count=4")
    game_id = game_response.json()["game_id"]
    players = game_response.json()["players"]
    player_ids = [p["id"] for p in players]

    # Hole 18: Big Dick declared
    response = client.post(f"/games/{game_id}/holes/complete", json={
        "hole_number": 18,
        "rotation_order": player_ids,
        "captain_index": 0,
        "big_dick_invoked_by": player_ids[0],
        "teams": {
            "type": "solo",
            "captain": player_ids[0],
            "opponents": [player_ids[1], player_ids[2], player_ids[3]]
        },
        "final_wager": 2,
        "winner": "captain",
        "scores": {player_ids[0]: 3, player_ids[1]: 5, player_ids[2]: 5, player_ids[3]: 6},
        "hole_par": 4
    })

    assert response.status_code == 200
    result = response.json()["hole_result"]

    # Verify big_dick_invoked_by is in result
    assert "big_dick_invoked_by" in result
    assert result["big_dick_invoked_by"] == player_ids[0]


def test_normal_solo_on_hole_18_still_works():
    """Test that normal solo (not Big Dick) still works on hole 18"""
    game_response = client.post("/games/create-test?player_count=4")
    game_id = game_response.json()["game_id"]
    players = game_response.json()["players"]
    player_ids = [p["id"] for p in players]

    # Hole 18: Normal solo by captain (not Big Dick)
    response = client.post(f"/games/{game_id}/holes/complete", json={
        "hole_number": 18,
        "rotation_order": player_ids,
        "captain_index": 0,
        "teams": {
            "type": "solo",
            "captain": player_ids[0],
            "opponents": [player_ids[1], player_ids[2], player_ids[3]]
        },
        "final_wager": 2,
        "winner": "captain",
        "scores": {player_ids[0]: 3, player_ids[1]: 5, player_ids[2]: 5, player_ids[3]: 6},
        "hole_par": 4
    })

    assert response.status_code == 200
    result = response.json()["hole_result"]

    # Verify no Big Dick marker
    assert result.get("big_dick_invoked_by") is None

"""Test The Duncan - Captain goes solo before hitting for 3-for-2 payout"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_duncan_pays_3_for_2():
    """Test The Duncan pays 3 quarters for every 2 wagered"""
    game_response = client.post("/games/create-test?player_count=4")
    game_id = game_response.json()["game_id"]
    players = game_response.json()["players"]
    player_ids = [p["id"] for p in players]

    # Hole 1: p1 invokes Duncan (solo before hitting), wager 2Q
    response = client.post(f"/games/{game_id}/holes/complete", json={
        "hole_number": 1,
        "rotation_order": player_ids,
        "captain_index": 0,
        "duncan_invoked": True,  # NEW FIELD
        "teams": {"type": "solo", "captain": player_ids[0], "opponents": [player_ids[1], player_ids[2], player_ids[3]]},
        "final_wager": 2,
        "winner": "captain",
        "scores": {player_ids[0]: 4, player_ids[1]: 5, player_ids[2]: 5, player_ids[3]: 6},
        "hole_par": 4
    })

    assert response.status_code == 200
    result = response.json()["hole_result"]

    # Captain wins 3Q (3-for-2 on 2Q wagered)
    # Each opponent loses 1Q
    assert result["points_delta"][player_ids[0]] == 3
    assert result["points_delta"][player_ids[1]] == -1
    assert result["points_delta"][player_ids[2]] == -1
    assert result["points_delta"][player_ids[3]] == -1


def test_duncan_only_for_solo():
    """Test The Duncan only applies to solo play"""
    game_response = client.post("/games/create-test?player_count=4")
    game_id = game_response.json()["game_id"]
    players = game_response.json()["players"]
    player_ids = [p["id"] for p in players]

    # Try to invoke Duncan with partners (should ignore Duncan flag)
    response = client.post(f"/games/{game_id}/holes/complete", json={
        "hole_number": 1,
        "rotation_order": player_ids,
        "captain_index": 0,
        "duncan_invoked": True,
        "teams": {"type": "partners", "team1": [player_ids[0], player_ids[1]], "team2": [player_ids[2], player_ids[3]]},
        "final_wager": 2,
        "winner": "team1",
        "scores": {player_ids[0]: 4, player_ids[1]: 5, player_ids[2]: 5, player_ids[3]: 6},
        "hole_par": 4
    })

    # Should succeed but ignore Duncan flag (normal 2Q split for partners)
    assert response.status_code == 200
    result = response.json()["hole_result"]
    assert result["points_delta"][player_ids[0]] == 2
    assert result["points_delta"][player_ids[1]] == 2

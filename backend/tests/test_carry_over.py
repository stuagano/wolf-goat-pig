"""Test carry-over logic for push outcomes"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_push_triggers_carryover():
    """Test that a push (tie) triggers carry-over to next hole"""
    # Create test game
    game_response = client.post("/games/create-test?player_count=4")
    assert game_response.status_code == 200
    game_id = game_response.json()["game_id"]
    players = game_response.json()["players"]
    player_ids = [p["id"] for p in players]

    # Hole 1: Push (tie)
    client.post(f"/games/{game_id}/holes/complete", json={
        "hole_number": 1,
        "rotation_order": player_ids,
        "captain_index": 0,
        "teams": {"type": "partners", "team1": [player_ids[0], player_ids[1]], "team2": [player_ids[2], player_ids[3]]},
        "final_wager": 2,  # Wager was 2Q
        "winner": "push",  # PUSH
        "scores": {player_ids[0]: 4, player_ids[1]: 4, player_ids[2]: 4, player_ids[3]: 4},
        "hole_par": 4
    })

    # Check next hole wager
    next_wager = client.get(f"/games/{game_id}/next-hole-wager")
    assert next_wager.status_code == 200
    data = next_wager.json()
    assert data["base_wager"] == 4  # 2Q × 2 = 4Q carry-over
    assert data["carry_over"] is True
    assert "Carry-over from hole 1 push" in data["message"]


def test_consecutive_carryover_blocked():
    """Test that carry-over cannot occur on consecutive holes"""
    # Create test game
    game_response = client.post("/games/create-test?player_count=4")
    assert game_response.status_code == 200
    game_id = game_response.json()["game_id"]
    players = game_response.json()["players"]
    player_ids = [p["id"] for p in players]

    # Hole 1: Push (wager 2Q)
    client.post(f"/games/{game_id}/holes/complete", json={
        "hole_number": 1,
        "rotation_order": player_ids,
        "captain_index": 0,
        "final_wager": 2,
        "winner": "push",
        "teams": {"type": "partners", "team1": [player_ids[0], player_ids[1]], "team2": [player_ids[2], player_ids[3]]},
        "scores": {player_ids[0]: 4, player_ids[1]: 4, player_ids[2]: 4, player_ids[3]: 4},
        "hole_par": 4
    })

    # Hole 2: Push again (wager 4Q from carry-over)
    client.post(f"/games/{game_id}/holes/complete", json={
        "hole_number": 2,
        "rotation_order": player_ids,
        "captain_index": 0,
        "final_wager": 4,
        "winner": "push",
        "teams": {"type": "partners", "team1": [player_ids[0], player_ids[1]], "team2": [player_ids[2], player_ids[3]]},
        "scores": {player_ids[0]: 5, player_ids[1]: 5, player_ids[2]: 5, player_ids[3]: 5},
        "hole_par": 4,
        "carry_over_applied": True
    })

    # Hole 3: Should NOT have another carry-over (consecutive block)
    next_wager = client.get(f"/games/{game_id}/next-hole-wager")
    assert next_wager.status_code == 200
    data = next_wager.json()
    assert data["base_wager"] == 4  # Stays at 4Q (no additional carry)
    assert data["carry_over"] is False
    assert "Consecutive carry-over blocked" in data["message"]


def test_carryover_resets_after_decided_hole():
    """Test carry-over can apply again after a decided hole"""
    # Create test game
    game_response = client.post("/games/create-test?player_count=4")
    assert game_response.status_code == 200
    game_id = game_response.json()["game_id"]
    players = game_response.json()["players"]
    player_ids = [p["id"] for p in players]

    # Hole 1: Push
    client.post(f"/games/{game_id}/holes/complete", json={
        "hole_number": 1,
        "rotation_order": player_ids,
        "captain_index": 0,
        "final_wager": 1,
        "winner": "push",
        "teams": {"type": "partners", "team1": [player_ids[0], player_ids[1]], "team2": [player_ids[2], player_ids[3]]},
        "scores": {player_ids[0]: 4, player_ids[1]: 4, player_ids[2]: 4, player_ids[3]: 4},
        "hole_par": 4
    })

    # Hole 2: Decided (Team 1 wins with carry-over)
    client.post(f"/games/{game_id}/holes/complete", json={
        "hole_number": 2,
        "rotation_order": player_ids,
        "captain_index": 0,
        "final_wager": 2,
        "winner": "team1",
        "teams": {"type": "partners", "team1": [player_ids[0], player_ids[1]], "team2": [player_ids[2], player_ids[3]]},
        "scores": {player_ids[0]: 4, player_ids[1]: 4, player_ids[2]: 5, player_ids[3]: 5},
        "hole_par": 4,
        "carry_over_applied": True
    })

    # Hole 3: Push again
    client.post(f"/games/{game_id}/holes/complete", json={
        "hole_number": 3,
        "rotation_order": player_ids,
        "captain_index": 0,
        "final_wager": 1,
        "winner": "push",
        "teams": {"type": "partners", "team1": [player_ids[0], player_ids[1]], "team2": [player_ids[2], player_ids[3]]},
        "scores": {player_ids[0]: 4, player_ids[1]: 4, player_ids[2]: 4, player_ids[3]: 4},
        "hole_par": 4
    })

    # Hole 4: Carry-over should work again (hole 2 was decided)
    next_wager = client.get(f"/games/{game_id}/next-hole-wager")
    assert next_wager.status_code == 200
    data = next_wager.json()
    assert data["base_wager"] == 2  # 1Q × 2
    assert data["carry_over"] is True

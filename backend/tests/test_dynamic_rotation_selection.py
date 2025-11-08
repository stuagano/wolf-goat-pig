"""Test Dynamic Rotation Selection - Phase 5, Task 2"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_goat_selects_position_hole_16_5man():
    """Test that Goat can select rotation position on hole 16 in 5-man games"""
    game_response = client.post("/games/create-test?player_count=5")
    game_id = game_response.json()["game_id"]
    players = game_response.json()["players"]
    player_ids = [p["id"] for p in players]

    # Play holes 1-15 to establish Goat (player with lowest points)
    # For simplicity, let's make player_ids[4] the Goat by having them lose consistently
    for hole_num in range(1, 16):
        client.post(f"/games/{game_id}/holes/complete", json={
            "hole_number": hole_num,
            "rotation_order": player_ids,
            "captain_index": 0,
            "teams": {
                "type": "partners",
                "team1": [player_ids[0], player_ids[1]],
                "team2": [player_ids[2], player_ids[3], player_ids[4]]
            },
            "final_wager": 2,
            "winner": "team1",  # Team2 loses (including player_ids[4])
            "scores": {player_ids[0]: 4, player_ids[1]: 4, player_ids[2]: 5, player_ids[3]: 5, player_ids[4]: 5},
            "hole_par": 4
        })

    # Get game state to verify Goat
    game_state = client.get(f"/games/{game_id}").json()

    # Find player with lowest total points
    player_totals = {p["id"]: p["total_points"] for p in game_state["players"]}
    goat_id = min(player_totals, key=player_totals.get)

    # Goat should be on team2 (one of the losing players)
    assert goat_id in [player_ids[2], player_ids[3], player_ids[4]]

    # On hole 16, Goat selects position 3
    response = client.post(f"/games/{game_id}/select-rotation", json={
        "hole_number": 16,
        "goat_player_id": goat_id,
        "selected_position": 3  # Goat wants to be 3rd in rotation
    })

    assert response.status_code == 200
    result = response.json()

    # Verify rotation order updated
    assert "rotation_order" in result
    new_rotation = result["rotation_order"]

    # Goat should be at index 2 (position 3)
    assert new_rotation[2] == goat_id

    # All 5 players should still be in rotation
    assert len(new_rotation) == 5
    assert set(new_rotation) == set(player_ids)


def test_goat_selects_position_hole_17_5man():
    """Test that Goat can select rotation position on hole 17"""
    game_response = client.post("/games/create-test?player_count=5")
    game_id = game_response.json()["game_id"]
    players = game_response.json()["players"]
    player_ids = [p["id"] for p in players]

    # Establish Goat (simplified - just use first player)
    # In real game, would play holes 1-16 first

    response = client.post(f"/games/{game_id}/select-rotation", json={
        "hole_number": 17,
        "goat_player_id": player_ids[0],
        "selected_position": 1
    })

    # Should accept rotation selection on hole 17
    assert response.status_code == 200


def test_goat_selects_position_hole_18_5man():
    """Test that Goat can select rotation position on hole 18"""
    game_response = client.post("/games/create-test?player_count=5")
    game_id = game_response.json()["game_id"]
    players = game_response.json()["players"]
    player_ids = [p["id"] for p in players]

    response = client.post(f"/games/{game_id}/select-rotation", json={
        "hole_number": 18,
        "goat_player_id": player_ids[2],
        "selected_position": 5
    })

    # Should accept rotation selection on hole 18
    assert response.status_code == 200


def test_rotation_selection_only_holes_16_17_18():
    """Test that rotation selection only allowed on holes 16, 17, 18"""
    game_response = client.post("/games/create-test?player_count=5")
    game_id = game_response.json()["game_id"]
    players = game_response.json()["players"]
    player_ids = [p["id"] for p in players]

    # Try on hole 15 (should fail)
    response = client.post(f"/games/{game_id}/select-rotation", json={
        "hole_number": 15,
        "goat_player_id": player_ids[0],
        "selected_position": 1
    })

    assert response.status_code == 400
    assert "16" in response.json()["detail"] or "17" in response.json()["detail"] or "18" in response.json()["detail"]


def test_rotation_selection_only_5man():
    """Test that rotation selection only applies to 5-man games"""
    game_response = client.post("/games/create-test?player_count=4")
    game_id = game_response.json()["game_id"]
    players = game_response.json()["players"]
    player_ids = [p["id"] for p in players]

    # Try rotation selection on 4-man game (should fail)
    response = client.post(f"/games/{game_id}/select-rotation", json={
        "hole_number": 16,
        "goat_player_id": player_ids[0],
        "selected_position": 1
    })

    assert response.status_code == 400
    assert "5" in response.json()["detail"] or "five" in response.json()["detail"].lower()


def test_non_goat_cannot_select_rotation():
    """Test that only the Goat can select rotation"""
    game_response = client.post("/games/create-test?player_count=5")
    game_id = game_response.json()["game_id"]
    players = game_response.json()["players"]
    player_ids = [p["id"] for p in players]

    # Play a few holes to establish clear Goat
    for hole_num in range(1, 4):
        client.post(f"/games/{game_id}/holes/complete", json={
            "hole_number": hole_num,
            "rotation_order": player_ids,
            "captain_index": 0,
            "teams": {
                "type": "partners",
                "team1": [player_ids[0], player_ids[1]],
                "team2": [player_ids[2], player_ids[3], player_ids[4]]
            },
            "final_wager": 2,
            "winner": "team1",
            "scores": {player_ids[0]: 4, player_ids[1]: 4, player_ids[2]: 5, player_ids[3]: 5, player_ids[4]: 5},
            "hole_par": 4
        })

    # Get game state to find Goat
    game_state = client.get(f"/games/{game_id}").json()
    player_totals = {p["id"]: p["total_points"] for p in game_state["players"]}
    goat_id = min(player_totals, key=player_totals.get)

    # Find a non-Goat player
    non_goat_id = max(player_totals, key=player_totals.get)

    assert goat_id != non_goat_id

    # Non-Goat tries to select rotation (should fail)
    response = client.post(f"/games/{game_id}/select-rotation", json={
        "hole_number": 16,
        "goat_player_id": non_goat_id,  # Not the Goat!
        "selected_position": 1
    })

    assert response.status_code == 400
    assert "goat" in response.json()["detail"].lower() or "lowest" in response.json()["detail"].lower()


def test_rotation_selection_invalid_position():
    """Test that invalid positions are rejected"""
    game_response = client.post("/games/create-test?player_count=5")
    game_id = game_response.json()["game_id"]
    players = game_response.json()["players"]
    player_ids = [p["id"] for p in players]

    # Try to select position 6 (invalid for 5-man)
    response = client.post(f"/games/{game_id}/select-rotation", json={
        "hole_number": 16,
        "goat_player_id": player_ids[0],
        "selected_position": 6
    })

    assert response.status_code in [400, 422]  # Either validation error or bad request

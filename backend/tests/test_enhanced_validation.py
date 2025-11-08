"""Test Enhanced Error Handling & Validation - Phase 4, Task 2"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_duplicate_players_on_same_team():
    """Test that duplicate players on the same team are rejected"""
    game_response = client.post("/games/create-test?player_count=4")
    game_id = game_response.json()["game_id"]
    players = game_response.json()["players"]
    player_ids = [p["id"] for p in players]

    # Try to put same player on team twice
    response = client.post(f"/games/{game_id}/holes/complete", json={
        "hole_number": 1,
        "rotation_order": player_ids,
        "captain_index": 0,
        "teams": {"type": "partners", "team1": [player_ids[0], player_ids[0]], "team2": [player_ids[2], player_ids[3]]},
        "final_wager": 2,
        "winner": "team1",
        "scores": {player_ids[0]: 4, player_ids[2]: 5, player_ids[3]: 5},
        "hole_par": 4
    })

    assert response.status_code == 400
    assert "duplicate" in response.json()["detail"].lower()


def test_duplicate_players_on_different_teams():
    """Test that same player on both teams is rejected"""
    game_response = client.post("/games/create-test?player_count=4")
    game_id = game_response.json()["game_id"]
    players = game_response.json()["players"]
    player_ids = [p["id"] for p in players]

    # Try to put same player on both teams
    response = client.post(f"/games/{game_id}/holes/complete", json={
        "hole_number": 1,
        "rotation_order": player_ids,
        "captain_index": 0,
        "teams": {"type": "partners", "team1": [player_ids[0], player_ids[1]], "team2": [player_ids[1], player_ids[3]]},
        "final_wager": 2,
        "winner": "team1",
        "scores": {player_ids[0]: 4, player_ids[1]: 4, player_ids[3]: 5},
        "hole_par": 4
    })

    assert response.status_code == 400
    assert "duplicate" in response.json()["detail"].lower() or "both teams" in response.json()["detail"].lower()


def test_captain_not_in_rotation_order():
    """Test that captain must be in rotation order"""
    game_response = client.post("/games/create-test?player_count=4")
    game_id = game_response.json()["game_id"]
    players = game_response.json()["players"]
    player_ids = [p["id"] for p in players]

    # Captain index 0 should be rotation_order[0]
    response = client.post(f"/games/{game_id}/holes/complete", json={
        "hole_number": 1,
        "rotation_order": player_ids,
        "captain_index": 0,
        "teams": {"type": "solo", "captain": player_ids[1], "opponents": [player_ids[0], player_ids[2], player_ids[3]]},
        "final_wager": 2,
        "winner": "captain",
        "scores": {player_ids[0]: 5, player_ids[1]: 4, player_ids[2]: 5, player_ids[3]: 6},
        "hole_par": 4
    })

    assert response.status_code == 400
    assert "captain" in response.json()["detail"].lower()


def test_negative_score_rejected():
    """Test that negative scores are rejected"""
    game_response = client.post("/games/create-test?player_count=4")
    game_id = game_response.json()["game_id"]
    players = game_response.json()["players"]
    player_ids = [p["id"] for p in players]

    # Try to submit negative score
    response = client.post(f"/games/{game_id}/holes/complete", json={
        "hole_number": 1,
        "rotation_order": player_ids,
        "captain_index": 0,
        "teams": {"type": "partners", "team1": [player_ids[0], player_ids[1]], "team2": [player_ids[2], player_ids[3]]},
        "final_wager": 2,
        "winner": "team1",
        "scores": {player_ids[0]: -1, player_ids[1]: 4, player_ids[2]: 5, player_ids[3]: 5},
        "hole_par": 4
    })

    assert response.status_code == 400
    assert "score" in response.json()["detail"].lower() or "negative" in response.json()["detail"].lower()


def test_unreasonably_high_score_rejected():
    """Test that unreasonably high scores are rejected (e.g., > 15)"""
    game_response = client.post("/games/create-test?player_count=4")
    game_id = game_response.json()["game_id"]
    players = game_response.json()["players"]
    player_ids = [p["id"] for p in players]

    # Try to submit score > 15 (unrealistic)
    response = client.post(f"/games/{game_id}/holes/complete", json={
        "hole_number": 1,
        "rotation_order": player_ids,
        "captain_index": 0,
        "teams": {"type": "partners", "team1": [player_ids[0], player_ids[1]], "team2": [player_ids[2], player_ids[3]]},
        "final_wager": 2,
        "winner": "team1",
        "scores": {player_ids[0]: 4, player_ids[1]: 4, player_ids[2]: 25, player_ids[3]: 5},
        "hole_par": 4
    })

    assert response.status_code == 400
    assert "score" in response.json()["detail"].lower()


def test_missing_player_in_scores():
    """Test that all players must have scores"""
    game_response = client.post("/games/create-test?player_count=4")
    game_id = game_response.json()["game_id"]
    players = game_response.json()["players"]
    player_ids = [p["id"] for p in players]

    # Missing one player's score
    response = client.post(f"/games/{game_id}/holes/complete", json={
        "hole_number": 1,
        "rotation_order": player_ids,
        "captain_index": 0,
        "teams": {"type": "partners", "team1": [player_ids[0], player_ids[1]], "team2": [player_ids[2], player_ids[3]]},
        "final_wager": 2,
        "winner": "team1",
        "scores": {player_ids[0]: 4, player_ids[1]: 4, player_ids[2]: 5},  # missing player_ids[3]
        "hole_par": 4
    })

    assert response.status_code == 400
    assert "score" in response.json()["detail"].lower() or "missing" in response.json()["detail"].lower()


def test_extra_player_in_scores():
    """Test that scores cannot include players not in rotation"""
    game_response = client.post("/games/create-test?player_count=4")
    game_id = game_response.json()["game_id"]
    players = game_response.json()["players"]
    player_ids = [p["id"] for p in players]

    # Extra player ID not in rotation
    fake_player_id = "fake-player-999"
    response = client.post(f"/games/{game_id}/holes/complete", json={
        "hole_number": 1,
        "rotation_order": player_ids,
        "captain_index": 0,
        "teams": {"type": "partners", "team1": [player_ids[0], player_ids[1]], "team2": [player_ids[2], player_ids[3]]},
        "final_wager": 2,
        "winner": "team1",
        "scores": {player_ids[0]: 4, player_ids[1]: 4, player_ids[2]: 5, player_ids[3]: 5, fake_player_id: 6},
        "hole_par": 4
    })

    assert response.status_code == 400
    assert "score" in response.json()["detail"].lower() or "rotation" in response.json()["detail"].lower()


def test_invalid_team_formation_solo_wrong_count():
    """Test that solo must be 1 vs N-1"""
    game_response = client.post("/games/create-test?player_count=4")
    game_id = game_response.json()["game_id"]
    players = game_response.json()["players"]
    player_ids = [p["id"] for p in players]

    # Solo with 2 captains (invalid)
    response = client.post(f"/games/{game_id}/holes/complete", json={
        "hole_number": 1,
        "rotation_order": player_ids,
        "captain_index": 0,
        "teams": {"type": "solo", "captain": player_ids[0], "opponents": [player_ids[2], player_ids[3]]},  # Missing 1 opponent
        "final_wager": 2,
        "winner": "captain",
        "scores": {player_ids[0]: 4, player_ids[2]: 5, player_ids[3]: 6},
        "hole_par": 4
    })

    assert response.status_code == 400
    assert "team" in response.json()["detail"].lower() or "opponent" in response.json()["detail"].lower()


def test_zero_or_negative_wager():
    """Test that wager must be positive"""
    game_response = client.post("/games/create-test?player_count=4")
    game_id = game_response.json()["game_id"]
    players = game_response.json()["players"]
    player_ids = [p["id"] for p in players]

    # Zero wager
    response = client.post(f"/games/{game_id}/holes/complete", json={
        "hole_number": 1,
        "rotation_order": player_ids,
        "captain_index": 0,
        "teams": {"type": "partners", "team1": [player_ids[0], player_ids[1]], "team2": [player_ids[2], player_ids[3]]},
        "final_wager": 0,
        "winner": "team1",
        "scores": {player_ids[0]: 4, player_ids[1]: 4, player_ids[2]: 5, player_ids[3]: 5},
        "hole_par": 4
    })

    # Accept either 400 (custom validation) or 422 (Pydantic validation)
    assert response.status_code in [400, 422]
    # Pydantic returns structured error detail, custom validation returns string
    detail = response.json()["detail"]
    if isinstance(detail, str):
        assert "wager" in detail.lower()
    # If Pydantic validation, it's validated (422 is correct for request validation)


def test_invalid_hole_number():
    """Test that hole number must be 1-18"""
    game_response = client.post("/games/create-test?player_count=4")
    game_id = game_response.json()["game_id"]
    players = game_response.json()["players"]
    player_ids = [p["id"] for p in players]

    # Hole 0 (invalid)
    response = client.post(f"/games/{game_id}/holes/complete", json={
        "hole_number": 0,
        "rotation_order": player_ids,
        "captain_index": 0,
        "teams": {"type": "partners", "team1": [player_ids[0], player_ids[1]], "team2": [player_ids[2], player_ids[3]]},
        "final_wager": 2,
        "winner": "team1",
        "scores": {player_ids[0]: 4, player_ids[1]: 4, player_ids[2]: 5, player_ids[3]: 5},
        "hole_par": 4
    })

    # Accept either 400 (custom validation) or 422 (Pydantic validation)
    assert response.status_code in [400, 422]
    detail = response.json()["detail"]
    if isinstance(detail, str):
        assert "hole" in detail.lower()
    # If Pydantic validation, it's validated (422 is correct)

    # Hole 19 (invalid)
    response = client.post(f"/games/{game_id}/holes/complete", json={
        "hole_number": 19,
        "rotation_order": player_ids,
        "captain_index": 0,
        "teams": {"type": "partners", "team1": [player_ids[0], player_ids[1]], "team2": [player_ids[2], player_ids[3]]},
        "final_wager": 2,
        "winner": "team1",
        "scores": {player_ids[0]: 4, player_ids[1]: 4, player_ids[2]: 5, player_ids[3]: 5},
        "hole_par": 4
    })

    # Accept either 400 (custom validation) or 422 (Pydantic validation)
    assert response.status_code in [400, 422]
    detail = response.json()["detail"]
    if isinstance(detail, str):
        assert "hole" in detail.lower()
    # If Pydantic validation, it's validated (422 is correct)


def test_all_players_accounted_for_in_teams():
    """Test that all rotation players must be on a team"""
    game_response = client.post("/games/create-test?player_count=4")
    game_id = game_response.json()["game_id"]
    players = game_response.json()["players"]
    player_ids = [p["id"] for p in players]

    # Only 3 players in teams (missing 1)
    response = client.post(f"/games/{game_id}/holes/complete", json={
        "hole_number": 1,
        "rotation_order": player_ids,
        "captain_index": 0,
        "teams": {"type": "partners", "team1": [player_ids[0], player_ids[1]], "team2": [player_ids[2]]},  # Missing player_ids[3]
        "final_wager": 2,
        "winner": "team1",
        "scores": {player_ids[0]: 4, player_ids[1]: 4, player_ids[2]: 5, player_ids[3]: 5},
        "hole_par": 4
    })

    assert response.status_code == 400
    assert "team" in response.json()["detail"].lower() or "player" in response.json()["detail"].lower()

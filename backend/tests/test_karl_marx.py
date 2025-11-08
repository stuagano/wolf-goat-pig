"""Test Karl Marx Rule - uneven distribution favors player furthest down"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_karl_marx_5man_uneven_loss():
    """Test Karl Marx rule in 5-man game - losing team owes uneven amount"""
    # Create 5-player game
    game_response = client.post("/games/create-test?player_count=5")
    game_id = game_response.json()["game_id"]
    players = game_response.json()["players"]
    player_ids = [p["id"] for p in players]

    # Simulate a few holes to establish standings
    # Hole 1: p1 & p2 win, p3 & p4 & p5 lose (3v2)
    client.post(f"/games/{game_id}/holes/complete", json={
        "hole_number": 1,
        "rotation_order": player_ids,
        "captain_index": 0,
        "teams": {"type": "partners", "team1": [player_ids[0], player_ids[1]], "team2": [player_ids[2], player_ids[3], player_ids[4]]},
        "final_wager": 2,
        "winner": "team1",
        "scores": {player_ids[0]: 4, player_ids[1]: 4, player_ids[2]: 5, player_ids[3]: 6, player_ids[4]: 6},
        "hole_par": 4
    })

    # Get current standings to verify Goat
    state_response = client.get(f"/games/{game_id}/state")
    game_state = state_response.json()

    players_state = game_state.get("players", [])
    # Find p3 and p4 in the players state
    p3_state = next(p for p in players_state if p["id"] == player_ids[2])
    p4_state = next(p for p in players_state if p["id"] == player_ids[3])
    p5_state = next(p for p in players_state if p["id"] == player_ids[4])

    # After hole 1:
    # - Team1 wins: p1 and p2 each get 2Q = 4Q total
    # - Team2 loses: p3, p4, p5 owe 4Q total
    # - With Karl Marx: 4Q / 3 players = 1.33Q average
    # - Two players lose 1Q, one loses 2Q
    # - The player furthest down (Goat) should lose the LEAST (1Q)

    # Since all three players on team2 start tied at 0, they're all equally "furthest down"
    # So we need another hole to create a Goat

    # Hole 2: Make p3 go further down
    client.post(f"/games/{game_id}/holes/complete", json={
        "hole_number": 2,
        "rotation_order": player_ids[1:] + [player_ids[0]],
        "captain_index": 0,
        "teams": {"type": "solo", "captain": player_ids[2], "opponents": [player_ids[1], player_ids[0], player_ids[3], player_ids[4]]},
        "final_wager": 1,
        "winner": "opponents",
        "scores": {player_ids[2]: 8, player_ids[1]: 4, player_ids[0]: 4, player_ids[3]: 5, player_ids[4]: 5},
        "hole_par": 4
    })

    # Now p3 is further down: -2Q (from hole 1) - 4Q (from hole 2 solo loss) = -6Q
    # p4 and p5 are at: -2Q each

    # Hole 3: 2v3 teams, with p3 & p4 on losing team
    # This will trigger Karl Marx: p3 (Goat at -6Q) should lose less than p4 (at -2Q)
    response = client.post(f"/games/{game_id}/holes/complete", json={
        "hole_number": 3,
        "rotation_order": player_ids[2:] + player_ids[:2],
        "captain_index": 0,
        "teams": {"type": "partners", "team1": [player_ids[2], player_ids[3]], "team2": [player_ids[4], player_ids[0], player_ids[1]]},
        "final_wager": 1,
        "winner": "team2",
        "scores": {player_ids[2]: 6, player_ids[3]: 6, player_ids[4]: 4, player_ids[0]: 4, player_ids[1]: 4},
        "hole_par": 4
    })

    assert response.status_code == 200
    result = response.json()["hole_result"]

    # Team2 wins: 3 players win 1Q each = 3Q total
    # Team1 loses: 2 players owe 3Q total
    # With Karl Marx: p3 (Goat) should lose 1Q, p4 should lose 2Q
    assert result["points_delta"][player_ids[2]] == -1  # p3 (Goat) loses less
    assert result["points_delta"][player_ids[3]] == -2  # p4 loses more


def test_karl_marx_5man_uneven_win():
    """Test Karl Marx rule in 5-man game - winning team receives uneven amount"""
    # Create 5-player game
    game_response = client.post("/games/create-test?player_count=5")
    game_id = game_response.json()["game_id"]
    players = game_response.json()["players"]
    player_ids = [p["id"] for p in players]

    # Simulate holes to establish p1 as Goat
    # Hole 1: p1 goes solo and loses
    client.post(f"/games/{game_id}/holes/complete", json={
        "hole_number": 1,
        "rotation_order": player_ids,
        "captain_index": 0,
        "teams": {"type": "solo", "captain": player_ids[0], "opponents": [player_ids[1], player_ids[2], player_ids[3], player_ids[4]]},
        "final_wager": 2,
        "winner": "opponents",
        "scores": {player_ids[0]: 8, player_ids[1]: 4, player_ids[2]: 4, player_ids[3]: 5, player_ids[4]: 5},
        "hole_par": 4
    })

    # Now p1 is Goat at -8Q, others are at +2Q each

    # Hole 2: p1 & p2 win on 2v3 team (uneven split)
    response = client.post(f"/games/{game_id}/holes/complete", json={
        "hole_number": 2,
        "rotation_order": player_ids[1:] + [player_ids[0]],
        "captain_index": 0,
        "teams": {"type": "partners", "team1": [player_ids[0], player_ids[1]], "team2": [player_ids[2], player_ids[3], player_ids[4]]},
        "final_wager": 1,
        "winner": "team1",
        "scores": {player_ids[0]: 4, player_ids[1]: 4, player_ids[2]: 5, player_ids[3]: 6, player_ids[4]: 6},
        "hole_par": 4
    })

    assert response.status_code == 200
    result = response.json()["hole_result"]

    # Team1 wins: 2 players win 3Q total (team2 has 3 players at 1Q each)
    # With Karl Marx: p1 (Goat) should win MORE (2Q), p2 should win less (1Q)
    assert result["points_delta"][player_ids[0]] == 2  # p1 (Goat) wins more
    assert result["points_delta"][player_ids[1]] == 1  # p2 wins less


def test_karl_marx_hanging_chad():
    """Test hanging chad - wait for tied players to diverge"""
    # Create 5-player game
    game_response = client.post("/games/create-test?player_count=5")
    game_id = game_response.json()["game_id"]
    players = game_response.json()["players"]
    player_ids = [p["id"] for p in players]

    # Hole 1: 2v3 with p1 & p2 on team1 (both start at 0 = tied)
    response = client.post(f"/games/{game_id}/holes/complete", json={
        "hole_number": 1,
        "rotation_order": player_ids,
        "captain_index": 0,
        "teams": {"type": "partners", "team1": [player_ids[0], player_ids[1]], "team2": [player_ids[2], player_ids[3], player_ids[4]]},
        "final_wager": 1,
        "winner": "team2",
        "scores": {player_ids[0]: 5, player_ids[1]: 5, player_ids[2]: 4, player_ids[3]: 4, player_ids[4]: 4},
        "hole_par": 4
    })

    assert response.status_code == 200
    result = response.json()["hole_result"]

    # p1 and p2 are tied at 0 before this hole
    # They owe 3Q total between them (1.5Q each on average)
    # Since tied, "hanging chad" - temporarily distribute evenly or mark for future resolution
    # For simplicity, we could distribute evenly and mark as "hanging_chad": true
    # When their scores diverge, we retroactively adjust

    # For this test, we'll just verify that the split was done (implementation can be deferred)
    total_loss = result["points_delta"][player_ids[0]] + result["points_delta"][player_ids[1]]
    assert total_loss == -3  # Combined loss is correct


def test_karl_marx_not_applied_in_4man():
    """Test Karl Marx rule does NOT apply in 4-man partners (even splits)"""
    game_response = client.post("/games/create-test?player_count=4")
    game_id = game_response.json()["game_id"]
    players = game_response.json()["players"]
    player_ids = [p["id"] for p in players]

    # Make p1 the Goat
    client.post(f"/games/{game_id}/holes/complete", json={
        "hole_number": 1,
        "rotation_order": player_ids,
        "captain_index": 0,
        "teams": {"type": "solo", "captain": player_ids[0], "opponents": [player_ids[1], player_ids[2], player_ids[3]]},
        "final_wager": 2,
        "winner": "opponents",
        "scores": {player_ids[0]: 8, player_ids[1]: 4, player_ids[2]: 4, player_ids[3]: 4},
        "hole_par": 4
    })

    # Now p1 is Goat at -6Q

    # Hole 2: p1 & p2 partners (2v2)
    response = client.post(f"/games/{game_id}/holes/complete", json={
        "hole_number": 2,
        "rotation_order": player_ids[1:] + [player_ids[0]],
        "captain_index": 0,
        "teams": {"type": "partners", "team1": [player_ids[0], player_ids[1]], "team2": [player_ids[2], player_ids[3]]},
        "final_wager": 2,
        "winner": "team2",
        "scores": {player_ids[0]: 5, player_ids[1]: 5, player_ids[2]: 4, player_ids[3]: 4},
        "hole_par": 4
    })

    assert response.status_code == 200
    result = response.json()["hole_result"]

    # In 4-man partners, split is ALWAYS even (no Karl Marx needed)
    # Each loser loses exactly 2Q
    assert result["points_delta"][player_ids[0]] == -2  # Even split
    assert result["points_delta"][player_ids[1]] == -2  # Even split

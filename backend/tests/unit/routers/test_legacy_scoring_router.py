"""Unit tests for legacy scoring router — simplified in-memory game scoring."""

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

PLAYERS = [
    {"id": "p1", "name": "Alice"},
    {"id": "p2", "name": "Bob"},
    {"id": "p3", "name": "Charlie"},
    {"id": "p4", "name": "Dana"},
]


# ── Helpers ──────────────────────────────────────────────────────────────────


def _start_game(**overrides):
    """Start a simplified game and return the response."""
    payload = {"players": PLAYERS}
    payload.update(overrides)
    return client.post("/wgp/simplified/start-game", json=payload)


def _start_and_get_id(**overrides):
    """Start a game and return its game_id."""
    resp = _start_game(**overrides)
    return resp.json()["game_id"]


# =============================================================================
# START GAME
# =============================================================================


class TestStartSimplifiedGame:
    def test_returns_200(self):
        resp = _start_game()
        assert resp.status_code == 200

    def test_returns_success_true(self):
        resp = _start_game()
        assert resp.json()["success"] is True

    def test_returns_game_id(self):
        resp = _start_game()
        data = resp.json()
        assert "game_id" in data
        assert isinstance(data["game_id"], str)
        assert len(data["game_id"]) > 0

    def test_returns_player_data(self):
        resp = _start_game()
        data = resp.json()
        assert "players" in data

    def test_custom_game_id(self):
        resp = _start_game(game_id="custom-123")
        data = resp.json()
        assert data["game_id"] == "custom-123"

    def test_returns_message_with_player_count(self):
        resp = _start_game()
        data = resp.json()
        assert "message" in data
        assert "4 players" in data["message"]

    def test_returns_400_without_players(self):
        """Empty players list returns 400."""
        resp = client.post("/wgp/simplified/start-game", json={"players": []})
        assert resp.status_code == 400

    def test_returns_400_with_empty_payload(self):
        """Missing players key defaults to empty list, returns 400."""
        resp = client.post("/wgp/simplified/start-game", json={})
        assert resp.status_code == 400

    def test_error_detail_mentions_players(self):
        resp = client.post("/wgp/simplified/start-game", json={"players": []})
        data = resp.json()
        assert "detail" in data
        assert "Players required" in data["detail"] or "Failed to start" in data["detail"]


# =============================================================================
# SCORE HOLE
# =============================================================================


class TestScoreHoleSimplified:
    def test_returns_200_for_valid_score(self):
        game_id = _start_and_get_id()
        resp = client.post(
            "/wgp/simplified/score-hole",
            json={
                "game_id": game_id,
                "hole_number": 1,
                "scores": {"p1": 4, "p2": 5, "p3": 3, "p4": 6},
                "teams": {
                    "type": "partners",
                    "team1": ["p1", "p2"],
                    "team2": ["p3", "p4"],
                },
                "wager": 1,
            },
        )
        assert resp.status_code == 200

    def test_returns_success_true(self):
        game_id = _start_and_get_id()
        resp = client.post(
            "/wgp/simplified/score-hole",
            json={
                "game_id": game_id,
                "hole_number": 1,
                "scores": {"p1": 4, "p2": 5, "p3": 3, "p4": 6},
                "teams": {
                    "type": "partners",
                    "team1": ["p1", "p2"],
                    "team2": ["p3", "p4"],
                },
            },
        )
        assert resp.json()["success"] is True

    def test_returns_hole_result_and_summary(self):
        game_id = _start_and_get_id()
        resp = client.post(
            "/wgp/simplified/score-hole",
            json={
                "game_id": game_id,
                "hole_number": 1,
                "scores": {"p1": 4, "p2": 5, "p3": 3, "p4": 6},
                "teams": {
                    "type": "partners",
                    "team1": ["p1", "p2"],
                    "team2": ["p3", "p4"],
                },
            },
        )
        data = resp.json()
        assert "hole_result" in data
        assert "game_summary" in data

    def test_returns_404_for_nonexistent_game(self):
        resp = client.post(
            "/wgp/simplified/score-hole",
            json={
                "game_id": "does-not-exist",
                "hole_number": 1,
                "scores": {"p1": 4},
                "teams": {"type": "solo", "solo_player": "p1"},
            },
        )
        assert resp.status_code == 404

    def test_returns_404_without_game_id(self):
        resp = client.post(
            "/wgp/simplified/score-hole",
            json={
                "hole_number": 1,
                "scores": {"p1": 4},
                "teams": {"type": "solo"},
            },
        )
        assert resp.status_code == 404

    def test_returns_400_without_hole_number(self):
        game_id = _start_and_get_id()
        resp = client.post(
            "/wgp/simplified/score-hole",
            json={
                "game_id": game_id,
                "scores": {"p1": 4, "p2": 5, "p3": 3, "p4": 6},
                "teams": {
                    "type": "partners",
                    "team1": ["p1", "p2"],
                    "team2": ["p3", "p4"],
                },
            },
        )
        assert resp.status_code == 400

    def test_returns_400_without_scores(self):
        game_id = _start_and_get_id()
        resp = client.post(
            "/wgp/simplified/score-hole",
            json={
                "game_id": game_id,
                "hole_number": 1,
                "teams": {"type": "partners", "team1": ["p1"], "team2": ["p2"]},
            },
        )
        assert resp.status_code == 400

    def test_solo_scoring(self):
        game_id = _start_and_get_id()
        resp = client.post(
            "/wgp/simplified/score-hole",
            json={
                "game_id": game_id,
                "hole_number": 1,
                "scores": {"p1": 3, "p2": 5, "p3": 4, "p4": 6},
                "teams": {"type": "solo", "solo_player": "p1"},
                "wager": 2,
            },
        )
        assert resp.status_code == 200
        assert resp.json()["success"] is True


# =============================================================================
# GAME STATUS
# =============================================================================


class TestGetSimplifiedGameStatus:
    def test_returns_200_for_existing_game(self):
        game_id = _start_and_get_id()
        resp = client.get(f"/wgp/simplified/{game_id}/status")
        assert resp.status_code == 200

    def test_returns_game_id(self):
        game_id = _start_and_get_id()
        resp = client.get(f"/wgp/simplified/{game_id}/status")
        data = resp.json()
        assert data["game_id"] == game_id

    def test_returns_game_summary(self):
        game_id = _start_and_get_id()
        resp = client.get(f"/wgp/simplified/{game_id}/status")
        data = resp.json()
        assert "game_summary" in data

    def test_returns_hole_history(self):
        game_id = _start_and_get_id()
        resp = client.get(f"/wgp/simplified/{game_id}/status")
        data = resp.json()
        assert "hole_history" in data
        assert isinstance(data["hole_history"], list)

    def test_returns_404_for_nonexistent_game(self):
        resp = client.get("/wgp/simplified/nonexistent-game/status")
        assert resp.status_code == 404

    def test_status_reflects_scored_holes(self):
        game_id = _start_and_get_id()
        # Score a hole
        client.post(
            "/wgp/simplified/score-hole",
            json={
                "game_id": game_id,
                "hole_number": 1,
                "scores": {"p1": 4, "p2": 5, "p3": 3, "p4": 6},
                "teams": {
                    "type": "partners",
                    "team1": ["p1", "p2"],
                    "team2": ["p3", "p4"],
                },
            },
        )
        resp = client.get(f"/wgp/simplified/{game_id}/status")
        data = resp.json()
        assert data["game_summary"]["holes_played"] == 1


# =============================================================================
# HOLE HISTORY
# =============================================================================


class TestGetSimplifiedHoleHistory:
    def test_returns_200_for_existing_game(self):
        game_id = _start_and_get_id()
        resp = client.get(f"/wgp/simplified/{game_id}/hole-history")
        assert resp.status_code == 200

    def test_returns_game_id(self):
        game_id = _start_and_get_id()
        resp = client.get(f"/wgp/simplified/{game_id}/hole-history")
        data = resp.json()
        assert data["game_id"] == game_id

    def test_returns_empty_history_for_new_game(self):
        game_id = _start_and_get_id()
        resp = client.get(f"/wgp/simplified/{game_id}/hole-history")
        data = resp.json()
        assert data["hole_history"] == []

    def test_returns_404_for_nonexistent_game(self):
        resp = client.get("/wgp/simplified/nonexistent-game/hole-history")
        assert resp.status_code == 404

    def test_history_contains_scored_holes(self):
        game_id = _start_and_get_id()
        # Score two holes
        for hole in [1, 2]:
            client.post(
                "/wgp/simplified/score-hole",
                json={
                    "game_id": game_id,
                    "hole_number": hole,
                    "scores": {"p1": 4, "p2": 5, "p3": 3, "p4": 6},
                    "teams": {
                        "type": "partners",
                        "team1": ["p1", "p2"],
                        "team2": ["p3", "p4"],
                    },
                },
            )
        resp = client.get(f"/wgp/simplified/{game_id}/hole-history")
        data = resp.json()
        assert len(data["hole_history"]) == 2
        assert data["hole_history"][0]["hole"] == 1
        assert data["hole_history"][1]["hole"] == 2

    def test_history_entry_has_expected_keys(self):
        game_id = _start_and_get_id()
        client.post(
            "/wgp/simplified/score-hole",
            json={
                "game_id": game_id,
                "hole_number": 1,
                "scores": {"p1": 4, "p2": 5, "p3": 3, "p4": 6},
                "teams": {
                    "type": "partners",
                    "team1": ["p1", "p2"],
                    "team2": ["p3", "p4"],
                },
            },
        )
        resp = client.get(f"/wgp/simplified/{game_id}/hole-history")
        entry = resp.json()["hole_history"][0]
        assert "hole" in entry
        assert "scores" in entry
        assert "team_type" in entry
        assert "wager" in entry
        assert "winners" in entry
        assert "points_awarded" in entry

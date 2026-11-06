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

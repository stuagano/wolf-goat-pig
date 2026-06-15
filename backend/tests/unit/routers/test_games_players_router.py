"""Unit tests for games_players router — create-test, update name, remove player, update handicap."""

import uuid

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _unique_id():
    return uuid.uuid4().hex[:8]


# ── Helper: create a test game via the API ──────────────────────────────────


def _create_test_game(player_count=4, course_name=None):
    """Create a test game with mock players and return the JSON response."""
    params = {"player_count": player_count}
    if course_name:
        params["course_name"] = course_name
    resp = client.post("/games/create-test", params=params)
    return resp


def _create_setup_game():
    """Create a game in 'setup' status with a couple of players joined."""
    resp = client.post("/games/create", params={"player_count": 4})
    game = resp.json()
    join_code = game["join_code"]

    p1 = client.post(
        f"/games/join/{join_code}",
        json={"player_name": f"Alice-{_unique_id()}", "handicap": 12.0},
    ).json()
    p2 = client.post(
        f"/games/join/{join_code}",
        json={"player_name": f"Bob-{_unique_id()}", "handicap": 18.0},
    ).json()

    return game, p1, p2


# ── POST /games/create-test ────────────────────────────────────────────────


class TestCreateTestGame:
    def test_create_test_game_returns_200(self):
        resp = _create_test_game()
        assert resp.status_code == 200

    def test_create_test_game_response_shape(self):
        resp = _create_test_game()
        data = resp.json()
        assert "game_id" in data
        assert "join_code" in data
        assert data["status"] == "in_progress"
        assert data["test_mode"] is True
        assert data["player_count"] == 4

    def test_create_test_game_default_four_players(self):
        resp = _create_test_game(player_count=4)
        data = resp.json()
        assert len(data["players"]) == 4
        assert data["player_count"] == 4

    def test_create_test_game_five_players(self):
        resp = _create_test_game(player_count=5)
        data = resp.json()
        assert len(data["players"]) == 5
        assert data["player_count"] == 5

    def test_create_test_game_six_players(self):
        resp = _create_test_game(player_count=6)
        data = resp.json()
        assert len(data["players"]) == 6
        assert data["player_count"] == 6

    def test_create_test_game_unsupported_player_count_raises(self):
        # WolfGoatPigGame only supports 4-6 players; fewer causes a ValueError
        with pytest.raises(ValueError, match="4, 5, or 6 players only"):
            _create_test_game(player_count=2)

    def test_create_test_game_players_have_expected_fields(self):
        resp = _create_test_game()
        data = resp.json()
        player = data["players"][0]
        assert "id" in player
        assert "name" in player
        assert "handicap" in player

    def test_create_test_game_persistence_field(self):
        resp = _create_test_game()
        data = resp.json()
        # Should be either "database" or "memory" depending on DB availability
        assert "persistence" in data

    def test_create_test_game_has_created_at(self):
        resp = _create_test_game()
        data = resp.json()
        assert "created_at" in data

    def test_create_test_game_unique_game_ids(self):
        resp1 = _create_test_game()
        resp2 = _create_test_game()
        assert resp1.json()["game_id"] != resp2.json()["game_id"]

    def test_create_test_game_message_field(self):
        resp = _create_test_game()
        data = resp.json()
        assert "message" in data


# ── PATCH /games/{game_id}/players/{player_id}/name ─────────────────────────


class TestUpdatePlayerName:
    def test_update_name_in_test_game(self):
        game = _create_test_game().json()
        game_id = game["game_id"]
        player_id = game["players"][0]["id"]
        resp = client.patch(
            f"/games/{game_id}/players/{player_id}/name",
            json={"name": "New Name"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["name"] == "New Name"

    def test_update_name_response_shape(self):
        game = _create_test_game().json()
        game_id = game["game_id"]
        player_id = game["players"][0]["id"]
        resp = client.patch(
            f"/games/{game_id}/players/{player_id}/name",
            json={"name": "Updated"},
        )
        data = resp.json()
        assert data["game_id"] == game_id
        assert data["player_id"] == player_id
        assert data["success"] is True
        assert data["name"] == "Updated"

    def test_update_name_empty_name_returns_422(self):
        # Empty string fails Pydantic min-length validation before the handler
        game = _create_test_game().json()
        game_id = game["game_id"]
        player_id = game["players"][0]["id"]
        resp = client.patch(
            f"/games/{game_id}/players/{player_id}/name",
            json={"name": ""},
        )
        assert resp.status_code == 422

    def test_update_name_whitespace_only_returns_422(self):
        # Whitespace passes min_length but strips to blank → AfterValidator raises → 422
        game = _create_test_game().json()
        game_id = game["game_id"]
        player_id = game["players"][0]["id"]
        resp = client.patch(
            f"/games/{game_id}/players/{player_id}/name",
            json={"name": "   "},
        )
        assert resp.status_code == 422

    def test_update_name_missing_name_field_returns_422(self):
        # Missing required field is a Pydantic validation error
        game = _create_test_game().json()
        game_id = game["game_id"]
        player_id = game["players"][0]["id"]
        resp = client.patch(
            f"/games/{game_id}/players/{player_id}/name",
            json={},
        )
        assert resp.status_code == 422

    def test_update_name_nonexistent_player_returns_404(self):
        game = _create_test_game().json()
        game_id = game["game_id"]
        resp = client.patch(
            f"/games/{game_id}/players/nonexistent-player/name",
            json={"name": "Ghost"},
        )
        assert resp.status_code == 404

    def test_update_name_strips_whitespace(self):
        game = _create_test_game().json()
        game_id = game["game_id"]
        player_id = game["players"][0]["id"]
        resp = client.patch(
            f"/games/{game_id}/players/{player_id}/name",
            json={"name": "  Trimmed Name  "},
        )
        data = resp.json()
        assert data["name"] == "Trimmed Name"

    def test_update_name_persists(self):
        """Read-back: the new name is visible via GET /state, not just echoed
        in the PATCH response."""
        game = _create_test_game().json()
        game_id = game["game_id"]
        player_id = game["players"][0]["id"]
        client.patch(f"/games/{game_id}/players/{player_id}/name", json={"name": "Persisted Name"})
        state = client.get(f"/games/{game_id}/state").json()
        names = {p["id"]: p["name"] for p in state.get("players", [])}
        assert names.get(player_id) == "Persisted Name"

    def test_update_name_persists_ctk(self):
        """Same read-back as above, expressed with claude-test-kit's
        `claim_vs_reality` — the explicit guard against the silent-persistence
        bug: a PATCH that returns 200 but never actually writes (the class of
        bug the flag_modified / MutableDict fixes addressed).

        Demonstrates the vendored `.ctk/` kit wired in via pyproject's
        `pythonpath`. The verifier re-reads GET /state and raises if the
        claimed-successful write didn't reach durable state.
        """
        from ctk import claim_vs_reality

        game = _create_test_game().json()
        game_id = game["game_id"]
        player_id = game["players"][0]["id"]

        resp = client.patch(f"/games/{game_id}/players/{player_id}/name", json={"name": "CTK Persisted"})

        def reality_is_persisted():
            state = client.get(f"/games/{game_id}/state").json()
            names = {p["id"]: p["name"] for p in state.get("players", [])}
            assert names.get(player_id) == "CTK Persisted", (
                f"GET /state shows {names.get(player_id)!r}, not the patched name — "
                "the PATCH reported success but did not persist"
            )

        claim_vs_reality(
            claimed_success=(resp.status_code == 200),
            verifier=reality_is_persisted,
            claim_label="update player name",
        )


# ── DELETE /games/{game_id}/players/{player_slot_id} ────────────────────────


class TestRemovePlayer:
    def test_remove_nonexistent_game_returns_404(self):
        resp = client.delete("/games/nonexistent-id/players/p1")
        assert resp.status_code == 404

    def test_remove_player_succeeds(self):
        """Remove a player from a game."""
        game, p1, _p2 = _create_setup_game()
        resp = client.delete(
            f"/games/{game['game_id']}/players/{p1['player_slot_id']}",
        )
        assert resp.status_code == 200

    def test_remove_player_persists(self):
        """Read-back: the removed player is actually gone from GET /state."""
        game, p1, _p2 = _create_setup_game()
        game_id = game["game_id"]
        slot = p1["player_slot_id"]
        client.delete(f"/games/{game_id}/players/{slot}")
        state = client.get(f"/games/{game_id}/state").json()
        ids = [p["id"] for p in state.get("players", [])]
        assert slot not in ids

    def test_remove_nonexistent_player_returns_404(self):
        """Removing a nonexistent player slot returns 404."""
        game, _p1, _p2 = _create_setup_game()
        resp = client.delete(
            f"/games/{game['game_id']}/players/nonexistent-slot",
        )
        assert resp.status_code == 404


# ── PATCH /games/{game_id}/players/{player_slot_id}/handicap ────────────────


class TestUpdatePlayerHandicap:
    def test_update_handicap_missing_value_returns_400(self):
        game, p1, _p2 = _create_setup_game()
        resp = client.patch(
            f"/games/{game['game_id']}/players/{p1['player_slot_id']}/handicap",
            json={},
        )
        assert resp.status_code == 400

    def test_update_handicap_invalid_value_returns_400(self):
        game, p1, _p2 = _create_setup_game()
        resp = client.patch(
            f"/games/{game['game_id']}/players/{p1['player_slot_id']}/handicap",
            json={"handicap": "not-a-number"},
        )
        assert resp.status_code == 400

    def test_update_handicap_negative_returns_400(self):
        game, p1, _p2 = _create_setup_game()
        resp = client.patch(
            f"/games/{game['game_id']}/players/{p1['player_slot_id']}/handicap",
            json={"handicap": -1.0},
        )
        assert resp.status_code == 400

    def test_update_handicap_over_54_returns_400(self):
        game, p1, _p2 = _create_setup_game()
        resp = client.patch(
            f"/games/{game['game_id']}/players/{p1['player_slot_id']}/handicap",
            json={"handicap": 55.0},
        )
        assert resp.status_code == 400

    def test_update_handicap_nonexistent_game_returns_404(self):
        resp = client.patch(
            "/games/nonexistent-id/players/p1/handicap",
            json={"handicap": 10.0},
        )
        assert resp.status_code == 404

    def test_update_handicap_valid_value_succeeds(self):
        """Update a player's handicap."""
        game, p1, _p2 = _create_setup_game()
        resp = client.patch(
            f"/games/{game['game_id']}/players/{p1['player_slot_id']}/handicap",
            json={"handicap": 15.5},
        )
        assert resp.status_code == 200

    def test_update_handicap_persists(self):
        """Read-back: the new handicap is visible via GET /state."""
        game, p1, _p2 = _create_setup_game()
        game_id = game["game_id"]
        slot = p1["player_slot_id"]
        client.patch(f"/games/{game_id}/players/{slot}/handicap", json={"handicap": 15.5})
        state = client.get(f"/games/{game_id}/state").json()
        hcaps = {p["id"]: p.get("handicap") for p in state.get("players", [])}
        assert hcaps.get(slot) == 15.5

    def test_update_handicap_nonexistent_player_returns_404(self):
        """Updating handicap for nonexistent player returns 404."""
        game, _p1, _p2 = _create_setup_game()
        resp = client.patch(
            f"/games/{game['game_id']}/players/nonexistent-slot/handicap",
            json={"handicap": 10.0},
        )
        assert resp.status_code == 404


class TestUpdatePlayerNameValidation:
    """Request-shape validation for PATCH /games/{id}/players/{pid}/name."""

    def test_whitespace_only_name_returns_422(self):
        from fastapi.testclient import TestClient

        from app.main import app

        client = TestClient(app)
        resp = client.patch("/games/nonexistent/players/p1/name", json={"name": "  "})
        assert resp.status_code == 422
        assert "detail" in resp.json()

    def test_valid_name_passes_validation_then_404s(self):
        from fastapi.testclient import TestClient

        from app.main import app

        client = TestClient(app)
        resp = client.patch("/games/nonexistent/players/p1/name", json={"name": "Valid Name"})
        # Passes body validation, then fails the DB player lookup.
        assert resp.status_code == 404

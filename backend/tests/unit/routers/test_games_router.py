"""Unit tests for games router — create, join, lobby, list, delete, complete."""

import uuid

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _unique_id():
    return uuid.uuid4().hex[:8]


# ── Helper: create a game via the API ────────────────────────────────────────


def _create_game(**kwargs):
    """Create a game and return the JSON response."""
    params = {}
    if "course_name" in kwargs:
        params["course_name"] = kwargs["course_name"]
    if "player_count" in kwargs:
        params["player_count"] = kwargs["player_count"]
    if "user_id" in kwargs:
        params["user_id"] = kwargs["user_id"]
    resp = client.post("/games/create", params=params)
    return resp


def _join_game(join_code, player_name=None, handicap=18.0, user_id=None):
    """Join a game and return the response."""
    payload = {
        "player_name": player_name or f"Player-{_unique_id()}",
        "handicap": handicap,
    }
    if user_id:
        payload["user_id"] = user_id
    return client.post(f"/games/join/{join_code}", json=payload)


# ── POST /games/create ──────────────────────────────────────────────────────


class TestCreateGame:
    def test_create_game_returns_200(self):
        resp = _create_game()
        assert resp.status_code == 200

    def test_create_game_response_has_game_id(self):
        resp = _create_game()
        data = resp.json()
        assert "game_id" in data
        assert data["game_id"]  # non-empty

    def test_create_game_response_has_join_code(self):
        resp = _create_game()
        data = resp.json()
        assert "join_code" in data
        assert len(data["join_code"]) == 6

    def test_create_game_default_player_count(self):
        resp = _create_game()
        data = resp.json()
        assert data["player_count"] == 4

    def test_create_game_custom_player_count(self):
        resp = _create_game(player_count=3)
        data = resp.json()
        assert data["player_count"] == 3

    def test_create_game_status_is_setup(self):
        resp = _create_game()
        data = resp.json()
        assert data["status"] == "setup"

    def test_create_game_has_join_url(self):
        resp = _create_game()
        data = resp.json()
        assert "join_url" in data
        assert data["join_code"] in data["join_url"]


# ── POST /games/join/{join_code} ─────────────────────────────────────────────


class TestJoinGame:
    def test_join_game_returns_200(self):
        game = _create_game().json()
        resp = _join_game(game["join_code"], player_name="Alice")
        assert resp.status_code == 200

    def test_join_game_returns_player_slot(self):
        game = _create_game().json()
        resp = _join_game(game["join_code"], player_name="Bob")
        data = resp.json()
        assert "player_slot_id" in data

    def test_join_game_increments_player_count(self):
        game = _create_game().json()
        join_code = game["join_code"]
        resp1 = _join_game(join_code, player_name="Charlie")
        resp2 = _join_game(join_code, player_name="Dana")
        assert resp1.json()["players_joined"] == 1
        assert resp2.json()["players_joined"] == 2

    def test_join_nonexistent_game_returns_404(self):
        resp = _join_game("ZZZZZZ", player_name="Ghost")
        assert resp.status_code == 404

    def test_join_full_game_returns_400(self):
        game = _create_game(player_count=2).json()
        join_code = game["join_code"]
        _join_game(join_code, player_name="Player1")
        _join_game(join_code, player_name="Player2")
        resp = _join_game(join_code, player_name="Player3")
        assert resp.status_code == 400

    def test_join_game_missing_name_returns_422(self):
        game = _create_game().json()
        resp = client.post(f"/games/join/{game['join_code']}", json={"handicap": 10.0})
        assert resp.status_code == 422

    def test_join_game_short_name_returns_422(self):
        game = _create_game().json()
        resp = client.post(
            f"/games/join/{game['join_code']}",
            json={"player_name": "A", "handicap": 10.0},
        )
        assert resp.status_code == 422

    def test_duplicate_user_returns_already_joined(self):
        game = _create_game().json()
        user = f"user-{_unique_id()}"
        _join_game(game["join_code"], player_name="Eve", user_id=user)
        resp = _join_game(game["join_code"], player_name="Eve", user_id=user)
        data = resp.json()
        assert data.get("status") == "already_joined"


# ── GET /games/{game_id}/lobby ───────────────────────────────────────────────


class TestGameLobby:
    def test_lobby_returns_200(self):
        game = _create_game().json()
        resp = client.get(f"/games/{game['game_id']}/lobby")
        assert resp.status_code == 200

    def test_lobby_has_game_info(self):
        game = _create_game().json()
        resp = client.get(f"/games/{game['game_id']}/lobby")
        data = resp.json()
        assert data["game_id"] == game["game_id"]
        assert data["join_code"] == game["join_code"]
        assert data["status"] == "setup"

    def test_lobby_shows_joined_players(self):
        game = _create_game().json()
        _join_game(game["join_code"], player_name="Frank")
        resp = client.get(f"/games/{game['game_id']}/lobby")
        data = resp.json()
        assert data["players_joined"] == 1
        assert len(data["players"]) == 1
        assert data["players"][0]["player_name"] == "Frank"

    def test_lobby_nonexistent_game_returns_404(self):
        resp = client.get("/games/nonexistent-id/lobby")
        assert resp.status_code == 404

    def test_lobby_ready_to_start_with_two_players(self):
        game = _create_game().json()
        _join_game(game["join_code"], player_name="Grace")
        _join_game(game["join_code"], player_name="Henry")
        resp = client.get(f"/games/{game['game_id']}/lobby")
        data = resp.json()
        assert data["ready_to_start"] is True


# ── GET /games ───────────────────────────────────────────────────────────────


class TestListGames:
    def test_list_games_returns_200(self):
        resp = client.get("/games")
        assert resp.status_code == 200

    def test_list_games_has_expected_shape(self):
        resp = client.get("/games")
        data = resp.json()
        assert "games" in data
        assert "total_count" in data
        assert isinstance(data["games"], list)

    def test_list_games_with_status_filter(self):
        _create_game()
        resp = client.get("/games", params={"status": "setup"})
        data = resp.json()
        for game in data["games"]:
            assert game["game_status"] == "setup"

    def test_list_games_with_limit(self):
        resp = client.get("/games", params={"limit": 2})
        data = resp.json()
        assert len(data["games"]) <= 2

    def test_list_games_pagination_has_more(self):
        resp = client.get("/games", params={"limit": 1, "offset": 0})
        data = resp.json()
        assert "has_more" in data


# ── DELETE /games/{game_id} ──────────────────────────────────────────────────


class TestDeleteGame:
    def test_delete_game_returns_200(self):
        game = _create_game().json()
        resp = client.delete(f"/games/{game['game_id']}")
        assert resp.status_code == 200

    def test_delete_game_returns_success(self):
        game = _create_game().json()
        resp = client.delete(f"/games/{game['game_id']}")
        data = resp.json()
        assert data["success"] is True
        assert data["game_id"] == game["game_id"]

    def test_delete_nonexistent_game_returns_404(self):
        resp = client.delete("/games/nonexistent-id")
        assert resp.status_code == 404

    def test_delete_game_with_players(self):
        game = _create_game().json()
        _join_game(game["join_code"], player_name="Iris")
        resp = client.delete(f"/games/{game['game_id']}")
        assert resp.status_code == 200
        assert resp.json()["players_deleted"] >= 1

    def test_deleted_game_not_in_lobby(self):
        game = _create_game().json()
        client.delete(f"/games/{game['game_id']}")
        resp = client.get(f"/games/{game['game_id']}/lobby")
        assert resp.status_code == 404


# ── PATCH /games/{game_id}/tee-order ─────────────────────────────────────────


class TestTeeOrder:
    def _setup_game_with_players(self, count=2):
        game = _create_game(player_count=count).json()
        join_code = game["join_code"]
        slots = []
        for i in range(count):
            resp = _join_game(join_code, player_name=f"Player{i + 1}")
            slots.append(resp.json()["player_slot_id"])
        return game["game_id"], slots

    def test_set_tee_order_returns_200(self):
        game_id, slots = self._setup_game_with_players(2)
        resp = client.patch(
            f"/games/{game_id}/tee-order",
            json={"player_order": slots},
        )
        assert resp.status_code == 200

    def test_set_tee_order_success_message(self):
        game_id, slots = self._setup_game_with_players(2)
        resp = client.patch(
            f"/games/{game_id}/tee-order",
            json={"player_order": slots},
        )
        data = resp.json()
        assert data["status"] == "success"
        assert data["player_order"] == slots

    def test_set_tee_order_nonexistent_game_returns_404(self):
        resp = client.patch(
            "/games/nonexistent-id/tee-order",
            json={"player_order": ["p1", "p2"]},
        )
        assert resp.status_code == 404

    def test_set_tee_order_empty_order_returns_400(self):
        game_id, _ = self._setup_game_with_players(2)
        resp = client.patch(
            f"/games/{game_id}/tee-order",
            json={"player_order": []},
        )
        assert resp.status_code == 400

    def test_set_tee_order_wrong_count_returns_400(self):
        game_id, slots = self._setup_game_with_players(3)
        resp = client.patch(
            f"/games/{game_id}/tee-order",
            json={"player_order": slots[:2]},  # only 2 of 3
        )
        assert resp.status_code == 400


# ── POST /games/{game_id}/start ──────────────────────────────────────────────


class TestStartGame:
    def test_start_nonexistent_game_returns_404(self):
        resp = client.post("/games/nonexistent-id/start")
        assert resp.status_code == 404

    def test_start_game_without_tee_order_returns_400(self):
        game = _create_game().json()
        _join_game(game["join_code"], player_name="Alice")
        _join_game(game["join_code"], player_name="Bob")
        resp = client.post(f"/games/{game['game_id']}/start")
        assert resp.status_code == 400

    def test_start_game_with_one_player_returns_400(self):
        game = _create_game(player_count=2).json()
        join_resp = _join_game(game["join_code"], player_name="Solo")
        slot = join_resp.json()["player_slot_id"]
        # Set tee order with just 1 player — start should still fail (need >=2)
        client.patch(
            f"/games/{game['game_id']}/tee-order",
            json={"player_order": [slot]},
        )
        resp = client.post(f"/games/{game['game_id']}/start")
        assert resp.status_code == 400

    def test_start_game_success(self):
        game = _create_game(player_count=4).json()
        join_code = game["join_code"]
        slots = []
        for i, name in enumerate(["Alice", "Bob", "Carol", "Dave"]):
            r = _join_game(join_code, player_name=name, handicap=10.0 + i)
            slots.append(r.json()["player_slot_id"])
        client.patch(
            f"/games/{game['game_id']}/tee-order",
            json={"player_order": slots},
        )
        resp = client.post(f"/games/{game['game_id']}/start")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "started"
        assert len(data["players"]) == 4

    def test_start_already_started_game_returns_400(self):
        game = _create_game(player_count=4).json()
        join_code = game["join_code"]
        slots = []
        for i, name in enumerate(["Alice", "Bob", "Carol", "Dave"]):
            r = _join_game(join_code, player_name=name, handicap=10.0 + i)
            slots.append(r.json()["player_slot_id"])
        client.patch(
            f"/games/{game['game_id']}/tee-order",
            json={"player_order": slots},
        )
        client.post(f"/games/{game['game_id']}/start")
        resp = client.post(f"/games/{game['game_id']}/start")
        assert resp.status_code == 400

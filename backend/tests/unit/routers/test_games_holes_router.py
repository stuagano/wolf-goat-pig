"""Unit tests for games_holes router — /scores persistence and hole CRUD."""

import uuid

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _unique_id():
    return uuid.uuid4().hex[:8]


# ── Helpers ──────────────────────────────────────────────────────────────────


def _create_game(**kwargs):
    params = {}
    if "course_name" in kwargs:
        params["course_name"] = kwargs["course_name"]
    if "player_count" in kwargs:
        params["player_count"] = kwargs["player_count"]
    if "user_id" in kwargs:
        params["user_id"] = kwargs["user_id"]
    return client.post("/games/create", params=params)


def _join_game(join_code, player_name=None, handicap=18.0, user_id=None):
    payload = {
        "player_name": player_name or f"Player-{_unique_id()}",
        "handicap": handicap,
    }
    if user_id:
        payload["user_id"] = user_id
    return client.post(f"/games/join/{join_code}", json=payload)


def _setup_started_game(player_count=4):
    """Create a game, join players, set tee order, start it. Return (game_id, player_slots)."""
    game = _create_game(player_count=player_count).json()
    join_code = game["join_code"]
    slots = []
    for i in range(player_count):
        r = _join_game(join_code, player_name=f"Player{i + 1}", handicap=10.0 + i)
        slots.append(r.json()["player_slot_id"])
    client.patch(
        f"/games/{game['game_id']}/tee-order",
        json={"player_order": slots},
    )
    client.post(f"/games/{game['game_id']}/start")
    return game["game_id"], slots


def _post_scores(game_id, payload):
    """Post hole scores via /scores, converting the legacy quarters-only
    payload shape ({"hole_quarters": {hole: {player: q}}}) to the typed
    HoleScore list the endpoint now expects."""
    details = payload.get("optional_details", {})
    holes = []
    for hole_str, quarters in payload["hole_quarters"].items():
        hole = {"hole_number": int(hole_str), "quarters": quarters}
        hole.update(details.get(hole_str, {}))
        holes.append(hole)
    body = {"holes": holes}
    if "current_hole" in payload:
        body["current_hole"] = payload["current_hole"]
    return client.post(f"/games/{game_id}/scores", json=body)


# ── POST /games/{game_id}/scores ─────────────────────────────────────────────


class TestSaveScores:
    def test_save_scores_returns_200(self):
        game_id, slots = _setup_started_game()
        resp = _post_scores(
            game_id,
            {
                "hole_quarters": {
                    "1": {slots[0]: 2, slots[1]: -1, slots[2]: 0, slots[3]: -1},
                },
                "current_hole": 1,
            },
        )
        assert resp.status_code == 200

    def test_save_scores_success_response_shape(self):
        game_id, slots = _setup_started_game()
        resp = _post_scores(
            game_id,
            {
                "hole_quarters": {
                    "1": {slots[0]: 3, slots[1]: -1, slots[2]: -1, slots[3]: -1},
                },
                "current_hole": 1,
            },
        )
        data = resp.json()
        assert data["success"] is True
        assert "standings" in data
        assert "holes_saved" in data
        assert data["holes_saved"] == 1
        assert data["game_id"] == game_id

    def test_save_scores_standings_are_correct(self):
        game_id, slots = _setup_started_game()
        resp = _post_scores(
            game_id,
            {
                "hole_quarters": {
                    "1": {slots[0]: 4, slots[1]: -2, slots[2]: -1, slots[3]: -1},
                    "2": {slots[0]: -2, slots[1]: 2, slots[2]: 1, slots[3]: -1},
                },
                "current_hole": 2,
            },
        )
        data = resp.json()
        standings = data["standings"]
        assert standings[slots[0]] == 2  # 4 + (-2)
        assert standings[slots[1]] == 0  # -2 + 2
        assert standings[slots[2]] == 0  # -1 + 1
        assert standings[slots[3]] == -2  # -1 + (-1)

    def test_save_scores_zero_sum_validation_fails(self):
        game_id, slots = _setup_started_game()
        resp = _post_scores(
            game_id,
            {
                "hole_quarters": {
                    "1": {slots[0]: 5, slots[1]: -1, slots[2]: -1, slots[3]: -1},
                },
                "current_hole": 1,
            },
        )
        assert resp.status_code == 400
        assert "Zero-sum" in resp.json()["detail"]

    def test_save_scores_nonexistent_game_returns_404(self):
        resp = _post_scores(
            "nonexistent-id",
            {
                "hole_quarters": {"1": {"p1": 1, "p2": -1}},
                "current_hole": 1,
            },
        )
        assert resp.status_code == 404

    def test_save_scores_multiple_holes(self):
        game_id, slots = _setup_started_game()
        hole_quarters = {}
        for h in range(1, 6):
            hole_quarters[str(h)] = {slots[0]: 1, slots[1]: -1, slots[2]: 1, slots[3]: -1}
        resp = _post_scores(
            game_id,
            {"hole_quarters": hole_quarters, "current_hole": 5},
        )
        data = resp.json()
        assert data["holes_saved"] == 5
        assert data["standings"][slots[0]] == 5
        assert data["standings"][slots[1]] == -5

    def test_save_scores_with_optional_details(self):
        game_id, slots = _setup_started_game()
        resp = _post_scores(
            game_id,
            {
                "hole_quarters": {
                    "1": {slots[0]: 2, slots[1]: -2, slots[2]: 0, slots[3]: 0},
                },
                "optional_details": {
                    "1": {"notes": "Great drive by Player1", "winner": "team1"},
                },
                "current_hole": 1,
            },
        )
        assert resp.status_code == 200
        assert resp.json()["success"] is True

    def test_save_scores_sets_in_progress_status(self):
        game_id, slots = _setup_started_game()
        resp = _post_scores(
            game_id,
            {
                "hole_quarters": {
                    "1": {slots[0]: 1, slots[1]: -1, slots[2]: 0, slots[3]: 0},
                },
                "current_hole": 1,
            },
        )
        data = resp.json()
        assert data["game_status"] == "in_progress"

    def test_save_scores_18_holes_sets_completed(self):
        game_id, slots = _setup_started_game()
        hole_quarters = {}
        for h in range(1, 19):
            hole_quarters[str(h)] = {slots[0]: 1, slots[1]: -1, slots[2]: 1, slots[3]: -1}
        resp = _post_scores(
            game_id,
            {"hole_quarters": hole_quarters, "current_hole": 18},
        )
        data = resp.json()
        assert data["game_status"] == "completed"
        assert data["holes_saved"] == 18


# ── DELETE /games/{game_id}/holes/{hole_number} ──────────────────────────────


class TestDeleteHole:
    def _save_quarters_and_get_state(self, game_id, slots, hole_quarters):
        """Save scores so hole_history is populated."""
        _post_scores(
            game_id,
            {"hole_quarters": hole_quarters, "current_hole": len(hole_quarters)},
        )

    def test_delete_hole_nonexistent_game_returns_404(self):
        resp = client.delete("/games/nonexistent-id/holes/1")
        assert resp.status_code == 404

    def test_delete_hole_no_history_returns_404(self):
        game_id, _ = _setup_started_game()
        resp = client.delete(f"/games/{game_id}/holes/1")
        assert resp.status_code == 404

    def test_delete_hole_not_in_history_returns_404(self):
        game_id, slots = _setup_started_game()
        self._save_quarters_and_get_state(
            game_id,
            slots,
            {"1": {slots[0]: 1, slots[1]: -1, slots[2]: 0, slots[3]: 0}},
        )
        resp = client.delete(f"/games/{game_id}/holes/5")
        assert resp.status_code == 404

    def test_delete_hole_success(self):
        game_id, slots = _setup_started_game()
        # Save scores and verify it worked
        save_resp = _post_scores(
            game_id,
            {
                "hole_quarters": {
                    "1": {slots[0]: 1, slots[1]: -1, slots[2]: 0, slots[3]: 0},
                    "2": {slots[0]: -1, slots[1]: 1, slots[2]: 0, slots[3]: 0},
                },
                "current_hole": 2,
            },
        )
        assert save_resp.status_code == 200
        assert save_resp.json()["holes_saved"] == 2

        resp = client.delete(f"/games/{game_id}/holes/2")
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["hole_number"] == 2

        # Hole 2 is gone — deleting again returns 404; hole 1 still deletable
        assert client.delete(f"/games/{game_id}/holes/2").status_code == 404
        assert client.delete(f"/games/{game_id}/holes/1").status_code == 200

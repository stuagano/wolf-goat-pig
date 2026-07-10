"""Unit tests for players router — CRUD, validation, error handling."""

import uuid

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def unique_name(prefix="Player"):
    """Generate a unique player name to avoid duplicate conflicts."""
    return f"{prefix}-{uuid.uuid4().hex[:8]}"


def unique_email(prefix="player"):
    return f"{prefix}-{uuid.uuid4().hex[:8]}@test.com"


# ── GET /players ──────────────────────────────────────────────────────────────


class TestGetPlayers:
    def test_list_players_returns_200(self):
        resp = client.get("/players")
        assert resp.status_code == 200

    def test_list_players_returns_list(self):
        resp = client.get("/players")
        assert isinstance(resp.json(), list)

    def test_all_players_returns_200(self):
        resp = client.get("/players/all")
        assert resp.status_code == 200

    def test_all_players_returns_list(self):
        resp = client.get("/players/all")
        assert isinstance(resp.json(), list)


# ── POST /players ─────────────────────────────────────────────────────────────


class TestCreatePlayer:
    def test_create_player_returns_201_or_200(self):
        payload = {"name": unique_name("Coverage"), "email": unique_email("coverage"), "handicap": 12.0}
        resp = client.post("/players", json=payload)
        assert resp.status_code in (200, 201)

    def test_create_player_response_has_id(self):
        payload = {"name": unique_name("Router"), "email": unique_email("router"), "handicap": 15.0}
        resp = client.post("/players", json=payload)
        if resp.status_code in (200, 201):
            data = resp.json()
            assert "id" in data

    def test_create_player_response_has_name(self):
        name = unique_name("NameCheck")
        payload = {"name": name, "email": unique_email("namecheck"), "handicap": 10.0}
        resp = client.post("/players", json=payload)
        if resp.status_code in (200, 201):
            assert resp.json()["name"] == name

    def test_missing_name_returns_422(self):
        resp = client.post("/players", json={"email": unique_email("noname")})
        assert resp.status_code == 422

    def test_invalid_payload_returns_422(self):
        resp = client.post("/players", json={"handicap": "not-a-number"})
        assert resp.status_code == 422


# ── GET /players/{player_id} ──────────────────────────────────────────────────


class TestGetPlayerById:
    def test_get_nonexistent_player_returns_404(self):
        resp = client.get("/players/999999")
        assert resp.status_code == 404

    def test_get_player_by_name_not_found_returns_404(self):
        resp = client.get("/players/name/NonExistentPlayerXYZ")
        assert resp.status_code == 404


# ── GET /players/{player_id}/public-profile ───────────────────────────────────


class TestPublicProfile:
    def test_public_profile_requires_no_auth(self):
        """Player profile pages are public — no Authorization header, no override."""
        create = client.post("/players", json={"name": unique_name("PublicProfile"), "handicap": 12.0})
        assert create.status_code in (200, 201)
        player_id = create.json()["id"]

        resp = client.get(f"/players/{player_id}/public-profile")
        assert resp.status_code == 200
        body = resp.json()
        assert body["id"] == player_id
        assert "game_history" in body

    def test_public_profile_nonexistent_player_returns_404(self):
        resp = client.get("/players/999999/public-profile")
        assert resp.status_code == 404

    def test_public_profile_exposes_hole_by_hole_only_when_present(self):
        """A round with real hole_scores (in-app/scanned) surfaces per-hole detail
        under 'holes'; a legacy-sheet-only round (hole_scores=None) does not."""
        from unittest.mock import MagicMock, patch

        from app.services.unified_data_service import UnifiedRound

        create = client.post("/players", json={"name": unique_name("HoleDetail"), "handicap": 12.0})
        player_id = create.json()["id"]

        rounds = [
            UnifiedRound(
                date="6-Apr",
                date_sortable="2026-04-06",
                group="A",
                member=create.json()["name"],
                score=4,
                location="Wing Point",
                source="database",
                hole_scores=[
                    {"hole": 2, "quarters": -1, "gross_score": 6},
                    {"hole": 1, "quarters": 2, "gross_score": 4},
                ],
            ),
            UnifiedRound(
                date="1-Apr",
                date_sortable="2026-04-01",
                group="A",
                member=create.json()["name"],
                score=-2,
                location="Wing Point",
                source="primary_sheet",
            ),
        ]
        fake_service = MagicMock()
        fake_service.get_player_history.return_value = rounds

        with patch("app.routers.players.get_unified_data_service", return_value=fake_service):
            resp = client.get(f"/players/{player_id}/public-profile")

        assert resp.status_code == 200
        history = resp.json()["game_history"]
        assert history[0]["holes"] == [
            {"hole": 1, "quarters": 2, "gross_score": 4},
            {"hole": 2, "quarters": -1, "gross_score": 6},
        ]
        assert history[1]["holes"] is None


# ── PUT /players/{player_id} ──────────────────────────────────────────────────


class TestUpdatePlayer:
    def _create_player(self, prefix="UpdateTarget"):
        resp = client.post(
            "/players", json={"name": unique_name(prefix), "email": unique_email(prefix.lower()), "handicap": 18.0}
        )
        if resp.status_code in (200, 201):
            return resp.json()["id"]
        return None

    def test_update_nonexistent_player_returns_404(self):
        resp = client.put("/players/999999", json={"name": unique_name("NewName")})
        assert resp.status_code == 404

    def test_update_player_name(self):
        pid = self._create_player("PreUpdate")
        if pid:
            new_name = unique_name("PostUpdate")
            resp = client.put(f"/players/{pid}", json={"name": new_name})
            assert resp.status_code == 200
            assert resp.json()["name"] == new_name

    def test_update_player_handicap(self):
        pid = self._create_player("HandicapUpdate")
        if pid:
            resp = client.put(f"/players/{pid}", json={"handicap": 5.0})
            assert resp.status_code == 200
            assert resp.json()["handicap"] == 5.0


# ── DELETE /players/{player_id} ───────────────────────────────────────────────


class TestDeletePlayer:
    def test_delete_nonexistent_player_returns_404(self):
        resp = client.delete("/players/999999")
        assert resp.status_code == 404

    def test_delete_player_returns_success_message(self):
        resp = client.post(
            "/players", json={"name": unique_name("DeleteMe"), "email": unique_email("deleteme"), "handicap": 20.0}
        )
        if resp.status_code in (200, 201):
            pid = resp.json()["id"]
            del_resp = client.delete(f"/players/{pid}")
            assert del_resp.status_code == 200
            assert "deleted" in str(del_resp.json()).lower() or "success" in str(del_resp.json()).lower()


# ── GET /players/{player_id}/statistics ──────────────────────────────────────


class TestPlayerStatistics:
    def test_statistics_for_nonexistent_player_returns_404(self):
        resp = client.get("/players/999999/statistics")
        assert resp.status_code == 404

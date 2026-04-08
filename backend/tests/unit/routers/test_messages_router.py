"""Unit tests for messages router — daily message CRUD."""

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

VALID_DATE = "2026-01-15"


# ── Helper ────────────────────────────────────────────────────────────────────


def _create_message(date=VALID_DATE, message="Hello group!", player_name="Alice"):
    """Create a message and return the response."""
    return client.post(
        "/messages",
        json={
            "date": date,
            "message": message,
            "player_name": player_name,
            "player_profile_id": 1,
        },
    )


# ── GET /messages/daily ──────────────────────────────────────────────────────


class TestGetDailyMessages:
    def test_get_messages_returns_200(self):
        resp = client.get("/messages/daily", params={"date": VALID_DATE})
        assert resp.status_code == 200

    def test_get_messages_returns_list(self):
        resp = client.get("/messages/daily", params={"date": VALID_DATE})
        assert isinstance(resp.json(), list)

    def test_get_messages_missing_date_returns_422(self):
        resp = client.get("/messages/daily")
        assert resp.status_code == 422

    def test_get_messages_returns_created_message(self):
        unique_date = "2026-09-01"
        _create_message(date=unique_date, message="Visible msg")
        resp = client.get("/messages/daily", params={"date": unique_date})
        assert resp.status_code == 200
        messages = resp.json()
        assert any(m["message"] == "Visible msg" for m in messages)

    def test_get_messages_excludes_deleted(self):
        unique_date = "2026-09-02"
        create_resp = _create_message(date=unique_date, message="To delete")
        msg_id = create_resp.json()["id"]
        client.delete(f"/messages/{msg_id}")

        resp = client.get("/messages/daily", params={"date": unique_date})
        messages = resp.json()
        assert not any(m["id"] == msg_id for m in messages)


# ── POST /messages ───────────────────────────────────────────────────────────


class TestCreateMessage:
    def test_create_message_returns_200(self):
        resp = _create_message()
        assert resp.status_code == 200

    def test_create_message_returns_message_fields(self):
        resp = _create_message(message="Test content")
        data = resp.json()
        assert data["message"] == "Test content"
        assert "id" in data
        assert "date" in data
        assert "message_time" in data
        assert "created_at" in data

    def test_create_message_defaults_player_name(self):
        resp = client.post(
            "/messages",
            json={"date": VALID_DATE, "message": "No name"},
        )
        assert resp.status_code == 200
        assert resp.json()["player_name"] == "Anonymous"

    def test_create_message_sets_active(self):
        resp = _create_message()
        assert resp.json()["is_active"] == 1


# ── PUT /messages/{message_id} ───────────────────────────────────────────────


class TestUpdateMessage:
    def test_update_message_returns_200(self):
        msg = _create_message().json()
        resp = client.put(
            f"/messages/{msg['id']}",
            json={"message": "Updated text"},
        )
        assert resp.status_code == 200

    def test_update_message_changes_content(self):
        msg = _create_message().json()
        resp = client.put(
            f"/messages/{msg['id']}",
            json={"message": "New content"},
        )
        assert resp.json()["message"] == "New content"

    def test_update_nonexistent_message_returns_404(self):
        resp = client.put("/messages/999999", json={"message": "Nope"})
        assert resp.status_code == 404

    def test_update_message_preserves_other_fields(self):
        msg = _create_message(player_name="Bob").json()
        resp = client.put(
            f"/messages/{msg['id']}",
            json={"message": "Changed"},
        )
        data = resp.json()
        assert data["player_name"] == "Bob"
        assert data["date"] == msg["date"]


# ── DELETE /messages/{message_id} ────────────────────────────────────────────


class TestDeleteMessage:
    def test_delete_message_returns_200(self):
        msg = _create_message().json()
        resp = client.delete(f"/messages/{msg['id']}")
        assert resp.status_code == 200

    def test_delete_message_returns_success(self):
        msg = _create_message().json()
        resp = client.delete(f"/messages/{msg['id']}")
        assert resp.json()["message"] == "Message deleted successfully"

    def test_delete_nonexistent_message_returns_404(self):
        resp = client.delete("/messages/999999")
        assert resp.status_code == 404

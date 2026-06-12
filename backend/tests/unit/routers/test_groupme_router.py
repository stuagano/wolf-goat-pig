"""Tests for the GroupMe bridge — service normalization + router behavior.

All GroupMe HTTP calls are mocked; no network.
"""

from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app
from app.services import groupme_service

client = TestClient(app)


RAW_MESSAGE = {
    "id": "123",
    "name": "Gregg Colburn",
    "text": "who's in sunday?",
    "avatar_url": "https://i.groupme.com/abc",
    "created_at": 1765500000,
    "favorited_by": ["u1", "u2"],
    "attachments": [{"type": "image", "url": "https://i.groupme.com/pic"}],
    "sender_type": "user",
    "system": False,
}


class TestNormalization:
    def test_normalize_message_shape(self):
        m = groupme_service._normalize_message(RAW_MESSAGE)
        assert m["name"] == "Gregg Colburn"
        assert m["text"] == "who's in sunday?"
        assert m["likes"] == 2
        assert m["images"] == ["https://i.groupme.com/pic"]
        assert m["created_at"].startswith("2025-12-")  # unix ts -> ISO
        assert m["is_system"] is False
        assert m["is_bot"] is False

    def test_system_message_flagged(self):
        m = groupme_service._normalize_message({**RAW_MESSAGE, "system": True})
        assert m["is_system"] is True


class TestStatusEndpoint:
    def test_unconfigured_status(self):
        with patch.dict("os.environ", {}, clear=False):
            for k in ("GROUPME_ACCESS_TOKEN", "GROUPME_GROUP_ID", "GROUPME_BOT_ID"):
                patch.dict("os.environ", {k: ""}).start()
            resp = client.get("/groupme/status")
        assert resp.status_code == 200
        body = resp.json()
        assert set(body.keys()) == {"read", "post"}


class TestMessagesEndpoint:
    def test_unconfigured_returns_empty_gracefully(self):
        groupme_service._cache = {}
        groupme_service._cache_ts = 0.0
        with patch.object(groupme_service, "_token", return_value=None):
            resp = client.get("/groupme/messages")
        assert resp.status_code == 200
        assert resp.json() == {"configured": False, "messages": []}

    def test_messages_oldest_first_and_cached(self):
        groupme_service._cache = {}
        groupme_service._cache_ts = 0.0
        newest_first = {
            "messages": [
                {**RAW_MESSAGE, "id": "2", "text": "second", "created_at": 1765500100},
                {**RAW_MESSAGE, "id": "1", "text": "first", "created_at": 1765500000},
            ]
        }
        with (
            patch.object(groupme_service, "_token", return_value="tok"),
            patch.object(groupme_service, "_group_id", return_value="g1"),
            patch.object(groupme_service, "_api_get", return_value=newest_first) as api,
        ):
            resp = client.get("/groupme/messages")
            texts = [m["text"] for m in resp.json()["messages"]]
            assert texts == ["first", "second"]  # reversed for chat rendering
            # Second call within TTL: served from cache, no upstream call
            client.get("/groupme/messages")
            assert api.call_count == 1

    def test_fetch_error_serves_stale_cache(self):
        groupme_service._cache = {"configured": True, "messages": [{"id": "x", "text": "stale"}]}
        groupme_service._cache_ts = 0.0  # expired — forces refetch
        with (
            patch.object(groupme_service, "_token", return_value="tok"),
            patch.object(groupme_service, "_group_id", return_value="g1"),
            patch.object(groupme_service, "_api_get", side_effect=OSError("down")),
        ):
            resp = client.get("/groupme/messages")
        assert resp.json()["messages"][0]["text"] == "stale"


class TestPostEndpoint:
    def test_post_requires_auth(self):
        resp = client.post("/groupme/messages", json={"text": "hi"})
        assert resp.status_code in (401, 403)

    def test_post_attributes_author(self):
        from app.services.auth_service import get_current_user

        class FakeUser:
            name = "Stuart Gano"

        app.dependency_overrides[get_current_user] = lambda: FakeUser()
        try:
            with patch("app.routers.groupme.post_message", return_value={"posted": True}) as pm:
                resp = client.post("/groupme/messages", json={"text": "nice round"})
            assert resp.status_code == 200
            pm.assert_called_once_with("nice round", author="Stuart Gano")
        finally:
            app.dependency_overrides.pop(get_current_user, None)

    def test_post_unconfigured_returns_502(self):
        from app.services.auth_service import get_current_user

        class FakeUser:
            name = "Stuart Gano"

        app.dependency_overrides[get_current_user] = lambda: FakeUser()
        try:
            with patch(
                "app.routers.groupme.post_message",
                return_value={"posted": False, "error": "GROUPME_BOT_ID not configured"},
            ):
                resp = client.post("/groupme/messages", json={"text": "hi"})
            assert resp.status_code == 502
        finally:
            app.dependency_overrides.pop(get_current_user, None)


class TestPostMessageService:
    def test_author_prefixed_and_truncated(self):
        captured = {}

        def fake_urlopen(req, timeout=None):
            import json as _json

            captured.update(_json.loads(req.data.decode()))

            class R:
                status = 202

                def __enter__(self):
                    return self

                def __exit__(self, *a):
                    return False

            return R()

        with (
            patch.object(groupme_service, "_bot_id", return_value="bot1"),
            patch.object(groupme_service.urllib.request, "urlopen", fake_urlopen),
        ):
            result = groupme_service.post_message("x" * 2000, author="Stu")
        assert result == {"posted": True}
        assert captured["bot_id"] == "bot1"
        assert captured["text"].startswith("Stu: ")
        assert len(captured["text"]) <= 990

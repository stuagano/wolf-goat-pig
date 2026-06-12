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
        assert result == {"posted": True, "via": "bot"}
        assert captured["bot_id"] == "bot1"
        assert captured["text"].startswith("Stu: ")
        assert len(captured["text"]) <= 990

    def test_user_post_fallback_when_no_bot(self):
        """Without a bot, posting falls back to the token owner's account
        via the group messages API (works without group-admin rights)."""
        captured = {}

        def fake_urlopen(req, timeout=None):
            import json as _json

            captured["url"] = req.full_url
            captured.update(_json.loads(req.data.decode()))

            class R:
                status = 201

                def __enter__(self):
                    return self

                def __exit__(self, *a):
                    return False

            return R()

        with (
            patch.object(groupme_service, "_bot_id", return_value=None),
            patch.object(groupme_service, "_token", return_value="tok"),
            patch.object(groupme_service, "_group_id", return_value="g1"),
            patch.object(groupme_service.urllib.request, "urlopen", fake_urlopen),
        ):
            result = groupme_service.post_message("see you sunday", author="Hart")
        assert result == {"posted": True, "via": "user"}
        assert "/groups/g1/messages" in captured["url"]
        assert captured["message"]["text"] == "Hart: see you sunday"
        assert captured["message"]["source_guid"]

    def test_post_unconfigured_entirely(self):
        with (
            patch.object(groupme_service, "_bot_id", return_value=None),
            patch.object(groupme_service, "_token", return_value=None),
        ):
            result = groupme_service.post_message("hi", author="Stu")
        assert result["posted"] is False


class TestHistoryPaging:
    def test_before_id_passed_through_and_uncached(self):
        groupme_service._cache = {"configured": True, "messages": [{"id": "cached"}]}
        groupme_service._cache_ts = __import__("time").time()  # fresh cache
        page = {"messages": [{**RAW_MESSAGE, "id": "old1", "text": "older"}]}
        with (
            patch.object(groupme_service, "_token", return_value="tok"),
            patch.object(groupme_service, "_group_id", return_value="g1"),
            patch.object(groupme_service, "_api_get", return_value=page) as api,
        ):
            resp = client.get("/groupme/messages?before_id=178000")
        # bypassed the fresh head cache and hit upstream with before_id
        assert api.call_args[0][1]["before_id"] == "178000"
        assert resp.json()["messages"][0]["text"] == "older"
        # head cache untouched
        assert groupme_service._cache["messages"][0]["id"] == "cached"


class TestVideoNormalization:
    def test_video_attachment_extracted(self):
        m = groupme_service._normalize_message(
            {
                **RAW_MESSAGE,
                "attachments": [
                    {
                        "type": "video",
                        "url": "https://v.groupme.com/clip.mp4",
                        "preview_url": "https://v.groupme.com/p.jpg",
                    }
                ],
            }
        )
        assert m["videos"] == [{"url": "https://v.groupme.com/clip.mp4", "preview_url": "https://v.groupme.com/p.jpg"}]

    def test_bare_mp4_link_in_text_becomes_video(self):
        url = "https://m.groupme.com/uploads/8bf56120350442b4bdfd499a32506f7c/1080x1920.original.mp4"
        m = groupme_service._normalize_message({**RAW_MESSAGE, "text": url, "attachments": []})
        assert m["videos"] == [{"url": url, "preview_url": None}]
        assert m["text"] is None  # link-only text suppressed; player renders instead

    def test_text_with_video_link_keeps_caption(self):
        url = "https://m.groupme.com/uploads/abc/1080x1920.original.mp4"
        m = groupme_service._normalize_message({**RAW_MESSAGE, "text": rf"chip-in on 9\! {url}", "attachments": []})
        assert m["videos"][0]["url"] == url
        assert r"chip-in on 9\!" in m["text"]


class TestMediaArchive:
    def _clear(self):
        from app import models
        from app.database import SessionLocal

        db = SessionLocal()
        db.query(models.LivSowMedia).delete()
        db.commit()
        db.close()

    def _msg(self, mid, **kw):
        return {
            "id": mid,
            "name": kw.get("name", "Hart Williams"),
            "text": kw.get("text"),
            "created_at": kw.get("created_at", "2026-06-11T21:00:00+00:00"),
            "likes": kw.get("likes", 3),
            "images": kw.get("images", []),
            "videos": kw.get("videos", []),
            "avatar_url": None,
            "is_system": False,
            "is_bot": False,
        }

    def test_harvest_and_list(self):
        self._clear()
        page1 = {
            "configured": True,
            "messages": [
                self._msg(
                    "m1", videos=[{"url": "https://m.groupme.com/a.mp4", "preview_url": None}], text=None, likes=5
                ),
                self._msg("m2", images=["https://i.groupme.com/pic1"], text=r"net eagle\!"),
                self._msg("m3"),  # no media
            ],
        }
        empty = {"configured": True, "messages": []}
        with patch(
            "app.services.league_media_service.get_messages",
            side_effect=[page1, empty],
        ):
            resp = client.post("/groupme/media/harvest")
        body = resp.json()
        assert body["status"] == "ok"
        assert body["inserted"] == 2

        vids = client.get("/groupme/media?kind=video").json()
        assert vids["total"] == 1
        assert vids["media"][0]["url"] == "https://m.groupme.com/a.mp4"
        assert vids["media"][0]["author"] == "Hart Williams"
        assert vids["media"][0]["likes"] == 5

        imgs = client.get("/groupme/media?kind=image").json()
        assert imgs["total"] == 1
        assert imgs["media"][0]["caption"] == r"net eagle\!"

    def test_harvest_idempotent_and_refreshes_likes(self):
        self._clear()
        v = [{"url": "https://m.groupme.com/a.mp4", "preview_url": None}]
        first = {"configured": True, "messages": [self._msg("m1", videos=v, likes=2)]}
        empty = {"configured": True, "messages": []}
        with patch("app.services.league_media_service.get_messages", side_effect=[first, empty]):
            client.post("/groupme/media/harvest")
        again = {"configured": True, "messages": [self._msg("m1", videos=v, likes=9)]}
        with patch("app.services.league_media_service.get_messages", side_effect=[again, empty]):
            resp = client.post("/groupme/media/harvest")
        assert resp.json()["inserted"] == 0
        media = client.get("/groupme/media?kind=video").json()["media"]
        assert len(media) == 1
        assert media[0]["likes"] == 9

    def test_harvest_unconfigured_skips(self):
        self._clear()
        with patch(
            "app.services.league_media_service.get_messages",
            return_value={"configured": False, "messages": []},
        ):
            resp = client.post("/groupme/media/harvest")
        assert resp.json() == {"status": "skipped", "reason": "not_configured"}

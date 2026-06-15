"""Unit tests for the notifications router.

Focus on read-after-write: marking a notification read must actually persist —
verified by re-reading via the list / unread-count endpoints, not just trusting
the POST response.
"""

import uuid

from fastapi.testclient import TestClient

from app import database, models
from app.main import app
from app.services.auth_service import get_current_user

client = TestClient(app)

# Distinct synthetic player id per module run so rows never collide with others.
_PLAYER_ID = 900000 + (uuid.uuid4().int % 90000)


class _FakeUser:
    id = _PLAYER_ID


def _override_user():
    app.dependency_overrides[get_current_user] = lambda: _FakeUser()


def _clear_override():
    app.dependency_overrides.pop(get_current_user, None)


def _seed_notification(is_read=False):
    db = database.SessionLocal()
    try:
        n = models.Notification(
            player_profile_id=_PLAYER_ID,
            notification_type="turn_notification",
            message="Your turn",
            data=None,
            is_read=is_read,
            created_at="2026-06-14T00:00:00",
        )
        db.add(n)
        db.commit()
        return n.id
    finally:
        db.close()


def _cleanup():
    db = database.SessionLocal()
    try:
        db.query(models.Notification).filter(models.Notification.player_profile_id == _PLAYER_ID).delete()
        db.commit()
    finally:
        db.close()


class TestMarkRead:
    def test_mark_read_persists(self):
        _override_user()
        try:
            nid = _seed_notification(is_read=False)
            assert client.get("/notifications/unread-count").json()["unread_count"] >= 1

            resp = client.post(f"/notifications/{nid}/read")
            assert resp.status_code == 200

            # Read-back: the notification is no longer unread.
            unread = client.get("/notifications?unread_only=true").json()
            assert nid not in [n["id"] for n in unread]
            assert client.get("/notifications/unread-count").json()["unread_count"] == 0
        finally:
            _cleanup()
            _clear_override()

    def test_mark_read_nonexistent_returns_404(self):
        _override_user()
        try:
            assert client.post("/notifications/999999999/read").status_code == 404
        finally:
            _clear_override()


class TestMarkAllRead:
    def test_mark_all_read_persists(self):
        _override_user()
        try:
            _seed_notification(is_read=False)
            _seed_notification(is_read=False)
            assert client.get("/notifications/unread-count").json()["unread_count"] == 2

            resp = client.post("/notifications/read-all")
            assert resp.status_code == 200
            assert resp.json()["marked_read"] == 2

            # Read-back: nothing unread remains.
            assert client.get("/notifications/unread-count").json()["unread_count"] == 0
        finally:
            _cleanup()
            _clear_override()

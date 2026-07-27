"""Unit tests for media_storage_service helpers (no live GCS)."""

from __future__ import annotations

from app.services import media_storage_service as mss


def test_avatar_markers(monkeypatch):
    monkeypatch.delenv("MEDIA_BUCKET", raising=False)
    assert mss.is_enabled() is False

    monkeypatch.setenv("MEDIA_BUCKET", "wgp-media-test")
    mss._client.cache_clear()
    assert mss.is_enabled() is True
    assert mss.avatar_object_path(20) == "avatars/20.jpg"
    marker = mss.avatar_gcs_marker(20)
    assert marker == "gcs:avatars/20.jpg"
    assert mss.is_gcs_avatar_url(marker) is True
    assert mss.is_gcs_avatar_url("https://example.com/a.jpg") is False
    assert mss.gcs_path_from_marker(marker) == "avatars/20.jpg"


def test_has_avatar_image_property_with_gcs_marker():
    from app.models import PlayerProfile

    p = PlayerProfile(name="X", avatar_url="gcs:avatars/1.jpg", avatar_image=None)
    assert p.has_avatar_image is True

    p2 = PlayerProfile(name="Y", avatar_url="https://lh3.googleusercontent.com/a", avatar_image=None)
    assert p2.has_avatar_image is False

    p3 = PlayerProfile(name="Z", avatar_url=None, avatar_image="abc")
    assert p3.has_avatar_image is True

    p4 = PlayerProfile(name="W", avatar_url="data:image/jpeg;base64,/9j/4AAQ", avatar_image=None)
    assert p4.has_avatar_image is True

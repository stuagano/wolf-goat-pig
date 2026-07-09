"""Unit tests for player avatar upload/serve.

Covers: self-service upload downscales+stores the image, rejects bad
content-types, and the public serve endpoint round-trips real bytes (404
when unset).
"""

from __future__ import annotations

from io import BytesIO

import pytest
from fastapi import Depends
from fastapi.testclient import TestClient
from PIL import Image
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.models import PlayerProfile
from app.services.auth_service import get_current_user


def _make_jpeg_bytes(size=(120, 80), color=(200, 30, 30)) -> bytes:
    buf = BytesIO()
    Image.new("RGB", size, color).save(buf, format="JPEG")
    return buf.getvalue()


@pytest.fixture
def db_session():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    session.add(PlayerProfile(id=1, name="Kevin Gent", legacy_name="Stuart Gano", created_at="2026-01-01T00:00:00"))
    session.commit()
    yield TestingSessionLocal
    session.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(db_session):
    def _override_get_db():
        db = db_session()
        try:
            yield db
        finally:
            db.close()

    def _override_get_current_user(db=Depends(get_db)):
        # `db` resolves through the overridden get_db above, so this is the
        # same session the endpoint uses (needed for db.refresh(current_user)).
        return db.query(PlayerProfile).filter_by(id=1).first()

    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_current_user] = _override_get_current_user

    test_client = TestClient(app)
    yield test_client

    app.dependency_overrides.pop(get_db, None)
    app.dependency_overrides.pop(get_current_user, None)


class TestAvatarUpload:
    def test_upload_stores_downscaled_image(self, client):
        resp = client.post(
            "/players/me/avatar",
            files={"file": ("photo.jpg", _make_jpeg_bytes(size=(2000, 1500)), "image/jpeg")},
        )
        assert resp.status_code == 200
        assert resp.json()["has_avatar_image"] is True

        avatar_resp = client.get("/players/1/avatar")
        assert avatar_resp.status_code == 200
        assert avatar_resp.headers["content-type"] == "image/jpeg"
        img = Image.open(BytesIO(avatar_resp.content))
        assert max(img.size) <= 400  # downscaled, not the original 2000x1500

    def test_upload_rejects_bad_content_type(self, client):
        resp = client.post(
            "/players/me/avatar",
            files={"file": ("notes.txt", b"hello", "text/plain")},
        )
        assert resp.status_code == 400

    def test_avatar_404_when_not_set(self, client):
        resp = client.get("/players/1/avatar")
        assert resp.status_code == 404

    def test_public_profile_reports_has_avatar_image(self, client):
        client.post(
            "/players/me/avatar",
            files={"file": ("photo.jpg", _make_jpeg_bytes(), "image/jpeg")},
        )
        resp = client.get("/players/1/public-profile")
        assert resp.status_code == 200
        body = resp.json()
        assert body["has_avatar_image"] is True
        assert "game_history" in body

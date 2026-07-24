"""CTK-grade contracts for league media harvest/list."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models import Base, LivSowMedia
from app.services import league_media_service

TEST_DATABASE_URL = "sqlite:///./test_league_media_service.db"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture
def db():
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


def _msg(mid, **kw):
    return {
        "id": mid,
        "name": kw.get("name", "Hart Williams"),
        "text": kw.get("text"),
        "created_at": kw.get("created_at", "2026-06-11T21:00:00+00:00"),
        "likes": kw.get("likes", 3),
        "images": kw.get("images", []),
        "videos": kw.get("videos", []),
    }


def test_harvest_inserts_then_list_returns_media(db, monkeypatch):
    page = {
        "configured": True,
        "messages": [
            _msg("m1", videos=[{"url": "https://m.groupme.com/a.mp4", "preview_url": None}], likes=5),
            _msg("m2", images=["https://i.groupme.com/pic1"], text="net eagle"),
            _msg("m3"),
        ],
    }
    monkeypatch.setattr(
        league_media_service,
        "get_messages",
        lambda **kwargs: page if kwargs.get("before_id") is None else {"configured": True, "messages": []},
    )

    result = league_media_service.harvest_media(db)
    assert result["status"] == "ok"
    assert result["inserted"] == 2

    videos = league_media_service.list_media(db, kind="video")
    assert videos["total"] == 1
    assert videos["media"][0]["url"] == "https://m.groupme.com/a.mp4"
    assert videos["media"][0]["likes"] == 5


def test_harvest_idempotent_refreshes_likes(db, monkeypatch):
    video = [{"url": "https://m.groupme.com/a.mp4", "preview_url": None}]
    calls = {"n": 0}

    def fake_get_messages(**kwargs):
        calls["n"] += 1
        if kwargs.get("before_id") is not None:
            return {"configured": True, "messages": []}
        likes = 2 if calls["n"] == 1 else 9
        return {"configured": True, "messages": [_msg("m1", videos=video, likes=likes)]}

    monkeypatch.setattr(league_media_service, "get_messages", fake_get_messages)

    first = league_media_service.harvest_media(db)
    second = league_media_service.harvest_media(db)
    assert first["inserted"] == 1
    assert second["inserted"] == 0
    assert second["updated"] >= 1
    assert league_media_service.list_media(db, kind="video")["media"][0]["likes"] == 9
    assert db.query(LivSowMedia).count() == 1


def test_harvest_skips_when_unconfigured(db, monkeypatch):
    monkeypatch.setattr(
        league_media_service,
        "get_messages",
        lambda **kwargs: {"configured": False, "messages": []},
    )
    assert league_media_service.harvest_media(db) == {
        "status": "skipped",
        "reason": "not_configured",
    }

"""Tests for badge routes — /available previously 500'd on func.case misuse."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_available_badges_returns_200():
    resp = client.get("/api/badges/available")
    assert resp.status_code == 200
    body = resp.json()
    assert isinstance(body, list)
    # seeded badges exist and carry the emoji field that drifted in prod
    if body:
        assert "emoji" in body[0]


def test_available_badges_rarity_filter():
    resp = client.get("/api/badges/available?rarity=legendary")
    assert resp.status_code == 200
    assert all(b["rarity"] == "legendary" for b in resp.json())


def test_earned_badges_empty_for_unknown_player():
    resp = client.get("/api/badges/player/999999/earned")
    assert resp.status_code == 200
    assert resp.json() == []

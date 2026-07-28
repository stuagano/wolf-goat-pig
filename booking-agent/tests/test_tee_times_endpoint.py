from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from app.config import get_settings
from app.main import app
from app.tee_sheet import ForeteesAuthError, ForeteesSheetError

AUTH_HEADERS = {"Authorization": "Bearer test-secret"}
TEE_TIMES_PAYLOAD = {"username": "u", "password": "p", "date": "2026-07-28"}


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("BOOKING_SERVICE_SECRET", "test-secret")

    get_settings.cache_clear()
    with TestClient(app) as c:
        yield c
    get_settings.cache_clear()


def test_tee_times_unauthorized(client):
    resp = client.post(
        "/tee-times",
        json=TEE_TIMES_PAYLOAD,
    )
    assert resp.status_code == 401


def test_tee_times_missing_creds(client):
    resp = client.post(
        "/tee-times",
        headers=AUTH_HEADERS,
        json={**TEE_TIMES_PAYLOAD, "username": ""},
    )
    assert resp.status_code == 400


def test_tee_times_missing_date(client):
    resp = client.post(
        "/tee-times",
        headers=AUTH_HEADERS,
        json={**TEE_TIMES_PAYLOAD, "date": " "},
    )
    assert resp.status_code == 400


def test_tee_times_ok(client):
    slots = [
        {
            "date": "2026-07-28",
            "time": "11:00 AM",
            "front_back": "F",
            "players": [{"name": "Jane D", "transport": "WLK"}],
            "open_slots": 3,
            "max_players": 4,
            "ttdata": "abc",
            "jump": 7,
            "p5_allowed": False,
        }
    ]
    with patch("app.main.fetch_tee_times", new=AsyncMock(return_value=slots)):
        resp = client.post(
            "/tee-times",
            headers=AUTH_HEADERS,
            json=TEE_TIMES_PAYLOAD,
        )
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["date"] == "2026-07-28"
    assert body["slots"] == slots


def test_tee_times_strips_username_and_date(client):
    slots = []
    fetch_mock = AsyncMock(return_value=slots)
    with patch("app.main.fetch_tee_times", new=fetch_mock):
        resp = client.post(
            "/tee-times",
            headers=AUTH_HEADERS,
            json={"username": " u ", "password": "p", "date": " 2026-07-28 "},
        )
    assert resp.status_code == 200
    fetch_mock.assert_awaited_once_with("u", "p", "2026-07-28")
    assert resp.json() == {"status": "ok", "date": "2026-07-28", "slots": slots}


def test_tee_times_value_error_is_400(client):
    with patch(
        "app.main.fetch_tee_times",
        new=AsyncMock(side_effect=ValueError("invalid date")),
    ):
        resp = client.post(
            "/tee-times",
            headers=AUTH_HEADERS,
            json={**TEE_TIMES_PAYLOAD, "date": "not-a-date"},
        )
    assert resp.status_code == 400


def test_tee_times_auth_failure_is_502(client):
    with patch(
        "app.main.fetch_tee_times",
        new=AsyncMock(side_effect=ForeteesAuthError("no sso")),
    ):
        resp = client.post(
            "/tee-times",
            headers=AUTH_HEADERS,
            json=TEE_TIMES_PAYLOAD,
        )
    assert resp.status_code == 502
    assert resp.json() == {"status": "failed", "error": "foretees_auth_failed"}


def test_tee_times_sheet_failure_is_502(client):
    with patch(
        "app.main.fetch_tee_times",
        new=AsyncMock(side_effect=ForeteesSheetError("sheet unavailable")),
    ):
        resp = client.post(
            "/tee-times",
            headers=AUTH_HEADERS,
            json=TEE_TIMES_PAYLOAD,
        )
    assert resp.status_code == 502
    assert resp.json() == {"status": "failed", "error": "foretees_sheet_failed"}

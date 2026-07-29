from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from app.services.foretees_service import (
    ForeteesTeeTimesError,
    fetch_tee_times_via_booking_agent,
)


@pytest.mark.asyncio
async def test_happy_path_returns_slots(monkeypatch):
    monkeypatch.setenv("BOOKING_SERVICE_URL", "https://booking.test")
    monkeypatch.setenv("BOOKING_SERVICE_SECRET", "sec")

    slots = [{"time": "08:00 AM", "players": [], "open_slots": 4, "max_players": 4}]
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.headers = {"content-type": "application/json"}
    mock_resp.json.return_value = {"status": "ok", "date": "2026-07-29", "slots": slots}

    mock_client = AsyncMock()
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = None
    mock_client.get = AsyncMock(return_value=MagicMock(status_code=200))
    mock_client.post = AsyncMock(return_value=mock_resp)

    with patch("app.services.foretees_service.httpx.AsyncClient", return_value=mock_client):
        result = await fetch_tee_times_via_booking_agent("u", "p", "2026-07-29")
    assert result == slots
    mock_client.post.assert_awaited()
    args, kwargs = mock_client.post.await_args
    assert args[0] == "https://booking.test/tee-times"
    assert kwargs["json"] == {"username": "u", "password": "p", "date": "2026-07-29"}
    assert kwargs["headers"]["Authorization"] == "Bearer sec"


@pytest.mark.asyncio
async def test_agent_auth_failed_raises(monkeypatch):
    monkeypatch.setenv("BOOKING_SERVICE_URL", "https://booking.test")
    monkeypatch.setenv("BOOKING_SERVICE_SECRET", "sec")
    mock_resp = MagicMock()
    mock_resp.status_code = 502
    mock_resp.headers = {"content-type": "application/json"}
    mock_resp.json.return_value = {"status": "failed", "error": "foretees_auth_failed"}

    mock_client = AsyncMock()
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = None
    mock_client.get = AsyncMock(return_value=MagicMock(status_code=200))
    mock_client.post = AsyncMock(return_value=mock_resp)

    with patch("app.services.foretees_service.httpx.AsyncClient", return_value=mock_client):
        with pytest.raises(ForeteesTeeTimesError) as exc:
            await fetch_tee_times_via_booking_agent("u", "p", "2026-07-29")
    assert exc.value.code == "foretees_auth_failed"


@pytest.mark.asyncio
async def test_booking_service_401_raises(monkeypatch):
    monkeypatch.setenv("BOOKING_SERVICE_URL", "https://booking.test")
    monkeypatch.setenv("BOOKING_SERVICE_SECRET", "bad")
    mock_resp = MagicMock()
    mock_resp.status_code = 401
    mock_resp.headers = {"content-type": "application/json"}
    mock_resp.json.return_value = {"detail": "Unauthorized"}

    mock_client = AsyncMock()
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = None
    mock_client.get = AsyncMock(return_value=MagicMock(status_code=200))
    mock_client.post = AsyncMock(return_value=mock_resp)

    with patch("app.services.foretees_service.httpx.AsyncClient", return_value=mock_client):
        with pytest.raises(ForeteesTeeTimesError) as exc:
            await fetch_tee_times_via_booking_agent("u", "p", "2026-07-29")
    assert exc.value.code == "booking_service_auth"


@pytest.mark.asyncio
async def test_timeout_raises(monkeypatch):
    monkeypatch.setenv("BOOKING_SERVICE_URL", "https://booking.test")
    monkeypatch.setenv("BOOKING_SERVICE_SECRET", "sec")
    mock_client = AsyncMock()
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = None
    mock_client.get = AsyncMock(return_value=MagicMock(status_code=200))
    mock_client.post = AsyncMock(side_effect=httpx.TimeoutException("timeout"))

    with patch("app.services.foretees_service.httpx.AsyncClient", return_value=mock_client):
        with pytest.raises(ForeteesTeeTimesError) as exc:
            await fetch_tee_times_via_booking_agent("u", "p", "2026-07-29")
    assert exc.value.code == "booking_service_timeout"

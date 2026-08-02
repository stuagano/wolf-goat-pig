"""Tests for scorecard-agent HTTP client."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from app.services.scorecard_agent_client import scan_via_scorecard_agent


@pytest.mark.asyncio
async def test_scan_via_agent_posts_multipart(monkeypatch):
    monkeypatch.setenv("SCORECARD_SERVICE_URL", "https://scorecard.test")
    monkeypatch.setenv("SCORECARD_SERVICE_SECRET", "sec")

    response = MagicMock()
    response.status_code = 200
    response.headers = {"content-type": "application/json"}
    response.json.return_value = {"players": [], "method": "vertex-agent"}

    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=MagicMock(status_code=200))
    mock_client.post = AsyncMock(return_value=response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    with patch("app.services.scorecard_agent_client.httpx.AsyncClient", return_value=mock_client):
        result = await scan_via_scorecard_agent(b"img", "image/jpeg", ["CK", "SS"])

    assert result["method"] == "vertex-agent"
    mock_client.post.assert_awaited_once()
    call_kwargs = mock_client.post.call_args.kwargs
    assert call_kwargs["headers"]["Authorization"] == "Bearer sec"
    assert call_kwargs["data"]["players"] == json.dumps(["CK", "SS"])


@pytest.mark.asyncio
async def test_scan_via_agent_requires_service_url(monkeypatch):
    monkeypatch.delenv("SCORECARD_SERVICE_URL", raising=False)

    with pytest.raises(ValueError, match="SCORECARD_SERVICE_URL"):
        await scan_via_scorecard_agent(b"img", "image/jpeg")


@pytest.mark.asyncio
async def test_scan_via_agent_maps_422(monkeypatch):
    monkeypatch.setenv("SCORECARD_SERVICE_URL", "https://scorecard.test")

    response = MagicMock()
    response.status_code = 422
    response.headers = {"content-type": "application/json"}
    response.json.return_value = {"detail": "Could not parse scorecard"}

    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=MagicMock(status_code=200))
    mock_client.post = AsyncMock(return_value=response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    with (
        patch("app.services.scorecard_agent_client.httpx.AsyncClient", return_value=mock_client),
        pytest.raises(ValueError, match="Could not parse scorecard"),
    ):
        await scan_via_scorecard_agent(b"img", "image/jpeg")


@pytest.mark.asyncio
async def test_scan_via_agent_timeout(monkeypatch):
    monkeypatch.setenv("SCORECARD_SERVICE_URL", "https://scorecard.test")

    mock_client = AsyncMock()
    mock_client.get = AsyncMock(side_effect=httpx.TimeoutException("slow"))
    mock_client.post = AsyncMock(side_effect=httpx.TimeoutException("slow"))
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    with (
        patch("app.services.scorecard_agent_client.httpx.AsyncClient", return_value=mock_client),
        pytest.raises(ValueError, match="timed out"),
    ):
        await scan_via_scorecard_agent(b"img", "image/jpeg")

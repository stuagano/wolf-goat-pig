"""Tests for scorecard scan provider dispatch."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from app.services.scorecard_scan_dispatcher import dispatch_scorecard_scan


@pytest.mark.asyncio
async def test_dispatch_defaults_to_groq(monkeypatch):
    monkeypatch.delenv("SCORECARD_VISION_PROVIDER", raising=False)

    with patch(
        "app.services.scorecard_scan_service.scan_scorecard",
        new_callable=AsyncMock,
        return_value={"method": "single"},
    ) as mock_groq:
        result = await dispatch_scorecard_scan(b"img", "image/jpeg")

    assert result["method"] == "single"
    mock_groq.assert_awaited_once_with(b"img", "image/jpeg", expected_players=None)


@pytest.mark.asyncio
async def test_dispatch_agent_provider(monkeypatch):
    monkeypatch.setenv("SCORECARD_VISION_PROVIDER", "agent")

    with patch(
        "app.services.scorecard_agent_client.scan_via_scorecard_agent",
        new_callable=AsyncMock,
        return_value={"method": "vertex-agent"},
    ) as mock_agent:
        result = await dispatch_scorecard_scan(b"img", "image/png", ["A", "B"])

    assert result["method"] == "vertex-agent"
    mock_agent.assert_awaited_once_with(b"img", "image/png", ["A", "B"])

"""Unit tests for Commissioner ADK data-chat service."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.commissioner_adk_service import (
    _build_instruction,
    _extract_text,
    run_data_chat_adk,
)


class TestBuildInstruction:
    def test_includes_schema_and_context(self):
        instruction = _build_instruction("## Current Season Leaderboard\n  1. Alice: +10Q")
        assert "legacy_rounds_official" in instruction
        assert "Alice: +10Q" in instruction
        assert "Commissioner Hover Over" in instruction


class TestExtractText:
    def test_returns_empty_when_no_content(self):
        event = MagicMock()
        event.content = None
        assert _extract_text(event) == ""

    def test_joins_text_parts(self):
        part1 = MagicMock(text="Hello ")
        part2 = MagicMock(text="world")
        event = MagicMock()
        event.content = MagicMock(parts=[part1, part2])
        assert _extract_text(event) == "Hello world"


class TestRunDataChatAdk:
    @pytest.mark.asyncio
    async def test_returns_agent_response_and_sql_trace(self, monkeypatch):
        monkeypatch.setenv("GCP_PROJECT_ID", "test-project")
        monkeypatch.setenv("COMMISSIONER_MODEL", "gemini-2.5-flash")

        mock_db = MagicMock()
        final_event = MagicMock()
        final_event.is_final_response.return_value = True
        final_event.content = MagicMock(parts=[MagicMock(text="Steve leads.")])

        async def fake_run_async(**_kwargs):
            yield final_event

        mock_runner = MagicMock()
        mock_runner.run_async = fake_run_async

        with (
            patch("app.services.commissioner_adk_service.Runner", return_value=mock_runner),
            patch("app.services.commissioner_adk_service.InMemorySessionService") as mock_session_cls,
        ):
            mock_session_service = AsyncMock()
            mock_session = MagicMock()
            mock_session.id = "sess-1"
            mock_session_service.create_session = AsyncMock(return_value=mock_session)
            mock_session_cls.return_value = mock_session_service

            result = await run_data_chat_adk(
                mock_db,
                "Who leads?",
                "## Current Season Leaderboard",
            )

        assert result["response"] == "Steve leads."
        assert result["table_data"] is None
        assert result["sql_used"] is None

    @pytest.mark.asyncio
    async def test_raises_when_vertex_project_missing(self, monkeypatch):
        monkeypatch.delenv("GCP_PROJECT_ID", raising=False)
        with pytest.raises(ValueError, match="GCP_PROJECT_ID"):
            await run_data_chat_adk(MagicMock(), "hi", "")

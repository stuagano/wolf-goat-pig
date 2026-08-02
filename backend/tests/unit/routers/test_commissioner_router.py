"""Unit tests for commissioner router — AI-powered rules chat using Vertex Gemini."""

from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


# =============================================================================
# POST /api/commissioner/chat — missing config
# =============================================================================


class TestCommissionerChatNoConfig:
    def test_returns_400_when_vertex_project_missing(self, monkeypatch):
        monkeypatch.setenv("COMMISSIONER_LLM_PROVIDER", "vertex")
        monkeypatch.delenv("GCP_PROJECT_ID", raising=False)
        resp = client.post(
            "/api/commissioner/chat",
            json={"message": "What is the Wolf?"},
        )
        assert resp.status_code == 400
        assert "GCP_PROJECT_ID" in resp.json()["detail"]


# =============================================================================
# POST /api/commissioner/chat — happy path
# =============================================================================


class TestCommissionerChatHappyPath:
    def test_returns_200_with_response(self):
        with patch(
            "app.routers.commissioner.llm_generate",
            new_callable=AsyncMock,
            return_value="The Wolf is the Captain who goes solo.",
        ):
            resp = client.post(
                "/api/commissioner/chat",
                json={"message": "What is the Wolf?"},
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert "response" in data["data"]

    def test_accepts_game_state(self):
        with patch(
            "app.routers.commissioner.llm_generate",
            new_callable=AsyncMock,
            return_value="You are on hole 5.",
        ):
            resp = client.post(
                "/api/commissioner/chat",
                json={
                    "message": "What hole are we on?",
                    "game_state": {
                        "current_hole": 5,
                        "players": [
                            {"name": "Alice", "score": 4},
                            {"name": "Bob", "score": -2},
                        ],
                    },
                },
            )

        assert resp.status_code == 200

    def test_accepts_null_game_state(self):
        with patch(
            "app.routers.commissioner.llm_generate",
            new_callable=AsyncMock,
            return_value="Ask me anything.",
        ):
            resp = client.post(
                "/api/commissioner/chat",
                json={"message": "Hello", "game_state": None},
            )

        assert resp.status_code == 200


# =============================================================================
# POST /api/commissioner/chat — validation errors
# =============================================================================


class TestCommissionerChatValidation:
    def test_returns_422_for_missing_message(self):
        resp = client.post("/api/commissioner/chat", json={})
        assert resp.status_code == 422

    def test_returns_422_for_empty_body(self):
        resp = client.post(
            "/api/commissioner/chat",
            content="not json",
            headers={"Content-Type": "application/json"},
        )
        assert resp.status_code == 422


# =============================================================================
# POST /api/commissioner/chat — LLM errors
# =============================================================================


class TestCommissionerChatApiErrors:
    def test_returns_400_on_llm_error(self):
        with patch(
            "app.routers.commissioner.llm_generate",
            new_callable=AsyncMock,
            side_effect=ValueError("LLM API error: unavailable"),
        ):
            resp = client.post(
                "/api/commissioner/chat",
                json={"message": "What are the rules?"},
            )

        assert resp.status_code == 400
        assert "LLM API error" in resp.json()["detail"]

    def test_returns_400_on_rate_limit_message(self):
        with patch(
            "app.routers.commissioner.llm_generate",
            new_callable=AsyncMock,
            side_effect=ValueError("Commissioner is getting too many questions right now. Try again in a minute."),
        ):
            resp = client.post(
                "/api/commissioner/chat",
                json={"message": "What are the rules?"},
            )

        assert resp.status_code == 400
        assert "too many questions" in resp.json()["detail"].lower()


# =============================================================================
# Internal helpers — _build_game_context
# =============================================================================


class TestBuildGameContext:
    def test_returns_empty_for_none(self):
        from app.routers.commissioner import _build_game_context

        assert _build_game_context(None) == ""

    def test_returns_empty_for_empty_dict(self):
        from app.routers.commissioner import _build_game_context

        assert _build_game_context({}) == ""

    def test_includes_current_hole(self):
        from app.routers.commissioner import _build_game_context

        result = _build_game_context({"current_hole": 7})
        assert "7" in result
        assert "Current hole" in result

    def test_includes_players(self):
        from app.routers.commissioner import _build_game_context

        result = _build_game_context(
            {
                "players": [
                    {"name": "Alice", "score": 4},
                    {"name": "Bob", "score": -2},
                ],
            }
        )
        assert "Alice" in result
        assert "Bob" in result
        assert "+4" in result
        assert "-2" in result

    def test_includes_both_hole_and_players(self):
        from app.routers.commissioner import _build_game_context

        result = _build_game_context(
            {
                "current_hole": 12,
                "players": [{"name": "Charlie", "score": 0}],
            }
        )
        assert "12" in result
        assert "Charlie" in result


# =============================================================================
# Internal helpers — _build_data_context
# =============================================================================


class TestBuildDataContext:
    def test_handles_empty_db(self):
        from app.routers.commissioner import _build_data_context

        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_query.group_by.return_value.order_by.return_value.limit.return_value.all.return_value = []
        mock_query.order_by.return_value.all.return_value = []
        mock_db.query.return_value = mock_query
        result = _build_data_context(mock_db)
        assert isinstance(result, str)

    def test_handles_db_exception_gracefully(self):
        from app.routers.commissioner import _build_data_context

        mock_db = MagicMock()
        mock_db.query.side_effect = Exception("DB connection lost")
        result = _build_data_context(mock_db)
        assert isinstance(result, str)


# =============================================================================
# Schema guidance — club season vs in-app tables
# =============================================================================


class TestDataSchemaGuidance:
    def test_schema_steers_leaderboard_to_legacy_rounds_official(self):
        from app.routers.commissioner import DATA_SCHEMA

        assert "legacy_rounds_official" in DATA_SCHEMA
        assert "ALWAYS use" in DATA_SCHEMA or "Default to" in DATA_SCHEMA
        assert "In-app WGP game aggregates ONLY" in DATA_SCHEMA
        assert "Never use them for the club" in DATA_SCHEMA
        assert "season leaderboard" in DATA_SCHEMA
        assert "determined ONLY by total quarters" in DATA_SCHEMA
        assert "Do not calculate, rank by, or narrate wins" in DATA_SCHEMA

    def test_data_chat_uses_adk_on_vertex(self, monkeypatch):
        """Leaderboard questions route through the ADK agent on Vertex."""
        from app.routers import commissioner as mod

        monkeypatch.setenv("COMMISSIONER_LLM_PROVIDER", "vertex")
        monkeypatch.setenv("GCP_PROJECT_ID", "test-project")

        captured: dict[str, str] = {}

        async def fake_adk(db, question, data_context):
            captured["question"] = question
            captured["data_context"] = data_context
            return {
                "response": "Steve Sutorius leads the season.",
                "table_data": None,
                "sql_used": None,
            }

        with (
            patch(
                "app.services.commissioner_adk_service.run_data_chat_adk",
                side_effect=fake_adk,
            ),
            patch.object(
                mod,
                "_build_data_context",
                return_value="## Current Season Leaderboard\n  1. Steve Sutorius: +3510Q over 123 rounds",
            ),
        ):
            resp = client.post(
                "/api/commissioner/data-chat",
                json={"question": "Who is on the leaderboard?"},
            )

        assert resp.status_code == 200
        assert captured["question"] == "Who is on the leaderboard?"
        assert "Steve Sutorius" in captured["data_context"]
        data = resp.json()["data"]
        assert data["response"] == "Steve Sutorius leads the season."

    def test_data_chat_system_prompt_includes_season_context_and_guidance(self):
        """Groq path still builds the legacy SQL-generation system prompt."""
        from app.routers import commissioner as mod

        captured: dict[str, str] = {}

        async def fake_llm(message: str, system: str) -> str:
            captured["system"] = system
            return "Steve Sutorius leads the season."

        with (
            patch.object(mod, "commissioner_provider", return_value="groq"),
            patch.object(mod, "llm_generate", side_effect=fake_llm),
            patch.object(
                mod,
                "_build_data_context",
                return_value="## Current Season Leaderboard\n  1. Steve Sutorius: +3510Q over 123 rounds",
            ),
        ):
            resp = client.post(
                "/api/commissioner/data-chat",
                json={"question": "Who is on the leaderboard?"},
            )

        assert resp.status_code == 200
        system = captured["system"]
        assert "legacy_rounds_official" in system
        assert "Steve Sutorius" in system
        assert "Default to `legacy_rounds_official`" in system
        assert "Who is leading / leaderboard / standings?" in system
        assert "total quarters is the only ranking metric" in system
        assert "win percentage" in system

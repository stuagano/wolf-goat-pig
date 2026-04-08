"""Unit tests for commissioner router — AI-powered rules chat using Gemini API."""

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


# =============================================================================
# POST /api/commissioner/chat — missing API key
# =============================================================================


class TestCommissionerChatNoApiKey:
    @patch.dict("os.environ", {}, clear=False)
    @patch("app.routers.commissioner.os.getenv", return_value=None)
    def test_returns_400_when_gemini_key_missing(self, mock_getenv):
        resp = client.post(
            "/api/commissioner/chat",
            json={"message": "What is the Wolf?"},
        )
        # The handle_api_errors decorator converts ValueError -> 400
        assert resp.status_code == 400
        assert "GEMINI_API_KEY" in resp.json()["detail"]


# =============================================================================
# POST /api/commissioner/chat — happy path
# =============================================================================


class TestCommissionerChatHappyPath:
    @patch("app.routers.commissioner.os.getenv", return_value="fake-gemini-key")
    @patch("app.routers.commissioner.genai", create=True)
    def test_returns_200_with_response(self, mock_genai_module, mock_getenv):
        # We need to mock the import inside the function
        mock_model = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "The Wolf is the Captain who goes solo."
        mock_model.generate_content.return_value = mock_response

        with patch("app.routers.commissioner.genai", create=True) as mock_genai:
            mock_genai.configure = MagicMock()
            mock_genai.GenerativeModel.return_value = mock_model

            # Also patch the import inside the function
            with patch.dict("sys.modules", {"google.generativeai": mock_genai}):
                resp = client.post(
                    "/api/commissioner/chat",
                    json={"message": "What is the Wolf?"},
                )

        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert "response" in data["data"]

    @patch("app.routers.commissioner.os.getenv", return_value="fake-gemini-key")
    def test_accepts_game_state(self, mock_getenv):
        mock_model = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "You are on hole 5."
        mock_model.generate_content.return_value = mock_response

        mock_genai = MagicMock()
        mock_genai.GenerativeModel.return_value = mock_model

        with patch.dict("sys.modules", {"google.generativeai": mock_genai}):
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

    @patch("app.routers.commissioner.os.getenv", return_value="fake-gemini-key")
    def test_accepts_null_game_state(self, mock_getenv):
        mock_model = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "Ask me anything."
        mock_model.generate_content.return_value = mock_response

        mock_genai = MagicMock()
        mock_genai.GenerativeModel.return_value = mock_model

        with patch.dict("sys.modules", {"google.generativeai": mock_genai}):
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
# POST /api/commissioner/chat — Gemini API errors
# =============================================================================


class TestCommissionerChatApiErrors:
    @patch("app.routers.commissioner.os.getenv", return_value="fake-gemini-key")
    def test_returns_500_on_gemini_error(self, mock_getenv):
        mock_genai = MagicMock()
        mock_model = MagicMock()
        mock_model.generate_content.side_effect = RuntimeError("Gemini quota exceeded")
        mock_genai.GenerativeModel.return_value = mock_model

        with patch.dict("sys.modules", {"google.generativeai": mock_genai}):
            resp = client.post(
                "/api/commissioner/chat",
                json={"message": "What are the rules?"},
            )

        assert resp.status_code == 500


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
        # Make the query chain return empty results
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
        # Should not raise — just returns what it can
        result = _build_data_context(mock_db)
        assert isinstance(result, str)

"""Unit tests for commissioner router — AI-powered rules chat using Groq API."""

from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _groq_response(text: str = "Test response", status_code: int = 200) -> MagicMock:
    """Build a mock httpx.Response shaped like Groq's chat/completions reply."""
    resp = MagicMock()
    resp.status_code = status_code
    resp.headers = {"content-type": "application/json"}
    if status_code == 200:
        resp.json.return_value = {
            "choices": [{"message": {"content": text}}],
        }
    else:
        resp.json.return_value = {"error": {"message": f"HTTP {status_code}"}}
    return resp


def _patched_httpx_client(response: MagicMock) -> MagicMock:
    """Build an AsyncMock httpx.AsyncClient context-manager that returns `response` from .post()."""
    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.post = AsyncMock(return_value=response)
    return mock_client


# =============================================================================
# POST /api/commissioner/chat — missing API key
# =============================================================================


class TestCommissionerChatNoApiKey:
    def test_returns_400_when_groq_key_missing(self):
        # Stub os.getenv at the call site so we don't disturb other env vars
        # (DATABASE_URL etc. are still needed by the test app).
        with patch("app.routers.commissioner.os.getenv", return_value=None):
            resp = client.post(
                "/api/commissioner/chat",
                json={"message": "What is the Wolf?"},
            )
        # handle_api_errors decorator converts ValueError -> 400
        assert resp.status_code == 400
        assert "GROQ_API_KEY" in resp.json()["detail"]


# =============================================================================
# POST /api/commissioner/chat — happy path (Groq httpx mocked)
# =============================================================================


class TestCommissionerChatHappyPath:
    def test_returns_200_with_response(self):
        mock_client = _patched_httpx_client(_groq_response("The Wolf is the Captain who goes solo."))
        with (
            patch.dict("os.environ", {"GROQ_API_KEY": "fake-key"}, clear=False),
            patch("httpx.AsyncClient", return_value=mock_client),
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
        mock_client = _patched_httpx_client(_groq_response("You are on hole 5."))
        with (
            patch.dict("os.environ", {"GROQ_API_KEY": "fake-key"}, clear=False),
            patch("httpx.AsyncClient", return_value=mock_client),
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
        mock_client = _patched_httpx_client(_groq_response("Ask me anything."))
        with (
            patch.dict("os.environ", {"GROQ_API_KEY": "fake-key"}, clear=False),
            patch("httpx.AsyncClient", return_value=mock_client),
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
# POST /api/commissioner/chat — Groq API errors
# =============================================================================


class TestCommissionerChatApiErrors:
    def test_returns_400_on_groq_non_200(self):
        """Non-200 from Groq raises ValueError → handle_api_errors returns 400."""
        mock_client = _patched_httpx_client(_groq_response(status_code=503))
        with (
            patch.dict("os.environ", {"GROQ_API_KEY": "fake-key"}, clear=False),
            patch("httpx.AsyncClient", return_value=mock_client),
        ):
            resp = client.post(
                "/api/commissioner/chat",
                json={"message": "What are the rules?"},
            )

        assert resp.status_code == 400
        assert "LLM API error" in resp.json()["detail"]

    def test_returns_400_on_groq_rate_limit(self):
        """429 from Groq surfaces a friendly user-facing message."""
        mock_client = _patched_httpx_client(_groq_response(status_code=429))
        with (
            patch.dict("os.environ", {"GROQ_API_KEY": "fake-key"}, clear=False),
            patch("httpx.AsyncClient", return_value=mock_client),
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

"""Unit tests for scorecard_scan_service — Groq Vision scorecard extraction."""

from __future__ import annotations

import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.scorecard_scan_service import _compute_per_hole_deltas

# ── _compute_per_hole_deltas ──────────────────────────────────────────────────


class TestComputePerHoleDeltas:
    def test_simple_increasing_running_totals(self):
        totals = [
            {"hole": 1, "value": 4, "is_circled": False},
            {"hole": 2, "value": 8, "is_circled": False},
            {"hole": 3, "value": 12, "is_circled": False},
        ]
        deltas = _compute_per_hole_deltas(totals, num_holes=3)
        assert deltas[0] == {"hole": 1, "quarters": 4}
        assert deltas[1] == {"hole": 2, "quarters": 4}
        assert deltas[2] == {"hole": 3, "quarters": 4}

    def test_circled_values_pre_negated(self):
        """By the time _compute_per_hole_deltas runs, circled values are already negative."""
        totals = [{"hole": 1, "value": -96, "is_circled": True}]
        deltas = _compute_per_hole_deltas(totals, num_holes=1)
        assert deltas[0] == {"hole": 1, "quarters": -96}

    def test_missing_holes_are_carry_overs(self):
        totals = [
            {"hole": 1, "value": 10, "is_circled": False},
            # hole 2 missing → carry-over
            {"hole": 3, "value": 14, "is_circled": False},
        ]
        deltas = _compute_per_hole_deltas(totals, num_holes=3)
        assert deltas[0] == {"hole": 1, "quarters": 10}
        assert deltas[1] == {"hole": 2, "quarters": 0}
        assert deltas[2] == {"hole": 3, "quarters": 4}

    def test_all_carry_overs_after_first_hole(self):
        totals = [{"hole": 1, "value": 20, "is_circled": False}]
        deltas = _compute_per_hole_deltas(totals, num_holes=3)
        assert deltas[0]["quarters"] == 20
        assert deltas[1]["quarters"] == 0
        assert deltas[2]["quarters"] == 0

    def test_value_decrease_produces_negative_delta(self):
        totals = [
            {"hole": 1, "value": 10, "is_circled": False},
            {"hole": 2, "value": 6, "is_circled": False},
        ]
        deltas = _compute_per_hole_deltas(totals, num_holes=2)
        assert deltas[1]["quarters"] == -4

    def test_starts_from_zero(self):
        totals = [{"hole": 1, "value": 96, "is_circled": False}]
        deltas = _compute_per_hole_deltas(totals, num_holes=1)
        assert deltas[0]["quarters"] == 96

    def test_produces_correct_number_of_entries(self):
        totals = [{"hole": 1, "value": 4, "is_circled": False}]
        deltas = _compute_per_hole_deltas(totals, num_holes=18)
        assert len(deltas) == 18

    def test_hole_numbers_sequential(self):
        totals = [{"hole": 1, "value": 4, "is_circled": False}]
        deltas = _compute_per_hole_deltas(totals, num_holes=9)
        assert [d["hole"] for d in deltas] == list(range(1, 10))

    def test_zero_running_total_produces_zero_delta(self):
        totals = [
            {"hole": 1, "value": 0, "is_circled": False},
            {"hole": 2, "value": 0, "is_circled": False},
        ]
        deltas = _compute_per_hole_deltas(totals, num_holes=2)
        assert deltas[0]["quarters"] == 0
        assert deltas[1]["quarters"] == 0

    def test_gano_ground_truth_h1_to_h9(self):
        """Validate against confirmed Stuart Gano running totals from example_001."""
        totals = [
            {"hole": 1, "value": 0, "is_circled": False},
            {"hole": 2, "value": 0, "is_circled": False},
            {"hole": 3, "value": 96, "is_circled": False},
            {"hole": 4, "value": 96, "is_circled": False},
            {"hole": 5, "value": 96, "is_circled": False},
            {"hole": 6, "value": 76, "is_circled": False},
            {"hole": 7, "value": 80, "is_circled": False},
            {"hole": 8, "value": 92, "is_circled": False},
            {"hole": 9, "value": 88, "is_circled": False},
        ]
        deltas = _compute_per_hole_deltas(totals, num_holes=9)
        expected = [0, 0, 96, 0, 0, -20, 4, 12, -4]
        assert [d["quarters"] for d in deltas] == expected

    def test_sum_of_all_deltas_equals_final_running_total(self):
        """Sum of all hole deltas must equal the player's final running total."""
        totals = [
            {"hole": 1, "value": 4, "is_circled": False},
            {"hole": 2, "value": 8, "is_circled": False},
            {"hole": 4, "value": 12, "is_circled": False},  # hole 3 missing
        ]
        deltas = _compute_per_hole_deltas(totals, num_holes=4)
        assert sum(d["quarters"] for d in deltas) == 12  # == last running total


# ── Groq Vision response helpers ─────────────────────────────────────────────


def _groq_response(content: str, status_code: int = 200) -> MagicMock:
    """Build a mock httpx.Response with the given content and status code."""
    resp = MagicMock()
    resp.status_code = status_code
    resp.headers = {"content-type": "application/json"}
    if status_code == 200:
        resp.json.return_value = {
            "choices": [{"message": {"content": content}}],
        }
    else:
        resp.json.return_value = {
            "error": {"message": f"Error {status_code}"},
        }
    return resp


def _run_scan(
    response: MagicMock,
    image_bytes: bytes = b"fake",
    env_overrides: dict | None = None,
) -> dict:
    """Run scan_scorecard synchronously with mocked httpx and Groq env."""
    from app.services.scorecard_scan_service import scan_scorecard

    env = {"GROQ_API_KEY": "fake-groq-key"}
    if env_overrides:
        env.update(env_overrides)

    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.post = AsyncMock(return_value=response)

    with (
        patch.dict("os.environ", env, clear=True),
        patch("app.services.scorecard_scan_service._load_reference_image", return_value=None),
        patch("httpx.AsyncClient", return_value=mock_client),
    ):
        result = asyncio.run(scan_scorecard(image_bytes, "image/jpeg"))

    return result, mock_client


# ── scan_scorecard (Groq Vision mocked) ──────────────────────────────────────


class TestScanScorecardParsing:
    def test_missing_groq_api_key_raises(self):
        """GROQ_API_KEY must be set or scan_scorecard raises ValueError."""
        from app.services.scorecard_scan_service import scan_scorecard

        with patch.dict("os.environ", {}, clear=True), pytest.raises(ValueError, match="GROQ_API_KEY"):
            asyncio.run(scan_scorecard(b"fake", "image/jpeg"))

    def test_result_has_required_keys(self):
        resp = _groq_response('{"players": [], "running_totals": []}')
        result, _ = _run_scan(resp)
        assert "players" in result
        assert "running_totals" in result
        assert "per_hole_quarters" in result

    def test_successful_scan_with_player_data(self):
        """Full round-trip: Groq returns player data, service parses it correctly."""
        groq_json = json.dumps(
            {
                "players": [{"name": "Jeff", "confidence": 0.95}],
                "running_totals": [
                    {"player_index": 0, "hole": 1, "value": 4, "is_circled": False, "confidence": 0.9},
                    {"player_index": 0, "hole": 2, "value": 8, "is_circled": False, "confidence": 0.9},
                ],
            }
        )
        result, _ = _run_scan(_groq_response(groq_json))
        assert len(result["players"]) == 1
        assert result["players"][0]["name"] == "Jeff"
        player_deltas = [d for d in result["per_hole_quarters"] if d["player_index"] == 0]
        assert len(player_deltas) == 18
        assert player_deltas[0]["quarters"] == 4
        assert player_deltas[1]["quarters"] == 4

    def test_circled_value_becomes_negative(self):
        groq_json = json.dumps(
            {
                "players": [{"name": "Jeff", "confidence": 1.0}],
                "running_totals": [
                    {"player_index": 0, "hole": 1, "value": 96, "is_circled": True, "confidence": 1.0},
                ],
            }
        )
        result, _ = _run_scan(_groq_response(groq_json))
        h1 = next(d for d in result["per_hole_quarters"] if d["hole"] == 1)
        assert h1["quarters"] == -96

    def test_uncircled_value_stays_positive(self):
        groq_json = json.dumps(
            {
                "players": [{"name": "Stuart", "confidence": 1.0}],
                "running_totals": [
                    {"player_index": 0, "hole": 1, "value": 96, "is_circled": False, "confidence": 1.0},
                ],
            }
        )
        result, _ = _run_scan(_groq_response(groq_json))
        h1 = next(d for d in result["per_hole_quarters"] if d["hole"] == 1)
        assert h1["quarters"] == 96

    def test_per_hole_quarters_covers_all_18_holes(self):
        groq_json = json.dumps(
            {
                "players": [{"name": "Stuart", "confidence": 1.0}],
                "running_totals": [
                    {"player_index": 0, "hole": 1, "value": 4, "is_circled": False, "confidence": 1.0},
                ],
            }
        )
        result, _ = _run_scan(_groq_response(groq_json))
        player_0 = [d for d in result["per_hole_quarters"] if d["player_index"] == 0]
        assert len(player_0) == 18

    def test_empty_players_list(self):
        resp = _groq_response('{"players": [], "running_totals": []}')
        result, _ = _run_scan(resp)
        assert result["players"] == []
        assert result["per_hole_quarters"] == []

    def test_openai_compatible_payload_structure(self):
        """Verify the request payload follows OpenAI vision API format."""
        groq_json = '{"players": [], "running_totals": []}'
        resp = _groq_response(groq_json)
        _, mock_client = _run_scan(resp)

        call_kwargs = mock_client.post.call_args
        url = call_kwargs.args[0] if call_kwargs.args else call_kwargs.kwargs.get("url")
        assert "api.groq.com/openai/v1/chat/completions" in url

        payload = call_kwargs.kwargs.get("json") or call_kwargs[1].get("json")
        assert "model" in payload
        assert "messages" in payload
        assert payload["messages"][0]["role"] == "user"

        # Content should be a list of parts (text + image_url)
        content = payload["messages"][0]["content"]
        assert isinstance(content, list)
        types = {part["type"] for part in content}
        assert "text" in types
        assert "image_url" in types

        # The image_url part should contain a base64 data URI
        image_parts = [p for p in content if p["type"] == "image_url"]
        assert len(image_parts) >= 1
        assert image_parts[-1]["image_url"]["url"].startswith("data:image/jpeg;base64,")

    def test_authorization_header_uses_groq_key(self):
        """Bearer token in the request must come from GROQ_API_KEY."""
        groq_json = '{"players": [], "running_totals": []}'
        resp = _groq_response(groq_json)
        _, mock_client = _run_scan(resp)

        call_kwargs = mock_client.post.call_args
        headers = call_kwargs.kwargs.get("headers") or call_kwargs[1].get("headers")
        assert headers["Authorization"] == "Bearer fake-groq-key"

    # ── Markdown fence stripping ──────────────────────────────────────────────

    def test_markdown_json_fence_stripped(self):
        """Groq sometimes wraps JSON in ```json ... ``` fences."""
        wrapped = '```json\n{"players": [], "running_totals": []}\n```'
        result, _ = _run_scan(_groq_response(wrapped))
        assert result["players"] == []

    def test_markdown_plain_fence_stripped(self):
        """Groq sometimes wraps JSON in ``` ... ``` without a language tag."""
        wrapped = '```\n{"players": [], "running_totals": []}\n```'
        result, _ = _run_scan(_groq_response(wrapped))
        assert result["players"] == []

    # ── Error handling ────────────────────────────────────────────────────────

    def test_rate_limit_429_raises(self):
        """429 from Groq should raise a user-friendly rate-limit message."""
        resp = _groq_response("", status_code=429)
        with pytest.raises(ValueError, match="rate-limited"):
            _run_scan(resp)

    def test_server_error_500_raises(self):
        """500 from Groq should raise with the error message from the body."""
        resp = _groq_response("", status_code=500)
        with pytest.raises(ValueError, match="Vision API error"):
            _run_scan(resp)

    def test_empty_choices_raises(self):
        """If Groq returns an empty choices array, raise ValueError."""
        resp = MagicMock()
        resp.status_code = 200
        resp.headers = {"content-type": "application/json"}
        resp.json.return_value = {"choices": []}

        with pytest.raises(ValueError, match="no choices"):
            _run_scan(resp)

    def test_non_json_response_raises(self):
        """If Groq returns non-JSON text in the content, raise ValueError."""
        resp = _groq_response("Not JSON at all")
        with pytest.raises(ValueError, match="Failed to parse"):
            _run_scan(resp)


# ── Zero-sum within a single player's deltas ─────────────────────────────────


class TestDeltaSumProperty:
    def test_sum_of_deltas_equals_final_running_total_simple(self):
        """For any player, sum(deltas) == last running total value."""
        totals = [
            {"hole": 1, "value": 10, "is_circled": False},
            {"hole": 3, "value": 20, "is_circled": False},  # hole 2 missing
            {"hole": 5, "value": 15, "is_circled": False},  # hole 4 missing, value drops
        ]
        deltas = _compute_per_hole_deltas(totals, num_holes=5)
        assert sum(d["quarters"] for d in deltas) == 15

    def test_negative_running_total_sum(self):
        totals = [{"hole": 1, "value": -96, "is_circled": True}]
        deltas = _compute_per_hole_deltas(totals, num_holes=9)
        assert sum(d["quarters"] for d in deltas) == -96


class TestScanScorecardCallsPreprocessing:
    """scan_scorecard() must run deskew + grid_crop + annotate_circles once each, in order."""

    def test_preprocessing_pipeline_order_and_diagnostics(self, monkeypatch):
        from app.services import scorecard_scan_service as svc

        deskew_calls = {"n": 0}
        grid_calls = {"n": 0}
        annotate_calls = {"n": 0}

        def fake_deskew(image_bytes, content_type):
            deskew_calls["n"] += 1
            assert image_bytes == b"ORIGINAL", "deskew runs on original bytes"
            return b"DESKEWED", "image/jpeg", {"deskew_applied": True, "warped_dimensions": [800, 400]}

        def fake_grid(image_bytes, content_type):
            grid_calls["n"] += 1
            assert image_bytes == b"DESKEWED", "grid_crop must receive deskewed bytes"
            return (
                b"GRID_CROPPED",
                "image/jpeg",
                {
                    "grid_crop_applied": True,
                    "row_lines": [10, 50, 100, 150, 200],
                    "col_lines": [5, 20, 40, 60, 80, 100],
                },
            )

        def fake_annotate(image_bytes, content_type):
            annotate_calls["n"] += 1
            assert image_bytes == b"GRID_CROPPED", "annotate must receive grid-cropped bytes"
            return b"ANNOTATED", "image/jpeg", {"preprocessing_applied": True, "circles_detected": 7}

        async def fake_call_groq(image_bytes, content_type, *, strict=False):
            assert image_bytes == b"ANNOTATED", "vision must receive annotated bytes"
            return {
                "players": [{"name": "P1", "confidence": 1.0}, {"name": "P2", "confidence": 1.0}],
                "running_totals": [
                    {"player_index": 0, "hole": h, "value": 0, "is_circled": False, "confidence": 1.0}
                    for h in range(1, 19)
                ]
                + [
                    {"player_index": 1, "hole": h, "value": 0, "is_circled": False, "confidence": 1.0}
                    for h in range(1, 19)
                ],
            }

        monkeypatch.setattr(svc, "deskew_to_card", fake_deskew)
        monkeypatch.setattr(svc, "crop_to_grid", fake_grid)
        monkeypatch.setattr(svc, "annotate_circles", fake_annotate)
        monkeypatch.setattr(svc, "_call_groq_vision", fake_call_groq)

        result = asyncio.run(svc.scan_scorecard(b"ORIGINAL", "image/jpeg"))

        assert deskew_calls["n"] == 1, "deskew_to_card must run exactly once per scan"
        assert grid_calls["n"] == 1, "crop_to_grid must run exactly once per scan"
        assert annotate_calls["n"] == 1, "annotate_circles must run exactly once per scan"
        assert result["preprocessing"]["deskew"]["deskew_applied"] is True
        assert result["preprocessing"]["grid_crop"]["grid_crop_applied"] is True
        assert result["preprocessing"]["circles"]["preprocessing_applied"] is True
        assert result["preprocessing"]["circles"]["circles_detected"] == 7

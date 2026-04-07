"""Unit tests for scorecard_scan_service — Gemini Vision scorecard extraction."""

from __future__ import annotations

import asyncio
import sys
from types import ModuleType
from unittest.mock import MagicMock, patch

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


# ── scan_scorecard integration (Gemini mocked) ───────────────────────────────

def _make_mock_genai(json_str: str) -> ModuleType:
    """Create a fake google.generativeai module."""
    mock_response = MagicMock()
    mock_response.text = json_str

    mock_model = MagicMock()
    mock_model.generate_content.return_value = mock_response

    mock_genai = MagicMock()
    mock_genai.GenerativeModel.return_value = mock_model
    return mock_genai, mock_model


def _run_scan(json_str: str, image_bytes: bytes = b"fake"):
    """Run scan_scorecard synchronously with mocked Gemini."""
    from app.services.scorecard_scan_service import scan_scorecard

    mock_genai, mock_model = _make_mock_genai(json_str)

    # Inject fake google.generativeai into sys.modules
    fake_google = MagicMock()
    fake_google.generativeai = mock_genai

    with patch.dict("sys.modules", {
        "google": fake_google,
        "google.generativeai": mock_genai,
    }), patch.dict("os.environ", {"GEMINI_API_KEY": "fake-key"}), \
        patch("app.services.scorecard_scan_service._load_reference_image", return_value=None):
        return asyncio.run(scan_scorecard(image_bytes, "image/jpeg")), mock_model


class TestScanScorecardParsing:
    def test_result_has_required_keys(self):
        result, _ = _run_scan('{"players": [], "running_totals": []}')
        assert "players" in result
        assert "running_totals" in result
        assert "per_hole_quarters" in result

    def test_circled_value_becomes_negative(self):
        gemini_json = """{
            "players": [{"name": "Jeff", "confidence": 1.0}],
            "running_totals": [
                {"player_index": 0, "hole": 1, "value": 96, "is_circled": true, "confidence": 1.0}
            ]
        }"""
        result, _ = _run_scan(gemini_json)
        h1 = next(d for d in result["per_hole_quarters"] if d["hole"] == 1)
        assert h1["quarters"] == -96

    def test_uncircled_value_stays_positive(self):
        gemini_json = """{
            "players": [{"name": "Stuart", "confidence": 1.0}],
            "running_totals": [
                {"player_index": 0, "hole": 1, "value": 96, "is_circled": false, "confidence": 1.0}
            ]
        }"""
        result, _ = _run_scan(gemini_json)
        h1 = next(d for d in result["per_hole_quarters"] if d["hole"] == 1)
        assert h1["quarters"] == 96

    def test_per_hole_quarters_covers_all_18_holes(self):
        gemini_json = """{
            "players": [{"name": "Stuart", "confidence": 1.0}],
            "running_totals": [
                {"player_index": 0, "hole": 1, "value": 4, "is_circled": false, "confidence": 1.0}
            ]
        }"""
        result, _ = _run_scan(gemini_json)
        player_0 = [d for d in result["per_hole_quarters"] if d["player_index"] == 0]
        assert len(player_0) == 18

    def test_markdown_fences_stripped(self):
        wrapped = '```json\n{"players": [], "running_totals": []}\n```'
        result, _ = _run_scan(wrapped)
        assert result["players"] == []

    def test_empty_players_list(self):
        result, _ = _run_scan('{"players": [], "running_totals": []}')
        assert result["players"] == []
        assert result["per_hole_quarters"] == []

    def test_missing_api_key_raises(self):
        from app.services.scorecard_scan_service import scan_scorecard
        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(ValueError, match="GEMINI_API_KEY"):
                asyncio.run(scan_scorecard(b"fake", "image/jpeg"))

    def test_non_json_response_raises_value_error(self):
        from app.services.scorecard_scan_service import scan_scorecard
        mock_genai, _ = _make_mock_genai("Not JSON at all")
        fake_google = MagicMock()
        fake_google.generativeai = mock_genai
        with patch.dict("sys.modules", {"google": fake_google, "google.generativeai": mock_genai}), \
             patch.dict("os.environ", {"GEMINI_API_KEY": "fake-key"}), \
             patch("app.services.scorecard_scan_service._load_reference_image", return_value=None):
            with pytest.raises(ValueError, match="Failed to parse"):
                asyncio.run(scan_scorecard(b"fake", "image/jpeg"))

    def test_few_shot_contents_include_reference_image(self):
        """When reference image is available it goes into the Gemini contents list."""
        gemini_json = '{"players": [], "running_totals": []}'
        mock_genai, mock_model = _make_mock_genai(gemini_json)
        fake_google = MagicMock()
        fake_google.generativeai = mock_genai
        fake_ref = b"ref-image-bytes"

        with patch.dict("sys.modules", {"google": fake_google, "google.generativeai": mock_genai}), \
             patch.dict("os.environ", {"GEMINI_API_KEY": "fake-key"}), \
             patch("app.services.scorecard_scan_service._load_reference_image",
                   return_value=(fake_ref, "image/jpeg")), \
             patch("app.services.scorecard_scan_service._EXAMPLES_DIR") as mock_dir:
            mock_path = MagicMock()
            mock_path.exists.return_value = True
            mock_path.read_text.return_value = '{"players":[],"running_totals":[]}'
            mock_dir.__truediv__ = lambda s, x: mock_path

            from app.services.scorecard_scan_service import scan_scorecard
            asyncio.run(scan_scorecard(b"new-image", "image/jpeg"))

        call_args = mock_model.generate_content.call_args[0][0]
        assert isinstance(call_args, list)
        ref_parts = [p for p in call_args if isinstance(p, dict) and p.get("data") == fake_ref]
        assert len(ref_parts) >= 1


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

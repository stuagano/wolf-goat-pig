"""Unit tests for scorecard router — upload and scan scorecard photos."""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


# ── Helper: create a fake image file for upload ─────────────────────────────


def _fake_image_bytes(size_bytes=1024):
    """Create fake image bytes of a given size."""
    return b"\x89PNG\r\n\x1a\n" + b"\x00" * (size_bytes - 8)


# ── POST /scorecard/scan ───────────────────────────────────────────────────


class TestScanScorecard:
    def test_scan_missing_file_returns_422(self):
        resp = client.post("/scorecard/scan")
        assert resp.status_code == 422

    def test_scan_unsupported_content_type_returns_400(self):
        resp = client.post(
            "/scorecard/scan",
            files={"file": ("scorecard.pdf", b"fake-pdf-content", "application/pdf")},
        )
        assert resp.status_code == 400
        assert "Unsupported image type" in resp.json()["detail"]

    def test_scan_unsupported_gif_returns_400(self):
        resp = client.post(
            "/scorecard/scan",
            files={"file": ("scorecard.gif", b"GIF89a", "image/gif")},
        )
        assert resp.status_code == 400

    def test_scan_unsupported_svg_returns_400(self):
        resp = client.post(
            "/scorecard/scan",
            files={"file": ("scorecard.svg", b"<svg></svg>", "image/svg+xml")},
        )
        assert resp.status_code == 400

    def test_scan_image_too_large_returns_400(self):
        # 21MB exceeds the 20MB limit
        large_image = _fake_image_bytes(21 * 1024 * 1024)
        resp = client.post(
            "/scorecard/scan",
            files={"file": ("big.jpg", large_image, "image/jpeg")},
        )
        assert resp.status_code == 400
        assert "too large" in resp.json()["detail"]

    @patch("app.services.scorecard_scan_service.scan_scorecard", new_callable=AsyncMock)
    def test_scan_valid_jpeg_calls_service(self, mock_scan):
        mock_scan.return_value = {
            "players": [{"name": "Alice", "running_totals": [1, 2, 3]}],
            "holes_detected": 9,
        }
        image_data = _fake_image_bytes(2048)
        resp = client.post(
            "/scorecard/scan",
            files={"file": ("scorecard.jpg", image_data, "image/jpeg")},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "players" in data
        mock_scan.assert_called_once()

    @patch("app.services.scorecard_scan_service.scan_scorecard", new_callable=AsyncMock)
    def test_scan_valid_png_accepted(self, mock_scan):
        mock_scan.return_value = {"players": [], "holes_detected": 0}
        image_data = _fake_image_bytes(1024)
        resp = client.post(
            "/scorecard/scan",
            files={"file": ("scorecard.png", image_data, "image/png")},
        )
        assert resp.status_code == 200

    @patch("app.services.scorecard_scan_service.scan_scorecard", new_callable=AsyncMock)
    def test_scan_valid_webp_accepted(self, mock_scan):
        mock_scan.return_value = {"players": [], "holes_detected": 0}
        image_data = _fake_image_bytes(1024)
        resp = client.post(
            "/scorecard/scan",
            files={"file": ("scorecard.webp", image_data, "image/webp")},
        )
        assert resp.status_code == 200

    @patch("app.services.scorecard_scan_service.scan_scorecard", new_callable=AsyncMock)
    def test_scan_valid_heic_accepted(self, mock_scan):
        mock_scan.return_value = {"players": [], "holes_detected": 0}
        image_data = _fake_image_bytes(1024)
        resp = client.post(
            "/scorecard/scan",
            files={"file": ("scorecard.heic", image_data, "image/heic")},
        )
        assert resp.status_code == 200

    @patch("app.services.scorecard_scan_service.scan_scorecard", new_callable=AsyncMock)
    def test_scan_service_value_error_returns_422(self, mock_scan):
        mock_scan.side_effect = ValueError("Could not parse scorecard")
        image_data = _fake_image_bytes(1024)
        resp = client.post(
            "/scorecard/scan",
            files={"file": ("scorecard.jpg", image_data, "image/jpeg")},
        )
        assert resp.status_code == 422
        assert "Could not parse scorecard" in resp.json()["detail"]

    @patch("app.services.scorecard_scan_service.scan_scorecard", new_callable=AsyncMock)
    def test_scan_service_generic_error_returns_500(self, mock_scan):
        mock_scan.side_effect = RuntimeError("Gemini API down")
        image_data = _fake_image_bytes(1024)
        resp = client.post(
            "/scorecard/scan",
            files={"file": ("scorecard.jpg", image_data, "image/jpeg")},
        )
        assert resp.status_code == 500
        assert "Scan failed" in resp.json()["detail"]

    @patch("app.services.scorecard_scan_service.scan_scorecard", new_callable=AsyncMock)
    def test_scan_passes_correct_content_type(self, mock_scan):
        mock_scan.return_value = {"players": []}
        image_data = _fake_image_bytes(1024)
        client.post(
            "/scorecard/scan",
            files={"file": ("scorecard.png", image_data, "image/png")},
        )
        # The second argument should be the content type
        call_args = mock_scan.call_args
        assert call_args[0][1] == "image/png"

    @patch("app.services.scorecard_scan_service.scan_scorecard", new_callable=AsyncMock)
    def test_scan_returns_service_result_as_is(self, mock_scan):
        expected = {
            "players": [
                {"name": "Alice", "running_totals": [1, 3, 5, 7]},
                {"name": "Bob", "running_totals": [2, 4, 6, 8]},
            ],
            "holes_detected": 4,
            "deltas": [[1, 2, 2, 2], [2, 2, 2, 2]],
        }
        mock_scan.return_value = expected
        image_data = _fake_image_bytes(1024)
        resp = client.post(
            "/scorecard/scan",
            files={"file": ("card.jpg", image_data, "image/jpeg")},
        )
        assert resp.json() == expected

from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


@patch("app.main.scan_scorecard", new_callable=AsyncMock)
def test_scan_returns_service_result(mock_scan):
    mock_scan.return_value = {
        "players": [{"name": "Alice", "confidence": 0.9}],
        "running_totals": [],
        "per_hole_quarters": [],
        "validation": {"valid": True, "bad_holes": {}},
        "method": "vertex-agent",
    }
    image = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64
    resp = client.post(
        "/scan",
        files={"file": ("card.png", image, "image/png")},
        data={"players": '["Alice"]'},
    )
    assert resp.status_code == 200
    assert resp.json()["method"] == "vertex-agent"
    mock_scan.assert_awaited_once()

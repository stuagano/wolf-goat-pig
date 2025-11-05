# backend/tests/test_betting_events.py
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_create_betting_events():
    game_id = "test-game-123"
    payload = {
        "holeNumber": 5,
        "events": [
            {
                "eventId": "event-1",
                "eventType": "DOUBLE_OFFERED",
                "actor": "Player1",
                "data": {"proposedMultiplier": 2},
                "timestamp": "2025-11-04T10:00:00Z"
            }
        ],
        "clientTimestamp": "2025-11-04T10:00:00Z"
    }

    response = client.post(f"/api/games/{game_id}/betting-events", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert len(data["confirmedEvents"]) == 1
    assert data["confirmedEvents"][0] == "event-1"

def test_invalid_event_type():
    game_id = "test-game-123"
    payload = {
        "holeNumber": 5,
        "events": [
            {
                "eventId": "event-1",
                "eventType": "INVALID_TYPE",
                "actor": "Player1",
                "data": {},
                "timestamp": "2025-11-04T10:00:00Z"
            }
        ],
        "clientTimestamp": "2025-11-04T10:00:00Z"
    }

    response = client.post(f"/api/games/{game_id}/betting-events", json=payload)

    assert response.status_code == 400

"""Unit tests for websocket routes router — game and user WebSocket channels."""

import json

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


# =============================================================================
# GAME WEBSOCKET — /ws/{game_id}
# =============================================================================


class TestGameWebSocket:
    def test_connect_and_receive(self):
        with client.websocket_connect("/ws/test-game-1") as ws:
            ws.send_text("hello")
            data = ws.receive_text()
            assert "test-game-1" in data
            assert "hello" in data

    def test_message_is_broadcast_back(self):
        with client.websocket_connect("/ws/test-game-2") as ws:
            ws.send_text("ping")
            data = ws.receive_text()
            assert data == "Message from client for game test-game-2: ping"

    def test_different_game_ids_are_isolated(self):
        """Two connections on different game_ids should not cross-talk."""
        with client.websocket_connect("/ws/game-a") as ws_a, client.websocket_connect("/ws/game-b") as ws_b:
            ws_a.send_text("from-a")
            msg_a = ws_a.receive_text()
            assert "game-a" in msg_a

            ws_b.send_text("from-b")
            msg_b = ws_b.receive_text()
            assert "game-b" in msg_b

    def test_multiple_messages(self):
        with client.websocket_connect("/ws/multi-msg") as ws:
            for i in range(3):
                ws.send_text(f"msg-{i}")
                data = ws.receive_text()
                assert f"msg-{i}" in data


# =============================================================================
# USER WEBSOCKET — /ws/user/{player_id}
# =============================================================================


class TestUserWebSocket:
    def test_connect_and_pong(self):
        with client.websocket_connect("/ws/user/42") as ws:
            ws.send_text("hello")
            data = ws.receive_text()
            parsed = json.loads(data)
            assert parsed["type"] == "pong"
            assert parsed["data"] == "hello"

    def test_pong_preserves_data(self):
        with client.websocket_connect("/ws/user/99") as ws:
            ws.send_text("test-payload")
            data = ws.receive_text()
            parsed = json.loads(data)
            assert parsed["type"] == "pong"
            assert parsed["data"] == "test-payload"

    def test_multiple_pongs(self):
        with client.websocket_connect("/ws/user/7") as ws:
            for msg in ["a", "b", "c"]:
                ws.send_text(msg)
                data = ws.receive_text()
                parsed = json.loads(data)
                assert parsed["type"] == "pong"
                assert parsed["data"] == msg

    def test_different_player_ids(self):
        """Connections for different player_ids should work independently."""
        with client.websocket_connect("/ws/user/1") as ws1, client.websocket_connect("/ws/user/2") as ws2:
            ws1.send_text("from-1")
            data1 = json.loads(ws1.receive_text())
            assert data1["data"] == "from-1"

            ws2.send_text("from-2")
            data2 = json.loads(ws2.receive_text())
            assert data2["data"] == "from-2"

    def test_json_response_format(self):
        with client.websocket_connect("/ws/user/100") as ws:
            ws.send_text("check-format")
            raw = ws.receive_text()
            parsed = json.loads(raw)
            assert set(parsed.keys()) == {"type", "data"}

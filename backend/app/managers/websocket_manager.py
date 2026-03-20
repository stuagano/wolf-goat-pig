import json
import logging
from typing import Any, Dict, List, Optional

from fastapi import WebSocket

logger = logging.getLogger("app.managers.websocket_manager")


class WebSocketManager:
    """Manages WebSocket connections for both game channels and user channels.

    Supports two types of channels:
    - Game channels (keyed by game_id): for real-time game state updates
    - User channels (keyed by "user:{player_id}"): for personal notifications
    """

    def __init__(self) -> None:
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, channel_id: str) -> None:
        await websocket.accept()
        if channel_id not in self.active_connections:
            self.active_connections[channel_id] = []
        self.active_connections[channel_id].append(websocket)

    def disconnect(self, websocket: WebSocket, channel_id: str) -> None:
        if channel_id in self.active_connections:
            if websocket in self.active_connections[channel_id]:
                self.active_connections[channel_id].remove(websocket)
            # Clean up empty channel
            if not self.active_connections[channel_id]:
                del self.active_connections[channel_id]

    async def broadcast(self, message: str, channel_id: str) -> None:
        if channel_id in self.active_connections:
            dead_connections: List[WebSocket] = []
            for connection in self.active_connections[channel_id]:
                try:
                    await connection.send_text(message)
                except Exception:
                    dead_connections.append(connection)
            # Clean up dead connections
            for dead in dead_connections:
                self.disconnect(dead, channel_id)

    # ========================================================================
    # User-channel helpers for notifications
    # ========================================================================

    @staticmethod
    def user_channel(player_id: int) -> str:
        """Get the channel ID for a user's personal notification channel."""
        return f"user:{player_id}"

    async def connect_user(self, websocket: WebSocket, player_id: int) -> None:
        """Connect a user to their personal notification channel."""
        await self.connect(websocket, self.user_channel(player_id))

    def disconnect_user(self, websocket: WebSocket, player_id: int) -> None:
        """Disconnect a user from their personal notification channel."""
        self.disconnect(websocket, self.user_channel(player_id))

    async def send_to_user(
        self,
        player_id: int,
        notification_type: str,
        data: Optional[Dict[str, Any]] = None,
        message: str = "",
    ) -> bool:
        """Send a notification to a specific user via WebSocket.

        Returns True if the user was connected and message was sent.
        """
        channel = self.user_channel(player_id)
        if channel not in self.active_connections:
            return False

        payload = json.dumps({
            "type": notification_type,
            "message": message,
            "data": data or {},
        })
        await self.broadcast(payload, channel)
        return True

    async def notify_match_found(
        self,
        player_ids: List[int],
        match_data: Dict[str, Any],
    ) -> int:
        """Notify multiple players about a new match found.

        Returns the number of players who were connected and notified.
        """
        count = 0
        for pid in player_ids:
            sent = await self.send_to_user(
                pid,
                notification_type="match_found",
                data=match_data,
                message="A new match has been found!",
            )
            if sent:
                count += 1
        return count

    async def notify_match_update(
        self,
        player_ids: List[int],
        match_id: int,
        update_type: str,
        detail: str = "",
    ) -> int:
        """Notify players about a match status change.

        update_type: match_accepted, match_declined, match_confirmed
        """
        count = 0
        for pid in player_ids:
            sent = await self.send_to_user(
                pid,
                notification_type=update_type,
                data={"match_suggestion_id": match_id},
                message=detail,
            )
            if sent:
                count += 1
        return count


manager = WebSocketManager()

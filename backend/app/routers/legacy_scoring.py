"""
Legacy Scoring Router (DEPRECATED)

In-memory simplified scoring endpoints. Use /games/{game_id}/quarters-only instead.
"""

import logging
import uuid
from typing import Any

from fastapi import APIRouter, HTTPException

from ..simplified_scoring import SimplifiedScoring

logger = logging.getLogger("app.routers.legacy_scoring")

router = APIRouter(prefix="/wgp/simplified", tags=["deprecated"])

# Global simplified scoring instances (keyed by game_id) - in-memory only
simplified_games: dict[str, SimplifiedScoring] = {}


@router.post("/start-game", deprecated=True)
async def start_simplified_game(payload: dict[str, Any]):  # type: ignore
    """
    DEPRECATED: Use POST /games/create then POST /games/{game_id}/quarters-only instead.

    This endpoint stores data in memory only and doesn't persist to database.
    Start a new game with simplified scoring system.
    """
    try:
        game_id = payload.get("game_id", str(uuid.uuid4()))
        players = payload.get("players", [])

        if not players:
            raise HTTPException(status_code=400, detail="Players required")

        simplified_games[game_id] = SimplifiedScoring(players)

        return {
            "success": True,
            "game_id": game_id,
            "message": f"Simplified game started with {len(players)} players",
            "players": simplified_games[game_id].players,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting simplified game: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start game: {e!s}")

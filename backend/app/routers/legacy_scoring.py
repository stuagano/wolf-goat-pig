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

    except Exception as e:
        logger.error(f"Error starting simplified game: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start game: {e!s}")


@router.post("/score-hole", deprecated=True)
async def score_hole_simplified(payload: dict[str, Any]):  # type: ignore
    """
    DEPRECATED: Use POST /games/{game_id}/quarters-only instead.

    Score a hole using the simplified scoring system (in-memory, not persisted).
    """
    try:
        game_id = payload.get("game_id")
        if not game_id or game_id not in simplified_games:
            raise HTTPException(status_code=404, detail="Game not found")

        hole_number = payload.get("hole_number")
        scores = payload.get("scores", {})
        teams = payload.get("teams", {})
        wager = payload.get("wager", 1)

        if not hole_number or not scores:
            raise HTTPException(status_code=400, detail="Hole number and scores required")

        game = simplified_games[game_id]
        result = game.enter_hole_scores(hole_number, scores, teams, wager)

        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])

        return {
            "success": True,
            "hole_result": result,
            "game_summary": game.get_game_summary(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error scoring hole: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to score hole: {e!s}")


@router.get("/{game_id}/status", deprecated=True)
async def get_simplified_game_status(game_id: str):  # type: ignore
    """
    DEPRECATED: Use GET /games/{game_id}/state instead.

    Get current status of a simplified scoring game (in-memory only).
    """
    try:
        if game_id not in simplified_games:
            raise HTTPException(status_code=404, detail="Game not found")

        game = simplified_games[game_id]

        return {
            "game_id": game_id,
            "game_summary": game.get_game_summary(),
            "hole_history": game.get_hole_history(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting game status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get status: {e!s}")


@router.get("/{game_id}/hole-history", deprecated=True)
async def get_simplified_hole_history(game_id: str):  # type: ignore
    """
    DEPRECATED: Use GET /games/{game_id}/state instead.

    Get hole-by-hole history for a simplified scoring game (in-memory only).
    """
    try:
        if game_id not in simplified_games:
            raise HTTPException(status_code=404, detail="Game not found")

        game = simplified_games[game_id]

        return {"game_id": game_id, "hole_history": game.get_hole_history()}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting hole history: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get history: {e!s}")

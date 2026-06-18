"""GHIN-enhanced leaderboard and game result recording."""

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from .. import schemas
from ..database import get_db
from ..services.ghin_service import GHINService
from ..services.player_service import PlayerService

logger = logging.getLogger("app.routers.leaderboard")

router = APIRouter(tags=["leaderboard"])


@router.get("/leaderboard/ghin-enhanced")
def get_ghin_enhanced_leaderboard(  # type: ignore
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Get leaderboard enhanced with stored GHIN handicap data.

    Serves from DB only — no live GHIN API call. Handicaps are refreshed
    daily by the background scheduler (or on-demand via POST /ghin/sync-handicaps).
    """
    try:
        ghin_service = GHINService(db)
        return ghin_service.get_leaderboard_with_ghin_data(limit=limit)

    except Exception as e:
        logger.error(f"Error getting GHIN enhanced leaderboard: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get GHIN enhanced leaderboard: {e!s}")


@router.post("/game-results")
def record_game_result(game_result: schemas.GamePlayerResultCreate, db: Session = Depends(get_db)) -> dict[str, Any]:
    """Record a game result for a player."""
    try:
        player_service = PlayerService(db)
        success = player_service.record_game_result(game_result)

        if not success:
            raise HTTPException(status_code=500, detail="Failed to record game result")

        # Check for achievements
        achievements = player_service.check_and_award_achievements(game_result.player_profile_id, game_result)

        logger.info(f"Recorded game result for player {game_result.player_profile_id}")

        return {
            "message": "Game result recorded successfully",
            "achievements_earned": achievements,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error recording game result: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to record game result: {e!s}")

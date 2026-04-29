"""
Leaderboard Router

Leaderboard rankings, GHIN-enhanced leaderboard, and game result recording.
"""

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session

from .. import schemas
from ..database import get_db
from ..services.ghin_service import GHINService
from ..services.leaderboard_service import get_leaderboard_service
from ..services.player_service import PlayerService

logger = logging.getLogger("app.routers.leaderboard")

router = APIRouter(tags=["leaderboard"])


@router.get("/leaderboard", response_model=list[schemas.LeaderboardEntry])
def get_leaderboard(  # type: ignore
    response: Response,
    limit: int = Query(100, ge=1, le=100),  # Default to 100 to show all players
    sort: str = Query("desc", pattern="^(asc|desc)$"),  # Add sort parameter
    db: Session = Depends(get_db),
):
    """Get the player leaderboard. Uses LeaderboardService for consolidated leaderboard logic."""
    response.headers["Cache-Control"] = "public, max-age=60"
    try:
        # Use LeaderboardService for leaderboard queries
        leaderboard_service = get_leaderboard_service(db)
        leaderboard_type = "total_earnings"  # Default leaderboard type
        leaderboard = leaderboard_service.get_leaderboard(leaderboard_type=leaderboard_type, db=db, limit=limit)

        # Sort by value (the metric returned by the leaderboard service) based on sort parameter
        if sort == "asc":
            leaderboard.sort(key=lambda x: x.get("value", 0))
        else:
            leaderboard.sort(key=lambda x: x.get("value", 0), reverse=True)

        # Convert to schema format
        entries = []
        for i, entry in enumerate(leaderboard, 1):
            total_earnings = (
                entry.get("value", 0) if leaderboard_type == "total_earnings" else entry.get("total_earnings", 0)
            )
            games = entry.get("games_played", 1)
            entries.append(
                schemas.LeaderboardEntry(
                    rank=entry.get("rank", i),
                    player_id=entry.get("player_id"),
                    player_name=entry.get("player_name"),
                    total_earnings=total_earnings,
                    games_played=games,
                    win_percentage=(
                        entry.get("win_percentage", 0) * 100
                        if entry.get("win_percentage", 0) <= 1
                        else entry.get("win_percentage", 0)
                    ),
                    avg_earnings=total_earnings / games if games > 0 else 0,
                    partnership_success=entry.get("partnership_success", 0),
                )
            )

        return entries

    except Exception as e:
        logger.error(f"Error getting leaderboard: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get leaderboard: {e!s}")


@router.get("/leaderboard/{metric}")
def get_leaderboard_by_metric(metric: str, limit: int = Query(10, ge=1, le=100), db: Session = Depends(get_db)):  # type: ignore
    """Get leaderboard sorted by specific metric. Uses LeaderboardService."""
    try:
        # Use LeaderboardService for metric-based leaderboards
        leaderboard_service = get_leaderboard_service(db)

        # Map metric names to leaderboard types
        metric_map = {
            "earnings": "total_earnings",
            "total_earnings": "total_earnings",
            "win_rate": "win_rate",
            "games_played": "games_played",
            "avg_score": "avg_score",
        }

        leaderboard_type = metric_map.get(metric, "total_earnings")
        leaderboard = leaderboard_service.get_leaderboard(leaderboard_type=leaderboard_type, db=db, limit=limit)

        return {
            "metric": metric,
            "leaderboard": leaderboard,
            "total_players": len(leaderboard),
        }

    except Exception as e:
        logger.error(f"Error getting leaderboard by metric {metric}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get leaderboard: {e!s}")


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

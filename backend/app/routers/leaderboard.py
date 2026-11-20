"""GHIN-enhanced leaderboard and game result recording."""

import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..services.ghin_service import GHINService

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

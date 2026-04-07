"""
GHIN Router

GHIN integration endpoints for golfer lookup, handicap sync, and diagnostics.
"""

import logging
import os
from typing import Any

import httpx
from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy.orm import Session

from .. import database
from ..database import get_db

logger = logging.getLogger("app.routers.ghin")

router = APIRouter(prefix="/ghin", tags=["ghin"])


@router.get("/lookup")
async def ghin_lookup(
    last_name: str = Query(..., description="Golfer's last name"),
    first_name: str = Query(None, description="Golfer's first name (optional)"),
    page: int = Query(1),
    per_page: int = Query(10),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Look up golfers by name using GHIN API"""
    try:
        from ..services.ghin_service import GHINService

        # Get GHIN credentials from environment
        email = os.getenv("GHIN_API_USER")
        password = os.getenv("GHIN_API_PASS")
        os.getenv("GHIN_API_STATIC_TOKEN", "ghincom")

        if not email or not password:
            raise HTTPException(
                status_code=500,
                detail="GHIN credentials not configured in environment variables.",
            )

        ghin_service = GHINService(db)
        if not await ghin_service.initialize():
            raise HTTPException(
                status_code=500,
                detail="GHIN service not available. Check credentials and logs.",
            )

        search_results = await ghin_service.search_golfers(last_name, first_name, page, per_page)
        return search_results

    except httpx.HTTPStatusError as e:
        logger.error(f"GHIN API error: {e.response.status_code} - {e.response.text}")
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"GHIN API error: {e.response.status_code} - {e.response.text}",
        )
    except Exception as e:
        logger.error(f"Error in GHIN lookup: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to lookup golfer: {e!s}")


@router.post("/sync-player-handicap/{player_id}", response_model=dict[str, Any])
async def sync_player_ghin_handicap(
    player_id: int = Path(..., description="The ID of the player to sync"),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Sync a specific player's handicap from GHIN."""
    from ..services.ghin_service import GHINService

    logger.info(f"Attempting to sync GHIN handicap for player ID: {player_id}")
    ghin_service = GHINService(db)
    if not await ghin_service.initialize():
        raise HTTPException(
            status_code=500,
            detail="GHIN service not available. Check credentials and logs.",
        )

    synced_data = await ghin_service.sync_player_handicap(player_id)

    if synced_data:
        logger.info(f"Successfully synced handicap for player {player_id}")
        return {
            "status": "success",
            "message": "Handicap synced successfully",
            "data": synced_data,
        }
    logger.error(f"Failed to sync handicap for player {player_id}")
    raise HTTPException(
        status_code=500,
        detail=f"Failed to sync handicap for player {player_id}. Check if player has a GHIN ID and logs for details.",
    )


@router.get("/diagnostic")
def ghin_diagnostic() -> dict[str, Any]:
    """Diagnostic endpoint for GHIN API configuration"""
    email = os.getenv("GHIN_API_USER")
    password = os.getenv("GHIN_API_PASS")
    static_token = os.getenv("GHIN_API_STATIC_TOKEN")

    return {
        "email_configured": bool(email),
        "password_configured": bool(password),
        "static_token_configured": bool(static_token),
        "all_configured": bool(email and password),
        "environment": os.getenv("ENVIRONMENT", "development"),
    }


@router.post("/sync-handicaps")
async def sync_ghin_handicaps():
    """Sync handicaps for all players with GHIN IDs."""
    try:
        db = database.SessionLocal()
        from ..services.ghin_service import GHINService

        ghin_service = GHINService(db)

        # Initialize and check if available
        await ghin_service.initialize()
        if not ghin_service.is_available():
            raise HTTPException(
                status_code=503,
                detail="GHIN service not available. Check configuration.",
            )

        # Sync all player handicaps
        sync_results = await ghin_service.sync_all_players_handicaps()

        return {"message": "GHIN handicap sync completed", "results": sync_results}

    except Exception as e:
        logger.error(f"Error syncing GHIN handicaps: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to sync GHIN handicaps: {e!s}")
    finally:
        db.close()

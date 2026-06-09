"""
GHIN Router

GHIN integration endpoints for golfer lookup, handicap sync, and diagnostics.
"""

import logging
import os
from typing import Any

import httpx
from fastapi import APIRouter, Depends, HTTPException, Path, Query
from pydantic import BaseModel
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


@router.get("/courses")
async def search_courses(
    q: str = Query(..., min_length=2, description="Course name search"),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Search for golf courses by name via GHIN API."""
    from ..services.ghin_service import GHINService

    ghin_service = GHINService(db)
    if not await ghin_service.initialize():
        raise HTTPException(status_code=503, detail="GHIN service not available. Check credentials.")

    try:
        return await ghin_service.search_courses(q)
    except httpx.HTTPStatusError as e:
        logger.error("GHIN course search error: %s", e)
        raise HTTPException(status_code=e.response.status_code, detail=f"GHIN API error: {e.response.text[:200]}")
    except Exception as e:
        logger.error("Course search failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


class GHINScorePost(BaseModel):
    ghin_id: str
    course_id: int
    tee_set_rating_id: int
    gross_score: int
    played_at: str  # YYYY-MM-DD
    number_of_holes: int = 18


@router.post("/post-score")
async def post_score(
    body: GHINScorePost,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Post a score to GHIN."""
    from ..services.ghin_service import GHINService

    ghin_service = GHINService(db)
    if not await ghin_service.initialize():
        raise HTTPException(status_code=503, detail="GHIN service not available. Check credentials.")

    try:
        result = await ghin_service.post_score(
            ghin_id=body.ghin_id,
            course_id=body.course_id,
            tee_set_rating_id=body.tee_set_rating_id,
            gross_score=body.gross_score,
            played_at=body.played_at,
            number_of_holes=body.number_of_holes,
        )
        return {"success": True, "result": result}
    except httpx.HTTPStatusError as e:
        logger.error("GHIN score post error %d: %s", e.response.status_code, e.response.text)
        raise HTTPException(status_code=e.response.status_code, detail=f"GHIN rejected score: {e.response.text[:300]}")
    except Exception as e:
        logger.error("Score post failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/find-players")
async def find_players_on_ghin(
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Search GHIN for all local player profiles that don't yet have a GHIN ID.
    Uses a single authenticated session for all searches."""
    from .. import models
    from ..services.ghin_service import GHINService

    single_names = {"bob", "dave", "mike", "sarah", "scott", "vince", "test user"}

    ghin_service = GHINService(db)
    if not await ghin_service.initialize():
        raise HTTPException(status_code=503, detail="GHIN service not available. Check credentials.")

    players = db.query(models.PlayerProfile).filter(
        models.PlayerProfile.ghin_id.is_(None)
    ).all()

    found = []
    not_found = []
    errors = []

    import asyncio
    for player in players:
        name = (player.name or "").strip()
        if not name or name.lower() in single_names or len(name.split()) < 2:
            continue
        parts = name.split()
        first, last = parts[0], parts[-1]
        try:
            result = await ghin_service.search_golfers(last, first, per_page=5)
            golfers = result.get("golfers", [])
            if golfers:
                found.append({
                    "player_id": player.id,
                    "player_name": name,
                    "matches": [
                        {
                            "ghin_number": g.get("ghin_number") or g.get("id"),
                            "name": f"{g.get('first_name','')} {g.get('last_name','')}".strip(),
                            "club": g.get("club_name", ""),
                            "state": g.get("state", ""),
                            "handicap_index": g.get("handicap_index") or g.get("hi"),
                        }
                        for g in golfers[:3]
                    ],
                })
            else:
                not_found.append({"player_id": player.id, "player_name": name})
            await asyncio.sleep(0.2)
        except Exception as e:
            errors.append({"player_id": player.id, "player_name": name, "error": str(e)})

    return {"found": found, "not_found": not_found, "errors": errors}


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

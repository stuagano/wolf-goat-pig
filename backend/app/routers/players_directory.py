"""Players router — create/list and other static-path /players endpoints.

Included by ``players.router`` before the ``/me`` and ``/{player_id}`` routes so
static paths match first.
"""

import logging
from typing import Any

from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..services.player_service import PlayerService
from ..utils.admin_auth import require_admin
from ..utils.api_helpers import handle_api_errors, require_not_none

logger = logging.getLogger("app.routers.players")

router = APIRouter(prefix="/players", tags=["players"])


# ============================================================================
# Player Profile Create/List Endpoints (no path params)
# ============================================================================


@router.post("", response_model=schemas.PlayerProfileResponse, dependencies=[Depends(require_admin)])
@handle_api_errors(operation_name="create player profile")
def create_player_profile(
    profile: schemas.PlayerProfileCreate, db: Session = Depends(get_db)
) -> schemas.PlayerProfileResponse:
    """Create a new player profile."""
    player_service = PlayerService(db)
    result = player_service.create_player_profile(profile)
    logger.info(f"Created player profile: {result.name}")
    return result


@router.get("", response_model=list[schemas.PublicPlayerProfileResponse])
@handle_api_errors(operation_name="get player profiles")
def get_all_player_profiles(
    response: Response,
    active_only: bool = Query(True, description="Return only active profiles"),
    db: Session = Depends(get_db),
) -> list[schemas.PlayerProfileResponse]:
    """Get all player profiles."""
    response.headers["Cache-Control"] = "public, max-age=60"
    player_service = PlayerService(db)
    profiles = player_service.get_all_player_profiles(active_only=active_only)
    logger.info(f"Retrieved {len(profiles)} player profiles")
    return profiles


# ============================================================================
# Player Search Endpoints (static paths - must be before /{player_id})
# ============================================================================


@router.get("/all", response_model=list[schemas.PublicPlayerProfileResponse])
@handle_api_errors(operation_name="get all players")
def get_all_players(
    active_only: bool = Query(True, description="Only return active players"),
    db: Session = Depends(get_db),
) -> list[schemas.PlayerProfileResponse]:
    """Get all player profiles."""
    player_service = PlayerService(db)
    return player_service.get_all_player_profiles(active_only=active_only)


@router.get("/name/{player_name}", response_model=schemas.PublicPlayerProfileResponse)
@handle_api_errors(operation_name="get player by name")
def get_player_profile_by_name(player_name: str, db: Session = Depends(get_db)) -> schemas.PlayerProfileResponse:
    """Get a player profile by name."""
    player_service = PlayerService(db)
    profile = player_service.get_player_profile_by_name(player_name)
    return require_not_none(profile, "Player", player_name)


@router.get("/availability/all", response_model=list[dict])
@handle_api_errors(operation_name="get all players availability")
def get_all_players_availability(db: Session = Depends(get_db)) -> list[dict[str, Any]]:
    """Get all players' weekly availability with their names.

    Uses two queries instead of N+1: one for all players, one for all availability records.
    """
    from collections import defaultdict

    players = db.query(models.PlayerProfile).all()
    all_availability = db.query(models.PlayerAvailability).all()

    # Group availability by player_profile_id
    availability_by_player: dict[int, list[models.PlayerAvailability]] = defaultdict(list)
    for avail in all_availability:
        availability_by_player[avail.player_profile_id].append(avail)

    result: list[dict[str, Any]] = []
    for player in players:
        player_data: dict[str, Any] = {
            "player_id": player.id,
            "player_name": player.name,
            "email": player.email,
            "availability": [
                {
                    "day_of_week": avail.day_of_week,
                    "is_available": avail.is_available,
                    "available_from_time": avail.available_from_time,
                    "available_to_time": avail.available_to_time,
                    "notes": avail.notes,
                }
                for avail in availability_by_player.get(player.id, [])
            ],
        }
        result.append(player_data)

    return result

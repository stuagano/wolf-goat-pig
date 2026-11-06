"""Players router — availability and email preferences by ``player_id``."""

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..services.auth_service import get_current_user
from ..utils.admin_auth import is_admin_profile
from ..utils.api_helpers import handle_api_errors, require_not_none
from ..utils.time import utc_now

logger = logging.getLogger("app.routers.players")

router = APIRouter(prefix="/players", tags=["players"])


# ============================================================================
# Player Availability Endpoints (by player_id)
# ============================================================================


@router.get("/{player_id}/availability", response_model=list[schemas.PlayerAvailabilityResponse])
@handle_api_errors(operation_name="get player availability")
def get_player_availability(player_id: int, db: Session = Depends(get_db)) -> list[schemas.PlayerAvailabilityResponse]:
    """Get a player's weekly availability."""
    availability = (
        db.query(models.PlayerAvailability)
        .filter(models.PlayerAvailability.player_profile_id == player_id)
        .order_by(models.PlayerAvailability.day_of_week)
        .all()
    )
    return [schemas.PlayerAvailabilityResponse.from_orm(avail) for avail in availability]


def _require_self_or_admin(player_id: int, current_user: models.PlayerProfile) -> None:
    """Only the player themselves, or an admin, may act on a player-scoped record."""
    if current_user.id != player_id and not is_admin_profile(current_user):
        raise HTTPException(status_code=403, detail="You can only change your own settings")


@router.post("/{player_id}/availability", response_model=schemas.PlayerAvailabilityResponse)
@handle_api_errors(operation_name="set player availability")
def set_player_availability(
    player_id: int,
    availability: schemas.PlayerAvailabilityCreate,
    db: Session = Depends(get_db),
    current_user: models.PlayerProfile = Depends(get_current_user),
) -> schemas.PlayerAvailabilityResponse:
    """Set or update a player's availability for a specific day."""
    _require_self_or_admin(player_id, current_user)
    existing = (
        db.query(models.PlayerAvailability)
        .filter(
            models.PlayerAvailability.player_profile_id == player_id,
            models.PlayerAvailability.day_of_week == availability.day_of_week,
        )
        .first()
    )

    now = utc_now().isoformat()

    if existing:
        existing.available_from_time = availability.available_from_time  # type: ignore
        existing.available_to_time = availability.available_to_time  # type: ignore
        existing.is_available = int(availability.is_available)  # type: ignore
        existing.notes = availability.notes  # type: ignore
        existing.updated_at = now  # type: ignore
        db.commit()
        db.refresh(existing)
        logger.info(f"Updated availability for player {player_id}, day {availability.day_of_week}")
        return schemas.PlayerAvailabilityResponse.from_orm(existing)

    # Create new
    db_availability = models.PlayerAvailability(
        player_profile_id=player_id,
        day_of_week=availability.day_of_week,
        available_from_time=availability.available_from_time,
        available_to_time=availability.available_to_time,
        is_available=int(availability.is_available),
        notes=availability.notes,
        created_at=now,
        updated_at=now,
    )
    db.add(db_availability)
    db.commit()
    db.refresh(db_availability)

    logger.info(f"Created availability for player {player_id}, day {availability.day_of_week}")
    return schemas.PlayerAvailabilityResponse.from_orm(db_availability)


# ============================================================================
# Email Preferences Endpoints (by player_id)
# ============================================================================


@router.get("/{player_id}/email-preferences", response_model=schemas.EmailPreferencesResponse)
@handle_api_errors(operation_name="get email preferences")
def get_email_preferences(
    player_id: int,
    db: Session = Depends(get_db),
    current_user: models.PlayerProfile = Depends(get_current_user),
) -> schemas.EmailPreferencesResponse:
    """Get a player's email preferences."""
    _require_self_or_admin(player_id, current_user)
    now = utc_now().isoformat()

    preferences = (
        db.query(models.EmailPreferences).filter(models.EmailPreferences.player_profile_id == player_id).first()
    )

    if not preferences:
        preferences = models.EmailPreferences(player_profile_id=player_id, created_at=now, updated_at=now)
        db.add(preferences)
        db.commit()
        db.refresh(preferences)

    return schemas.EmailPreferencesResponse.from_orm(preferences)


@router.put("/{player_id}/email-preferences", response_model=schemas.EmailPreferencesResponse)
@handle_api_errors(operation_name="update email preferences")
def update_email_preferences(
    player_id: int,
    preferences_update: schemas.EmailPreferencesUpdate,
    db: Session = Depends(get_db),
    current_user: models.PlayerProfile = Depends(get_current_user),
) -> schemas.EmailPreferencesResponse:
    """Update a player's email preferences."""
    _require_self_or_admin(player_id, current_user)
    preferences_result = (
        db.query(models.EmailPreferences).filter(models.EmailPreferences.player_profile_id == player_id).first()
    )

    preferences = require_not_none(preferences_result, "Email preferences for player", player_id)

    # Update fields that are provided
    update_data = preferences_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        if hasattr(preferences, field):
            setattr(preferences, field, value)

    preferences.updated_at = utc_now().isoformat()  # type: ignore
    db.commit()
    db.refresh(preferences)

    logger.info(f"Updated email preferences for player {player_id}")
    return schemas.EmailPreferencesResponse.from_orm(preferences)

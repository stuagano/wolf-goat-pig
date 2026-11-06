"""Players router — current-user (``/players/me``) endpoints.

Included by ``players.router`` before the ``/{player_id}`` routes.
"""

import base64
import logging
from typing import Any, cast

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..services import account_claim_service, media_storage_service
from ..services.auth_service import get_current_auth0_user, get_current_user
from ..services.legacy_player_service import (
    find_unclaimed_similar_players,
    get_canonical_name,
    link_profile_to_canonical_name,
)
from ..utils.admin_auth import admin_role
from ..utils.api_helpers import handle_api_errors
from ..utils.time import utc_now
from .players_avatar import (
    AVATAR_ALLOWED_TYPES,
    AVATAR_MAX_UPLOAD_BYTES,
    _downscale_avatar_jpeg,
)

logger = logging.getLogger("app.routers.players")

router = APIRouter(prefix="/players", tags=["players"])


# ============================================================================
# Current User Endpoints (/me) - must be before /{player_id}
# ============================================================================


@router.get("/me", response_model=schemas.PlayerProfileResponse)
@handle_api_errors(operation_name="get my profile")
async def get_my_profile(
    current_user: models.PlayerProfile = Depends(get_current_user),
    auth0_user: dict[str, Any] = Depends(get_current_auth0_user),
    db: Session = Depends(get_db),
) -> schemas.PlayerProfileResponse:
    """Get current authenticated user's profile.

    Adds two computed fields not stored on the row:
    - ``legacy_name_suggestion``: when the account has no confirmed legacy link,
      a fuzzy roster match to *suggest* (never auto-persist) in onboarding (#322).
    - authorization role: derived from the verified Auth0 login email claim
      and the server-side super-admin allowlist (never the DB profile email).
    """
    profile = schemas.PlayerProfileResponse.model_validate(current_user)

    if not current_user.legacy_name:
        suggestions = find_unclaimed_similar_players(
            cast("str", current_user.name),
            cast("int", current_user.id),
            max_results=1,
            db=db,
        )
        profile.legacy_name_suggestion = suggestions[0] if suggestions else None

    profile.role = admin_role(db, auth0_user)
    profile.is_super_admin = profile.role == "super_admin"
    profile.is_admin = profile.role != "normal"
    claim = account_claim_service.pending_claim_for(db, cast("int", current_user.id))
    profile.pending_claim = (
        schemas.PendingClaimInfo(canonical_name=claim.canonical_name, created_at=claim.created_at) if claim else None
    )
    return profile


@router.put(
    "/me/legacy-name",
    response_model=schemas.PlayerProfileResponse,
    responses={202: {"description": "Name belongs to an original profile with no login; a claim was sent to admins"}},
)
@handle_api_errors(operation_name="update my legacy name")
async def update_my_legacy_name(
    legacy_name_update: dict[str, str | None],
    current_user: models.PlayerProfile = Depends(get_current_user),
    auth0_user: dict[str, Any] = Depends(get_current_auth0_user),
    db: Session = Depends(get_db),
) -> schemas.PlayerProfileResponse:
    """
    Update current user's legacy name for tee sheet sync.

    The legacy_name must match a player in the thousand-cranes.com tee sheet system.
    """
    legacy_name = legacy_name_update.get("legacy_name")

    if legacy_name:
        # Validate against legacy player list
        canonical = get_canonical_name(legacy_name, db)
        if not canonical:
            raise HTTPException(
                status_code=400,
                detail=f"'{legacy_name}' is not a valid legacy player name. Use /legacy-players to see valid names.",
            )
        link_result = link_profile_to_canonical_name(
            db,
            cast("int", current_user.id),
            canonical,
            allow_relink=True,
        )
        if not link_result["linked"]:
            if link_result["status"] == "claimed":
                outcome = account_claim_service.request_claim_for_name(
                    db,
                    current_user,
                    canonical,
                    email=((auth0_user.get("email") or current_user.email or "").strip().lower() or None),
                    email_verified=auth0_user.get("email_verified"),
                )
                if outcome["status"] == "unverified":
                    raise HTTPException(
                        status_code=403,
                        detail="Verify your email address, then pick your name again so a club admin can connect you.",
                    )
                if outcome["status"] == "pending":
                    claim = outcome["claim"]
                    db.commit()
                    if outcome["created"]:
                        account_claim_service.notify_admins_of_claim(canonical, claim.requester_email)
                    return JSONResponse(
                        status_code=202,
                        content={
                            "status": "claim_pending",
                            "canonical_name": canonical,
                            "message": "Request sent — a club admin will connect you to your history.",
                        },
                    )
                raise HTTPException(
                    status_code=409,
                    detail=f"'{canonical}' already has a player profile. Ask a club admin to connect your sign-in to that player in Account links.",
                )
            raise HTTPException(status_code=400, detail="Could not link this club player.")
        legacy_name = canonical
    else:
        current_user.legacy_name = None
        current_user.updated_at = utc_now().isoformat()

    stale_claim = account_claim_service.pending_claim_for(db, cast("int", current_user.id))
    if stale_claim:
        stale_claim.status = "dismissed"
        stale_claim.resolved_at = utc_now().isoformat()
        stale_claim.resolved_by = "superseded"

    db.commit()
    db.refresh(current_user)

    logger.info(f"Updated legacy_name for user {current_user.id} to '{legacy_name}'")
    return schemas.PlayerProfileResponse.model_validate(current_user)


@router.put("/me/venmo")
@handle_api_errors(operation_name="update venmo handle")
async def update_my_venmo(
    body: dict[str, str | None],
    current_user: models.PlayerProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update current user's Venmo handle."""
    handle = (body.get("venmo_handle") or "").strip()
    # Normalize: ensure @ prefix
    if handle and not handle.startswith("@"):
        handle = f"@{handle}"
    current_user.venmo_handle = handle or None
    current_user.updated_at = utc_now().isoformat()
    db.commit()
    db.refresh(current_user)
    logger.info("Updated venmo_handle for user %s to '%s'", current_user.id, handle)
    return schemas.PlayerProfileResponse.model_validate(current_user)


@router.put("/me/description")
@handle_api_errors(operation_name="update description")
async def update_my_description(
    body: dict[str, str | None],
    current_user: models.PlayerProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update current user's profile description/bio."""
    description = (body.get("description") or "").strip() or None
    current_user.description = description
    current_user.updated_at = utc_now().isoformat()
    db.commit()
    db.refresh(current_user)
    return {"description": current_user.description}


@router.post("/me/avatar")
@handle_api_errors(operation_name="upload avatar")
async def upload_my_avatar(
    file: UploadFile = File(...),
    current_user: models.PlayerProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Upload a profile photo. Stored in GCS when MEDIA_BUCKET is set, else DB blob."""
    content_type = file.content_type or "image/jpeg"
    if content_type not in AVATAR_ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail=f"Unsupported image type: {content_type}. Use JPEG, PNG, or WebP.")

    image_bytes = await file.read()
    if len(image_bytes) > AVATAR_MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=400, detail="Image too large. Maximum size is 8MB.")

    try:
        jpeg_bytes = _downscale_avatar_jpeg(image_bytes)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not read image: {e}") from e

    if media_storage_service.is_enabled():
        object_path = media_storage_service.avatar_object_path(current_user.id)
        try:
            media_storage_service.upload_bytes(object_path, jpeg_bytes, content_type="image/jpeg")
        except Exception as e:
            logger.exception("GCS avatar upload failed for player %s", current_user.id)
            raise HTTPException(status_code=502, detail=f"Could not store avatar: {e}") from e
        current_user.avatar_url = media_storage_service.avatar_gcs_marker(current_user.id)
        current_user.avatar_image = None
    else:
        current_user.avatar_image = base64.b64encode(jpeg_bytes).decode("ascii")

    current_user.updated_at = utc_now().isoformat()
    db.commit()
    db.refresh(current_user)
    logger.info(f"Updated avatar for user {current_user.id}")
    return {"has_avatar_image": True, "updated_at": current_user.updated_at}


@router.get("/me/availability", response_model=list[schemas.PlayerAvailabilityResponse])
@handle_api_errors(operation_name="get my availability")
async def get_my_availability(
    current_user: models.PlayerProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[schemas.PlayerAvailabilityResponse]:
    """Get current user's weekly availability."""
    availability = (
        db.query(models.PlayerAvailability).filter(models.PlayerAvailability.player_profile_id == current_user.id).all()
    )
    return [schemas.PlayerAvailabilityResponse.from_orm(a) for a in availability]


@router.post("/me/availability", response_model=schemas.PlayerAvailabilityWithMatchesResponse)
@handle_api_errors(operation_name="set my availability")
async def set_my_availability(
    availability: schemas.PlayerAvailabilityCreate,
    current_user: models.PlayerProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> schemas.PlayerAvailabilityWithMatchesResponse:
    """Set or update current user's availability for a specific day.

    After saving, automatically runs matchmaking to find compatible groups
    and notifies matched players.
    """
    from .matchmaking import run_matchmaking_for_player

    # Override the player_profile_id with the current user's ID
    availability.player_profile_id = cast("int", current_user.id)

    existing = (
        db.query(models.PlayerAvailability)
        .filter(
            models.PlayerAvailability.player_profile_id == current_user.id,
            models.PlayerAvailability.day_of_week == availability.day_of_week,
        )
        .first()
    )

    now = utc_now().isoformat()

    if existing:
        existing.available_from_time = availability.available_from_time
        existing.available_to_time = availability.available_to_time
        existing.is_available = availability.is_available
        existing.notes = availability.notes
        existing.updated_at = now
        db.commit()
        db.refresh(existing)
        logger.info(f"Updated availability for user {current_user.id}, day {availability.day_of_week}")
        avail_response = schemas.PlayerAvailabilityResponse.from_orm(existing)
    else:
        # Create new
        db_availability = models.PlayerAvailability(
            player_profile_id=current_user.id,
            day_of_week=availability.day_of_week,
            available_from_time=availability.available_from_time,
            available_to_time=availability.available_to_time,
            is_available=availability.is_available,
            notes=availability.notes,
            created_at=now,
            updated_at=now,
        )
        db.add(db_availability)
        db.commit()
        db.refresh(db_availability)
        logger.info(f"Created availability for user {current_user.id}, day {availability.day_of_week}")
        avail_response = schemas.PlayerAvailabilityResponse.from_orm(db_availability)

    # Auto-trigger matchmaking if user is marking themselves available
    new_matches: list[dict] = []
    matches_notified = 0
    if availability.is_available:
        try:
            new_matches = run_matchmaking_for_player(
                player_id=cast("int", current_user.id),
                db=db,
            )
            matches_notified = sum(m.get("notifications_sent", 0) for m in new_matches)
            if new_matches:
                logger.info(
                    f"Auto-matchmaking for user {current_user.id}: "
                    f"found {len(new_matches)} new matches, "
                    f"notified {matches_notified} players"
                )
        except Exception as e:
            # Don't fail the availability save if matchmaking has an error
            logger.error(f"Auto-matchmaking error for user {current_user.id}: {e}")

    return schemas.PlayerAvailabilityWithMatchesResponse(
        availability=avail_response,
        new_matches=new_matches,
        matches_notified=matches_notified,
    )


@router.get("/me/email-preferences", response_model=schemas.EmailPreferencesResponse)
@handle_api_errors(operation_name="get my email preferences")
async def get_my_email_preferences(
    current_user: models.PlayerProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> schemas.EmailPreferencesResponse:
    """Get current user's email preferences."""
    now = utc_now().isoformat()

    prefs = (
        db.query(models.EmailPreferences).filter(models.EmailPreferences.player_profile_id == current_user.id).first()
    )

    if not prefs:
        prefs = models.EmailPreferences(player_profile_id=current_user.id, created_at=now, updated_at=now)
        db.add(prefs)
        db.commit()
        db.refresh(prefs)

    return schemas.EmailPreferencesResponse(
        id=cast("int", prefs.id),
        player_profile_id=cast("int", prefs.player_profile_id),
        daily_signups_enabled=bool(prefs.daily_signups_enabled),
        signup_confirmations_enabled=bool(prefs.signup_confirmations_enabled),
        same_day_signups_enabled=bool(prefs.same_day_signups_enabled),
        signup_reminders_enabled=bool(prefs.signup_reminders_enabled),
        game_invitations_enabled=bool(prefs.game_invitations_enabled),
        weekly_summary_enabled=bool(prefs.weekly_summary_enabled),
        callout_list_enabled=bool(prefs.callout_list_enabled),
        email_frequency=cast("str", prefs.email_frequency),
        preferred_notification_time=cast("str", prefs.preferred_notification_time),
        created_at=cast("str", prefs.created_at),
        updated_at=cast("str", prefs.updated_at),
    )


@router.put("/me/email-preferences", response_model=schemas.EmailPreferencesResponse)
@handle_api_errors(operation_name="update my email preferences")
async def update_my_email_preferences(
    preferences_update: schemas.EmailPreferencesUpdate,
    current_user: models.PlayerProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> schemas.EmailPreferencesResponse:
    """Update current user's email preferences."""
    now = utc_now().isoformat()

    prefs = (
        db.query(models.EmailPreferences).filter(models.EmailPreferences.player_profile_id == current_user.id).first()
    )

    if not prefs:
        prefs = models.EmailPreferences(player_profile_id=current_user.id, created_at=now)
        db.add(prefs)

    update_data = preferences_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        if hasattr(prefs, field):
            # Convert bool to int for SQLite
            if isinstance(value, bool):
                value = 1 if value else 0
            setattr(prefs, field, value)

    prefs.updated_at = now  # type: ignore
    db.commit()
    db.refresh(prefs)

    logger.info(f"Updated email preferences for user {current_user.id}")

    return schemas.EmailPreferencesResponse(
        id=cast("int", prefs.id),
        player_profile_id=cast("int", prefs.player_profile_id),
        daily_signups_enabled=bool(prefs.daily_signups_enabled),
        signup_confirmations_enabled=bool(prefs.signup_confirmations_enabled),
        same_day_signups_enabled=bool(prefs.same_day_signups_enabled),
        signup_reminders_enabled=bool(prefs.signup_reminders_enabled),
        game_invitations_enabled=bool(prefs.game_invitations_enabled),
        weekly_summary_enabled=bool(prefs.weekly_summary_enabled),
        callout_list_enabled=bool(prefs.callout_list_enabled),
        email_frequency=cast("str", prefs.email_frequency),
        preferred_notification_time=cast("str", prefs.preferred_notification_time),
        created_at=cast("str", prefs.created_at),
        updated_at=cast("str", prefs.updated_at),
    )

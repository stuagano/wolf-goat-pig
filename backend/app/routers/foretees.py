"""ForeTees tee time integration router.

Exposes ForeTees tee sheet data and booking endpoints.
All endpoints require Auth0 authentication.
Per-user credentials are stored encrypted in player_profiles.
"""

import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel, field_validator
from sqlalchemy.orm import Session

from .. import models
from ..database import get_db
from ..services.auth_service import get_current_user
from ..services.encryption_service import decrypt, encrypt
from ..services.foretees_service import (
    create_user_foretees_service,
    get_foretees_service,
)
from ..utils.api_helpers import ApiResponse, handle_api_errors

logger = logging.getLogger("app.routers.foretees")

router = APIRouter(prefix="/api/foretees", tags=["foretees"])

VALID_TRANSPORT_MODES = {"WLK", "CRT", "PC"}


# ------------------------------------------------------------------
# Request / Response Models
# ------------------------------------------------------------------

class BookTeeTimeRequest(BaseModel):
    ttdata: str
    transport_mode: str = "WLK"
    date: Optional[str] = None  # YYYY-MM-DD, used for v5 browser booking
    time: Optional[str] = None  # "12:00 PM", used for v5 browser booking

    @field_validator("transport_mode")
    @classmethod
    def validate_transport_mode(cls, v: str) -> str:
        upper = v.upper()
        if upper not in VALID_TRANSPORT_MODES:
            raise ValueError(f"Must be one of: {', '.join(sorted(VALID_TRANSPORT_MODES))}")
        return upper

    @field_validator("ttdata")
    @classmethod
    def validate_ttdata(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("ttdata is required")
        return v.strip()


class CancelTeeTimeRequest(BaseModel):
    date: str   # YYYY-MM-DD
    time: str   # "12:00 PM"


class ForeteesCredentials(BaseModel):
    username: str
    password: str


class ForeteesCredentialsStatus(BaseModel):
    configured: bool
    username: Optional[str] = None


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _get_user_service(player: models.PlayerProfile):
    """Return a ForeteesService for the given player.

    Uses per-user credentials if configured, otherwise falls back to
    the env-var singleton for backwards compatibility.
    """
    if player.foretees_username and player.foretees_password_encrypted:
        try:
            password = decrypt(player.foretees_password_encrypted)
            return create_user_foretees_service(player.foretees_username, password)
        except Exception:
            logger.warning("Failed to decrypt credentials for player %s, falling back to env", player.id)

    return get_foretees_service()


def _mask_username(username: str) -> str:
    """Mask a username for display, e.g. '1453-smith' → '1453-***'."""
    if not username:
        return None
    if "-" in username:
        prefix = username.split("-")[0]
        return f"{prefix}-***"
    if len(username) > 3:
        return username[:3] + "***"
    return "***"


# ------------------------------------------------------------------
# Credential Management Endpoints
# ------------------------------------------------------------------

@router.get("/credentials")
@handle_api_errors(operation_name="get credentials status")
async def get_credentials_status(
    current_user: models.PlayerProfile = Depends(get_current_user),
) -> Dict[str, Any]:
    """Check whether the current user has ForeTees credentials configured."""
    configured = bool(current_user.foretees_username and current_user.foretees_password_encrypted)
    status = ForeteesCredentialsStatus(
        configured=configured,
        username=_mask_username(current_user.foretees_username) if configured else None,
    )
    return ApiResponse.success(data=status.model_dump())


@router.put("/credentials")
@handle_api_errors(operation_name="save credentials")
async def save_credentials(
    creds: ForeteesCredentials,
    current_user: models.PlayerProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Save (and validate) ForeTees credentials for the current user.

    Attempts a ForeTees login to verify the credentials are correct
    before persisting them.
    """
    # Validate by attempting login
    test_service = create_user_foretees_service(creds.username, creds.password)
    try:
        login_ok = await test_service._ensure_session()
    finally:
        await test_service.close()

    if not login_ok:
        raise ValueError("ForeTees login failed. Please check your username and password.")

    # Persist encrypted credentials
    current_user.foretees_username = creds.username
    current_user.foretees_password_encrypted = encrypt(creds.password)
    db.commit()

    logger.info("Saved ForeTees credentials for player %s", current_user.id)
    return ApiResponse.success(
        data={"configured": True, "username": _mask_username(creds.username)},
        message="ForeTees credentials saved and verified",
    )


@router.delete("/credentials")
@handle_api_errors(operation_name="remove credentials")
async def remove_credentials(
    current_user: models.PlayerProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Remove stored ForeTees credentials for the current user."""
    current_user.foretees_username = None
    current_user.foretees_password_encrypted = None
    db.commit()

    logger.info("Removed ForeTees credentials for player %s", current_user.id)
    return ApiResponse.success(message="ForeTees credentials removed")


# ------------------------------------------------------------------
# Tee Time Endpoints (now use per-user credentials)
# ------------------------------------------------------------------

@router.get("/tee-times")
@handle_api_errors(operation_name="get tee times")
async def get_tee_times(
    date: str,
    current_user: models.PlayerProfile = Depends(get_current_user),
) -> Dict[str, Any]:
    """Get available tee times for a given date."""
    service = _get_user_service(current_user)
    if not service.config.enabled:
        return ApiResponse.success(data=[], message="ForeTees integration is disabled")

    try:
        slots = await service.get_tee_times(date)
    finally:
        # Close request-scoped services (singleton is unaffected)
        if service is not get_foretees_service():
            await service.close()

    return ApiResponse.success(
        data=slots,
        message=f"Found {len(slots)} tee time slots for {date}",
    )


@router.get("/bookings")
@handle_api_errors(operation_name="get my bookings")
async def get_my_bookings(
    current_user: models.PlayerProfile = Depends(get_current_user),
) -> Dict[str, Any]:
    """Get the current member's upcoming tee time bookings."""
    service = _get_user_service(current_user)
    if not service.config.enabled:
        return ApiResponse.success(data=[], message="ForeTees integration is disabled")

    try:
        bookings = await service.get_my_tee_times()
    finally:
        if service is not get_foretees_service():
            await service.close()

    return ApiResponse.success(
        data=bookings,
        message=f"Found {len(bookings)} bookings",
    )


@router.post("/book")
@handle_api_errors(operation_name="book tee time")
async def book_tee_time(
    request: BookTeeTimeRequest,
    current_user: models.PlayerProfile = Depends(get_current_user),
) -> Dict[str, Any]:
    """Book the current user into a tee time slot."""
    service = _get_user_service(current_user)
    if not service.config.enabled:
        raise ValueError("ForeTees integration is disabled")

    try:
        result = await service.book_tee_time(
            ttdata=request.ttdata,
            transport_mode=request.transport_mode,
            date=request.date,
            slot_time=request.time,
        )
    finally:
        if service is not get_foretees_service():
            await service.close()

    if result.get("success"):
        return ApiResponse.success(
            data=result,
            message=result["messages"][0] if result.get("messages") else "Booking confirmed",
        )

    # If there's debug info from a form parse failure, return it directly
    if result.get("debug"):
        return ApiResponse.success(data=result, message=result.get("message", "Booking failed"))

    # Build a clear error from title + all messages ForeTees returned
    parts = []
    if result.get("title"):
        parts.append(result["title"])
    for msg in result.get("messages", []):
        if msg and msg != result.get("title"):
            parts.append(msg)
    error_msg = result.get("message") or ". ".join(parts) or "Booking failed"
    raise ValueError(error_msg)


@router.post("/cancel")
@handle_api_errors(operation_name="cancel tee time")
async def cancel_tee_time(
    request: CancelTeeTimeRequest,
    current_user: models.PlayerProfile = Depends(get_current_user),
) -> Dict[str, Any]:
    """Cancel the current user's tee time."""
    service = _get_user_service(current_user)
    if not service.config.enabled:
        raise ValueError("ForeTees integration is disabled")

    try:
        result = await service.cancel_tee_time(
            date=request.date,
            slot_time=request.time,
        )
    finally:
        if service is not get_foretees_service():
            await service.close()

    if result.get("success"):
        return ApiResponse.success(
            data=result,
            message=result["messages"][0] if result.get("messages") else "Tee time cancelled",
        )

    parts = []
    if result.get("title"):
        parts.append(result["title"])
    for msg in result.get("messages", []):
        if msg and msg != result.get("title"):
            parts.append(msg)
    error_msg = result.get("message") or ". ".join(parts) or "Cancellation failed"
    raise ValueError(error_msg)

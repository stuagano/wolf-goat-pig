"""Cancel a signup from the confirmation email without logging in.

The link carries a signed token, not a signup id. GET only previews the
signup so a mail scanner that prefetches the link cannot cancel it. POST is
the confirmation step and uses the same cancellation as DELETE /signups/{id}.
"""

import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from .. import database, models
from ..services.signup_cancel_token import CancelTokenError, read_cancel_token
from .signups import apply_signup_cancellation

logger = logging.getLogger("app.routers.signup_cancel")

router = APIRouter(tags=["signups"])


class SignupCancelPreview(BaseModel):
    player_name: str
    date: str
    status: str
    can_cancel: bool


class SignupCancelResult(BaseModel):
    message: str
    name: str
    date: str
    already_cancelled: bool
    live_write: bool
    legacy_sync: str


def _signup_for_token(db, token: str) -> models.DailySignup:
    try:
        claims = read_cancel_token(token)
    except CancelTokenError as exc:
        if exc.code == "expired":
            raise HTTPException(status_code=410, detail="This cancel link has expired.") from None
        raise HTTPException(status_code=404, detail="This cancel link is not valid.") from None
    signup = db.query(models.DailySignup).filter(models.DailySignup.id == claims.signup_id).first()
    if signup is None or signup.player_profile_id != claims.player_profile_id or signup.date != claims.signup_date:
        raise HTTPException(status_code=404, detail="This cancel link is not valid.")
    return signup


@router.get("/signups/cancel/{token}", response_model=SignupCancelPreview)
def preview_signup_cancellation(token: str):
    """Show whose signup this link would cancel. Does not change anything."""
    db = database.SessionLocal()
    try:
        signup = _signup_for_token(db, token)
        return SignupCancelPreview(
            player_name=signup.player_name or "",
            date=signup.date or "",
            status=signup.status or "",
            can_cancel=signup.status == "signed_up",
        )
    finally:
        db.close()


@router.post("/signups/cancel/{token}", response_model=SignupCancelResult)
def confirm_signup_cancellation(token: str):
    """Cancel the signup this token was issued for, after the player confirms."""
    db = database.SessionLocal()
    try:
        signup = _signup_for_token(db, token)
        if signup.status == "cancelled":
            return SignupCancelResult(
                message="This signup is already cancelled",
                name=signup.player_name or "",
                date=signup.date or "",
                already_cancelled=True,
                live_write=False,
                legacy_sync="skipped",
            )
        result = apply_signup_cancellation(db, signup)
        return SignupCancelResult(
            message=result["message"],
            name=result["name"] or "",
            date=result["date"] or "",
            already_cancelled=False,
            live_write=result["live_write"],
            legacy_sync=result["legacy_sync"],
        )
    except HTTPException:
        raise
    except Exception as exc:
        db.rollback()
        logger.error("Error cancelling signup from email link: %s", exc)
        raise HTTPException(status_code=500, detail="Failed to cancel signup") from None
    finally:
        db.close()

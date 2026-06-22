"""
Callout endpoints — driven by an external scheduler (GitHub Actions cron).

The in-process email scheduler is a no-op in production (a vendored `schedule`
shim never fires jobs), so real scheduled work runs as GitHub Actions cron jobs
that POST to an endpoint — the same pattern as GHIN sync (POST /ghin/sync-handicaps).
This router exposes the headcount callout so a Friday (pre-pairing) and Sunday
(morning-of) cron can fire it. Once-per-window dedup lives in the service.
"""

import logging
from datetime import date, timedelta

from fastapi import APIRouter, Header, HTTPException, Query

from .. import database
from ..services.callout_service import run_callout, run_callout_for_next_sunday
from ..services.email_service import get_email_service
from ..utils.admin_auth import get_admin_emails

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/callouts", tags=["callouts"])

VALID_WINDOWS = ("pre_pairing", "morning_of")


@router.post("/test-email")
async def send_test_callout_email(
    to: str = Query(..., description="Recipient email for the sample callout"),
    x_admin_email: str = Header(default=None),
):
    """Send a sample headcount/matchmaking callout email to one address (admin only).

    Diagnostic for proving the notification path works end-to-end. Does NOT touch
    the opt-in list or the once-per-window dedup table — it just renders and sends
    the real callout template with sample data.
    """
    if not x_admin_email or x_admin_email not in get_admin_emails():
        raise HTTPException(status_code=403, detail="Admin access required")

    email_service = get_email_service()
    if not email_service.is_configured():
        raise HTTPException(status_code=503, detail="Email service not configured")

    sample_date = (date.today() + timedelta(days=3)).isoformat()
    ok = email_service.send_callout_notification(
        to_email=to,
        player_name="Stuart",
        game_date=sample_date,
        signup_count=2,
        needed=2,
    )
    if not ok:
        raise HTTPException(status_code=500, detail="Email provider returned failure")
    return {"sent": True, "to": to, "game_date": sample_date, "template": "callout_notification"}


@router.post("/run")
async def run_headcount_callout(
    window: str = Query(..., description="Callout window: pre_pairing or morning_of"),
    game_date: str | None = Query(
        default=None,
        description="YYYY-MM-DD to evaluate; defaults to the upcoming Sunday",
    ),
):
    """Evaluate the game date and, if short of a full foursome, email the opt-in list.

    Intended to be called by the callout-list GitHub Actions cron. Idempotent
    within a (date, window): a second call in the same window sends nothing.
    """
    if window not in VALID_WINDOWS:
        raise HTTPException(
            status_code=422,
            detail=f"window must be one of {', '.join(VALID_WINDOWS)}",
        )

    db = database.SessionLocal()
    try:
        if game_date:
            result = run_callout(db, game_date, window)
        else:
            result = run_callout_for_next_sunday(db, window)
        return {"message": "Callout check completed", "result": result}
    except Exception as e:
        logger.error(f"Error running headcount callout: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to run callout: {e!s}")
    finally:
        db.close()

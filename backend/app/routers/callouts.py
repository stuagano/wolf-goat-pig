"""
Callout endpoints — driven by an external scheduler (GitHub Actions cron).

The in-process email scheduler is a no-op in production (a vendored `schedule`
shim never fires jobs), so real scheduled work runs as GitHub Actions cron jobs
that POST to an endpoint — the same pattern as GHIN sync (POST /ghin/sync-handicaps).
This router exposes the headcount callout so a Friday (pre-pairing) and Sunday
(morning-of) cron can fire it. Once-per-window dedup lives in the service.
"""

import logging

from fastapi import APIRouter, HTTPException, Query

from .. import database
from ..services.callout_service import run_callout, run_callout_for_next_sunday

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/callouts", tags=["callouts"])

VALID_WINDOWS = ("pre_pairing", "morning_of")


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

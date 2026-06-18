"""Spreadsheet sync ops endpoint — driven by an external scheduler (GitHub Actions cron).

The in-process email scheduler is a no-op in production (a vendored `schedule`
shim never fires jobs), so the nightly drain of the pending sheet-sync queue runs
as a GitHub Actions cron that POSTs here — the same pattern as GHIN sync
(POST /ghin/sync-handicaps) and the headcount callout (POST /callouts/run).

Completed app games are enqueued (POST /admin/spreadsheet/sync-round) into the
pending_sheet_syncs table; this endpoint flushes that queue, writing new/updated
rounds to the WRITABLE copy (19AabC...). Idempotent: dedup against legacy_rounds
means a re-run writes nothing already present.
"""

import logging

from fastapi import APIRouter, HTTPException

from ..services.email_scheduler import email_scheduler

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/spreadsheet", tags=["spreadsheet"])


@router.post("/drain-pending-syncs")
def drain_pending_sheet_syncs():
    """Flush the pending sheet-sync queue to the writable Google Sheet.

    Runs the same drain the (no-op-in-prod) in-process scheduler was meant to run
    nightly. Intended to be called by the sheet-sync-drain GitHub Actions cron.
    Returns a small summary (pending/written/duplicates/failed) of what was flushed.

    A plain (non-async) handler so FastAPI runs the blocking Sheets I/O in a
    threadpool rather than stalling the event loop.
    """
    try:
        summary = email_scheduler._process_pending_sheet_syncs()
        return {"message": "Pending sheet syncs drained", "summary": summary}
    except Exception as e:
        logger.error(f"Error draining pending sheet syncs: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to drain pending sheet syncs: {e!s}")

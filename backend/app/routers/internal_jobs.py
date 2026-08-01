"""Internal job-trigger endpoints for Cloud Scheduler (design doc Phase 4 / §12).

Each in-process `schedule` loop in ``email_scheduler`` also exists here as a
one-shot POST endpoint so that **Cloud Scheduler** can drive the periodic work on
Cloud Run — where the single-long-lived-process assumption behind the in-process
thread does not hold (every autoscaled instance would otherwise run its own copy).

Security: the Cloud Run service is deployed ``--allow-unauthenticated``, so these
endpoints are guarded at the application layer by a shared secret,
``INTERNAL_JOB_TOKEN`` (supplied as the ``X-Internal-Job-Token`` header or a
``?token=`` query param — Cloud Scheduler sends the header). **Fail-closed:** when
the env var is unset every request is rejected, so the endpoints can never be
triggered anonymously.
"""

import logging
import os

from fastapi import APIRouter, Header, HTTPException, Query

from ..services.email_scheduler import EmailScheduler, email_scheduler

logger = logging.getLogger(__name__)

# Hidden from the public OpenAPI schema — these are infra-internal.
router = APIRouter(prefix="/internal/jobs", tags=["internal"], include_in_schema=False)


def _require_job_token(supplied: str | None) -> None:
    """Authorize an internal-job request, or raise. Fail-closed when unset."""
    expected = os.getenv("INTERNAL_JOB_TOKEN")
    if not expected:
        # No token configured → endpoints are disabled (safe default).
        raise HTTPException(status_code=503, detail="internal jobs disabled (INTERNAL_JOB_TOKEN unset)")
    if supplied != expected:
        raise HTTPException(status_code=403, detail="forbidden")


@router.post("/{job}")
def run_internal_job(
    job: str,
    x_internal_job_token: str | None = Header(default=None),
    token: str | None = Query(default=None),
) -> dict:
    """Run a single scheduled job once. See ``EmailScheduler.JOB_METHODS`` for keys."""
    _require_job_token(x_internal_job_token or token)

    if job not in EmailScheduler.JOB_METHODS:
        known = ", ".join(sorted(EmailScheduler.JOB_METHODS))
        raise HTTPException(status_code=404, detail=f"unknown job '{job}'. Known jobs: {known}")

    try:
        return email_scheduler.run_job(job)
    except Exception as exc:  # the target logs its own internals; surface a 500 here
        logger.error("Internal job '%s' failed: %s", job, exc)
        raise HTTPException(status_code=500, detail=f"job '{job}' failed") from exc

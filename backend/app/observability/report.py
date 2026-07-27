"""Report operational failures to Cloud Logging (no third-party error SaaS).

On Cloud Run these land in the project Logs Explorer — any GCP project member
can see them. Call sites that previously used Sentry use these helpers so
swallowed exceptions still leave a durable signal.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger("app.observability.report")


def report_exception(exc: BaseException, *args: Any, **kwargs: Any) -> None:
    """Log an exception with stack trace (Cloud Logging ERROR + stack)."""
    logger.exception("Reported exception: %s", exc, *args, **kwargs)


def report_message(message: str, *, level: str = "error", **kwargs: Any) -> None:
    """Log an operational message (default ERROR so Monitoring can alert on it)."""
    log = getattr(logger, level if level in {"debug", "info", "warning", "error", "critical"} else "error")
    log(message, **kwargs)

"""Bounded request correlation for score writes; never record bodies or exceptions."""

import json
import logging
import re
import uuid
from contextvars import ContextVar

from starlette.datastructures import Headers, MutableHeaders
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Message, Receive, Scope, Send

logger = logging.getLogger(__name__)
_SAFE_REQUEST_ID = re.compile(r"[A-Za-z0-9_-]{8,64}")
# A shared request-local object also carries commit state back from sync endpoints
# running in a worker thread (ContextVar assignments alone don't propagate back).
_context: ContextVar[dict | None] = ContextVar("score_save_context", default=None)


def _emit(event: str, **fields: object) -> None:
    context = _context.get()
    if context is not None:
        logger.info(json.dumps({"event": event, "request_id": context["request_id"], **fields}))


def is_score_save_request() -> bool:
    """Let shared exception handlers avoid logging score payloads."""
    return _context.get() is not None


def log_score_commit() -> None:
    """Call only after the database commit returns, with no ORM attribute access."""
    context = _context.get()
    if context is not None:
        context["committed"] = True
        _emit("score_save_committed")


class ScoreSaveDiagnostics:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if (
            scope["type"] != "http"
            or scope["method"] != "POST"
            or not re.fullmatch(r"/games/[^/]+/scores/?", scope["path"])
        ):
            await self.app(scope, receive, send)
            return

        candidate = Headers(scope=scope).get("X-Request-ID", "")
        request_id = candidate if _SAFE_REQUEST_ID.fullmatch(candidate) else uuid.uuid4().hex
        scope.setdefault("state", {})["score_save_request_id"] = request_id
        token = _context.set({"request_id": request_id, "committed": False})
        reported_failure = False
        response_started = False

        async def correlated_send(message: Message) -> None:
            nonlocal reported_failure, response_started
            if message["type"] == "http.response.start":
                response_started = True
                MutableHeaders(scope=message)["X-Request-ID"] = request_id
                status = message["status"]
                if status >= 400:
                    reported_failure = True
                    _emit("score_save_failed" if status >= 500 else "score_save_rejected", status_code=status)
            await send(message)

        try:
            _emit("score_save_attempt")
            await self.app(scope, receive, correlated_send)
        except Exception:
            if response_started:
                if not reported_failure:
                    _emit("score_save_failed", status_code=500)
                raise
            # Handle pre-response failures here, including authorization DB
            # failures. The outer generic handler would lose correlation and
            # log exception text that can contain SQL parameters. CORS still
            # wraps this response, so browser clients can read the reference.
            response = JSONResponse(status_code=500, content={"detail": "Unable to save scores. Please retry."})
            await response(scope, receive, correlated_send)
        finally:
            _context.reset(token)

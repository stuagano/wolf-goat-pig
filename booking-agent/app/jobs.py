"""In-memory booking jobs (requires Cloud Run session affinity for confirm)."""

from __future__ import annotations

import asyncio
import base64
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from playwright.async_api import Browser, BrowserContext, Page


class JobKind(str, Enum):
    BOOK = "book"
    CANCEL = "cancel"


class JobStatus(str, Enum):
    RUNNING = "running"
    NEEDS_CONFIRMATION = "needs_confirmation"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class BookingJob:
    id: str
    kind: JobKind
    args: dict[str, Any]
    status: JobStatus = JobStatus.RUNNING
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    confirm_kind: str | None = None
    explanation: str | None = None
    screenshot_b64: str | None = None
    result: dict[str, Any] | None = None
    error: str | None = None
    # Agent runtime (owned by the job until terminal)
    browser: Browser | None = None
    context: BrowserContext | None = None
    page: Page | None = None
    contents: list[Any] = field(default_factory=list)
    pending_function_calls: list[Any] = field(default_factory=list)
    confirm_event: asyncio.Event = field(default_factory=asyncio.Event)
    confirm_decision: bool | None = None
    # A job is a single book-or-cancel, so our own policy gate is asked once.
    # Google's safety gates are separate and always surfaced.
    action_confirmed: bool = False
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)

    def touch(self) -> None:
        self.updated_at = time.time()

    async def close_browser(self) -> None:
        try:
            if self.context:
                await self.context.close()
        except Exception:
            pass
        pw = getattr(self.browser, "_wgp_playwright", None) if self.browser else None
        try:
            if self.browser:
                await self.browser.close()
        except Exception:
            pass
        if pw is not None:
            try:
                await pw.stop()
            except Exception:
                pass
        self.context = None
        self.browser = None
        self.page = None

    def to_response(self) -> dict[str, Any]:
        if self.status == JobStatus.NEEDS_CONFIRMATION:
            return {
                "status": JobStatus.NEEDS_CONFIRMATION.value,
                "job_id": self.id,
                "kind": self.confirm_kind or "safety",
                "explanation": self.explanation or "Confirmation required",
                "screenshot_b64": self.screenshot_b64,
                "success": False,
            }
        if self.status == JobStatus.COMPLETED and self.result is not None:
            return {
                "status": JobStatus.COMPLETED.value,
                **self.result,
            }
        if self.status == JobStatus.FAILED:
            return {
                "status": JobStatus.FAILED.value,
                "success": False,
                "error": self.error or "Booking agent failed",
                "job_id": self.id,
            }
        return {
            "status": self.status.value,
            "job_id": self.id,
            "success": False,
        }


class JobStore:
    def __init__(self) -> None:
        self._jobs: dict[str, BookingJob] = {}
        self._lock = asyncio.Lock()

    async def create(self, kind: JobKind, args: dict[str, Any]) -> BookingJob:
        job = BookingJob(id=str(uuid.uuid4()), kind=kind, args=args)
        async with self._lock:
            self._jobs[job.id] = job
        return job

    async def get(self, job_id: str) -> BookingJob | None:
        async with self._lock:
            return self._jobs.get(job_id)

    async def purge_expired(self, ttl_seconds: int) -> None:
        cutoff = time.time() - ttl_seconds
        async with self._lock:
            expired = [j.id for j in self._jobs.values() if j.updated_at < cutoff]
            for job_id in expired:
                job = self._jobs.pop(job_id, None)
                if job:
                    await job.close_browser()


def screenshot_to_b64(png: bytes) -> str:
    return base64.b64encode(png).decode("ascii")


job_store = JobStore()

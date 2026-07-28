"""HTTP API for the ForeTees Computer Use booking agent."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

from .agent import confirm_job, start_job
from .config import get_settings
from .jobs import JobKind, job_store

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger("booking_agent")

app = FastAPI(title="WGP ForeTees Booking Agent", version="0.1.0")


class BookRequest(BaseModel):
    username: str
    password: str
    date: str
    time: str
    transport_mode: str = "WLK"
    players: list[str] = Field(default_factory=list)


class CancelRequest(BaseModel):
    username: str
    password: str
    date: str = ""
    time: str = ""
    ttdata: str | None = None


class ConfirmRequest(BaseModel):
    confirm: bool = True


def _check_auth(authorization: str | None) -> None:
    secret = get_settings().booking_service_secret
    if not secret:
        return
    if authorization != f"Bearer {secret}":
        raise HTTPException(status_code=401, detail="Unauthorized")


@app.on_event("startup")
async def _startup() -> None:
    settings = get_settings()
    logger.info(
        "booking-agent starting model=%s project=%s",
        settings.computer_use_model,
        settings.gcp_project_id,
    )


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/book")
async def book(
    body: BookRequest,
    authorization: str | None = Header(default=None),
) -> dict[str, Any]:
    _check_auth(authorization)
    logger.info("POST /book date=%s time=%s", body.date, body.time)
    return await start_job(
        JobKind.BOOK,
        {
            "username": body.username,
            "password": body.password,
            "date": body.date,
            "time": body.time,
            "transport_mode": body.transport_mode,
            "players": [p for p in body.players if p],
        },
    )


@app.post("/cancel")
async def cancel(
    body: CancelRequest,
    authorization: str | None = Header(default=None),
) -> dict[str, Any]:
    _check_auth(authorization)
    if not body.ttdata and not (body.date and body.time):
        raise HTTPException(status_code=400, detail="ttdata or date+time required")
    logger.info("POST /cancel date=%s time=%s", body.date, body.time)
    return await start_job(
        JobKind.CANCEL,
        {
            "username": body.username,
            "password": body.password,
            "date": body.date,
            "time": body.time,
            "ttdata": body.ttdata,
        },
    )


@app.post("/jobs/{job_id}/confirm")
async def confirm(
    job_id: str,
    body: ConfirmRequest,
    authorization: str | None = Header(default=None),
) -> dict[str, Any]:
    _check_auth(authorization)
    logger.info("POST /jobs/%s/confirm confirm=%s", job_id, body.confirm)
    return await confirm_job(job_id, body.confirm)


@app.get("/jobs/{job_id}")
async def get_job(
    job_id: str,
    authorization: str | None = Header(default=None),
) -> dict[str, Any]:
    _check_auth(authorization)
    job = await job_store.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Unknown job")
    return job.to_response()

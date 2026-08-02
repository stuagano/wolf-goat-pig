"""Proxy scorecard scans to the Vertex scorecard-agent Cloud Run service."""

from __future__ import annotations

import json
import logging
import os
from typing import Any

import httpx

logger = logging.getLogger(__name__)


async def scan_via_scorecard_agent(
    image_bytes: bytes,
    content_type: str,
    expected_players: list[str] | None = None,
) -> dict[str, Any]:
    service_url = os.getenv("SCORECARD_SERVICE_URL", "").strip().rstrip("/")
    if not service_url:
        raise ValueError("SCORECARD_SERVICE_URL is not configured")

    secret = os.getenv("SCORECARD_SERVICE_SECRET", "") or os.getenv("BOOKING_SERVICE_SECRET", "")
    headers: dict[str, str] = {}
    if secret:
        headers["Authorization"] = f"Bearer {secret}"

    form_data: dict[str, str] = {}
    if expected_players:
        form_data["players"] = json.dumps(expected_players)

    files = {"file": ("scorecard.jpg", image_bytes, content_type)}
    timeout = httpx.Timeout(120.0, connect=30.0)

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            try:
                await client.get(f"{service_url}/health")
            except Exception:
                logger.warning("Scorecard agent health check failed, trying scan anyway")
            resp = await client.post(f"{service_url}/scan", data=form_data, files=files, headers=headers)
    except httpx.TimeoutException as exc:
        raise ValueError("Scorecard scan timed out — try again shortly.") from exc
    except Exception as exc:
        raise ValueError(f"Scorecard agent unavailable: {exc}") from exc

    if resp.status_code == 401:
        raise ValueError("Scorecard agent auth failed — check SCORECARD_SERVICE_SECRET")
    if resp.status_code == 422:
        body = resp.json() if resp.headers.get("content-type", "").startswith("application/json") else {}
        detail = body.get("detail", "Could not parse scorecard")
        raise ValueError(str(detail))
    if resp.status_code != 200:
        body = resp.json() if resp.headers.get("content-type", "").startswith("application/json") else {}
        detail = body.get("detail", f"Scorecard agent error {resp.status_code}")
        raise ValueError(str(detail))

    return resp.json()

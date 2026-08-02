"""Route scorecard scans to Groq (inline) or the Vertex scorecard agent service."""

from __future__ import annotations

import logging
import os
from typing import Any

logger = logging.getLogger(__name__)


async def dispatch_scorecard_scan(
    image_bytes: bytes,
    content_type: str,
    expected_players: list[str] | None = None,
) -> dict[str, Any]:
    provider = os.getenv("SCORECARD_VISION_PROVIDER", "groq").strip().lower()
    if provider == "agent":
        from .scorecard_agent_client import scan_via_scorecard_agent

        logger.info("Scorecard scan via agent service")
        return await scan_via_scorecard_agent(image_bytes, content_type, expected_players)

    from .scorecard_scan_service import scan_scorecard

    return await scan_scorecard(image_bytes, content_type, expected_players=expected_players)

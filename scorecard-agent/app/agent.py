"""Scorecard scan orchestration — preprocess, extract, validate, correct."""

from __future__ import annotations

import json
import logging
from typing import Any

from .config import Settings, get_settings
from .scorecard_preprocess import annotate_circles, crop_to_grid, deskew_to_card
from .extract import fit_image_to_budget, shape_extraction, validate_zero_sum
from .vision import extract_scorecard

logger = logging.getLogger("scorecard_agent.agent")


async def scan_scorecard(
    image_bytes: bytes,
    content_type: str,
    expected_players: list[str] | None = None,
    *,
    settings: Settings | None = None,
) -> dict[str, Any]:
    """Preprocess the photo, extract via Vertex Gemini, and retry on parse/zero-sum failures."""
    settings = settings or get_settings()

    image_bytes, content_type = fit_image_to_budget(
        image_bytes, content_type, max_dim=settings.preprocess_max_dim, max_b64_chars=10**12
    )
    deskewed_bytes, deskewed_ct, deskew_diag = deskew_to_card(image_bytes, content_type)
    cropped_bytes, cropped_ct, grid_diag = crop_to_grid(deskewed_bytes, deskewed_ct)
    annotated_bytes, annotated_ct, circle_diag = annotate_circles(cropped_bytes, cropped_ct)
    preprocessing_diag = {"deskew": deskew_diag, "grid_crop": grid_diag, "circles": circle_diag}

    raw: dict[str, Any] | None = None
    bad_holes: dict[int, float] | None = None
    passes = 0
    max_passes = 1 + settings.max_correction_passes

    while passes < max_passes:
        strict = passes > 0
        try:
            raw = await extract_scorecard(
                annotated_bytes,
                annotated_ct,
                expected_players=expected_players,
                strict=strict,
                bad_holes=bad_holes,
                settings=settings,
            )
        except json.JSONDecodeError as exc:
            passes += 1
            if passes >= max_passes:
                raise ValueError(f"Failed to parse vision response: {exc}") from exc
            logger.warning("Vision JSON parse failed — retrying strict (pass %s)", passes)
            continue

        result = shape_extraction(raw)
        validation = validate_zero_sum(result["per_hole_quarters"])
        if validation["valid"]:
            result["validation"] = validation
            result["preprocessing"] = preprocessing_diag
            result["method"] = "vertex-agent"
            result["passes"] = passes + 1
            return result

        bad_holes = validation["bad_holes"]
        passes += 1
        logger.warning("Zero-sum violation on holes %s — correction pass %s", list(bad_holes), passes)
        if passes >= max_passes:
            result["validation"] = validation
            result["preprocessing"] = preprocessing_diag
            result["method"] = "vertex-agent"
            result["passes"] = passes
            return result

    raise ValueError("Scorecard extraction failed after retries")

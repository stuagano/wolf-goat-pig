"""
Scorecard photo preprocessing.

Detects hand-drawn circles classically (Hough) and draws bright red
rectangles around each one. The downstream vision model can reliably
detect bright red rectangles, but is unreliable at detecting hand-drawn
circles — so we shift the burden.

Public entry point: annotate_circles().
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


def annotate_circles(
    image_bytes: bytes, content_type: str
) -> tuple[bytes, str, dict[str, Any]]:
    """
    Detect circles in the scorecard image and draw red rectangles around each.

    Returns (annotated_bytes, content_type, diagnostics). On any failure,
    returns (image_bytes, content_type, {...}) so the caller can fall back
    to the unmodified image.
    """
    return image_bytes, content_type, {"preprocessing_applied": False, "error": "not_implemented"}

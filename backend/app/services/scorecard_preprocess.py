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

import cv2
import numpy as np

logger = logging.getLogger(__name__)


def _decode_image(image_bytes: bytes) -> np.ndarray:
    """Decode bytes into a BGR numpy array. Raises ValueError on failure."""
    arr = np.frombuffer(image_bytes, dtype=np.uint8)
    if arr.size == 0:
        raise ValueError("empty image bytes")
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("could not decode image")
    return img


def annotate_circles(
    image_bytes: bytes, content_type: str
) -> tuple[bytes, str, dict[str, Any]]:
    """
    Detect circles in the scorecard image and draw red rectangles around each.

    Returns (annotated_bytes, content_type, diagnostics). On any failure,
    returns (image_bytes, content_type, {...}) so the caller can fall back
    to the unmodified image.
    """
    try:
        img = _decode_image(image_bytes)
    except ValueError as e:
        logger.warning("Scorecard preprocessing decode failed: %s", e)
        return image_bytes, content_type, {
            "preprocessing_applied": False,
            "error": str(e),
        }

    height, width = img.shape[:2]
    return image_bytes, content_type, {
        "preprocessing_applied": False,
        "error": "annotation_not_yet_implemented",
        "image_dimensions": [width, height],
    }

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

# Detection sanity bounds — outside these we assume detection failed and skip annotation.
_MIN_CIRCLES = 1
_MAX_CIRCLES = 150

# Crop from top of image — pre-printed yardages are in the top section, no handwriting there.
_TOP_CROP_FRACTION = 0.25


def _decode_image(image_bytes: bytes) -> np.ndarray:
    arr = np.frombuffer(image_bytes, dtype=np.uint8)
    if arr.size == 0:
        raise ValueError("empty image bytes")
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("could not decode image")
    return img


def _detect_circles(img: np.ndarray) -> list[tuple[int, int, int]]:
    """Return list of (x, y, radius) tuples for detected circles in the handwriting region."""
    height, width = img.shape[:2]
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blurred = cv2.medianBlur(gray, 3)

    min_radius = max(4, height // 80)
    max_radius = max(min_radius + 1, height // 25)
    min_dist = max(8, height // 40)

    circles = cv2.HoughCircles(
        blurred,
        cv2.HOUGH_GRADIENT,
        dp=1.2,
        minDist=min_dist,
        param1=100,
        param2=30,
        minRadius=min_radius,
        maxRadius=max_radius,
    )
    if circles is None:
        return []

    top_cutoff = height * _TOP_CROP_FRACTION
    out: list[tuple[int, int, int]] = []
    for x, y, r in circles[0]:
        if y < top_cutoff:
            continue
        out.append((int(x), int(y), int(r)))
    return out


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

    try:
        circles = _detect_circles(img)
    except cv2.error as e:
        logger.warning("Scorecard preprocessing Hough failed: %s", e)
        return image_bytes, content_type, {
            "preprocessing_applied": False,
            "error": f"hough_failed: {e}",
            "image_dimensions": [width, height],
        }

    if len(circles) < _MIN_CIRCLES or len(circles) > _MAX_CIRCLES:
        return image_bytes, content_type, {
            "preprocessing_applied": False,
            "circles_detected": len(circles),
            "image_dimensions": [width, height],
        }

    return image_bytes, content_type, {
        "preprocessing_applied": False,
        "circles_detected": len(circles),
        "image_dimensions": [width, height],
        "error": "annotation_not_yet_implemented",
    }

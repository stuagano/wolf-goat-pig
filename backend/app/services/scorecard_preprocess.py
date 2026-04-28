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

_MIN_CIRCLES = 1
_MAX_CIRCLES = 150
_TOP_CROP_FRACTION = 0.25

_RECT_COLOR_BGR = (0, 0, 255)  # pure red
_RECT_THICKNESS = 4
_RECT_PADDING_PX = 8
_JPEG_QUALITY = 90


def _decode_image(image_bytes: bytes) -> np.ndarray:
    arr = np.frombuffer(image_bytes, dtype=np.uint8)
    if arr.size == 0:
        raise ValueError("empty image bytes")
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("could not decode image")
    return img


def _detect_circles(img: np.ndarray) -> list[tuple[int, int, int]]:
    height, _ = img.shape[:2]
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
        param2=40,
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


def _draw_markers(img: np.ndarray, circles: list[tuple[int, int, int]]) -> np.ndarray:
    height, width = img.shape[:2]
    out = img.copy()
    for x, y, r in circles:
        x1 = max(0, x - r - _RECT_PADDING_PX)
        y1 = max(0, y - r - _RECT_PADDING_PX)
        x2 = min(width - 1, x + r + _RECT_PADDING_PX)
        y2 = min(height - 1, y + r + _RECT_PADDING_PX)
        cv2.rectangle(out, (x1, y1), (x2, y2), _RECT_COLOR_BGR, _RECT_THICKNESS)
    return out


def _encode_jpeg(img: np.ndarray) -> bytes:
    ok, buf = cv2.imencode(".jpg", img, [int(cv2.IMWRITE_JPEG_QUALITY), _JPEG_QUALITY])
    if not ok:
        raise ValueError("failed to encode annotated image as JPEG")
    return buf.tobytes()


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

    diag: dict[str, Any] = {
        "circles_detected": len(circles),
        "image_dimensions": [width, height],
    }

    if len(circles) < _MIN_CIRCLES or len(circles) > _MAX_CIRCLES:
        diag["preprocessing_applied"] = False
        return image_bytes, content_type, diag

    try:
        annotated = _draw_markers(img, circles)
        encoded = _encode_jpeg(annotated)
    except (cv2.error, ValueError) as e:
        logger.warning("Scorecard preprocessing annotation failed: %s", e)
        diag["preprocessing_applied"] = False
        diag["error"] = str(e)
        return image_bytes, content_type, diag

    diag["preprocessing_applied"] = True
    return encoded, "image/jpeg", diag

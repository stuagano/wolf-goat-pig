"""
Scorecard photo preprocessing.

Two stages, both with graceful fallback to the original image on failure:

1. deskew_to_card(): detect the scorecard's outer 4-corner contour and
   apply a perspective warp so the card fills a rectangular frame. This
   normalizes shooting angle so downstream steps see a clean top-down view.

2. annotate_circles(): detect hand-drawn circles classically (Hough) and
   draw bright red rectangles around each one. The vision model reliably
   detects bright red rectangles but struggles with hand-drawn circles —
   we shift the burden.

Public entry points: deskew_to_card(), annotate_circles().
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

_DESKEW_MIN_AREA_FRACTION = 0.30  # card must occupy ≥30% of frame
_DESKEW_APPROX_EPSILON = 0.02  # poly approx tolerance, fraction of perimeter
_DESKEW_TOP_CONTOURS = 5  # only check the largest N contours
# WGP scorecard prints landscape ~1.7-2.5:1. Anything outside this is more likely
# a tabletop, page, or background rectangle than the card itself.
_DESKEW_MIN_ASPECT = 1.3
_DESKEW_MAX_ASPECT = 3.5

_GRID_PEAK_RATIO = 0.5  # peaks are ≥50% of max projection
_GRID_MIN_H_LINES = 3  # need at least 3 horizontal lines for a meaningful grid
_GRID_MIN_V_LINES = 5  # 5 vertical lines = 4 columns minimum
_GRID_CROP_PADDING = 10  # px padding around detected grid bounds
_GRID_MIN_CROP_DIM = 50  # reject crops smaller than this


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


def _detect_card_corners(img: np.ndarray) -> np.ndarray | None:
    """
    Find the outer 4-corner contour of the scorecard. Returns 4×2 array of
    (x, y) corner points in undefined order, or None if no quad found that
    covers ≥_DESKEW_MIN_AREA_FRACTION of the image.
    """
    height, width = img.shape[:2]
    img_area = float(height * width)

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blurred, 50, 150)
    edges = cv2.dilate(edges, np.ones((3, 3), np.uint8), iterations=1)

    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None

    contours = sorted(contours, key=cv2.contourArea, reverse=True)[:_DESKEW_TOP_CONTOURS]

    for c in contours:
        if cv2.contourArea(c) < img_area * _DESKEW_MIN_AREA_FRACTION:
            return None  # remaining contours are even smaller
        peri = cv2.arcLength(c, True)
        approx = cv2.approxPolyDP(c, _DESKEW_APPROX_EPSILON * peri, True)
        if len(approx) != 4:
            continue
        _, _, w, h = cv2.boundingRect(approx)
        aspect = max(w, h) / max(min(w, h), 1)
        if aspect < _DESKEW_MIN_ASPECT or aspect > _DESKEW_MAX_ASPECT:
            continue  # quad shape doesn't match a WGP scorecard
        return approx.reshape(4, 2).astype("float32")

    return None


def _order_corners(pts: np.ndarray) -> np.ndarray:
    """
    Order 4 corner points as (top-left, top-right, bottom-right, bottom-left).
    TL has smallest x+y; BR has largest x+y; TR has smallest y-x; BL has largest y-x.
    """
    rect = np.zeros((4, 2), dtype="float32")
    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]  # TL
    rect[2] = pts[np.argmax(s)]  # BR
    diff = np.diff(pts, axis=1).ravel()  # y - x
    rect[1] = pts[np.argmin(diff)]  # TR
    rect[3] = pts[np.argmax(diff)]  # BL
    return rect


def _warp_to_rect(img: np.ndarray, corners: np.ndarray) -> np.ndarray:
    rect = _order_corners(corners)
    tl, tr, br, bl = rect

    width_top = np.linalg.norm(tr - tl)
    width_bot = np.linalg.norm(br - bl)
    height_left = np.linalg.norm(bl - tl)
    height_right = np.linalg.norm(br - tr)

    out_w = int(max(width_top, width_bot))
    out_h = int(max(height_left, height_right))
    if out_w < 50 or out_h < 50:
        raise ValueError(f"warped dimensions too small: {out_w}x{out_h}")

    dst = np.array(
        [[0, 0], [out_w - 1, 0], [out_w - 1, out_h - 1], [0, out_h - 1]],
        dtype="float32",
    )
    M = cv2.getPerspectiveTransform(rect, dst)
    return cv2.warpPerspective(img, M, (out_w, out_h))


def deskew_to_card(image_bytes: bytes, content_type: str) -> tuple[bytes, str, dict[str, Any]]:
    """
    Detect the scorecard's outer 4-corner frame and warp it to a rectangle.

    Returns (deskewed_bytes, content_type, diagnostics). On any failure
    (no 4-corner contour found, warp failure, decode failure), returns the
    original bytes/content_type so the caller can proceed with the unmodified
    image.
    """
    try:
        img = _decode_image(image_bytes)
    except ValueError as e:
        logger.warning("Deskew decode failed: %s", e)
        return image_bytes, content_type, {"deskew_applied": False, "error": str(e)}

    height, width = img.shape[:2]
    diag: dict[str, Any] = {"original_dimensions": [width, height]}

    try:
        corners = _detect_card_corners(img)
    except cv2.error as e:
        logger.warning("Deskew corner detection failed: %s", e)
        diag["deskew_applied"] = False
        diag["error"] = f"corner_detect_failed: {e}"
        return image_bytes, content_type, diag

    if corners is None:
        diag["deskew_applied"] = False
        diag["reason"] = "no_4corner_contour"
        return image_bytes, content_type, diag

    try:
        warped = _warp_to_rect(img, corners)
        encoded = _encode_jpeg(warped)
    except (cv2.error, ValueError) as e:
        logger.warning("Deskew warp failed: %s", e)
        diag["deskew_applied"] = False
        diag["error"] = str(e)
        return image_bytes, content_type, diag

    diag["deskew_applied"] = True
    diag["warped_dimensions"] = [warped.shape[1], warped.shape[0]]
    return encoded, "image/jpeg", diag


def _find_peaks(signal: np.ndarray, min_separation: int) -> list[int]:
    """
    Locate peak positions in a 1D signal. Each contiguous run of values above
    `_GRID_PEAK_RATIO * max(signal)` becomes one peak (its midpoint), then
    peaks closer than `min_separation` are merged keeping the stronger one.
    """
    if signal.size == 0 or signal.max() == 0:
        return []
    threshold = _GRID_PEAK_RATIO * signal.max()
    above = signal > threshold

    peaks: list[int] = []
    i = 0
    while i < len(above):
        if above[i]:
            start = i
            while i < len(above) and above[i]:
                i += 1
            peaks.append((start + i - 1) // 2)
        else:
            i += 1

    merged: list[int] = []
    for p in peaks:
        if not merged or (p - merged[-1]) >= min_separation:
            merged.append(p)
        elif signal[p] > signal[merged[-1]]:
            merged[-1] = p
    return merged


def _detect_grid_lines(img: np.ndarray) -> tuple[list[int], list[int]]:
    """
    Detect horizontal and vertical grid line positions. Uses morphological
    opening with long line-shaped kernels to isolate true grid lines from
    text and handwriting, then finds peaks in the row/column projections.

    Returns (horizontal_line_y_positions, vertical_line_x_positions),
    each sorted ascending.
    """
    height, width = img.shape[:2]
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    thresh = cv2.adaptiveThreshold(
        gray,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY_INV,
        15,
        -2,
    )

    h_kernel_w = max(20, width // 30)
    v_kernel_h = max(20, height // 30)
    h_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (h_kernel_w, 1))
    v_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, v_kernel_h))

    h_lines = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, h_kernel)
    v_lines = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, v_kernel)

    h_proj = h_lines.sum(axis=1)
    v_proj = v_lines.sum(axis=0)

    h_positions = _find_peaks(h_proj, min_separation=max(5, height // 50))
    v_positions = _find_peaks(v_proj, min_separation=max(5, width // 50))
    return h_positions, v_positions


def crop_to_grid(image_bytes: bytes, content_type: str) -> tuple[bytes, str, dict[str, Any]]:
    """
    Detect the table grid in the image and crop tightly to the grid bounds
    (with small padding). Drops scorecard branding/title/footer regions so
    the vision model and circle detector both work on a tighter frame.

    Returns (cropped_bytes, content_type, diagnostics). On any failure
    (decode, line detection, too few lines, crop too small), returns the
    original bytes — every step degrades gracefully.

    Cell-level bounding boxes are NOT computed here; downstream callers
    that need them can derive them from row_lines × col_lines in the diag.
    """
    try:
        img = _decode_image(image_bytes)
    except ValueError as e:
        logger.warning("Grid crop decode failed: %s", e)
        return image_bytes, content_type, {"grid_crop_applied": False, "error": str(e)}

    height, width = img.shape[:2]
    diag: dict[str, Any] = {"original_dimensions": [width, height]}

    try:
        h_lines, v_lines = _detect_grid_lines(img)
    except cv2.error as e:
        logger.warning("Grid line detection failed: %s", e)
        diag["grid_crop_applied"] = False
        diag["error"] = f"line_detect_failed: {e}"
        return image_bytes, content_type, diag

    diag["row_lines"] = h_lines
    diag["col_lines"] = v_lines

    if len(h_lines) < _GRID_MIN_H_LINES or len(v_lines) < _GRID_MIN_V_LINES:
        diag["grid_crop_applied"] = False
        diag["reason"] = "too_few_lines"
        return image_bytes, content_type, diag

    pad = _GRID_CROP_PADDING
    y1 = max(0, h_lines[0] - pad)
    y2 = min(height, h_lines[-1] + pad)
    x1 = max(0, v_lines[0] - pad)
    x2 = min(width, v_lines[-1] + pad)

    cropped = img[y1:y2, x1:x2]
    if cropped.shape[0] < _GRID_MIN_CROP_DIM or cropped.shape[1] < _GRID_MIN_CROP_DIM:
        diag["grid_crop_applied"] = False
        diag["reason"] = "crop_too_small"
        return image_bytes, content_type, diag

    try:
        encoded = _encode_jpeg(cropped)
    except (cv2.error, ValueError) as e:
        logger.warning("Grid crop encode failed: %s", e)
        diag["grid_crop_applied"] = False
        diag["error"] = str(e)
        return image_bytes, content_type, diag

    diag["grid_crop_applied"] = True
    diag["cropped_dimensions"] = [cropped.shape[1], cropped.shape[0]]
    diag["crop_bounds"] = [x1, y1, x2, y2]
    return encoded, "image/jpeg", diag


def annotate_circles(image_bytes: bytes, content_type: str) -> tuple[bytes, str, dict[str, Any]]:
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
        return (
            image_bytes,
            content_type,
            {
                "preprocessing_applied": False,
                "error": str(e),
            },
        )

    height, width = img.shape[:2]

    try:
        circles = _detect_circles(img)
    except cv2.error as e:
        logger.warning("Scorecard preprocessing Hough failed: %s", e)
        return (
            image_bytes,
            content_type,
            {
                "preprocessing_applied": False,
                "error": f"hough_failed: {e}",
                "image_dimensions": [width, height],
            },
        )

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

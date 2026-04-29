"""Unit tests for scorecard_preprocess — circle detection + annotation + deskew."""

from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np
import pytest

from app.services.scorecard_preprocess import (
    _find_peaks,
    _order_corners,
    annotate_circles,
    crop_to_grid,
    deskew_to_card,
)

EXAMPLE_PATH = Path(__file__).parent.parent.parent.parent / "app" / "data" / "scorecard_examples" / "example_001.jpeg"


@pytest.fixture
def example_image_bytes() -> bytes:
    return EXAMPLE_PATH.read_bytes()


def test_returns_tuple_of_bytes_content_type_diagnostics(example_image_bytes):
    annotated, content_type, diag = annotate_circles(example_image_bytes, "image/jpeg")
    assert isinstance(annotated, bytes)
    assert content_type in ("image/jpeg", "image/png")
    assert isinstance(diag, dict)
    assert "preprocessing_applied" in diag


def test_returns_original_on_bad_bytes():
    annotated, content_type, diag = annotate_circles(b"not an image", "image/jpeg")
    assert annotated == b"not an image"
    assert content_type == "image/jpeg"
    assert diag["preprocessing_applied"] is False
    assert diag.get("error")


def test_returns_original_on_empty_bytes():
    annotated, _content_type, diag = annotate_circles(b"", "image/jpeg")
    assert annotated == b""
    assert diag["preprocessing_applied"] is False


def test_detects_circles_in_example_001(example_image_bytes):
    """example_001.jpeg has many hand-drawn circles — detection should find some."""
    _annotated, _content_type, diag = annotate_circles(example_image_bytes, "image/jpeg")
    assert diag.get("circles_detected", 0) >= 5, (
        f"Expected ≥5 circles in example_001, got {diag.get('circles_detected')}"
    )
    assert diag["circles_detected"] <= 150, f"Detection blew up — got {diag['circles_detected']} circles"


def test_returns_diagnostics_when_no_circles_detected():
    """A blank white image should detect 0 circles and skip annotation."""
    blank = np.full((1000, 1500, 3), 255, dtype=np.uint8)
    ok, encoded = cv2.imencode(".jpg", blank)
    assert ok
    _annotated, _content_type, diag = annotate_circles(encoded.tobytes(), "image/jpeg")
    assert diag["preprocessing_applied"] is False
    assert diag["circles_detected"] == 0


def test_annotation_returns_jpeg_with_same_dimensions(example_image_bytes):
    annotated, content_type, diag = annotate_circles(example_image_bytes, "image/jpeg")
    if not diag.get("preprocessing_applied"):
        pytest.skip("annotation skipped — sanity bounds not met for example image")

    assert content_type == "image/jpeg"
    arr = np.frombuffer(annotated, dtype=np.uint8)
    decoded = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    assert decoded is not None, "annotated bytes must decode as a valid image"

    in_arr = np.frombuffer(example_image_bytes, dtype=np.uint8)
    in_decoded = cv2.imdecode(in_arr, cv2.IMREAD_COLOR)
    assert decoded.shape == in_decoded.shape


def test_annotation_introduces_red_pixels(example_image_bytes):
    """Annotated image should contain pure red pixels (the markers); originals shouldn't."""
    annotated, _, diag = annotate_circles(example_image_bytes, "image/jpeg")
    if not diag.get("preprocessing_applied"):
        pytest.skip("annotation skipped — sanity bounds not met for example image")

    arr = np.frombuffer(annotated, dtype=np.uint8)
    decoded = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    # BGR red: B=0, G=0, R=255 (with JPEG quantization slack)
    red_mask = (decoded[:, :, 0] < 30) & (decoded[:, :, 1] < 30) & (decoded[:, :, 2] > 220)
    assert red_mask.sum() > 100, "expected ≥100 pure-red marker pixels"


# ---------- Deskew ----------


def test_order_corners_handles_arbitrary_input_order():
    """4 corners in any order must come out as TL, TR, BR, BL."""
    tl, tr, br, bl = (10, 20), (110, 25), (115, 80), (5, 75)
    for perm in [
        [tl, tr, br, bl],
        [br, tl, bl, tr],
        [tr, bl, tl, br],
        [bl, br, tr, tl],
    ]:
        ordered = _order_corners(np.array(perm, dtype="float32"))
        assert tuple(ordered[0]) == tl
        assert tuple(ordered[1]) == tr
        assert tuple(ordered[2]) == br
        assert tuple(ordered[3]) == bl


def test_deskew_returns_original_on_bad_bytes():
    out_bytes, content_type, diag = deskew_to_card(b"not an image", "image/jpeg")
    assert out_bytes == b"not an image"
    assert content_type == "image/jpeg"
    assert diag["deskew_applied"] is False
    assert diag.get("error")


def test_deskew_returns_original_when_no_card_found():
    """Blank white image has no contour — deskew should pass through."""
    blank = np.full((1000, 1500, 3), 255, dtype=np.uint8)
    ok, encoded = cv2.imencode(".jpg", blank)
    assert ok
    out_bytes, _, diag = deskew_to_card(encoded.tobytes(), "image/jpeg")
    assert out_bytes == encoded.tobytes(), "no-card case must return original bytes"
    assert diag["deskew_applied"] is False
    assert diag.get("reason") == "no_4corner_contour"


def test_deskew_warps_synthetic_skewed_card():
    """A dark quad on a light background should be detected and warped to fill the frame."""
    canvas = np.full((1000, 1400, 3), 240, dtype=np.uint8)
    # Skewed quadrilateral, inset from edges so it's clearly the largest contour.
    quad = np.array([[200, 100], [1200, 200], [1150, 850], [150, 800]], dtype=np.int32)
    cv2.fillPoly(canvas, [quad], (40, 40, 40))
    ok, encoded = cv2.imencode(".jpg", canvas)
    assert ok

    out_bytes, content_type, diag = deskew_to_card(encoded.tobytes(), "image/jpeg")
    assert diag["deskew_applied"] is True, f"expected deskew, got diag={diag}"
    assert content_type == "image/jpeg"
    assert "warped_dimensions" in diag

    arr = np.frombuffer(out_bytes, dtype=np.uint8)
    warped = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    assert warped is not None
    # Warped output should be predominantly the dark quad's color.
    mean = warped.mean(axis=(0, 1))
    assert mean.mean() < 80, f"warped image should be mostly dark (the card), got mean={mean}"


def test_deskew_rejects_square_quad():
    """A near-square quad isn't scorecard-shaped — should fall through, not warp."""
    canvas = np.full((1200, 1200, 3), 240, dtype=np.uint8)
    quad = np.array([[200, 200], [1000, 200], [1000, 1000], [200, 1000]], dtype=np.int32)
    cv2.fillPoly(canvas, [quad], (40, 40, 40))
    ok, encoded = cv2.imencode(".jpg", canvas)
    assert ok

    out_bytes, _, diag = deskew_to_card(encoded.tobytes(), "image/jpeg")
    assert diag["deskew_applied"] is False, "square quad should not be accepted as a WGP scorecard"
    assert out_bytes == encoded.tobytes()


def test_deskew_then_annotate_pipeline_on_example(example_image_bytes):
    """End-to-end: real example image should not break either stage."""
    deskewed, ct, _ = deskew_to_card(example_image_bytes, "image/jpeg")
    assert isinstance(deskewed, bytes) and len(deskewed) > 0
    annotated, _, circle_diag = annotate_circles(deskewed, ct)
    assert isinstance(annotated, bytes)
    # Whether deskew applied or not, circle detection should still run cleanly.
    assert "preprocessing_applied" in circle_diag


# ---------- Grid detection / crop ----------


def test_find_peaks_empty_signal_returns_empty():
    assert _find_peaks(np.array([], dtype=np.int64), min_separation=5) == []


def test_find_peaks_zero_signal_returns_empty():
    assert _find_peaks(np.zeros(100, dtype=np.int64), min_separation=5) == []


def test_find_peaks_finds_distinct_peaks():
    """Three runs above 50% of max with gaps — should find 3 peak midpoints."""
    sig = np.zeros(200, dtype=np.int64)
    sig[10:14] = 100
    sig[60:65] = 100
    sig[150:154] = 100
    peaks = _find_peaks(sig, min_separation=5)
    assert len(peaks) == 3
    assert abs(peaks[0] - 11) <= 1
    assert abs(peaks[1] - 62) <= 1
    assert abs(peaks[2] - 151) <= 1


def test_find_peaks_merges_close_peaks():
    """Two peaks within min_separation collapse into one (the stronger)."""
    sig = np.zeros(200, dtype=np.int64)
    sig[10:14] = 50
    sig[20:24] = 100  # stronger
    sig[100:104] = 100
    peaks = _find_peaks(sig, min_separation=20)
    assert len(peaks) == 2
    # First merged peak should be at the stronger position (~22)
    assert abs(peaks[0] - 21) <= 2
    assert abs(peaks[1] - 101) <= 2


def test_crop_to_grid_returns_original_on_bad_bytes():
    out, _, diag = crop_to_grid(b"not an image", "image/jpeg")
    assert out == b"not an image"
    assert diag["grid_crop_applied"] is False
    assert diag.get("error")


def test_crop_to_grid_returns_original_on_blank_image():
    """Blank canvas has no grid lines — should pass through."""
    blank = np.full((400, 600, 3), 255, dtype=np.uint8)
    ok, encoded = cv2.imencode(".jpg", blank)
    assert ok
    out, _, diag = crop_to_grid(encoded.tobytes(), "image/jpeg")
    assert out == encoded.tobytes()
    assert diag["grid_crop_applied"] is False
    assert diag.get("reason") == "too_few_lines"


def test_crop_to_grid_detects_synthetic_grid():
    """A synthetic grid with 5 H-lines + 6 V-lines should crop to grid bounds."""
    canvas = np.full((400, 800, 3), 255, dtype=np.uint8)
    # Draw a grid covering ~half the canvas; outer region should get cropped away.
    h_ys = [50, 100, 150, 200, 250]
    v_xs = [100, 200, 300, 400, 500, 600]
    for y in h_ys:
        cv2.line(canvas, (v_xs[0], y), (v_xs[-1], y), (0, 0, 0), 2)
    for x in v_xs:
        cv2.line(canvas, (x, h_ys[0]), (x, h_ys[-1]), (0, 0, 0), 2)
    ok, encoded = cv2.imencode(".jpg", canvas)
    assert ok

    out, ct, diag = crop_to_grid(encoded.tobytes(), "image/jpeg")
    assert ct == "image/jpeg"
    assert diag["grid_crop_applied"] is True, f"expected crop, got diag={diag}"
    assert len(diag["row_lines"]) >= 5
    assert len(diag["col_lines"]) >= 6
    cw, ch = diag["cropped_dimensions"]
    # Cropped image should be smaller than the original 800x400 canvas.
    assert cw < 800 and ch < 400
    # And it should still contain the grid (decode is valid).
    arr = np.frombuffer(out, dtype=np.uint8)
    decoded = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    assert decoded is not None
    assert decoded.shape[0] == ch and decoded.shape[1] == cw

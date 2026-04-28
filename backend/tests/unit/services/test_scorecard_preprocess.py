"""Unit tests for scorecard_preprocess — circle detection + annotation."""

from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np
import pytest

from app.services.scorecard_preprocess import annotate_circles

EXAMPLE_PATH = (
    Path(__file__).parent.parent.parent.parent
    / "app" / "data" / "scorecard_examples" / "example_001.jpeg"
)


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
    annotated, content_type, diag = annotate_circles(b"", "image/jpeg")
    assert annotated == b""
    assert diag["preprocessing_applied"] is False


def test_detects_circles_in_example_001(example_image_bytes):
    """example_001.jpeg has many hand-drawn circles — detection should find some."""
    annotated, content_type, diag = annotate_circles(example_image_bytes, "image/jpeg")
    assert diag.get("circles_detected", 0) >= 5, (
        f"Expected ≥5 circles in example_001, got {diag.get('circles_detected')}"
    )
    assert diag["circles_detected"] <= 150, (
        f"Detection blew up — got {diag['circles_detected']} circles"
    )


def test_returns_diagnostics_when_no_circles_detected():
    """A blank white image should detect 0 circles and skip annotation."""
    blank = np.full((1000, 1500, 3), 255, dtype=np.uint8)
    ok, encoded = cv2.imencode(".jpg", blank)
    assert ok
    annotated, content_type, diag = annotate_circles(encoded.tobytes(), "image/jpeg")
    assert diag["preprocessing_applied"] is False
    assert diag["circles_detected"] == 0

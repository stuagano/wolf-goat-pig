# Scorecard Circle Preprocessing Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a server-side preprocessing step that detects hand-drawn circles classically (OpenCV Hough) and draws bright red rectangles around them so the Groq Vision model reliably tags `is_circled: true` for negative values.

**Architecture:** New module `backend/app/services/scorecard_preprocess.py` exposes one function `annotate_circles(image_bytes, content_type) -> (bytes, content_type, diagnostics)`. `scorecard_scan_service.scan_scorecard()` calls it once at the top and reuses the annotated bytes for both the initial Groq call and the strict-mode retry. Errors in preprocessing degrade gracefully — original bytes flow through.

**Tech Stack:** Python 3.12, OpenCV (`opencv-python-headless`), NumPy, Pillow (already a dep), pytest.

**Spec:** [`docs/superpowers/specs/2026-04-28-scorecard-circle-preprocessing-design.md`](../specs/2026-04-28-scorecard-circle-preprocessing-design.md)

---

## File Structure

| File | Responsibility |
|---|---|
| `backend/requirements.txt` | Add `opencv-python-headless` dependency |
| `backend/app/services/scorecard_preprocess.py` (NEW) | Circle detection + image annotation. One public entry point. |
| `backend/app/services/scorecard_scan_service.py` (MODIFY) | Call `annotate_circles` before vision; update prompt; surface diagnostics |
| `backend/tests/unit/services/test_scorecard_preprocess.py` (NEW) | Unit tests for the preprocessing module |

---

## Task 1: Add OpenCV dependency

**Files:**
- Modify: `backend/requirements.txt`

- [ ] **Step 1: Add the dependency line**

In `backend/requirements.txt`, find the line:
```
# Image processing (scorecard compression)
Pillow>=10.0.0
```

Replace it with:
```
# Image processing (scorecard compression + circle detection preprocessing)
Pillow>=10.0.0
opencv-python-headless>=4.9.0,<5.0
numpy>=1.26.0,<3.0
```

(`numpy` is a transitive dep of opencv but pinning it avoids a future surprise.)

- [ ] **Step 2: Install locally**

Run from repo root:
```bash
cd backend && pip install -r requirements.txt
```

Expected: `opencv-python-headless` and `numpy` install without error.

- [ ] **Step 3: Verify imports work**

Run:
```bash
cd backend && python -c "import cv2; import numpy as np; print(cv2.__version__, np.__version__)"
```

Expected: prints two version strings, e.g. `4.9.0 1.26.4`. No `ModuleNotFoundError`.

- [ ] **Step 4: Commit**

```bash
git add backend/requirements.txt
git commit -m "chore(backend): add opencv-python-headless for scorecard circle detection"
```

---

## Task 2: Stub the preprocessing module + first failing test

**Files:**
- Create: `backend/app/services/scorecard_preprocess.py`
- Create: `backend/tests/unit/services/test_scorecard_preprocess.py`

- [ ] **Step 1: Write the first failing test**

Create `backend/tests/unit/services/test_scorecard_preprocess.py`:

```python
"""Unit tests for scorecard_preprocess — circle detection + annotation."""

from __future__ import annotations

from pathlib import Path

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
```

- [ ] **Step 2: Run the test, confirm it fails**

```bash
cd backend && pytest tests/unit/services/test_scorecard_preprocess.py -v
```

Expected: ImportError or ModuleNotFoundError — `app.services.scorecard_preprocess` doesn't exist.

- [ ] **Step 3: Create the module skeleton**

Create `backend/app/services/scorecard_preprocess.py`:

```python
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
```

- [ ] **Step 4: Run the test, confirm it passes**

```bash
cd backend && pytest tests/unit/services/test_scorecard_preprocess.py -v
```

Expected: 1 passed.

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/scorecard_preprocess.py backend/tests/unit/services/test_scorecard_preprocess.py
git commit -m "feat(scorecard-scan): scaffold scorecard_preprocess module"
```

---

## Task 3: Decode + grayscale pipeline (failing on bad input)

**Files:**
- Modify: `backend/app/services/scorecard_preprocess.py`
- Modify: `backend/tests/unit/services/test_scorecard_preprocess.py`

- [ ] **Step 1: Write tests for decode behavior**

Append to `backend/tests/unit/services/test_scorecard_preprocess.py`:

```python
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
```

- [ ] **Step 2: Run the new tests, confirm decode tests fail meaningfully**

```bash
cd backend && pytest tests/unit/services/test_scorecard_preprocess.py -v
```

Expected: 1 passes, 2 fail (current stub always returns the same diag — but `not_implemented` may not match `error` truthiness assertion). At minimum the assertions should now exercise behavior.

- [ ] **Step 3: Implement decode + error handling**

Replace `backend/app/services/scorecard_preprocess.py` with:

```python
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
```

- [ ] **Step 4: Run all tests, confirm decode tests pass**

```bash
cd backend && pytest tests/unit/services/test_scorecard_preprocess.py -v
```

Expected: 3 passed.

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/scorecard_preprocess.py backend/tests/unit/services/test_scorecard_preprocess.py
git commit -m "feat(scorecard-scan): decode pipeline with graceful failure"
```

---

## Task 4: Hough circle detection on real card

**Files:**
- Modify: `backend/app/services/scorecard_preprocess.py`
- Modify: `backend/tests/unit/services/test_scorecard_preprocess.py`

- [ ] **Step 1: Write the failing detection test**

Append to `backend/tests/unit/services/test_scorecard_preprocess.py`:

```python
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
```

Add `import cv2` and `import numpy as np` at the top of the test file if not already present.

- [ ] **Step 2: Run new tests, confirm they fail**

```bash
cd backend && pytest tests/unit/services/test_scorecard_preprocess.py -v
```

Expected: 3 passed (existing) + 2 failed (no `circles_detected` key yet).

- [ ] **Step 3: Implement detection**

Replace `backend/app/services/scorecard_preprocess.py` with:

```python
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
        param1=80,
        param2=25,
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
```

- [ ] **Step 4: Run all tests, confirm pass**

```bash
cd backend && pytest tests/unit/services/test_scorecard_preprocess.py -v
```

Expected: 5 passed. If `test_detects_circles_in_example_001` fails because detection found 0 circles, the Hough params need tuning — try lowering `param2` (e.g. to 18) and re-run.

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/scorecard_preprocess.py backend/tests/unit/services/test_scorecard_preprocess.py
git commit -m "feat(scorecard-scan): hough circle detection on handwriting region"
```

---

## Task 5: Draw red rectangles + JPEG re-encode

**Files:**
- Modify: `backend/app/services/scorecard_preprocess.py`
- Modify: `backend/tests/unit/services/test_scorecard_preprocess.py`

- [ ] **Step 1: Write the failing annotation tests**

Append to `backend/tests/unit/services/test_scorecard_preprocess.py`:

```python
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
```

- [ ] **Step 2: Run tests, confirm new ones fail or skip**

```bash
cd backend && pytest tests/unit/services/test_scorecard_preprocess.py -v
```

Expected: existing 5 pass; new 2 either fail (not enough red pixels) or skip (annotation not applied yet — `preprocessing_applied` is False).

- [ ] **Step 3: Implement annotation**

Replace `backend/app/services/scorecard_preprocess.py` with:

```python
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
        param1=80,
        param2=25,
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
```

- [ ] **Step 4: Run all tests, confirm pass**

```bash
cd backend && pytest tests/unit/services/test_scorecard_preprocess.py -v
```

Expected: 7 passed. If `test_annotation_introduces_red_pixels` fails because detection found 0 circles in `example_001`, see Task 4 Step 4 — tune Hough params.

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/scorecard_preprocess.py backend/tests/unit/services/test_scorecard_preprocess.py
git commit -m "feat(scorecard-scan): draw red rectangles around detected circles"
```

---

## Task 6: Wire preprocessing into scan service + update prompt

**Files:**
- Modify: `backend/app/services/scorecard_scan_service.py`
- Modify: `backend/tests/unit/services/test_scorecard_scan_service.py`

- [ ] **Step 1: Write the failing integration test**

Append to `backend/tests/unit/services/test_scorecard_scan_service.py`:

```python
class TestScanScorecardCallsPreprocessing:
    """scan_scorecard() must run annotate_circles() once and reuse output."""

    def test_preprocessing_called_once_and_diagnostics_returned(self, monkeypatch):
        from app.services import scorecard_scan_service as svc

        call_count = {"n": 0}

        def fake_annotate(image_bytes, content_type):
            call_count["n"] += 1
            return b"ANNOTATED", "image/jpeg", {"preprocessing_applied": True, "circles_detected": 7}

        async def fake_call_groq(image_bytes, content_type, *, strict=False):
            assert image_bytes == b"ANNOTATED", "vision must receive annotated bytes"
            return {
                "players": [{"name": "P1", "confidence": 1.0}, {"name": "P2", "confidence": 1.0}],
                "running_totals": [
                    {"player_index": 0, "hole": h, "value": 0, "is_circled": False, "confidence": 1.0}
                    for h in range(1, 19)
                ] + [
                    {"player_index": 1, "hole": h, "value": 0, "is_circled": False, "confidence": 1.0}
                    for h in range(1, 19)
                ],
            }

        monkeypatch.setattr(svc, "annotate_circles", fake_annotate)
        monkeypatch.setattr(svc, "_call_groq_vision", fake_call_groq)

        result = asyncio.run(svc.scan_scorecard(b"ORIGINAL", "image/jpeg"))

        assert call_count["n"] == 1, "annotate_circles must run exactly once per scan"
        assert result["preprocessing"]["preprocessing_applied"] is True
        assert result["preprocessing"]["circles_detected"] == 7
```

- [ ] **Step 2: Run, confirm test fails**

```bash
cd backend && pytest tests/unit/services/test_scorecard_scan_service.py::TestScanScorecardCallsPreprocessing -v
```

Expected: AttributeError — `annotate_circles` not yet imported in `scorecard_scan_service`, OR `preprocessing` key missing from result.

- [ ] **Step 3: Update the prompt**

In `backend/app/services/scorecard_scan_service.py`, find the closing `}` and `"""` of `EXTRACTION_PROMPT` (the JSON example block ending around line 72). The prompt currently ends like this:

```python
{
  "players": [
    {"name": "John", "confidence": 0.95}
  ],
  "running_totals": [
    {"player_index": 0, "hole": 1, "value": 2, "is_circled": false, "confidence": 0.92},
    {"player_index": 0, "hole": 2, "value": 4, "is_circled": false, "confidence": 0.90},
    {"player_index": 0, "hole": 3, "value": 4, "is_circled": false, "confidence": 1.0}
  ]
}
"""
```

Add the circle hint block as text between the closing `}` line and the closing `"""`, so the file reads:

```python
{
  "players": [
    {"name": "John", "confidence": 0.95}
  ],
  "running_totals": [
    {"player_index": 0, "hole": 1, "value": 2, "is_circled": false, "confidence": 0.92},
    {"player_index": 0, "hole": 2, "value": 4, "is_circled": false, "confidence": 0.90},
    {"player_index": 0, "hole": 3, "value": 4, "is_circled": false, "confidence": 1.0}
  ]
}

CRITICAL — CIRCLE DETECTION HINTS:
Bright red rectangles have been pre-drawn around cells whose values are
CIRCLED on the original card. Treat any value inside a red rectangle as
is_circled: true. Cells WITHOUT a red rectangle are uncircled (positive).
The red rectangles are pre-processing markers — ignore them when reading
the value itself, only use them to determine the sign.
"""
```

Don't change anything earlier in the prompt — the new block is appended only.

- [ ] **Step 4: Add the import + integrate the call**

In `backend/app/services/scorecard_scan_service.py`, near the other imports at the top, add:

```python
from .scorecard_preprocess import annotate_circles
```

Then replace the existing `scan_scorecard` function (around line 223) with:

```python
async def scan_scorecard(image_bytes: bytes, content_type: str) -> dict[str, Any]:
    """
    Send scorecard image to Groq Vision and return extracted running totals
    plus computed per-hole quarter deltas. Retries once if the first attempt
    returns malformed JSON or violates the zero-sum invariant — these are
    the dominant failure modes in practice and a stricter retry catches
    most of them without doubling latency on the happy path.

    Preprocessing: classical circle detection draws red rectangles around
    each detected hand-drawn circle once at the top of the function. The
    annotated bytes are reused for both the initial call and the strict
    retry. Annotation failures degrade gracefully — original bytes are sent.
    """
    annotated_bytes, annotated_ct, preprocessing_diag = annotate_circles(
        image_bytes, content_type
    )

    parse_error: Exception | None = None
    try:
        extracted = await _call_groq_vision(annotated_bytes, annotated_ct, strict=False)
    except json.JSONDecodeError as e:
        logger.warning("First scan returned non-JSON, retrying strict: %s", e)
        parse_error = e
        extracted = None

    if extracted is not None:
        result = _shape_extraction(extracted)
        validation = _validate_zero_sum(result["per_hole_quarters"])
        if validation["valid"]:
            result["validation"] = validation
            result["preprocessing"] = preprocessing_diag
            return result
        logger.warning("Zero-sum violated on first scan: %s — retrying strict", validation["bad_holes"])

    try:
        extracted = await _call_groq_vision(annotated_bytes, annotated_ct, strict=True)
    except json.JSONDecodeError as e:
        if parse_error is not None:
            logger.error("Both scan attempts returned non-JSON")
        raise ValueError(f"Failed to parse vision response: {e}")

    result = _shape_extraction(extracted)
    result["validation"] = _validate_zero_sum(result["per_hole_quarters"])
    result["preprocessing"] = preprocessing_diag
    return result
```

- [ ] **Step 5: Run the new test, confirm it passes**

```bash
cd backend && pytest tests/unit/services/test_scorecard_scan_service.py::TestScanScorecardCallsPreprocessing -v
```

Expected: 1 passed.

- [ ] **Step 6: Run the full scan service test file to confirm nothing regressed**

```bash
cd backend && pytest tests/unit/services/test_scorecard_scan_service.py -v
```

Expected: all tests pass (existing tests + new one).

- [ ] **Step 7: Commit**

```bash
git add backend/app/services/scorecard_scan_service.py backend/tests/unit/services/test_scorecard_scan_service.py
git commit -m "feat(scorecard-scan): integrate circle preprocessing + prompt hint"
```

---

## Task 7: End-to-end smoke test against deployed API

**Files:**
- Read only: `/Users/stuart.gano/.claude/image-cache/37e95972-da2e-44fb-8503-518928b6b62d/1.png`

This task isn't a code change — it's a manual verification gate before declaring done. Skip if the user is in subagent mode and prefers to verify manually after merge.

- [ ] **Step 1: Run the full backend test suite**

```bash
cd backend && pytest tests/unit/services/test_scorecard_preprocess.py tests/unit/services/test_scorecard_scan_service.py -v
```

Expected: all tests pass.

- [ ] **Step 2: Run the preprocessing locally on the recent test image**

```bash
cd backend && python -c "
from pathlib import Path
from app.services.scorecard_preprocess import annotate_circles

src = Path('/Users/stuart.gano/.claude/image-cache/37e95972-da2e-44fb-8503-518928b6b62d/1.png')
annotated, ct, diag = annotate_circles(src.read_bytes(), 'image/png')
print('Diagnostics:', diag)
out = Path('/tmp/annotated_scorecard.jpg')
out.write_bytes(annotated)
print('Wrote', out, 'bytes:', len(annotated))
"
```

Expected: prints diagnostics with `circles_detected ≥ 5` and `preprocessing_applied: True`. Open `/tmp/annotated_scorecard.jpg` and visually confirm red rectangles surround the circled handwritten values on the card.

- [ ] **Step 3: If detection looks weak, tune Hough params**

If you see fewer than ~10 red rectangles on a card with many circles, edit `backend/app/services/scorecard_preprocess.py`:
- Lower `param2` from 25 to 18 (more permissive)
- Or raise `dp` from 1.2 to 1.5 (coarser accumulator)

Re-run Step 2 until annotation looks visually right. Then re-run Step 1 to confirm tests still pass.

- [ ] **Step 4: Commit any tuning**

```bash
git add backend/app/services/scorecard_preprocess.py
git commit -m "tune(scorecard-scan): hough params from real-image smoke test"
```

(Skip if no tuning needed.)

---

## Self-review checklist

Spec coverage check:
- ✅ New module `scorecard_preprocess.py` with single public function — Task 2
- ✅ `opencv-python-headless` dependency — Task 1
- ✅ Hough circle detection pipeline (grayscale, blur, HoughCircles, top-25% crop) — Task 4
- ✅ Sanity bounds (0 or >150 circles → skip annotation) — Task 4 + 5
- ✅ Red rectangles, 4px thick, 8px padding, BGR (0,0,255) — Task 5
- ✅ JPEG q=90 re-encode — Task 5
- ✅ Diagnostics dict (`circles_detected`, `preprocessing_applied`, `image_dimensions`, optional `error`) — Tasks 4, 5
- ✅ Run once at top of `scan_scorecard`, reuse for both calls — Task 6
- ✅ Updated `EXTRACTION_PROMPT` with red rectangle rule — Task 6
- ✅ Result includes `preprocessing` key — Task 6
- ✅ Errors logged + original bytes returned on any failure — all tasks
- ✅ Unit tests against `example_001.jpeg` — Task 4 + 5
- ✅ Tests for decode failure, no-circles, valid-JPEG-output, dimensions preserved — Tasks 3, 4, 5
- ✅ Smoke test against the user-provided image — Task 7

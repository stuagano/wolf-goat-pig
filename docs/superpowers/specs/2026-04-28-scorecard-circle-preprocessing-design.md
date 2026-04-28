# Scorecard Circle Preprocessing — Design

**Date:** 2026-04-28
**Author:** Stuart Gano
**Status:** Approved, ready for implementation plan

## Problem

The scorecard photo scan (`POST /scorecard/scan`) calls Groq Vision (Llama 4 Scout) to extract running quarter totals from a photo of a Wolf Goat Pig scorecard. Circled numbers represent negative values — the dominant convention on these cards.

The model is reliably bad at detecting circles. On a real scorecard with many circled values, every value comes back `is_circled: false`. The zero-sum validator catches the inconsistency (8 of 18 holes failed zero-sum on a recent test), but the strict-mode retry doesn't fix it because the failure mode is the model's circle-detection capability, not its prompt-following.

Final totals from a real test run:

| Player | Scan H18 | Actual card | Match? |
|---|---|---|---|
| Tony | +24 | -76 (TF) | ❌ |
| Erik | +8 | -48 (KG) | ❌ |
| Steve | +40 | +84 (SS) | ❌ |
| Alex | 0 | +40 (AA) | ❌ |
| **Sum** | **+72** | **0** | ❌ |

## Goal

Add a preprocessing step that detects circles classically and visually marks them on the image before the vision model sees it. The model's job becomes "read the value and check for a red rectangle around it" instead of "decide whether a hand-drawn pen squiggle is a circle." The first job it does well; the second it doesn't.

Out of scope: cell-grid alignment, per-cell crop extraction, alternate vision models. This spec is just preprocessing.

## Architecture

**New module:** `backend/app/services/scorecard_preprocess.py`

**Public function:**
```python
def annotate_circles(image_bytes: bytes, content_type: str) -> tuple[bytes, str, dict]:
    """Returns (annotated_bytes, content_type, diagnostics)."""
```

**Integration:** `scan_scorecard()` in `scorecard_scan_service.py` calls `annotate_circles()` once at the top of the function, before any `_call_groq_vision()` call. The annotated bytes are reused for both the initial call and the strict-mode retry. On any preprocessing exception, the original bytes flow through unchanged.

**Where it runs in the pipeline:**

```
Frontend                   Backend (scorecard.py)         Backend (scan service)
preprocessScorecardImage   compress if >2.5MB             annotate_circles  →  Groq Vision
(orientation, downscale)   (existing)                     (NEW)                (existing)
```

**Always-on, not lazy.** Preprocessing runs on every scan, including the first attempt. Lazy-only-on-retry would defeat the purpose since the first attempt is the one most users will see.

**Dependency:** add `opencv-python-headless` to `backend/requirements.txt`. The headless variant has no GUI deps — fits Render's container. Pillow is already a dep.

## Circle detection

OpenCV `HoughCircles` with `HOUGH_GRADIENT`. Standard tool for finding round shapes in a noisy image.

**Pipeline:**
1. Decode image bytes → numpy array
2. Convert BGR → grayscale
3. Median blur (kernel size 3) to suppress paper texture
4. `cv2.HoughCircles` with parameters scaled to image height:
   - `minRadius` ≈ image_height / 80
   - `maxRadius` ≈ image_height / 25
   - `minDist` ≈ image_height / 40
   - `param1=80, param2=25` (initial values; tune from logs)
5. Drop any circle whose center is in the top 25% of the image (pre-printed yardages live there, not handwriting)

**Sanity bounds:**
- Detected count = 0 → log warning, return original image with `preprocessing_applied: False`
- Detected count > 150 → likely false-positive blowout, return original
- Otherwise → annotate

The example scorecard `example_001.jpeg` has roughly 14 circled cells through hole 9 (per ground truth). Healthy detection should land in the 10–30 range. Recall matters more than precision — the model still verifies the value, so a few false-positive red rectangles cost less than missed circles.

**Tuning expectation:** Hough is parameter-sensitive. Initial values are reasonable starting points; will iterate from production logs after first deploys.

## Annotation

For each detected circle, draw a bright red rectangle around its bounding box.

- Color: pure red `(0, 0, 255)` in BGR
- Padding: ~8px outside the circle's bounding box
- Thickness: 4px
- Not filled — keeps the digit inside readable
- Re-encode to JPEG quality 90 to preserve crisp edges

**Why a rectangle, not another circle:** drawing a circle on top of a circle is visually noisy and the model has to disambiguate the original mark from our marker. A bright red rectangle is unambiguous and shape-distinct from anything that exists on a hand-marked scorecard.

## Prompt change

Append to `EXTRACTION_PROMPT` in `scorecard_scan_service.py`:

```
CRITICAL — CIRCLE DETECTION HINTS:
Bright red rectangles have been pre-drawn around cells whose values are
CIRCLED on the original card. Treat any value inside a red rectangle as
is_circled: true. Cells WITHOUT a red rectangle are uncircled (positive).
The red rectangles are pre-processing markers — ignore them when reading
the value itself, only use them to determine the sign.
```

This shifts the model's responsibility from "detect a hand-drawn circle" (it's failing at this) to "detect a bright red rectangle" (vision models handle this reliably).

## Diagnostics

The preprocessing function returns a third element with diagnostics:

```python
{
    "circles_detected": 23,
    "preprocessing_applied": True,   # False if sanity bounds tripped
    "image_dimensions": [width, height],
    "error": None,                   # error string if exception caught
}
```

The scan service includes this dict in its response under a new top-level `preprocessing` key, alongside the existing `validation` key. The frontend can surface this in the review UI later.

## Error handling

All preprocessing errors caught and logged. Preprocessing must never block a scan.

```python
try:
    annotated, ct, diag = _annotate_pipeline(image_bytes, content_type)
    return annotated, ct, diag
except Exception as e:
    logger.warning("Scorecard preprocessing failed: %s", e)
    return image_bytes, content_type, {
        "preprocessing_applied": False,
        "error": str(e),
    }
```

## Testing

New test file: `backend/tests/unit/services/test_scorecard_preprocess.py`

- `test_annotate_example_001_detects_circles` — runs against the existing reference image, asserts ≥10 circles detected
- `test_returns_original_on_decode_failure` — passes garbage bytes, asserts original returned with `error` populated
- `test_returns_original_on_no_circles_detected` — passes a blank white image, asserts no annotation applied
- `test_output_is_valid_jpeg` — asserts the returned bytes decode as a JPEG with the same dimensions as the input

No new integration test for the full scan service — existing tests still cover the end-to-end path with annotated images flowing through.

## Migration / rollback

- New code, new module, new dep — no schema or API contract changes
- Response shape gains a `preprocessing` key; existing consumers ignore unknown keys
- Rollback: revert the commit and drop `opencv-python-headless` from requirements.txt

## Out of scope (for v1)

- Cell-grid alignment (would be needed for coordinate-hint or classical-authority approaches)
- Per-cell crop extraction
- Per-scanner-style prompt tuning
- Alternate vision models
- Frontend visualization of detected circles

These can be follow-ups if v1's recall isn't sufficient.

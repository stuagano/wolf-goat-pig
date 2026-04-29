# Scorecard Scan — Improvement Roadmap

Improvement ideas for the photo-to-quarters pipeline. Companion to `SCORECARD_PHOTO_CAPTURE.md` (feature spec) and the implementation in `backend/app/services/scorecard_preprocess.py` + `scorecard_scan_service.py`.

## Current pipeline (as of 2026-04-28)

1. Decode image bytes (OpenCV).
2. Hough circle detection on grayscale + median blur (`param2=40`, top 25% cropped to skip header).
3. Draw bright red rectangles around each detected circle.
4. POST to Groq Vision (Llama 4 Scout) with annotated image + reference example + prompt.
5. Parse JSON, apply circle=negative, compute per-hole deltas.
6. Validate zero-sum across players per hole. If violated, retry once with a stricter prompt and `temperature=0`.

## Known failure modes

| Failure | Frequency | Where |
|---|---|---|
| Hough misses hand-drawn circles (broken / elliptical) | High on photos taken at an angle | `_detect_circles` |
| Hough finds spurious circles in printed scorecard graphics | Medium | `_detect_circles` (mitigated by top-crop only) |
| Vision misreads `6` as `u`/`U` | Medium | Vision model — partially mitigated by prompt hint |
| Grid topology errors (off-by-one column, swapped row) | Low-medium | Vision model |
| Zero-sum violation triggers full re-scan | All retries are full-image | `scan_scorecard` |
| Single hard-coded reference example doesn't match the scorer's handwriting | Persistent | `_load_reference_image` |

## High-leverage improvements

### 1. Perspective correction + grid cell crops (biggest unlock)

**What:** Detect the scorecard's outer 4-corner contour, warp to a known rectangle, then split into a 4×18 cell grid.

**Why:** The model is currently solving two hard problems at once — find the grid AND read each cell's digits. With pre-cropped cells, each request becomes per-cell OCR, which is dramatically more reliable on handwriting. Every downstream step gets easier:
- Hough operates on a normalized, deskewed image
- The vision prompt no longer needs to describe the grid
- Confidence is per-cell, not per-card
- Errors are bounded to one cell

**Cost:** Medium. Need contour detection for the outer frame, perspective transform, and a calibration step to map detected lines to the printed cell grid. Works only if the full card is in frame and not obscured.

**Tradeoff:** Adds a hard dependency on detecting the outer rectangle. Need a fallback path when warp fails — keep the current end-to-end vision flow as the fallback.

### 2. Contour-based circle detection alongside Hough

**What:** Threshold image, find contours, filter by circularity `4π·area/perimeter²` (≈1.0 for circles, lower for hand-drawn) and aspect ratio. Union with Hough results.

**Why:** Hough is sensitive to closed, smooth circles. Hand-drawn circles are often broken or elliptical and Hough misses them. Contour detection catches the irregular ones; combining both raises recall without much precision loss (we still draw red rectangles, the vision model tolerates over-marking better than under-marking).

**Cost:** Low — pure OpenCV, no new dependencies.

**Tradeoff:** Risk of over-marking false positives. Mitigate with a minimum area threshold and a circularity floor.

### 3. Targeted re-ask on zero-sum failure

**What:** Instead of re-scanning the entire card with a strict prompt when zero-sum fails, identify the bad hole(s), crop only those columns from the annotated image, and re-ask the vision model with a focused prompt.

**Why:** `_validate_zero_sum` already returns `bad_holes`. We have the information to localize. Cropping reduces tokens, focuses the model's attention, and is faster/cheaper than re-running the whole card.

**Cost:** Low-medium. Need column boundary estimation (free if grid detection from #1 is in place).

**Tradeoff:** If grid detection is unreliable, the re-ask cropping is unreliable too. Gate this on #1.

## Cheap but impactful

### 4. Confidence-driven UI highlights

**What:** Flag any cell with `confidence < 0.85` in the post-scan review screen — different border color, tap-to-edit. Per-cell confidences already come back from the model.

**Why:** The system will never be perfect on handwriting. Optimizing for fast human correction beats chasing the last 5% of model accuracy. The user is already going to review the scan; surfacing where to look is nearly free.

**Cost:** Low — frontend-only.

**Tradeoff:** Model confidence is sometimes miscalibrated (high confidence on wrong reads). Don't *trust* high confidence — just use low confidence as a hint.

### 5. Golden-image regression suite

**What:** Collect 5-10 real scorecards with ground-truth JSON. On every preprocess change, run the pipeline against all of them and report cell-level accuracy.

**Why:** The recent `param2=30→40` tune (commit `0aaf1ff`) was eyeballed. Without numeric pass/fail, future tuning will keep being eyeballed. A small suite catches regressions and makes parameter sweeps possible (auto-search for the best `param2`).

**Cost:** Low — tests only. Need a fixtures directory and a script that diffs extracted vs ground truth per cell.

**Tradeoff:** Real scorecards are sensitive — only commit ones with permission, anonymize player names if needed.

### 6. Auto-built few-shot examples from user corrections

**What:** When a user fixes a scanned cell in the review UI, save the cell crop + corrected label. On future scans, look up the closest visual match (by handwriting embedding, or just the same scorer if known) and inject it as a few-shot example in the prompt.

**Why:** Currently the prompt has one hard-coded `example_001` reference image. A library of corrections grows automatically and adapts to each scorer's handwriting (the "9u = 96" hint is one scorer's quirk; others have different ones).

**Cost:** Medium. Need a storage layer for cell crops + labels, and a similarity lookup. Cheapest version: keyed on `user_id`, no embedding needed.

**Tradeoff:** Crop storage adds DB/blob complexity. Start with the keyed-by-user version before adding similarity search.

## Lower priority

### 7. Adaptive Hough parameters

**What:** Auto-tune `param2` and radius bounds based on image stats (edge density, histogram, detected line spacing).

**Why:** `param2=40` is a hard-coded compromise. Different images need different sensitivities.

**Cost:** Low.

**Tradeoff:** Adaptive tuning can introduce its own bugs. Probably not worth doing without #5 (regression suite) in place to verify no accuracy loss.

### 8. Multi-model ensemble vote

**What:** Run Groq + a second vision model (Gemini, Claude) and reconcile. Agreement → high confidence; disagreement → flag for user.

**Why:** Different models fail on different cells. Ensemble accuracy is reliably higher than any single model.

**Cost:** High — doubles API spend, doubles latency unless run in parallel.

**Tradeoff:** Only worth it once #1-#3 are exhausted. Low ROI if the pipeline is already 95%+ accurate per cell.

### 9. Plausibility check on per-hole deltas

**What:** Add a soft check: per-hole quarter changes in WGP follow a smooth distribution (typically ±5-10, rarely ±50). Sudden +50 / -50 / +50 across consecutive holes is suspicious. Flag for re-scan or user review.

**Why:** Cheap sanity guard against the worst extraction errors (digit confusion turning 6 into 96 etc.).

**Cost:** Low.

**Tradeoff:** WGP can have legitimate large swings (doubles, aardvarks). Tune the threshold conservatively or expose it as a soft warning, not a hard error.

## Recommended sequencing

1. **Start:** #5 (regression suite) — needed to validate any other change.
2. **Then:** #1 (perspective + grid) — biggest accuracy unlock, downstream gains for everything.
3. **Then:** #4 (confidence highlights) — fastest user-experience win, parallel-able with #1.
4. **Then:** #2 (contour circles) and #3 (targeted re-ask) — complete the perception/recovery layer.
5. **Later:** #6 (correction-fed few-shot), then revisit #7-#9 if accuracy still has gaps.

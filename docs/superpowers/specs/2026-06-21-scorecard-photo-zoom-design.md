# Scorecard Photo Zoom (in-app totals validation) — Design

- **Date:** 2026-06-21
- **Status:** Approved (design)
- **Scope:** Part A only. Part B (persist the photo + backfill per-hole later) is a
  separate follow-on design.

## Problem

The scan reliably reads the final TOTAL column but the user wants to **validate those
totals against the actual photo without leaving the app** during the totals-first
review. Today the captured photo is processed and discarded, so there's nothing to look
at on the review screen.

## Goal

Let the user zoom/pan the captured scorecard photo from the review screen to verify the
totals (and any value), focused on the totals column.

## Design

- **Retain the original captured photo.** `ScorecardPhoto` currently preprocesses the
  file, scans, and drops it. Keep an object URL of the **original** file (sharpest, no
  red-rectangle annotations) and pass it as a prop to `ScorecardReview`. Revoke the URL
  on unmount to avoid a leak.
- **"📷 Check photo" control in the review.** Shown only when a photo URL is present.
  Tapping opens a full-screen overlay.
- **`ScorecardPhotoZoom` overlay** (new component): full-screen, dark backdrop, the photo
  in an `overflow:auto` container scaled via CSS `transform: scale`. Controls: **+ / −
  zoom buttons** and a **close (✕)** button; **pan by scroll/drag**. On open it **scrolls
  to the right edge** (the TOT column lives on the right of each page) so the totals are
  immediately in view. No new npm dependency.
- **View-only.** No editing or persistence here; Part B will persist the photo.
- Available in both totals and grid review modes (it's just validation).

## Components / files

- Create `frontend/src/components/game/ScorecardPhotoZoom.jsx` — the overlay (props:
  `src`, `onClose`).
- Modify `frontend/src/components/game/ScorecardPhoto.jsx` — keep the original file's
  object URL (state), pass `photoUrl` to `ScorecardReview`, revoke on unmount.
- Modify `frontend/src/components/game/ScorecardReview.jsx` — accept `photoUrl`, render
  the "Check photo" button (when present) + the overlay on toggle.

## Out of scope (YAGNI)

Persistence/storage (Part B), auto-crop to the exact totals box (we don't extract its
coordinates — pan/zoom covers it), pinch-zoom via a library (CSS buttons first; revisit
if clunky), editing values from the overlay.

## Testing

- `ScorecardReview`: the "Check photo" button renders when `photoUrl` is set and is
  absent when it isn't; clicking it shows the overlay; close hides it.
- `ScorecardPhotoZoom`: renders the image with the given `src`; +/− change the zoom
  scale; ✕ calls `onClose`.
- `ScorecardPhoto`: a captured file produces a `photoUrl` passed to review (object-URL
  creation mocked).

## Rollout

Frontend-only; no backend/migration. Pre-push gate: typecheck + vitest + build.

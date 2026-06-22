# Persist Scorecard Photo + Backfill Per-Hole Later (Part B) — Design

- **Date:** 2026-06-21
- **Status:** Approved (design)
- **Builds on:** the "scan a finished round" flow, the totals-first review, and the
  in-app photo zoom (`ScorecardPhotoZoom`, Part A).

## Problem

The scan reliably captures the final totals (settle-up), and the totals-first review
saves a round with correct standings — but the **per-hole detail is left blank**, and the
photo is **discarded after the scan**. The user wants to **save the photo with the round**
so that later (at home, possibly on another device) they can **pull it up and fill in the
hole-by-hole numbers** by reading the real card.

## Goal

Persist the scorecard photo on the saved round, let the user view it (zoom) on any device
from the completed-rounds list, and let them backfill the per-hole quarters later —
without changing the already-correct settle-up totals.

## Decisions (locked)

1. **Storage: a Postgres column** holding a downscaled JPEG as base64 (no object storage /
   new service). Cap the image at ~1200px / ~150–250KB so the DB stays lean.
2. **Save path: `image_base64` on the existing `POST /games/from-scorecard`** JSON body
   (no separate upload endpoint, no multipart).
3. **Backfill semantics: final totals are LOCKED.** The editor shows each player's locked
   total and **warns (non-blocking) if the entered per-hole doesn't sum to it**, so
   backfilling detail can't silently change who-owes-what.

## Data model

- Add `scorecard_image: Text | None` to `GameStateModel` (the round row). SQLite dev:
  `create_all` adds it. Postgres prod: a new `backend/migrations/NNNN_add_scorecard_image_postgres.sql`
  (`ALTER TABLE game_states ADD COLUMN scorecard_image TEXT`), applied once by the existing
  `migrations_runner` at startup ("already exists" tolerated).

## Backend

- **Save:** `from-scorecard` request gains optional `image_base64: str | None`. When
  present, store it on the new column when persisting the round. (Validated lightly: a
  data-URL or raw base64 string under a size ceiling, e.g. 2 MB; oversize → ignored, round
  still saves.)
- **Serve:** `GET /games/{id}/scorecard-photo` → returns the image (decoded bytes with the
  right content-type, or 404 if none). Keeps large blobs out of the `/state` payload.
- **Backfill:** `PATCH /games/{id}/scorecard` with `{ per_hole_quarters: [...] }` →
  recompute `hole_history` + standings via the existing `completed_game_service`
  (`build_hole_history`), re-persist the round state and `GamePlayerResult`s. Returns the
  updated state. The endpoint does NOT require the totals to match (it just recomputes
  standings from whatever per-hole is sent) — the "locked totals" guard is a frontend
  warning, and the recompute keeps standings = sum of the new per-hole.

## Frontend

- **Save:** when saving a scanned round, downscale the retained original photo to ~1200px
  and include it as `image_base64` in the `from-scorecard` POST. Best-effort: if encoding
  fails, save the round without the photo.
- **View later:** the completed-round view (where "View Game" lands) shows a **"📷 Photo"**
  button when the round has one (fetches `/games/{id}/scorecard-photo`), opening the same
  `ScorecardPhotoZoom` overlay.
- **Backfill:** a **"Fill in holes"** action opens the per-hole **grid** (reuse the
  `ScorecardReview` grid, pre-filled from the round's current `per_hole_quarters`), with the
  photo zoom available. It shows each player's **locked final total** and warns if the
  entered per-hole running totals don't reach it. **Save** → `PATCH /games/{id}/scorecard`.

## Error handling

- Oversize/garbled `image_base64` → ignored; the round still saves (photo just absent).
- `GET scorecard-photo` with no stored image → 404; the UI simply hides the Photo button.
- `PATCH` on a non-existent/incomplete round → 404/400; existing graceful patterns.
- Backfill that doesn't reach the locked totals → saved anyway (standings recompute from
  what's entered), with the frontend warning shown — consistent with "warn, don't block."

## Testing

**Backend:** `from-scorecard` stores `image_base64` (and tolerates oversize/missing);
`GET /scorecard-photo` returns the bytes / 404; `PATCH /scorecard` recomputes hole_history
+ standings from new per-hole and re-persists; migration column present.
**Frontend:** save includes `image_base64`; completed-round Photo button fetches + opens
the overlay; the fill-in grid loads current per-hole, the locked-total warning fires on
mismatch, and Save calls `PATCH`.

## Scope (YAGNI)

One photo per round; no multi-page/multi-photo; reuse `ScorecardPhotoZoom` + the
`ScorecardReview` grid; no re-running OCR on backfill (the user types from the photo); no
image editing/cropping beyond the save-time downscale.

## Rollout

Backend + frontend deploy together (push to main). DB migration auto-applies at startup
(postgres) / `create_all` (sqlite). Pre-push gate: backend ruff+pytest, frontend
typecheck+vitest+build.

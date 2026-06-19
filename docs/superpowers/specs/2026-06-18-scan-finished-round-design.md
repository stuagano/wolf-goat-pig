# Scan a Finished Round — Design

- **Date:** 2026-06-18
- **Status:** Approved (design)
- **Approach:** A — standalone "scan a finished round" path

## Problem

Scorecard scanning (`/scorecard-scan`) can only save into an **existing active
game**. Creating a game requires the multiplayer join-code → join → start flow,
so there is no way to record a completed round from a scorecard photo without
going through the live game flow. Scanning is meant to be a co-equal alternative
to live in-app scoring, not a feature gated behind it.

## Goal

A self-contained "scan a finished round" path: snap a photo of a completed Wolf
Goat Pig scorecard, confirm the players and quarters, and save a recorded round
that appears in standings/history **identically to a live-scored game** — with
no game setup or join-code dance.

## Non-goals (YAGNI)

- Editing or re-scanning an already-recorded round.
- A course picker (default to Wing Point).
- GHIN posting on this path (the scan yields quarters, not gross strokes — there
  is nothing to post).
- Capturing teams / gross golf scores / betting events. The paper card only has
  running quarter totals per player, so a scanned round is quarters-only.

## User flow

1. `/scorecard-scan` shows two choices:
   - **Scan a finished round** (new, primary) → camera capture, no game required.
   - **Add to an active game** (existing) → game picker (unchanged).
2. Capture → preprocess (existing) → `POST /scorecard/scan` (unchanged) →
   `{ players: [{name, confidence}], per_hole_quarters: [{player_index, hole, quarters}], running_totals }`.
3. **Review screen:**
   - **Player mapping** — one dropdown per scanned name, defaulted to the
     fuzzy-best roster match. User can change it or choose
     **"keep as typed (unlinked)"**.
   - **Quarters** — existing per-hole review/edit grid.
   - **Date** — defaults to today, editable. Course defaults to Wing Point.
   - **Zero-sum** — if any hole's quarters don't sum to zero, show a
     **non-blocking warning**; Save is still allowed (the user has confirmed the
     values off the card).
4. **Save** → `POST /games/from-scorecard` → "Round recorded" → View Game / Home.

## Backend

### New endpoint: `POST /games/from-scorecard`

Request:

```json
{
  "players": [ { "name": "John", "player_profile_id": 12 } ],
  "per_hole_quarters": [ { "player_index": 0, "hole": 1, "quarters": 2 } ],
  "course_name": "Wing Point",
  "played_at": "2026-06-18"
}
```

- `players`: 4–6 entries, in scan order. `player_profile_id` may be `null`
  (unlinked) or omitted.
- `per_hole_quarters`: per player_index per hole (holes 1–18).
- `course_name`, `played_at`: optional; default to `"Wing Point"` and today.

Behavior:

1. Validate `player_count ∈ {4, 5, 6}` and that `per_hole_quarters` references
   valid player indices / holes 1–18.
2. Assign each player a stable id (`p1`..`pN`). Resolve `player_profile_id` from
   the canonical `legacy_name` when not supplied and a matching `PlayerProfile`
   exists; otherwise store `null`. Name is always stored.
3. Build `hole_history`: for each hole, `points_delta = { player_id: quarters }`;
   derive `standings` (sum of per-hole deltas).
4. Create `GameStateModel` with these players + `hole_history`,
   `game_status="completed"`, `course_name`, `created_at = played_at or now`.
5. Persist results via a **shared helper** extracted from
   `/{game_id}/complete` → `GameRecord` + `GamePlayerResult`
   (earnings, holes_won, rank, profile link).
6. Return `{ "game_id": "...", "status": "completed" }`.

Zero-sum: do **not** reject holes whose quarters don't sum to zero — store as
given. The response may include a `warnings` field echoing the offending holes
(diagnostic only).

Transactional: build state + persist results in a single commit; roll back on
any error so a failed save never leaves a half-created game.

### Refactor

Extract the `GameRecord` / `GamePlayerResult` persistence block from
`mark_game_complete` (`backend/app/routers/games.py`, ~lines 785–end) into a
reusable function (e.g. `persist_completed_game(db, game)`), called by both
`/{game_id}/complete` and `/from-scorecard`. **No behavior change** to
`/complete` — existing tests must stay green.

### Roster resolution

Mapping of scanned name → canonical legacy name is done client-side via
`GET /legacy-players`. The endpoint resolves `player_profile_id` by matching
`PlayerProfile.legacy_name` when not provided. Unlinked players store
`player_profile_id = null` and name only.

## Frontend

### `ScorecardScanPage`

- Landing offers two actions: **"Scan a finished round"** (→ new-round mode) and
  **"Add to an active game"** (→ existing picker, unchanged).
- New-round mode renders `ScorecardPhoto` with no `gameId` and `mode="new-round"`;
  on save it routes through the new endpoint and shows the success screen.

### `ScorecardPhoto`

- Add `mode` prop (`"attach"` | `"new-round"`). `"attach"` behaves as today
  (`POST /games/{id}/scores`). `"new-round"` posts the confirmed payload to
  `POST /games/from-scorecard`.
- Skip the GHIN modal in new-round mode.
- Fix stale copy ("Gemini is extracting…" → "Reading scorecard…").

### `ScorecardReview`

- Add a **player-mapping** section: per scanned player, a dropdown of roster
  names (from `/legacy-players`), defaulted to the fuzzy-best match (client-side
  similarity on the scanned name), plus a **"keep as typed (unlinked)"** option.
- Add an editable **date** field (default today).
- Keep the per-hole quarters review/edit grid; surface the non-blocking zero-sum
  warning.
- `onConfirm` returns `{ players: [{name, player_profile_id|null}], per_hole_quarters, played_at }`.

## Error handling

- Scan failure: existing error UI (Try Again / Enter Manually).
- Save failure: existing error UI; endpoint is transactional so no partial game
  is left behind.
- Unmapped names: allowed (unlinked); never blocks save.
- Non-zero-sum holes: warn, allow.

## Testing

Backend (pytest):

- `from-scorecard` happy path: 4 players × 18 holes → `GameStateModel`
  completed + `GameRecord` + 4 `GamePlayerResult` with correct earnings/rank.
- Profile resolution: a name matching a `PlayerProfile.legacy_name` links
  `player_profile_id`; an unmatched name → `null`.
- A non-zero-sum hole is stored, not rejected.
- `player_count` validation rejects 3 or 7.
- Shared-helper parity: `/complete` still produces identical records (existing
  tests stay green).

Frontend (vitest):

- `ScorecardScanPage`: "Scan a finished round" enters new-round mode with no game.
- `ScorecardReview`: mapping dropdown defaults to the fuzzy-best match;
  "keep as typed" yields a `null` profile.
- `ScorecardPhoto` new-round save posts the correct `/games/from-scorecard`
  payload and skips GHIN.

## Rollout

Frontend + backend deploy together (push to `main` auto-deploys Vercel + Render).
No DB migration (reuses existing tables). Run the full gate before push:
`frontend: npm run typecheck && npx vitest run && npm run build`;
`backend: ruff check && ruff format --check && pytest`.

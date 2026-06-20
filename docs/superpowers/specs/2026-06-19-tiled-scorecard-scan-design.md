# Tiled Adaptive Scorecard Scanning — Design

- **Date:** 2026-06-19
- **Status:** Approved (design)
- **Builds on:** the existing Groq Vision scorecard scanner (`scorecard_scan_service.py`) and the "scan a finished round" flow.

## Problem

A live scan of a real, dense **5-man** phone scorecard scored **16%** front-nine
cell accuracy and **missed the 5th player entirely** (written in the lower band
below Par). The single whole-card call can't resolve the tiny handwritten cells,
and full-resolution preprocessing is too slow on free-tier infra — so a bigger
whole-card image isn't the answer. Reading the card by region (cropping it into
halves) *did* work by hand.

## Goal

Make the scanner reliably read dense multi-man cards by (a) telling it exactly
which players to find (pre-picked from the roster) and (b) falling back to a
**tiled** per-region scan when a cheap single call fails — without paying for
tiling on easy cards.

## Decisions (locked)

1. **Adaptive trigger:** one whole-card call first; tile only if it fails.
2. **Pre-pick players from the roster before capture** — the scan knows the
   exact names + count up front (both scan paths have known players).
3. **Tiling = Approach A:** 2 tiles, left/right page halves, full height.
4. `players` is an **optional form field** on the existing `POST /scorecard/scan`
   (no new endpoint).
5. The review screen **drops name-mapping** when players are pre-picked (mapping
   stays only as a manual override).
6. Tiling split is a **plain width/2** of the deskewed image (no fold detection).

## Flow

**New-round path** (`/scorecard-scan` → "Scan a finished round"):
pre-pick players (roster multiselect) → capture → adaptive scan (sends names) →
review/confirm quarters → save.

**Attach-to-game path:** unchanged except it passes the game's players to the
scan and skips review name-mapping.

## Backend

### Endpoint

`POST /scorecard/scan` gains an optional form field `players` — a JSON array of
expected player names, e.g. `["CK","SS","KG","BH","SG"]`. Absent → current
behavior (auto-detect; tile on zero-sum failure only).

### `scan_scorecard(image_bytes, content_type, expected_players=None)`

1. Downscale to the 2048px preprocessing working size; run deskew → crop → annotate
   (existing pipeline) for the single-call attempt.
2. **Single guided call** — when `expected_players` is given, the prompt states:
   *"Expect exactly these N players: [names]. Read each player's 18-hole running
   totals."* (When absent, the current generic prompt.)
3. **Validate** the result:
   - per-hole zero-sum holds (existing `_validate_zero_sum`), AND
   - every expected player is present (matched by normalized name).
4. **Valid → return** (`method="single"`). Cheap path = 1 Groq call.
5. **Invalid → tile** (see below), `method="tiled"`.
6. Return the existing shape (`players`, `running_totals`, `per_hole_quarters`,
   `validation`) plus `method` for observability.

### Tiling (Approach A)

- `deskew_to_card` once on the working-size image; **do not** tight-crop (the
  lower-band 5th player must survive).
- Split the deskewed image at **width/2**: left = front nine, right = back nine,
  each **full height**.
- `annotate_circles` on each half (cheap at half size).
- One **guided call per half**: *"This is the [front|back] nine. Read holes
  [1–9|10–18] running totals for these players: [names]. Ignore golf-score rows
  and notes."*
- **Merge by player:** for each expected player, take holes 1–9 from the left
  result and holes 10–18 from the right; align extracted rows to expected names
  (normalized match, fall back to row order). Build combined `running_totals` →
  `per_hole_quarters` → `_validate_zero_sum`.
- Tiling adds 2 Groq calls (total 3 on a hard card; ~60–80s worst case).

### Trigger summary

| expected_players | tile when |
|---|---|
| provided | zero-sum invalid OR any expected player missing |
| absent | zero-sum invalid |

## Frontend

- **Pre-pick step** (new-round mode): a roster multiselect (`/legacy-players`)
  before `ScorecardCapture`. Picked names flow to the scan and to review.
- `ScorecardPhoto`: send `players` (picked names, or the game's players in attach
  mode) in the `/scorecard/scan` form data.
- `ScorecardReview`: when players are known, render fixed player rows (no mapping
  dropdowns); keep mapping only as a manual override if the scan can't align.

## Error handling

- Each tile call degrades gracefully (a failed/garbled tile falls back to the
  single-call result for those holes rather than erroring the whole scan).
- If tiling also fails zero-sum, return the better of the two attempts with
  `validation.valid=false` — the review/correct screen remains the safety net.
- Non-image bytes / preprocessing failures: existing graceful fallthrough.

## Testing

**Backend unit:**
- Guided prompt includes the expected player names when provided.
- Adaptive: a valid single result does NOT tile; an invalid one DOES (mock
  `_call_groq_vision`).
- Merge: left holes 1–9 + right holes 10–18 → correct combined `running_totals`
  and `per_hole_quarters`.
- Split helper produces two sub-images from a deskewed frame.
- `method` is `"single"` vs `"tiled"` accordingly.

**Live eval (on-demand, `GROQ_API_KEY`):** extend the existing held-out accuracy
test to pass the 5 known players and assert the tiled path beats the 16%
single-call baseline (and finds all 5 players).

**Frontend:** pre-pick step renders and gates capture; scan posts `players`;
review uses known players (no mapping dropdowns).

## Scope (YAGNI)

2 tiles only; proportional width/2 split (no fold/band detection); keep the
single-call path; simple normalized-name alignment. No 3rd lower-band tile.

## Rollout

Frontend + backend deploy together (push to main). No DB migration. Pre-push
gate: frontend typecheck+vitest+build; backend ruff+pytest. Note: the live eval
is the real accuracy check and needs `GROQ_API_KEY` (not in CI).

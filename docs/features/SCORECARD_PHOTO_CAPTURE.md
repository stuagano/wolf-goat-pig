# Scorecard Photo Capture — Feature Spec

## Overview

Allow users to photograph a physical scorecard that has **quarters (wagering results)** written on it, extract those values via OCR, then confirm/edit before saving to a game. This is the primary data being captured — not strokes.

### How Quarters Are Tracked on Physical Cards

Players write **running totals** next to each hole — not per-hole values. This avoids mental math during the round. Additionally, **circled numbers mean negative** (quarters lost). There are no minus signs.

Example for one player's row on the card:
```
Hole:   1    2    3    4    5    6    7  ...
Card:   2    4   ③    1    3    5   ④  ...
```
Reading this:
- Hole 1: running total = +2 → per-hole = **+2**
- Hole 2: running total = +4 → per-hole = **+2**
- Hole 3: running total = -3 (circled) → per-hole = **-7** (swing from +4 to -3)
- Hole 4: running total = +1 → per-hole = **+4** (swing from -3 to +1)
- Hole 5: running total = +3 → per-hole = **+2**
- Hole 6: running total = +5 → per-hole = **+2**
- Hole 7: running total = -4 (circled) → per-hole = **-9**

The system must:
1. **Detect circled numbers** as negative values
2. **Recognize values as running totals**, not per-hole amounts
3. **Compute per-hole deltas** by diffing consecutive running totals (hole 1 uses the value itself as the delta, assuming starting from 0)

---

## User Flow

### 1. Entry Point
- **"Scan Scorecard"** button on the `SimpleScorekeeper` interface
- Also accessible from `GameCompletionView` for post-round bulk entry
- Accessible from game creation as a "Log quarters from a completed round" path

### 2. Capture
- Tap "Scan Scorecard" → opens device camera via `<input type="file" accept="image/*" capture="environment">`
- Also supports selecting an existing photo from the camera roll
- Brief overlay guide: _"Make sure all 18 holes and player names/quarters are visible."_
- Preview the captured image so the user can retake if blurry/cropped

### 3. Upload & Processing
- Image is uploaded to the backend (`POST /api/scorecard/scan`)
- Backend sends the image to Claude Vision API for extraction
- Frontend shows a loading state: _"Reading your scorecard..."_
- Target processing time: < 5 seconds

### 4. Confirmation & Editing (Critical Step)

The review screen has **two rows per player per hole**: the running total (what's on the card) and the computed per-hole delta (what gets saved).

- Display extracted data in an editable review screen:
  - **Player names** — mapped to existing game players
  - **Running totals row** (editable) — shows what was extracted from the card, with circled values shown as negative with a visual circle indicator. **This is what users edit** because it matches what they see on the physical card.
  - **Per-hole quarters row** (computed, read-only) — auto-calculated from running total diffs. Updates live as the user edits running totals.
  - **Final total** — the last running total value should match the overall quarters result for each player
- **Zero-sum validation**: Each hole's computed per-hole quarters across all players must sum to zero. Highlight any hole that doesn't balance.
- Visual indicators:
  - **High-confidence values** shown normally
  - **Low-confidence values** highlighted (yellow/orange border) — user should double-check
  - **Unreadable values** left blank with a red border
  - **Circled (negative) values** displayed with a circle indicator to match card notation
- Users tap running total cells to edit — per-hole deltas recompute automatically
- "Confirm Quarters" button is disabled until:
  - All running total cells have values
  - Every hole's per-hole deltas sum to zero across players
- Side-by-side or toggle view of the original photo for reference

### 5. Save

**Each hole is saved as an independent event** — this matches the existing data model and preserves per-hole history. The running-total-to-delta conversion is purely an input/extraction concern; by the time data reaches the backend, it looks identical to manual entry.

- Confirmed per-hole quarters are submitted through the existing `POST /games/{gameId}/quarters-only` endpoint
- Payload format matches the existing `QuartersOnlyRequest`:
  ```json
  {
    "hole_quarters": {
      "1": { "player_abc": 2, "player_def": -1, "player_ghi": -1 },
      "2": { "player_abc": -3, "player_def": 3, "player_ghi": 0 },
      ...
    }
  }
  ```
- No new data model for scores — the photo scan is just an alternative input method that produces the same per-hole quarter records
- Original photo stored for audit/reference (linked via `scorecard_scans` table)
- The `scorecard_scans` table stores the raw extraction and photo, but the **source of truth for scores remains the existing per-hole game state**

---

## Technical Architecture

### Frontend

#### New Components

| Component | Purpose |
|---|---|
| `ScorecardCapture.jsx` | Camera input, image preview, retake flow |
| `ScorecardReview.jsx` | Editable grid of extracted quarters with confidence indicators and zero-sum validation |
| `PlayerMapper.jsx` | Map extracted player names → existing game players |
| `ScorecardPhoto.jsx` | Orchestrator component managing the full capture → review → save flow |

#### State Shape (within ScorecardPhoto orchestrator)

```javascript
{
  step: "capture" | "processing" | "review" | "saving",
  image: {
    file: File,
    previewUrl: string,
  },
  extraction: {
    players: [
      { extractedName: "John", confidence: 0.95, mappedPlayerId: "player_abc" }
    ],
    // Raw running totals as extracted from the card
    runningTotals: {
      // playerIndex → running total per hole
      0: [
        { hole: 1, runningTotal: 2, isCircled: false, confidence: 0.92 },
        { hole: 2, runningTotal: 4, isCircled: false, confidence: 0.90 },
        { hole: 3, runningTotal: 3, isCircled: true, confidence: 0.85 }, // circled = -3
        ...
      ]
    },
    // Computed per-hole deltas (what gets saved)
    perHoleQuarters: {
      0: [
        { hole: 1, quarters: 2 },   // 0 → +2
        { hole: 2, quarters: 2 },   // +2 → +4
        { hole: 3, quarters: -7 },  // +4 → -3
        ...
      ]
    }
  },
  edits: {
    // User overrides to running totals, keyed by "playerIndex-holeNumber"
    // Editing a running total re-computes deltas for that hole AND the next
    "0-3": -2,
  },
  validation: {
    // Per-hole zero-sum check (on computed deltas)
    holesBalanced: { 1: true, 2: true, 3: false, ... }
  }
}
```

### Backend

#### New Endpoint

```
POST /api/scorecard/scan
Content-Type: multipart/form-data
Body: image file

Response:
{
  "scan_id": "uuid",
  "players": [
    { "name": "John", "confidence": 0.95 }
  ],
  "running_totals": [
    // Raw extraction: what was written on the card (running totals)
    {
      "player_index": 0,
      "hole_number": 1,
      "running_total": 2,       // plain "2" on card
      "is_circled": false,       // not circled = positive
      "confidence": 0.92
    },
    {
      "player_index": 0,
      "hole_number": 2,
      "running_total": 4,
      "is_circled": false,
      "confidence": 0.90
    },
    {
      "player_index": 0,
      "hole_number": 3,
      "running_total": -3,       // circled "3" on card → -3
      "is_circled": true,
      "confidence": 0.85
    },
    ...
  ],
  "per_hole_quarters": [
    // Computed by backend: diff of consecutive running totals
    {
      "player_index": 0,
      "hole_number": 1,
      "quarters": 2              // 0 → 2 = +2
    },
    {
      "player_index": 0,
      "hole_number": 2,
      "quarters": 2              // 2 → 4 = +2
    },
    {
      "player_index": 0,
      "hole_number": 3,
      "quarters": -7             // 4 → -3 = -7
    },
    ...
  ],
  "image_url": "s3://bucket/scans/uuid.jpg"
}
```

**Backend processing pipeline:**
1. Claude Vision extracts raw running totals + circle detection from the image
2. Backend converts running totals to per-hole deltas: `delta[n] = running_total[n] - running_total[n-1]` (with `running_total[0] = 0`)
3. Both raw running totals and computed per-hole quarters are returned to the frontend
4. On user confirmation, per-hole deltas are saved as **independent hole events** through the existing `quarters-only` endpoint — identical to manual entry. The running total is discarded; it was only needed as an intermediate step to derive per-hole values.

**Important:** The photo/OCR pipeline introduces no new scoring data model. It is purely an input method that produces the same `hole_quarters` payload the app already handles. Per-hole independence and historical traceability are fully preserved.

#### Claude Vision API Prompt Strategy

The prompt must account for running totals and circle notation:

> _"This is a golf scorecard photo. The numbers written on it represent a **running total of quarters** — a wagering unit — for each player across the round._
>
> _IMPORTANT conventions:_
> - _**Circled numbers are NEGATIVE.** A circle drawn around a number means that value is negative (the player is down). An uncircled number is positive (the player is up)._
> - _**Values are running totals, not per-hole amounts.** Each cell shows the player's cumulative quarter balance after that hole._
> - _Values are typically small integers (range roughly -15 to +15 by end of round), sometimes half-values (0.5 increments)._
>
> _Extract: player names (from leftmost column or top row), and the **running total** for each player on each hole (1–18). Mark circled values as negative. Return structured JSON with confidence scores."_

Key extraction hints for the model:
- **Circles = negative**: This is the most critical visual cue. A `③` means -3, a plain `3` means +3.
- Running totals generally move in small increments between holes (±1 to ±4 per hole is typical)
- Large jumps between consecutive holes are possible but should get lower confidence
- Empty/blank cells likely mean the player was at 0 (even) for that hole — or the hole wasn't played yet
- Some cards may have a separate "total" or "out/in" column for front/back 9 — extract those too if present

#### Image Storage
- Upload original image to S3/Cloudflare R2
- Store reference in a new `scorecard_scans` table
- Retain for audit trail and potential re-processing

#### New Model

```python
class ScorecardScan(Base):
    __tablename__ = "scorecard_scans"
    
    id = Column(UUID, primary_key=True, default=uuid4)
    game_id = Column(UUID, ForeignKey("game_states.game_id"), nullable=True)
    uploaded_by = Column(String, nullable=False)  # auth0 user ID
    image_url = Column(String, nullable=False)
    extracted_data = Column(JSON, nullable=False)  # raw extraction result
    confirmed_data = Column(JSON, nullable=True)   # user-confirmed quarters
    status = Column(String, default="pending")      # pending | confirmed | rejected
    created_at = Column(DateTime, default=func.now())
```

---

## Validation

### Zero-Sum Constraint (Most Important)

Each hole's quarters across all players **must** sum to zero. This is already enforced by the `quarters-only` backend endpoint, and the review screen should enforce it client-side too:

- After extraction, auto-check each hole's sum
- Highlight unbalanced holes in red with the discrepancy shown (e.g., "Hole 7: off by +1")
- Block submission until all holes balance
- This also serves as a built-in error-detection mechanism — if OCR misreads a value, the zero-sum check will likely catch it

### Value Range
- Quarters typically range from -4 to +4 per hole per player
- Half-values (0.5) are valid
- Flag any extracted value outside ±10 as suspicious

---

## Confidence Scoring

| Range | UI Treatment | Meaning |
|---|---|---|
| 0.85 – 1.0 | Normal (no highlight) | High confidence, likely correct |
| 0.50 – 0.84 | Yellow border + "?" icon | Medium confidence, user should verify |
| 0.0 – 0.49 | Red border, value blank or greyed | Low confidence, user must enter manually |

---

## Handling Edge Cases

| Scenario | Behavior |
|---|---|
| Blurry/dark photo | Show retake prompt with tips ("More light", "Hold steady") |
| Only front 9 visible | Extract what's available, leave back 9 blank for manual entry |
| Scorecard has strokes AND quarters rows | Vision prompt instructs to identify and extract only the quarters/running total rows |
| Circle detection ambiguity (smudge vs circle) | Flag as medium confidence; zero-sum check will likely catch errors |
| Scorecard format varies by course | Vision LLM handles layout variation better than template-based OCR |
| Player count mismatch (card has 4, game has 3) | PlayerMapper lets user select which rows to import |
| Handwriting is truly illegible | Flag cells as low-confidence, user fills in manually |
| Zero-sum doesn't balance after delta computation | Highlight the offending holes, user corrects the running total |
| Running total has a gap (blank cell mid-round) | Interpolate if possible, otherwise flag for manual entry |
| Player was at 0 (even) — cell might be blank or have "E" | Vision prompt covers common "even" notations; treat as 0 |
| Running total resets at the turn (hole 10) | Vision prompt notes that some groups restart at 0 for the back 9; detect and handle by treating front/back as independent sequences |
| Editing a running total cascades | Changing hole N's running total recomputes deltas for hole N and hole N+1 |

---

## Offline Considerations

- Photo capture works offline (camera is a device API)
- Image + extraction must happen online (requires API call)
- If offline: store the photo locally, queue for processing when back online
- Integrate with existing `syncManager.js` queue system

---

## Implementation Phases

### Phase 1 — MVP
- Camera capture + image upload
- Claude Vision API extraction of quarters
- Basic review grid (editable table)
- Zero-sum validation per hole
- Save confirmed quarters to existing game via `quarters-only` endpoint
- No image persistence (process and discard)

### Phase 2 — Polish
- Confidence-based highlighting in review grid
- Player name → game player auto-mapping
- Side-by-side photo reference during review
- Image stored in S3 for audit trail
- `scorecard_scans` table for history
- Smart suggestions when zero-sum is off (e.g., "Did you mean -2 instead of 2 for John on hole 7?")

### Phase 3 — Advanced
- Multi-image support (front 9 + back 9 as separate photos)
- Re-scan individual sections
- Historical scan gallery per game
- "Log a past round" flow from home screen (no active game required)

---

## Open Questions

1. **Should this work outside of an active game?** (e.g., "Log a past round" from the home screen)
2. **Cost management** — Claude Vision calls have a per-image cost. Any concern at expected volume?
3. **Multiple scorecards per round** — Some groups keep separate cards. Support merging?
4. **Fractional quarters** — How common are 0.5 values? This affects what the extraction prompt emphasizes.
5. **Back 9 reset** — Do your groups restart the running total at 0 on hole 10, or does it carry through all 18?
6. **"Even" notation** — When a player is at 0, do people write "0", "E", leave it blank, or something else?

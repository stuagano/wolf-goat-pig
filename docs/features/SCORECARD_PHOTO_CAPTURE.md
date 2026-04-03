# Scorecard Photo Capture — Feature Spec

## Overview

Allow users to photograph a physical scorecard that has **quarters (wagering results) per hole per player** written on it, extract those values via OCR, then confirm/edit before saving to a game. This is the primary data being captured — not strokes.

Golf groups typically track quarters won/lost per hole on the physical card during the round. This feature lets them snap a photo at the end instead of manually re-entering every value.

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
- Display extracted data in an editable review screen:
  - **Player names** — mapped to existing game players
  - **Per-hole quarters** — 18 columns, one row per player, pre-filled with extracted values
  - **Totals** — auto-calculated front 9, back 9, and 18-hole totals per player
- **Zero-sum validation**: Each hole's quarters across all players must sum to zero. Highlight any hole that doesn't balance.
- Visual indicators:
  - **High-confidence values** shown normally
  - **Low-confidence values** highlighted (yellow/orange border) — user should double-check
  - **Unreadable values** left blank with a red border
- Users can tap any cell to edit
- "Confirm Quarters" button is disabled until:
  - All cells have values
  - Every hole sums to zero across players
- Side-by-side or toggle view of the original photo for reference

### 5. Save
- On confirmation, scores are submitted through the existing `POST /games/{gameId}/quarters-only` endpoint
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
- Original photo stored for audit/reference

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
    holes: {
      // playerIndex → quarters per hole
      0: [
        { hole: 1, quarters: 2, confidence: 0.92 },
        { hole: 2, quarters: -1, confidence: 0.88 },
        { hole: 3, quarters: null, confidence: 0.0 },  // unreadable
        ...
      ]
    }
  },
  edits: {
    // User overrides, keyed by "playerIndex-holeNumber"
    "0-3": -2,
    "1-3": 2,
  },
  validation: {
    // Per-hole zero-sum check
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
  "holes": [
    {
      "player_index": 0,
      "hole_number": 1,
      "quarters": 2,
      "confidence": 0.92
    },
    {
      "player_index": 1,
      "hole_number": 1,
      "quarters": -1,
      "confidence": 0.88
    },
    {
      "player_index": 2,
      "hole_number": 1,
      "quarters": -1,
      "confidence": 0.90
    },
    ...
  ],
  "image_url": "s3://bucket/scans/uuid.jpg"
}
```

#### Claude Vision API Prompt Strategy

The prompt should be tailored for quarters extraction:

> _"This is a golf scorecard photo. The numbers written on it represent **quarters** — a wagering unit — won or lost by each player on each hole. Positive numbers mean quarters won, negative numbers mean quarters lost. Values are typically small integers or half-values (e.g., -2, 0, 1, 0.5, -0.5). Each hole's values across all players should sum to zero._
>
> _Extract: player names (from leftmost column or top row), and the quarters value for each player on each hole (1–18). Return structured JSON with confidence scores."_

Key extraction hints for the model:
- Values are small: typically -4 to +4, sometimes fractional (0.5 increments)
- Negative values may be written with a minus sign, parentheses, or in a different color
- Some cells may have circles, underlines, or other markings — focus on the number
- The zero-sum constraint can help disambiguate ambiguous values

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
| Scorecard has strokes AND quarters columns | Vision prompt instructs to extract only the quarters columns |
| Negative values written as parentheses e.g. `(2)` | Vision prompt covers common notations for negative numbers |
| Scorecard format varies by course | Vision LLM handles layout variation better than template-based OCR |
| Player count mismatch (card has 4, game has 3) | PlayerMapper lets user select which rows to import |
| Handwriting is truly illegible | Flag cells as low-confidence, user fills in manually |
| Zero-sum doesn't balance after extraction | Highlight the offending holes, user manually corrects |
| Carry-over / cumulative totals on card | Prompt instructs to extract per-hole values, not running totals |

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

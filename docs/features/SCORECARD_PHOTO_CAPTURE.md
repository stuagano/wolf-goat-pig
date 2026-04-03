# Scorecard Photo Capture — Feature Spec

## Overview

Allow users to photograph a physical golf scorecard and have scores automatically extracted via OCR, then confirm/edit the values before saving them to a game.

---

## User Flow

### 1. Entry Point
- New **"Scan Scorecard"** button on the `SimpleScorekeeper` scoring interface (alongside manual entry)
- Also accessible from `GameCompletionView` as an alternative to manual scoring for post-round entry
- Could be offered during game creation as a "Log scores from a completed round" path

### 2. Capture
- Tap "Scan Scorecard" → opens device camera via `<input type="file" accept="image/*" capture="environment">`
- Also supports selecting an existing photo from the camera roll
- Show a brief overlay guide: _"Lay the scorecard flat. Make sure all 18 holes and player names are visible."_
- Preview the captured image so the user can retake if blurry/cropped

### 3. Upload & Processing
- Image is uploaded to the backend (`POST /api/scorecard/scan`)
- Backend sends the image to an OCR/vision service for extraction
- Frontend shows a loading state: _"Reading your scorecard..."_
- Target processing time: < 5 seconds

### 4. Confirmation & Editing (Critical Step)
- Display extracted data in an editable review screen:
  - **Player names** — mapped to existing game players (or editable text fields)
  - **Per-hole scores** — 18 columns, one row per player, pre-filled with extracted values
  - **Totals** — auto-calculated front 9, back 9, and 18-hole totals
- Visual indicators:
  - **High-confidence values** shown normally
  - **Low-confidence values** highlighted (yellow/orange border) so users know where to double-check
  - **Unreadable values** left blank with a red border
- Users can tap any cell to edit
- "Confirm Scores" button is disabled until all cells have values
- Side-by-side or toggle view of the original photo for reference

### 5. Save
- On confirmation, scores are submitted through the existing `POST /games/{gameId}/quarters-only` flow
- Quarters/wagers are calculated separately (photo only captures strokes)
- Original photo is stored for audit/reference

---

## Technical Architecture

### Frontend

#### New Components

| Component | Purpose |
|---|---|
| `ScorecardCapture.jsx` | Camera input, image preview, retake flow |
| `ScorecardReview.jsx` | Editable grid of extracted scores with confidence indicators |
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
      // playerIndex → hole scores
      0: [
        { hole: 1, strokes: 4, confidence: 0.98 },
        { hole: 2, strokes: null, confidence: 0.0 },  // unreadable
        ...
      ]
    }
  },
  edits: {
    // User overrides, keyed by "playerIndex-holeNumber"
    "0-2": 5,
    "1-7": 3,
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
      "strokes": 4,
      "confidence": 0.98
    },
    ...
  ],
  "image_url": "s3://bucket/scans/uuid.jpg"
}
```

#### OCR Strategy — Options (pick one)

| Option | Pros | Cons |
|---|---|---|
| **A. Claude Vision API** | High accuracy on messy handwriting, understands scorecard layout semantically, already using Anthropic stack | Cost per call (~$0.01-0.03/image), requires prompt engineering |
| **B. Google Cloud Vision** | Strong OCR, good handwriting support, document AI features | Additional vendor, separate billing |
| **C. AWS Textract** | Table extraction built-in, good for structured forms | Additional vendor, more complex setup |

**Recommendation: Option A (Claude Vision API)** — Scorecards are semi-structured with handwriting. A vision LLM handles layout interpretation + messy handwriting better than traditional OCR. Prompt can include instructions like _"This is a golf scorecard. Extract player names from the leftmost column and scores from each numbered hole column."_

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
    confirmed_data = Column(JSON, nullable=True)   # user-confirmed scores
    status = Column(String, default="pending")      # pending | confirmed | rejected
    created_at = Column(DateTime, default=func.now())
```

---

## Confidence Scoring

The extraction response includes per-value confidence scores (0.0 – 1.0):

| Range | UI Treatment | Meaning |
|---|---|---|
| 0.85 – 1.0 | Normal (no highlight) | High confidence, likely correct |
| 0.50 – 0.84 | Yellow border + "?" icon | Medium confidence, user should verify |
| 0.0 – 0.49 | Red border, value blank or greyed | Low confidence, user must enter manually |

The vision model prompt should be structured to return confidence estimates alongside each extracted value.

---

## Handling Edge Cases

| Scenario | Behavior |
|---|---|
| Blurry/dark photo | Show retake prompt with tips ("More light", "Hold steady") |
| Only front 9 visible | Extract what's available, leave back 9 blank for manual entry |
| Extra columns (handicap, net scores) | Ignore non-gross-score columns via prompt instructions |
| Scorecard format varies by course | Vision LLM handles layout variation better than template-based OCR |
| Player count mismatch (card has 4, game has 3) | PlayerMapper lets user select which rows to import |
| Handwriting is truly illegible | Flag cells as low-confidence, user fills in manually |

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
- Claude Vision API extraction
- Basic review grid (editable table, no confidence highlighting)
- Save confirmed scores to existing game
- No image persistence (process and discard)

### Phase 2 — Polish
- Confidence-based highlighting in review grid
- Player name → game player auto-mapping
- Side-by-side photo reference during review
- Image stored in S3 for audit trail
- `scorecard_scans` table for history

### Phase 3 — Advanced
- Multi-image support (front 9 + back 9 as separate photos)
- Re-scan individual sections
- Historical scan gallery per game
- Batch import for logging past rounds outside of live games

---

## Open Questions

1. **Should this work outside of an active game?** (e.g., "Log a past round" from the home screen)
2. **Quarter/wager calculation** — Photo captures strokes only. Should the review screen also let users input quarters, or is that always done separately?
3. **Cost management** — Claude Vision calls have a per-image cost. Any concern at expected volume?
4. **Multiple scorecards per round** — Some groups keep separate cards. Support merging?

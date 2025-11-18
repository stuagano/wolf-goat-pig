# Stroke Display Feature - SimpleScorekeeper

**Date:** 2025-11-17
**Component:** `frontend/src/components/game/SimpleScorekeeper.jsx`
**Lines:** 1095-1208

## Overview

Added a prominent **Stroke Allocation Display** to the SimpleScorekeeper component that shows which players receive handicap strokes on the current hole **before play begins**. This critical information helps players know their advantages at the start of each hole.

---

## Feature Details

### Visual Design

The stroke display appears as a **purple gradient banner** positioned prominently between the hole header and the hitting order display:

```
┌────────────────────────────────────────┐
│  Hole 5 - Par 4                        │  ← Hole Header
└────────────────────────────────────────┘
┌────────────────────────────────────────┐
│  ⛳ STROKES ON HOLE 5                  │  ← NEW: Stroke Display
│  (Stroke Index: 5)                     │
│                                        │
│  ┌──────────────┐  ┌──────────────┐   │
│  │ Player 1     │  │ Player 3     │   │
│  │ 1 STROKE    │  │ ½ STROKE    │   │
│  └──────────────┘  └──────────────┘   │
│                                        │
│  💡 Based on handicap & hole difficulty│
└────────────────────────────────────────┘
┌────────────────────────────────────────┐
│  Hitting Order                         │  ← Existing Display
│  1. Player 1 👑  2. Player 2  ...      │
└────────────────────────────────────────┘
```

### Features

1. **Dynamic Calculation**
   - Uses the Creecher Feature logic we just implemented
   - Calculates strokes based on player handicap and hole stroke index
   - Supports full strokes (1.0) and half strokes (0.5)

2. **Visual Indicators**
   - **Green badge**: Full strokes (1 STROKE, 2 STROKES, etc.)
   - **Orange badge**: Half strokes (½ STROKE)
   - Player name clearly displayed
   - Only shows players who receive strokes (others hidden)

3. **Contextual Information**
   - Shows current hole number
   - Shows stroke index for the hole
   - Helpful tooltip explaining how strokes are awarded

4. **Smart Display**
   - Only appears when players have handicaps
   - Hidden during Hoepfinger phase
   - Hidden if no players get strokes on this hole
   - Automatically updates when hole changes

---

## Implementation Details

### Stroke Calculation Logic

The component includes a local implementation of the Creecher Feature:

```javascript
const getStrokesForHole = (handicap, strokeIndex) => {
  if (!handicap || !strokeIndex) return 0;

  const fullStrokes = Math.floor(handicap);
  const hasHalfStroke = (handicap - fullStrokes) >= 0.5;

  // Rule 1: Creecher Feature for high handicaps (>18)
  // Easiest 6 holes get ONLY half strokes
  if (handicap > 18 && strokeIndex >= 13 && strokeIndex <= 18) {
    const creecherStrokes = Math.min(Math.floor(handicap - 18), 6);
    const easiestHoles = [18, 17, 16, 15, 14, 13];
    if (easiestHoles.slice(0, creecherStrokes).includes(strokeIndex)) {
      return 0.5;
    }
  }

  // Rule 2: Full strokes on hardest holes
  if (strokeIndex <= fullStrokes) {
    return 1.0;
  }

  // Rule 3: Half stroke on next hardest hole (fractional handicaps)
  if (hasHalfStroke && strokeIndex === fullStrokes + 1) {
    return 0.5;
  }

  return 0;
};
```

### Data Requirements

**Player Object Must Include:**
```javascript
{
  id: "player123",
  name: "John Doe",
  handicap: 10.5,  // ← REQUIRED for stroke display
  // ... other properties
}
```

### Stroke Index Mapping

Currently uses a **simple mapping**: `strokeIndex = currentHole`
- Hole 1 → Stroke Index 1 (hardest)
- Hole 18 → Stroke Index 18 (easiest)

**Future Enhancement:** Fetch actual stroke index from course data via API.

---

## Examples

### Example 1: Player with 10.5 Handicap

**Hole 10:**
- Stroke Index: 10
- Handicap: 10.5
- **Strokes Awarded: 1.0** (full stroke - hole 10 ≤ handicap 10)
- Display: **"1 STROKE"** (green badge)

**Hole 11:**
- Stroke Index: 11
- Handicap: 10.5
- **Strokes Awarded: 0.5** (half stroke - fractional handicap)
- Display: **"½ STROKE"** (orange badge)

**Hole 12:**
- Stroke Index: 12
- Handicap: 10.5
- **Strokes Awarded: 0** (no stroke)
- Display: *Player not shown*

### Example 2: Player with 20 Handicap (Creecher Feature)

**Hole 5:**
- Stroke Index: 5
- Handicap: 20
- **Strokes Awarded: 1.0** (full stroke - regular hole)
- Display: **"1 STROKE"** (green badge)

**Hole 18:**
- Stroke Index: 18 (easiest hole)
- Handicap: 20
- **Strokes Awarded: 0.5** (half stroke - Creecher Feature for handicap >18)
- Display: **"½ STROKE"** (orange badge)

### Example 3: Multiple Players

**Hole 8 Display:**
```
┌────────────────────────────────────────┐
│  ⛳ STROKES ON HOLE 8                  │
│  (Stroke Index: 8)                     │
│                                        │
│  ┌──────────────┐  ┌──────────────┐   │
│  │ Alice        │  │ Bob          │   │
│  │ 1 STROKE    │  │ 1 STROKE    │   │
│  └──────────────┘  └──────────────┘   │
│                                        │
│  ┌──────────────┐                     │
│  │ Charlie      │                     │
│  │ ½ STROKE    │  Carol: 0 (hidden) │
│  └──────────────┘                     │
└────────────────────────────────────────┘
```

---

## User Benefits

### Before This Feature ❌
- Players had to manually calculate strokes per hole
- Easy to forget who gets strokes
- Required checking scorecard or asking partners
- Slowed down play

### After This Feature ✅
- **Clear visibility** - Impossible to miss who gets strokes
- **Starts the hole right** - Info displayed before play begins
- **Reduces disputes** - Everyone sees the same information
- **Speeds up play** - No need to calculate or discuss
- **Supports Creecher Feature** - Shows half strokes correctly

---

## Technical Details

### Styling

```javascript
{
  background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
  borderRadius: '12px',
  padding: '16px',
  marginBottom: '16px',
  boxShadow: '0 4px 6px rgba(0,0,0,0.15)',
  border: '2px solid rgba(255,255,255,0.2)'
}
```

**Design Choices:**
- **Purple gradient**: Distinguishes from other sections (blue for captain, etc.)
- **High contrast**: White text on purple ensures readability
- **Prominent position**: Above hitting order, can't be missed
- **Responsive**: Flex wrap ensures mobile compatibility

### Conditional Rendering

The display appears only when:
1. ✅ Not in Hoepfinger phase (`!isHoepfinger`)
2. ✅ Rotation order is set (`rotationOrder.length > 0`)
3. ✅ At least one player receives strokes (`playersWithStrokes.length > 0`)

---

## Integration Points

### Works With:
- ✅ **Creecher Feature** - Uses same half-stroke logic
- ✅ **Handicap Validator** - Matches backend calculation
- ✅ **Rotation System** - Displays alongside hitting order
- ✅ **Theme Provider** - Uses theme colors where appropriate

### Data Flow:
```
Game Setup
    ↓
Players with Handicaps
    ↓
SimpleScorekeeper Component
    ↓
Stroke Calculation (Creecher Logic)
    ↓
Display to User
```

---

## Future Enhancements

### Priority 1: Fetch Real Stroke Index
**Current:** Simple mapping (hole number = stroke index)
**Ideal:** Fetch from course data

```javascript
// Fetch stroke index from API
const courseHole = await fetch(`${API_URL}/courses/${courseId}/holes/${currentHole}`);
const { stroke_index } = await courseHole.json();
```

### Priority 2: Net Score Preview
Show what players need to shoot for par net:

```
┌──────────────┐
│ Alice        │
│ 1 STROKE    │
│ Par Net: 3   │  ← NEW
└──────────────┘
```

### Priority 3: Handicap Adjustment Info
For matchplay, show handicap differential:

```
Giving strokes:
Alice (10) gives Bob (15) → 5 strokes difference
```

### Priority 4: Animation
Fade in/slide in when hole changes for better UX.

---

## Testing Recommendations

### Manual Test Cases:

1. **Test Fractional Handicaps**
   - Set player handicap to 10.5
   - Navigate to hole 11
   - Verify "½ STROKE" appears

2. **Test High Handicaps (Creecher)**
   - Set player handicap to 22
   - Navigate to hole 18
   - Verify "½ STROKE" appears (not full stroke)

3. **Test No Strokes**
   - Set all players to scratch (0 handicap)
   - Verify stroke display doesn't appear

4. **Test Multiple Players**
   - Set players: 5, 10.5, 15, 20
   - Navigate through holes 1-18
   - Verify correct strokes shown each hole

5. **Test Hoepfinger Phase**
   - Advance to hole 17 (4-man game)
   - Verify stroke display is hidden

### Automated Test (Recommended):

```javascript
describe('Stroke Display', () => {
  it('shows players with strokes on current hole', () => {
    const players = [
      { id: '1', name: 'Alice', handicap: 10.5 },
      { id: '2', name: 'Bob', handicap: 5 }
    ];

    render(<SimpleScorekeeper players={players} currentHole={11} />);

    expect(screen.getByText('½ STROKE')).toBeInTheDocument();
    expect(screen.getByText('Alice')).toBeInTheDocument();
    expect(screen.queryByText('Bob')).not.toBeInTheDocument(); // No stroke on hole 11
  });
});
```

---

## Code Location

**File:** `frontend/src/components/game/SimpleScorekeeper.jsx`
**Lines:** 1095-1208
**Section:** Between "Hole Header" and "Rotation Order Display"

---

## Summary

✅ **Feature Added:** Stroke allocation display for each hole
✅ **Supports:** Full strokes and half strokes (Creecher Feature)
✅ **Position:** Prominent placement above hitting order
✅ **Design:** Clear, colorful, impossible to miss
✅ **Smart:** Only shows when relevant

**Impact:** Players now know exactly who gets strokes before starting each hole, eliminating confusion and speeding up play!

---

## Related Documentation

- `CREECHER_FEATURE_IMPLEMENTATION_SUMMARY.md` - Backend half-stroke logic
- `HALF_STROKE_COMPLIANCE_ANALYSIS.md` - Original problem analysis
- `RULES_COMPLIANCE_REPORT.md` - Overall rules compliance

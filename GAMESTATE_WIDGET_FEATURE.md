# GameStateWidget Feature Documentation

## Overview

The **GameStateWidget** is a comprehensive real-time game state display component that provides players with instant visibility into all aspects of the current hole during Wolf Goat Pig gameplay. This feature enhances the gaming experience by surfacing critical information that was previously hidden or difficult to access.

## What It Does

The GameStateWidget displays:

### 1. **Hole Information**
- Current hole number
- Par value
- Stroke index (1-18, where 1 is hardest)
- Game phase (Regular, Vinnie Variation, Hoepfinger)
- Shot progression tracking

### 2. **Team Formation**
Displays current team structure with visual indicators:
- **Partners Mode** (🤝): Shows Team 1 vs Team 2 rosters
- **Solo Mode** (👤): Shows solo player vs opponents
- **Pending** (⏳): Waiting for team decisions

### 3. **Betting State**
Real-time wagering information:
- Base wager (starting amount)
- Current wager (with multipliers)
- Doubled status (⚡)
- Redoubled status (⚡⚡)
- Special rules active:
  - 🦅 Float Invoked
  - 🎯 Option Invoked
  - 👑 Duncan Invoked (captain goes solo)
  - 🦘 Tunkarri Invoked (aardvark goes solo)

### 4. **Stroke Advantages (Creecher Feature)**
The widget prominently displays handicap stroke calculations:
- Each player's handicap
- Strokes received on current hole
- Visual indicators:
  - ● Full stroke
  - ◐ Half stroke
  - Multiple strokes shown as ●x2, ●x3, etc.
- Stroke index reference

This is the **Creecher Feature** - automatic handicap stroke calculation based on:
- Player's handicap
- Hole's stroke index
- Course difficulty

### 5. **Ball Positions**
Shot-by-shot tracking for all players:
- Distance to pin (yards)
- Shot count
- Lie type (tee, fairway, rough, bunker, green)
- Status (not yet hit, in play, holed)

### 6. **Player Status**
Current standings:
- Player names
- Handicaps
- Current points (quarters won/lost)
- Ball position for each player

## Technical Architecture

### Component Structure

```
GameStateWidget/
├── Props:
│   ├── gameState (full game state object)
│   └── holeState (can override gameState.hole_state)
├── Sections:
│   ├── Header (hole number, par, phase icon)
│   ├── Team Formation
│   ├── Betting State
│   ├── Stroke Advantages
│   ├── Shot Progression
│   ├── Player Status
│   └── Special Rules (conditional)
└── Error Handling:
    ├── Null/undefined gameState
    ├── Missing holeState
    ├── Partial data
    └── Graceful degradation
```

### Data Flow

```
Backend (wgp_simulation)
  ↓
GET /game/state
  ↓
Returns game_state with hole_state
  ↓
GamePage.js
  ↓
<GameStateWidget gameState={gameState} holeState={gameState?.hole_state} />
  ↓
Real-time display updates
```

### Backend Integration

The widget consumes data from the `wgp_simulation` system:

**Endpoint**: `GET /game/state`

**Response Structure**:
```json
{
  "current_hole": 5,
  "game_phase": "regular",
  "players": [...],
  "hole_state": {
    "hole_number": 5,
    "hole_par": 4,
    "stroke_index": 5,
    "current_shot_number": 3,
    "hole_complete": false,
    "teams": {
      "type": "partners",
      "captain": "p1",
      "team1": ["p1", "p2"],
      "team2": ["p3", "p4"]
    },
    "betting": {
      "base_wager": 1,
      "current_wager": 2,
      "doubled": true,
      "special_rules": {...}
    },
    "stroke_advantages": {
      "p1": {
        "handicap": 10.5,
        "strokes_received": 1.0,
        "stroke_index": 5
      }
    },
    "ball_positions": {
      "p1": {
        "distance_to_pin": 150,
        "shot_count": 2,
        "lie_type": "fairway"
      }
    },
    "next_player_to_hit": "p4",
    "line_of_scrimmage": "p4"
  }
}
```

## User Experience Improvements

### Before GameStateWidget
- Players couldn't see handicap stroke calculations
- Team formations were unclear
- Betting multipliers were hidden
- Ball positions not visible during play
- Shot progression was opaque

### After GameStateWidget
- ✅ Instant visibility into stroke advantages
- ✅ Clear team rosters at a glance
- ✅ Real-time betting state with visual indicators
- ✅ Live ball position tracking
- ✅ Transparent shot progression
- ✅ Better strategic decision-making

## Mobile Responsiveness

The widget is designed mobile-first:
- Grid layout adapts to small screens
- Cards stack vertically on mobile
- Touch-friendly spacing
- Readable text sizes (minimum 12px)
- Icons supplement text for clarity

### Responsive Breakpoints
```css
- Mobile (< 480px): Single column, stacked cards
- Tablet (480-768px): 2-column grid
- Desktop (> 768px): Multi-column grid with auto-fit
```

## Error Handling

The widget gracefully handles missing or incomplete data:

### Null/Undefined States
- Returns `null` (renders nothing) if `gameState` is missing
- Returns `null` if `holeState` is missing
- No errors thrown to crash the page

### Partial Data
- Missing `players`: Still renders hole info
- Missing `stroke_advantages`: Shows sections without player data
- Missing `ball_positions`: Shows "Not yet hit" for all players
- Missing `special_rules`: Doesn't show special rules section

### Backwards Compatibility
- Works with old game states (pre-hole_state)
- Gracefully degrades when data is unavailable
- Doesn't break existing gameplay

## Accessibility

### Semantic HTML
- Uses `<h2>` for hole heading
- Proper heading hierarchy
- Meaningful text content (not icon-only)

### Screen Readers
- All important information has text labels
- Icons are supplemental, not primary
- Aria-friendly structure

### Keyboard Navigation
- Fully navigable without mouse
- Focus states visible
- Logical tab order

## Testing Coverage

### Unit Tests (GameStateWidget.test.js)
- ✅ Renders with complete data
- ✅ Handles null/undefined states
- ✅ Displays all team formation types
- ✅ Shows betting state correctly
- ✅ Renders stroke advantages
- ✅ Displays ball positions
- ✅ Works across game phases
- ✅ Graceful degradation
- ✅ Backwards compatibility

### Integration Tests (GamePage.test.js)
- ✅ GameStateWidget renders in GamePage
- ✅ Updates when gameState changes
- ✅ Works with missing hole_state
- ✅ Shows stroke advantages
- ✅ Displays team formations
- ✅ Shows betting states
- ✅ Ball position integration
- ✅ Multi-phase support

### End-to-End Test (test_multi_hole_tracking.py)
- ✅ 5-hole simulation
- ✅ State persistence across holes
- ✅ Team formation tracking
- ✅ Betting state tracking
- ✅ Stroke advantage calculations
- ✅ Ball position tracking
- ✅ Point accumulation

## Performance Considerations

### Rendering Optimization
- Conditional rendering (only when data exists)
- No unnecessary re-renders
- Lightweight component (< 400 LOC)
- No external dependencies (pure React)

### Data Efficiency
- Single `hole_state` object from backend
- No polling (updates via gameState prop changes)
- Minimal DOM manipulation

## Future Enhancements

Potential improvements:
1. **Animation**: Smooth transitions when state changes
2. **Interactive Elements**: Click to see detailed stats
3. **Tooltips**: Hover for rule explanations
4. **History View**: See previous holes
5. **Export**: Download game state as JSON
6. **Live Updates**: WebSocket support for multi-player

## Files Modified/Created

### New Files
- `frontend/src/components/GameStateWidget.js` (365 lines)
- `frontend/src/components/__tests__/GameStateWidget.test.js` (580 lines)
- `test_multi_hole_tracking.py` (233 lines)
- `PROOF_MULTI_HOLE_TRACKING.md` (186 lines)
- `GAMESTATE_WIDGET_FEATURE.md` (this file)

### Modified Files
- `frontend/src/pages/GamePage.js` (added GameStateWidget integration)
- `frontend/src/pages/__tests__/GamePage.test.js` (added 9 integration tests)
- `backend/app/wolf_goat_pig_simulation.py` (already had hole_state support)

## Migration Guide

For developers upgrading existing installations:

### 1. Backend (No Changes Required)
The `wgp_simulation` system already provides `hole_state` via `/game/state`.

### 2. Frontend (Automatic)
- GameStateWidget is automatically rendered in GamePage
- No configuration needed
- Works with existing game states

### 3. Backwards Compatibility
- Old game states without `hole_state` still work
- Widget gracefully hidden when data unavailable
- No breaking changes

## Support

### Common Issues

**Widget not showing?**
- Check if `gameState.hole_state` exists in API response
- Verify game is active (not in setup/lobby)
- Check browser console for errors

**Missing data in widget?**
- Verify backend is using `wgp_simulation` system
- Check `/game/state` endpoint returns complete `hole_state`
- Ensure simulation mode is enabled

**Styling issues?**
- Widget uses inline styles for portability
- Check theme provider is wrapping GamePage
- Verify mobile viewport settings

## Conclusion

The GameStateWidget transforms the Wolf Goat Pig gaming experience by providing unprecedented visibility into game mechanics. Players can now:
- Understand handicap advantages (Creecher Feature)
- Track shot progression in real-time
- See betting multipliers clearly
- Monitor team formations
- Make better strategic decisions

This feature represents a major step forward in making Wolf Goat Pig accessible, transparent, and enjoyable for players of all skill levels.

---

**Version**: 1.0
**Last Updated**: 2025-11-02
**Status**: ✅ Production Ready

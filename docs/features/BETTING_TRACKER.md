# Betting Action Tracker

## Overview

The Betting Action Tracker provides real-time visibility into betting actions during each hole of a Wolf-Goat-Pig game, including doubles, presses, team formations, and complete betting history with event sourcing architecture.

## Features

### User-Facing Features

- **Expandable Panel**: Collapsed by default showing current bet and multiplier, expands to show full betting controls and history
- **Current Bet Status**: Real-time display of multiplier (e.g., 2x, 4x), base amount, and current bet total
- **Team Display**: Visual representation of current partnerships and individual bet amounts per team
- **Betting Controls**: Interactive buttons to offer/accept/decline doubles and presses
- **Event History**: Three-tab interface for viewing betting events
  - **Current Hole**: Events for the hole in progress
  - **Last Hole**: Events from the previous hole
  - **Game History**: Complete chronological event log for entire game
- **Mobile Responsive**: Bottom sheet UI on mobile devices (< 768px) with backdrop overlay
- **Pending Action Indicator**: Pulsing badge when actions require player response
- **Auto-sync**: Automatic batch syncing of events to backend

### Technical Features

- **Event Sourcing**: All betting actions stored as immutable events
- **Client-side State Management**: React hooks with optimistic updates
- **Batch Sync**: Events synced every 5 actions or at hole completion
- **Retry Logic**: Exponential backoff on sync failures (1s, 2s, 4s, max 30s)
- **Hole Completion**: Forced sync on hole transitions with state reset

## Usage

### For Players

#### Offering a Double

1. Expand the betting tracker by clicking on the collapsed bar
2. Click the "Offer Double" button
3. Other players will see accept/decline buttons
4. When accepted, the multiplier updates automatically (1x → 2x → 4x, etc.)

#### Accepting/Declining a Double

1. When another player offers a double, you'll see a pending action indicator
2. Expand the tracker to see the offer details
3. Click "Accept Double" to agree or "Decline" to reject
4. The multiplier updates immediately on acceptance

#### Viewing History

1. Expand the betting tracker
2. Navigate between tabs:
   - **Current Hole**: See all betting actions for the current hole
   - **Last Hole**: Review what happened on the previous hole
   - **Game History**: Browse the complete chronological event log
3. Each event shows the action type, player, and timestamp

#### Mobile Experience

- Tap the collapsed bar to expand (opens as bottom sheet)
- Swipe down or tap backdrop to collapse
- All buttons are touch-friendly with larger hit areas
- Bottom sheet takes up max 80% of viewport height

### For Developers

#### Component Architecture

```
BettingTracker (main container)
├── useBettingState (state management hook)
├── CurrentBetStatus (displays current bet info)
├── BettingControls (action buttons)
└── BettingHistory (tabbed event viewer)
```

#### State Management

The `useBettingState` hook manages:
- **Current state**: multiplier, base amount, teams, pending actions
- **Event history**: current hole, last hole, game-wide
- **Sync status**: 'synced', 'pending', or 'error'
- **Unsynced events**: queue of events awaiting backend sync

#### Event Types

```javascript
BettingEventTypes = {
  DOUBLE_OFFERED: 'DOUBLE_OFFERED',
  DOUBLE_ACCEPTED: 'DOUBLE_ACCEPTED',
  DOUBLE_DECLINED: 'DOUBLE_DECLINED',
  PRESS_OFFERED: 'PRESS_OFFERED',
  PRESS_ACCEPTED: 'PRESS_ACCEPTED',
  PRESS_DECLINED: 'PRESS_DECLINED',
  TEAMS_FORMED: 'TEAMS_FORMED',
  HOLE_COMPLETE: 'HOLE_COMPLETE'
}
```

#### API Integration

The tracker syncs events to the backend via:

**Endpoint**: `POST /api/games/{gameId}/betting-events`

**Payload**:
```json
{
  "holeNumber": 5,
  "events": [
    {
      "eventId": "uuid-v4",
      "eventType": "DOUBLE_OFFERED",
      "actor": "Player1",
      "data": {
        "currentMultiplier": 1,
        "proposedMultiplier": 2
      },
      "timestamp": "2025-11-05T10:00:00Z"
    }
  ],
  "clientTimestamp": "2025-11-05T10:00:00Z"
}
```

**Response**:
```json
{
  "success": true,
  "confirmedEvents": ["uuid-v4"],
  "corrections": []
}
```

#### Hole Completion Flow

When a hole completes:

1. Create `HOLE_COMPLETE` event with final multiplier and bet
2. Force sync all unsynced events (including `HOLE_COMPLETE`)
3. Move current hole events to `lastHole` array
4. Reset betting state for next hole:
   - Multiplier → 1
   - Current bet → base amount
   - Clear pending actions
   - Clear teams
   - Increment hole number

#### Mobile Responsiveness

The component detects viewport width and applies different styles:

- **Desktop (≥ 768px)**: Inline expandable panel
- **Mobile (< 768px)**: Fixed-position bottom sheet with:
  - Slide-up animation
  - Semi-transparent backdrop
  - 80vh max height
  - Scroll overflow

#### Testing Strategy

1. **Unit Tests**: Individual hooks and components
   - `useBettingState.test.js`: State management logic
   - `BettingControls.test.js`: Button interactions
   - `CurrentBetStatus.test.js`: Display rendering
   - `BettingHistory.test.js`: Tab navigation

2. **Integration Tests**: Full workflows
   - `BettingTracker.integration.test.js`: End-to-end scenarios
   - Double offer/accept/decline workflows
   - History tab switching
   - Mobile responsive behavior

3. **Manual Testing**: Visual and UX verification
   - Mobile viewport testing (< 768px)
   - Animation smoothness
   - Touch interactions

## Implementation Details

### Key Files

- `frontend/src/hooks/useBettingState.js` - State management hook
- `frontend/src/components/game/BettingTracker.jsx` - Main component
- `frontend/src/components/game/CurrentBetStatus.jsx` - Bet status display
- `frontend/src/components/game/BettingControls.jsx` - Action buttons
- `frontend/src/components/game/BettingHistory.jsx` - Event history viewer
- `frontend/src/constants/bettingEvents.js` - Event type definitions
- `frontend/src/api/bettingApi.js` - Backend sync API
- `backend/app/routes/betting_events.py` - API endpoint

### Dependencies

- `uuid`: For generating unique event IDs
- `react`: Component framework
- `@testing-library/react`: Testing utilities

### Future Enhancements

- Press functionality (currently stubbed)
- WebSocket real-time sync for multiplayer
- Conflict resolution for concurrent actions
- Undo/redo support via event log
- Export betting history to CSV/PDF
- Push notifications for pending actions
- Voice announcements for accessibility

## Troubleshooting

### Events not syncing

1. Check browser console for sync errors
2. Verify backend API is running
3. Check `syncStatus` in React DevTools
4. Events will retry automatically with exponential backoff

### Multiplier not updating

1. Ensure double was accepted, not declined
2. Check event history to verify DOUBLE_ACCEPTED event exists
3. Verify state updates in React DevTools

### Mobile bottom sheet not appearing

1. Verify viewport width is < 768px
2. Check browser console for React errors
3. Ensure no CSS conflicts with z-index

### History showing wrong events

1. Verify you're on the correct tab (Current/Last/Game)
2. Check if hole was completed (events move to Last Hole)
3. Inspect `eventHistory` state in React DevTools

## Support

For issues or feature requests, please:
1. Check existing issues in the project repository
2. Review this documentation thoroughly
3. Include browser console logs when reporting bugs
4. Describe expected vs. actual behavior clearly

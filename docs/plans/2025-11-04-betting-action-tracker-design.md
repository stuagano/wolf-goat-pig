# Betting Action Tracker Design

## Overview

A client-side betting action tracker integrated into the Game Page that manages betting actions during each hole, including doubles offered/accepted, current bet amounts, team partnerships, and full game betting history.

## Purpose

Players frequently need to reference:
- What is the current bet amount?
- Who are the current teams?
- What betting actions have occurred this hole?
- Who offered the last double?

This feature provides a real-time view of betting state with full historical context.

## Data Model

### Event-Sourced Architecture

Using a hybrid event log + snapshots approach for optimal performance and complete audit trail.

#### Betting Event Types

```javascript
// Event types tracked in the system
const BettingEventTypes = {
  DOUBLE_OFFERED: 'DOUBLE_OFFERED',     // Player offers to double the bet
  DOUBLE_ACCEPTED: 'DOUBLE_ACCEPTED',   // Opponent accepts the double
  DOUBLE_DECLINED: 'DOUBLE_DECLINED',   // Opponent declines the double
  PRESS_OFFERED: 'PRESS_OFFERED',       // Player offers a press (new side bet)
  PRESS_ACCEPTED: 'PRESS_ACCEPTED',     // Opponent accepts the press
  PRESS_DECLINED: 'PRESS_DECLINED',     // Opponent declines the press
  TEAMS_FORMED: 'TEAMS_FORMED',         // Partnership snapshot at hole start
  HOLE_COMPLETE: 'HOLE_COMPLETE'        // Final settlement of hole
};
```

#### Event Structure

```javascript
{
  eventId: 'uuid',
  gameId: 'game-uuid',
  holeNumber: 5,
  timestamp: '2025-11-04T10:30:00Z',
  eventType: 'DOUBLE_OFFERED',
  actor: 'Player1',
  data: {
    currentMultiplier: 2,
    proposedMultiplier: 4,
    baseAmount: 1.00,
    // Event-specific fields
  }
}
```

#### Current State Snapshot

```javascript
{
  holeNumber: 5,
  currentMultiplier: 4,
  baseAmount: 1.00,
  currentBet: 4.00,
  teams: [
    {
      players: ['Player1', 'Player2'],
      betAmount: 4.00,
      score: 0  // Current hole score
    },
    {
      players: ['Player3', 'Player4'],
      betAmount: 4.00,
      score: 0
    }
  ],
  pendingAction: {
    type: 'DOUBLE_OFFERED',
    by: 'Player1',
    proposedMultiplier: 8,
    expiresAt: '2025-11-04T10:35:00Z'
  } || null,
  presses: [
    // Parallel press bets tracked separately
  ]
}
```

### State Persistence Strategy

**Client-Side:**
- Immediate updates to local React state
- Event history stored in component state/context
- Optimistic UI updates with rollback capability

**Server-Side Sync:**
- Batch POST events to backend at:
  - Hole completion (guaranteed sync point)
  - Game end (final sync)
  - Every 5 events (prevents data loss)
- Endpoint: `POST /api/games/{gameId}/betting-events`
- Payload: `{ holeNumber, events: [...], timestamp }`
- Server responds with confirmation + any corrections

**Conflict Resolution:**
- Server timestamp is source of truth
- First valid action wins conflicts
- Failed syncs retry with exponential backoff (1s, 2s, 4s, max 30s)

## Component Architecture

### Component Hierarchy

```
GamePage
├── BettingTracker (expandable panel)
│   ├── CurrentBetStatus (always visible when expanded)
│   │   ├── TeamDisplay
│   │   │   ├── Team name/players
│   │   │   ├── Current hole score
│   │   │   ├── Bet amount at stake
│   │   │   └── Betting action history (who offered/accepted)
│   │   ├── MultiplierIndicator
│   │   │   ├── Current multiplier badge
│   │   │   ├── Base amount
│   │   │   └── Total bet calculation
│   │   └── PendingActionAlert
│   │       ├── Action type (double/press offered)
│   │       ├── Who offered
│   │       └── Accept/Decline buttons (if you're the responder)
│   ├── BettingControls (full betting actions)
│   │   ├── OfferDoubleButton
│   │   ├── AcceptDeclineButtons (context-aware visibility)
│   │   └── OfferPressButton
│   └── BettingHistory (tabbed interface)
│       ├── CurrentHoleTab (default, shows ongoing hole events)
│       ├── LastHoleTab (reference previous hole)
│       └── GameHistoryTab (chronological event log, all holes)
└── UnifiedGameInterface (existing scorecard, scoring, etc.)
```

### Component State Management

```javascript
// React Context or component state
const BettingTrackerContext = {
  currentState: { /* snapshot */ },
  eventHistory: {
    currentHole: [ /* events */ ],
    lastHole: [ /* events */ ],
    gameHistory: [ /* all events */ ]
  },
  actions: {
    offerDouble: (playerId) => {},
    acceptDouble: (playerId) => {},
    declineDouble: (playerId) => {},
    offerPress: (playerId, amount) => {},
    // ... other actions
  },
  syncStatus: 'synced' | 'pending' | 'error'
}
```

### UI States

**Collapsed State:**
- Minimal info bar: "Bet: $4.00 (4x)"
- Red badge if action pending (requires response)
- Click/tap to expand

**Expanded State:**
- Full betting tracker visible
- Current bet status at top (most important info)
- Betting controls in middle (action buttons)
- History tabs at bottom (context)

**Mobile Adaptations:**
- Bottom sheet UI pattern (swipe up/down)
- Simplified history (current hole only by default)
- Large touch targets for betting actions
- Sticky current bet status at top

## Betting Workflows

### Team Formation

**Timing:** At hole start only, locked during hole play

**Process:**
1. Before hole starts, teams can be set/changed
2. `TEAMS_FORMED` event recorded at hole start
3. Teams locked for duration of hole
4. Press creates parallel bet, NOT team change

**Team Data:**
```javascript
{
  team1: { players: ['Player1', 'Player2'] },
  team2: { players: ['Player3', 'Player4'] }
}
```

### Double Workflow

**Offer Double:**
1. Player clicks "Offer Double"
2. Client validates: correct player, no pending action, within bet limits
3. `DOUBLE_OFFERED` event created
4. Pending action state updated
5. UI shows accept/decline buttons to opponents
6. Event queued for server sync

**Response to Double:**
1. Opponent sees accept/decline buttons
2. Click one → creates `DOUBLE_ACCEPTED` or `DOUBLE_DECLINED` event
3. If accepted:
   - Current multiplier updates
   - Bet amount recalculated
   - Pending action cleared
4. If declined:
   - Pending action cleared
   - Multiplier stays same
5. Event queued for server sync

**State Transitions:**
```
IDLE → DOUBLE_OFFERED → (ACCEPTED → IDLE | DECLINED → IDLE)
```

### Press Workflow

Similar to double, but creates parallel betting context:
1. `PRESS_OFFERED` event
2. Acceptance creates new side bet
3. Tracked separately in `presses` array
4. Settles independently at hole end

### Hole Completion

1. Hole scored via existing scoring system
2. Winner determined
3. `HOLE_COMPLETE` event created
4. Settlement calculated (multiplier × base amount)
5. Payout flows into existing ledger system
6. Betting state reset for next hole
7. Previous hole events moved to history
8. Forced sync to backend (guaranteed persistence)

## Integration Points

### With UnifiedGameInterface

**Reads from game state:**
- Current hole number
- Active players list
- Team assignments (if set at game level)
- Game status (active, paused, complete)

**Writes to game state:**
- Betting events
- Current bet multiplier
- Settlement amounts at hole end

**Shared state updates:**
- Both betting tracker and game interface listen to same game context
- Changes propagate via React context/state management

### With Backend API

**New Endpoint:**
```
POST /api/games/{gameId}/betting-events
Body: {
  holeNumber: 5,
  events: [
    { eventId, eventType, actor, data, timestamp },
    // ... more events
  ],
  clientTimestamp: '2025-11-04T10:30:00Z'
}
Response: {
  success: true,
  confirmedEvents: ['eventId1', 'eventId2'],
  corrections: [] // Any server-side state corrections
}
```

**Existing Endpoints (enhanced):**
- `PATCH /api/games/{gameId}` - settlement amounts added to game state
- `GET /api/games/{gameId}` - includes betting event history
- WebSocket events - betting actions broadcast to all players

### With Scoring System

**At Hole Completion:**
1. Existing scoring determines winner
2. Betting tracker calculates payout: `winner gets (currentBet × 2)`
3. Settlement added to existing payout/ledger system
4. No duplication of score tracking

**Data Flow:**
```
Score Entered → Winner Determined → Betting Settlement Calculated → Ledger Updated
```

### Multiplayer Sync

**WebSocket Integration:**
- Betting events broadcast via existing WebSocket connection
- Event format: `{ type: 'BETTING_EVENT', gameId, event: {...} }`
- All players receive real-time updates
- Client applies event to local state immediately

**Conflict Handling:**
- Server validates all events
- Timestamp determines order
- First valid action wins
- Losers receive correction event
- UI updates to reflect server truth

## Display Requirements

### Current Bet Status

Always shows:
- Current multiplier (e.g., "4x")
- Base amount (e.g., "$1.00")
- Total bet (e.g., "$4.00")
- Team composition (players on each side)

### Team Display

For each team, show:
- **Player names** - clear partnership indication
- **Current team score** - running score for this hole
- **Bet amount** - how much this team has at stake
- **Betting history** - which team member offered/accepted actions

### Betting History Views

**Current Hole Tab:**
- Chronological list of betting events
- Visual timeline with icons
- Color-coded by event type
- Most recent at top

**Last Hole Tab:**
- Same format as current hole
- Provides reference context
- Shows final settlement

**Game History Tab:**
- All holes, grouped by hole number
- Expandable/collapsible sections
- Summary stats (total doubles, total pressed, etc.)

## Visual Design

### Color Coding

- **Teams:** Distinct colors (e.g., blue vs. orange)
- **Event types:**
  - Double offered: yellow/warning
  - Double accepted: green/success
  - Double declined: red/cancel
  - Press: purple/special
- **Pending actions:** Animated pulse, attention-grabbing

### Animations

- New events slide in from top
- Multiplier change animates (number flip)
- Accept/decline buttons fade in
- Panel expand/collapse smooth transition

### Responsive Breakpoints

- **Desktop (> 1024px):** Side panel, always visible option
- **Tablet (768-1024px):** Expandable panel, default collapsed
- **Mobile (< 768px):** Bottom sheet, swipe gestures

## Error Handling

### Client-Side Validation

Before creating event:
- Correct player making action
- No conflicting pending action
- Within bet limits (if configured)
- Game state allows action (hole active, not complete)

### Server-Side Validation

Server checks:
- Game exists and is active
- Player is in game
- Event order is valid
- No race conditions

### Sync Failures

**Retry Strategy:**
1. First failure: retry after 1s
2. Second failure: retry after 2s
3. Third failure: retry after 4s
4. Max retry: 30s
5. After max: show error to user, queue for later sync

**User Feedback:**
- Sync status indicator (synced, pending, error)
- Toast notification on persistent errors
- Option to manually retry

**Rollback:**
If server rejects event:
1. Remove from local event log
2. Recalculate state from remaining events
3. Update UI to reflect corrected state
4. Show user-friendly error message

## Future Enhancements

Possible additions (not in initial scope):

- Bet limits configuration per game
- Automatic press on specific conditions
- Betting statistics per player
- Export betting history to PDF
- Undo last betting action (within time window)
- Betting notifications/alerts

## Success Criteria

The betting tracker successfully:
1. Answers "what's the bet?" instantly
2. Shows "who's on which team?" clearly
3. Provides full betting action history
4. Handles doubles/presses without confusion
5. Syncs reliably to backend
6. Works seamlessly on mobile and desktop
7. Integrates with existing game without disruption

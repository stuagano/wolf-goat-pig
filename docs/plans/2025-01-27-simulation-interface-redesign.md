# Simulation Interface Redesign - Visual Decision Engine

**Date:** 2025-01-27
**Status:** Design Approved
**Design Approach:** Vertical Flow Layout

## Overview

Redesign the simulation mode interface to transform the current "big blob of JSON" into an effective visual decision-making interface. The design prioritizes balanced game state visibility with large, clear decision buttons.

## Design Principles

1. **Game State Analysis Focus** - Users need comprehensive context (betting, positions, shot info) to make informed decisions
2. **Equal Decision Prominence** - All decision types (partnership, betting, continue) get equal-sized large buttons
3. **Balanced Split** - 40-50% visualization, 40-50% decision interface
4. **Vertical Flow** - Top-to-bottom layout for mobile-friendly experience
5. **Use Existing Components** - Leverage Material-UI or current component library

## Layout Architecture: "Vertical Flow"

### Three-Section Layout (Top to Bottom)

```
┌─────────────────────────────────────────┐
│  HOLE VISUALIZATION (35%)               │
│  Top-down 2D golf hole with players    │
└─────────────────────────────────────────┘
┌─────────────┬─────────────┬─────────────┐
│  Players &  │  Betting    │  Shot       │
│  Scores     │  State      │  Context    │
│  (Card 1)   │  (Card 2)   │  (Card 3)   │
└─────────────┴─────────────┴─────────────┘
│  GAME STATE CARDS (25%)                 │
└─────────────────────────────────────────┘
┌─────────────────────────────────────────┐
│  DECISION BUTTONS (40%)                 │
│  Large, equal-sized action buttons      │
│  2-3 column grid                        │
└─────────────────────────────────────────┘
```

## Section 1: Hole Visualization (Top 35%)

### Visual Design
**Top-down 2D golf hole using SVG with 4-color zones:**

- **Tee Box** - Dark green rectangle at bottom
- **Fairway** - Light green path/oval in middle
- **Green** - Bright green circle at top
- **Rough/Out** - Tan/brown background

### Player Representation
- **Colored dots** (12-16px diameter) positioned on hole
- **Human player:** Blue dot with white border
- **Computer players:** Red, yellow, orange dots
- **Interaction:** Player name label on hover/tap

### Additional Elements
- Distance markers (yardage lines)
- Hole number and par in top-left corner
- Flagstick icon on the green

### Implementation Details
```jsx
<svg viewBox="0 0 300 500" style={{width: '100%', height: 'auto'}}>
  {/* Background - Rough */}
  <rect width="300" height="500" fill="#D2B48C" />

  {/* Fairway - Light green path */}
  <ellipse cx="150" cy="250" rx="80" ry="200" fill="#90EE90" />

  {/* Green - Bright green circle at top */}
  <circle cx="150" cy="50" r="40" fill="#00FF00" />

  {/* Tee Box - Dark green rectangle at bottom */}
  <rect x="120" y="460" width="60" height="30" fill="#006400" />

  {/* Player dots positioned dynamically */}
  {players.map(player => (
    <circle
      key={player.id}
      cx={player.x}
      cy={player.y}
      r="8"
      fill={player.color}
      stroke={player.is_human ? "white" : "none"}
      strokeWidth="2"
    />
  ))}

  {/* Flagstick */}
  <line x1="150" y1="50" x2="150" y2="30" stroke="red" strokeWidth="2" />
</svg>
```

### Responsive Behavior
- SVG scales naturally with viewport
- Maintains aspect ratio
- Min-height to prevent excessive squishing on mobile

## Section 2: Game State Cards (Middle 25%)

### Layout
Horizontal row of 3 equal-width cards (responsive: stacks vertically on mobile)

### Card 1: Players & Scores
**Content:**
- List of all 4 players with current points/scores
- Captain indicator (👑 crown icon/badge)
- Human player highlight (blue background tint)
- Partnership indicator (visual connection between teammates)

**Example:**
```
┌─────────────────┐
│ PLAYERS         │
├─────────────────┤
│ 👤 You (👑)     │
│ Points: 12      │
│                 │
│ 🤖 Alice        │
│ Points: 8       │
│                 │
│ 🤖 Bob          │
│ Points: 10      │
│                 │
│ 🤖 Carol        │
│ Points: 6       │
└─────────────────┘
```

### Card 2: Betting State
**Content:**
- Current wager (large, prominent)
- Base wager (for reference)
- Pot size if applicable
- Betting phase ("Pre-tee", "Tee shots", "In play")
- Doubled indicator (2x badge)

**Example:**
```
┌─────────────────┐
│ BETTING         │
├─────────────────┤
│ Current Wager   │
│   $20  [2x]     │
│                 │
│ Base: $10       │
│ Pot: $80        │
│                 │
│ Phase: In Play  │
└─────────────────┘
```

### Card 3: Shot Context
**Content:**
- Current shot number / total
- Distance to hole
- Lie quality (from shotState)
- Recommended shot type
- Win probability

**Example:**
```
┌─────────────────┐
│ SHOT CONTEXT    │
├─────────────────┤
│ Shot 2 of 4     │
│                 │
│ 🎯 185 yards    │
│ Lie: Fairway    │
│                 │
│ Recommended:    │
│ 5-iron          │
│                 │
│ Win Prob: 65%   │
└─────────────────┘
```

### Styling
- Use existing Card component
- Theme colors from context
- Typography hierarchy: labels (12px), values (16-20px)
- Subtle borders/shadows
- Icons for visual recognition

### Responsive Behavior
```css
/* Desktop: horizontal row */
.game-state-cards {
  display: flex;
  gap: 1rem;
}

/* Mobile: vertical stack */
@media (max-width: 768px) {
  .game-state-cards {
    flex-direction: column;
  }
}
```

## Section 3: Decision Buttons (Bottom 40%)

### Button Layout
**Dynamic grid based on available decisions:**
- 2-3 columns depending on decision count
- All buttons equal size (large, touch-friendly)
- Minimum height: 60-80px
- Generous spacing (16-24px gaps)

### Button Types

#### Partnership Decisions
**When:** `interactionNeeded.type` includes partnership-related types
**Buttons:**
- "🤝 Request Partner: [Name]" (one per available partner)
- "🚀 Go Solo"
- "👀 Keep Watching"

**Styling:**
- Color: Primary theme blue
- Icon prefix for recognition
- Description text below (12-14px): consequence of action

**Example:**
```
┌────────────────┐  ┌────────────────┐
│ 🤝 Partner:    │  │ 🤝 Partner:    │
│    Alice       │  │    Bob         │
│ Form team      │  │ Form team      │
└────────────────┘  └────────────────┘

┌────────────────┐  ┌────────────────┐
│ 🚀 Go Solo     │  │ 👀 Keep        │
│ Double & play  │  │    Watching    │
│ alone          │  │ See more shots │
└────────────────┘  └────────────────┘
```

#### Betting Decisions
**When:** `interactionNeeded.type` includes double-related types
**Buttons:**
- "💰 Offer Double"
- "✅ Accept Double"
- "❌ Decline Double"

**Styling:**
- Color: Gold/yellow theme
- Icon prefix
- Show wager amounts in description

**Example:**
```
┌────────────────┐  ┌────────────────┐
│ 💰 Offer       │  │ ❌ Decline     │
│    Double      │  │    Double      │
│ Raise to $20   │  │ Keep at $10    │
└────────────────┘  └────────────────┘
```

#### Continue Action
**When:** `hasNextShot` is true and no interaction needed
**Button:**
- "▶️ Play Next Shot"

**Styling:**
- Color: Green/success theme
- Full width (spans all columns if only button)
- Prominent call-to-action

**Example:**
```
┌───────────────────────────────────┐
│ ▶️  Play Next Shot                │
│    Continue simulation            │
└───────────────────────────────────┘
```

### Button Implementation
```jsx
<Button
  variant="contained"
  size="large"
  onClick={handleDecision}
  disabled={loading}
  style={{
    minHeight: '80px',
    fontSize: '18px',
    fontWeight: 'bold',
    display: 'flex',
    flexDirection: 'column',
    gap: '8px'
  }}
>
  <span style={{fontSize: '24px'}}>🤝</span>
  <span>Request Partner: Alice</span>
  <span style={{fontSize: '14px', opacity: 0.8}}>
    Form team
  </span>
</Button>
```

### Conditional Display Logic
```javascript
// Only show relevant buttons based on game state
if (!interactionNeeded && !hasNextShot) {
  return <div>Waiting for simulation...</div>;
}

if (interactionNeeded?.type === 'captain_chooses_partner') {
  // Show partnership buttons
}

if (interactionNeeded?.type === 'double_offer') {
  // Show betting buttons
}

if (hasNextShot && !interactionNeeded) {
  // Show continue button
}
```

### Loading State
- Show spinner overlay when `loading` is true
- Disable all buttons during processing
- Visual feedback on click (ripple effect from Material-UI)

## Component Structure

### Main Component: SimulationVisualInterface
```jsx
<div className="simulation-visual-interface">
  {/* Top 35% - Hole Visualization */}
  <HoleVisualization
    hole={gameState?.hole_info}
    players={gameState?.players}
    playerPositions={calculatePlayerPositions(gameState)}
  />

  {/* Middle 25% - Game State Cards */}
  <div className="game-state-cards">
    <PlayersCard
      players={gameState?.players}
      captainId={gameState?.captain_id}
    />
    <BettingCard
      betting={gameState?.betting}
      baseWager={gameState?.base_wager}
      pokerState={pokerState}
    />
    <ShotContextCard
      shotState={shotState}
      probabilities={shotProbabilities}
      holeState={gameState?.hole_state}
    />
  </div>

  {/* Bottom 40% - Decision Buttons */}
  <DecisionButtons
    interactionNeeded={interactionNeeded}
    hasNextShot={hasNextShot}
    onDecision={onMakeDecision}
    onNextShot={playNextShot}
    loading={loading}
  />
</div>
```

## Data Flow

### Input Props
```typescript
interface SimulationVisualInterfaceProps {
  gameState: GameState;           // Full game state from backend
  shotState: ShotState;           // Current shot context
  shotProbabilities: object;      // Probability data
  interactionNeeded: InteractionNeeded | null;
  hasNextShot: boolean;
  loading: boolean;
  pokerState: PokerState;
  onMakeDecision: (decision) => void;
  onNextShot: () => void;
}
```

### Derived State
- **Player positions** - Calculate from `gameState.hole_state` and player data
- **Available partners** - Filter from `interactionNeeded.available_partners`
- **Button visibility** - Conditional based on `interactionNeeded.type` and `hasNextShot`
- **Current wager** - From `gameState.betting.current_wager` or `base_wager`

## Styling & Theming

### Color Palette (4-color golf aesthetic)
```javascript
const golfColors = {
  teeBox: '#006400',      // Dark green
  fairway: '#90EE90',     // Light green
  green: '#00FF00',       // Bright green
  rough: '#D2B48C',       // Tan

  humanPlayer: '#2196F3',  // Blue
  computerPlayer1: '#F44336', // Red
  computerPlayer2: '#FFC107', // Yellow
  computerPlayer3: '#FF9800', // Orange
};
```

### Responsive Breakpoints
```css
/* Mobile: < 768px */
- Single column layout
- Cards stack vertically
- Buttons stack or 2-column grid

/* Tablet: 768px - 1024px */
- 2-column card layout (2 cards top, 1 bottom)
- 2-column button grid

/* Desktop: > 1024px */
- 3-column card layout (horizontal row)
- 2-3 column button grid based on count
```

## Integration Points

### Replace Current Component
**File:** `frontend/src/components/simulation/SimulationMode.js`
**Lines:** 863-922 (current rendering logic)

### Use Existing Hooks & Context
- `useGame()` - Game state and actions
- `useTheme()` - Theming
- `useSimulationApi()` - API calls

### Maintain Existing API Contract
- No changes to backend endpoints
- Same decision payload format
- Same game state structure expectations

## Success Criteria

1. ✅ **Visual Clarity** - Users can quickly understand game state at a glance
2. ✅ **Decision Confidence** - Large buttons with clear labels and consequences
3. ✅ **Mobile Responsive** - Works on all screen sizes
4. ✅ **Performance** - No lag in rendering updates
5. ✅ **Accessibility** - Keyboard navigation, screen reader friendly
6. ✅ **Consistency** - Uses existing component library and theme

## Out of Scope

- Backend changes or new API endpoints
- Game logic modifications
- Real-time multiplayer features
- Advanced animations or transitions
- 3D visualization or realistic graphics

## Next Steps

1. **Create implementation plan** - Break down into tasks
2. **Set up worktree** - Isolated development environment
3. **Build components** - Implement design incrementally
4. **Test with mock data** - Verify layout and interactions
5. **Integrate with real API** - Connect to backend
6. **User testing** - Validate decision-making experience

---

**Design approved and ready for implementation.**

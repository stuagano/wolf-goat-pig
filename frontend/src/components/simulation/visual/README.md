# Simulation Visual Interface

Visual decision-making interface for Wolf-Goat-Pig simulation mode.

## Architecture

**Vertical Flow Layout:** Top-to-bottom design optimized for decision-making

```
┌─────────────────────────────────────────┐
│  HoleVisualization (35%)                │
│  SVG top-down golf hole                 │
└─────────────────────────────────────────┘
┌─────────────┬─────────────┬─────────────┐
│  Players    │  Betting    │  Shot       │
│  Card       │  Card       │  Context    │
└─────────────┴─────────────┴─────────────┘
│  Game State Cards (25%)                 │
└─────────────────────────────────────────┘
┌─────────────────────────────────────────┐
│  DecisionButtons (40%)                  │
│  Large, equal-sized action buttons      │
└─────────────────────────────────────────┘
```

## Components

### SimulationVisualInterface (Container)
Main container component that composes all visual pieces.

**Props:**
- `gameState` - Full game state from backend
- `shotState` - Current shot context
- `shotProbabilities` - Probability data
- `interactionNeeded` - Pending decision info
- `hasNextShot` - Whether continue is available
- `loading` - Loading state
- `pokerState` - Betting state
- `onMakeDecision` - Callback for decisions
- `onNextShot` - Callback for continue

### HoleVisualization
4-color SVG top-down golf hole with player positions.

**Features:**
- Tee box, fairway, green, rough
- Player dots with colors
- Human player highlighted
- Hole info overlay

### PlayersCard
Display all players with scores and captain indicator.

**Features:**
- Player list with icons
- Points display
- Captain crown indicator
- Human player highlight

### BettingCard
Current wager, pot, and betting phase.

**Features:**
- Current wager (large)
- Doubled indicator
- Base wager reference
- Pot size
- Betting phase

### ShotContextCard
Shot context and recommendations.

**Features:**
- Shot number/total
- Distance to hole
- Lie quality
- Recommended shot
- Win probability

### DecisionButtons
Large, equal-sized decision buttons.

**Features:**
- Partnership buttons
- Betting buttons
- Continue button
- Dynamic grid layout
- Icon + label + description

## Responsive Behavior

### Desktop (>1024px)
- 3 cards in horizontal row
- All sections fully visible
- Optimal proportions (35-25-40)

### Tablet (768-1024px)
- 2 cards in row, 1 below
- Section heights adjust
- Buttons may wrap to 2 columns

### Mobile (<768px)
- All cards stack vertically
- Smaller section heights
- Single column button layout
- Reduced spacing

## Usage

```javascript
import { SimulationVisualInterface } from './components/simulation/visual';

<SimulationVisualInterface
  gameState={gameState}
  shotState={shotState}
  shotProbabilities={shotProbabilities}
  interactionNeeded={interactionNeeded}
  hasNextShot={hasNextShot}
  loading={loading}
  pokerState={pokerState}
  onMakeDecision={handleDecision}
  onNextShot={playNextShot}
/>
```

## Testing

Each component has comprehensive unit tests in `__tests__/` directory.

Run tests:
```bash
npm test -- visual/
```

## Design Reference

See `docs/plans/2025-01-27-simulation-interface-redesign.md` for complete design documentation.

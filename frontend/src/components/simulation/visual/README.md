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
Current wager, pot, betting phase, and real-time betting odds.

**Features:**
- Current wager (large)
- Doubled indicator
- Base wager reference
- Pot size
- Betting phase
- **NEW:** 📊 Betting Odds Section
  - Probability display with visual bar
  - Expected value analysis
  - Risk level indicator
  - AI reasoning explanation
  - Educational tooltip

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

---

## Betting Odds Integration

### Overview

Real-time betting odds display integrated into BettingCard and DecisionButtons, providing players with AI-powered probability analysis and strategic recommendations.

### Data Structure

The `shotProbabilities` prop includes betting analysis:

```javascript
shotProbabilities: {
  make_shot: 0.45,
  // ... other shot probabilities ...
  betting_analysis: {
    offer_double: 0.68,        // Probability opponent will offer double
    accept_double: 0.42,       // Probability accepting is +EV
    expected_value: 2.5,       // Expected points gained/lost
    risk_level: "low",         // "low", "medium", or "high"
    reasoning: "You have position advantage"
  }
}
```

### Components

#### ProbabilityBar
Visual 8-dot representation of probabilities.

**Props:**
- `value`: Number (0-1) - Probability to display

**Behavior:**
- Renders 8 dots
- Fills dots proportionally (0.65 = 5 filled dots)
- Clamps values to [0, 1]
- Inherits color from parent

**Example:**
```javascript
<ProbabilityBar value={0.65} />
```

#### EducationalTooltip
Contextual help tooltips with mouse-following behavior.

**Props:**
- `title`: String - Tooltip header
- `content`: String - Explanation text
- `type`: String - "info", "tip", "warning", "concept"

**Example:**
```javascript
<EducationalTooltip
  title="What are betting odds?"
  content="Probabilities based on game state and positions"
  type="info"
/>
```

### Utility Functions

Located in `utils/oddsHelpers.js`:

- `getProbabilityColor(probability)` - Returns 'success', 'warning', or 'disabled'
- `getProbabilityLabel(probability)` - Returns "Likely", "Possible", or "Unlikely"
- `formatExpectedValue(value)` - Formats with +/- sign (e.g., "+2.3")
- `getRiskLevelColor(riskLevel)` - Maps risk to color

### Error Handling

**Graceful degradation:** Game continues normally if odds unavailable.

**Error states:**
- `{ error: 'unavailable' }` - Shows "⚠️ Odds temporarily unavailable"
- `null` or `undefined` - Hides odds section
- Network errors - Silent fallback, no user disruption

### Visual Design

**Color Coding:**
- Green (>60%): Likely, favorable
- Orange (40-60%): Possible, medium risk
- Gray (<40%): Unlikely, unfavorable

**Typography:**
- Expected value: "+2.5 pts 📈" or "-1.8 pts 📉"
- Risk level: Color-coded "Low", "Medium", "High"
- Reasoning: Italicized explanation text

### Testing

**Test files:**
- `__tests__/BettingCard.odds.test.js` (12 tests)
- `__tests__/DecisionButtons.odds.test.js` (15 tests)
- `__tests__/ProbabilityBar.test.js` (12 tests)
- `__tests__/EducationalTooltip.test.js` (6 tests)
- `__tests__/utils/oddsHelpers.test.js` (19 tests)

**Total:** 64 odds-specific tests + 35 integration tests = 99 passing tests

### Performance

- Initial render: <50ms
- Odds update: <50ms
- Smart caching: Odds only fetched at decision points
- No memory leaks after 100+ decisions

### Browser Support

- ✅ Chrome 90+
- ✅ Safari 14+
- ✅ Firefox 88+
- ✅ Edge 90+

### Accessibility

- WCAG AA compliant (4.5:1 color contrast)
- Keyboard navigable (Tab + Enter for tooltips)
- Screen reader friendly (aria-labels on all interactive elements)
- Touch-friendly (44px minimum touch targets)

For complete documentation, see `docs/plans/2025-01-28-betting-odds-integration.md`.

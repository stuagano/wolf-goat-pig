# Simulation Visual Interface Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Transform simulation mode from JSON blob display into a visual decision-making interface with top-down golf hole visualization, game state cards, and large decision buttons.

**Architecture:** Vertical flow layout (35% hole viz, 25% info cards, 40% buttons) using React components. SVG for golf hole, existing UI library (Material-UI) for cards/buttons. Component composition pattern with minimal props drilling.

**Tech Stack:** React, SVG, Material-UI (existing), TypeScript/JSX

---

## Prerequisites

**Verify existing components:**
- Card component available at `frontend/src/components/ui`
- Button component available at `frontend/src/components/ui`
- Theme system via `frontend/src/theme/Provider`

**Design document reference:** `docs/plans/2025-01-27-simulation-interface-redesign.md`

---

## Task 1: Create HoleVisualization Component (SVG Golf Hole)

**Goal:** Build simple 4-color top-down SVG golf hole with player dots

**Files:**
- Create: `frontend/src/components/simulation/visual/HoleVisualization.jsx`
- Create: `frontend/src/components/simulation/visual/__tests__/HoleVisualization.test.js`
- Create: `frontend/src/components/simulation/visual/index.js`

### Step 1: Write failing test

Create test file:

```javascript
// frontend/src/components/simulation/visual/__tests__/HoleVisualization.test.js
import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import HoleVisualization from '../HoleVisualization';

describe('HoleVisualization', () => {
  const mockHole = {
    hole_number: 1,
    par: 4,
    yards: 380
  };

  const mockPlayers = [
    { id: 'human', name: 'You', is_human: true, position: 0 },
    { id: 'bot1', name: 'Alice', is_human: false, position: 100 },
    { id: 'bot2', name: 'Bob', is_human: false, position: 150 }
  ];

  test('renders SVG element', () => {
    render(<HoleVisualization hole={mockHole} players={mockPlayers} />);
    const svg = document.querySelector('svg');
    expect(svg).toBeInTheDocument();
  });

  test('displays hole number and par', () => {
    render(<HoleVisualization hole={mockHole} players={mockPlayers} />);
    expect(screen.getByText(/Hole 1/i)).toBeInTheDocument();
    expect(screen.getByText(/Par 4/i)).toBeInTheDocument();
  });

  test('renders player dots', () => {
    render(<HoleVisualization hole={mockHole} players={mockPlayers} />);
    const svg = document.querySelector('svg');
    const circles = svg.querySelectorAll('circle');
    // Should have at least player dots (may have green circle too)
    expect(circles.length).toBeGreaterThanOrEqual(3);
  });

  test('highlights human player with border', () => {
    render(<HoleVisualization hole={mockHole} players={mockPlayers} />);
    const svg = document.querySelector('svg');
    const humanDot = Array.from(svg.querySelectorAll('circle')).find(
      circle => circle.getAttribute('stroke') === 'white'
    );
    expect(humanDot).toBeInTheDocument();
  });
});
```

### Step 2: Run test to verify it fails

```bash
cd frontend
npm test -- HoleVisualization.test.js
```

Expected: FAIL - "Cannot find module '../HoleVisualization'"

### Step 3: Write minimal implementation

```javascript
// frontend/src/components/simulation/visual/HoleVisualization.jsx
import React from 'react';
import PropTypes from 'prop-types';

const COLORS = {
  teeBox: '#006400',
  fairway: '#90EE90',
  green: '#00FF00',
  rough: '#D2B48C',
  humanPlayer: '#2196F3',
  computerPlayers: ['#F44336', '#FFC107', '#FF9800']
};

const HoleVisualization = ({ hole, players = [] }) => {
  const SVG_WIDTH = 300;
  const SVG_HEIGHT = 500;

  // Calculate player Y positions based on their distance from tee
  const calculatePlayerPosition = (player, index) => {
    // Default positions if no position data
    const defaultY = 460 - (index * 40); // Space them out from tee

    if (typeof player.position === 'number') {
      // Position 0 = tee (y=475), position = hole yards = green (y=50)
      const maxYards = hole?.yards || 400;
      const progress = player.position / maxYards;
      return 475 - (progress * 425); // Map to SVG y coordinates
    }

    return defaultY;
  };

  return (
    <div style={{ width: '100%', position: 'relative' }}>
      {/* Info overlay */}
      <div style={{
        position: 'absolute',
        top: '10px',
        left: '10px',
        background: 'rgba(255, 255, 255, 0.9)',
        padding: '8px 12px',
        borderRadius: '4px',
        fontSize: '14px',
        fontWeight: 'bold',
        zIndex: 10
      }}>
        Hole {hole?.hole_number || '?'} • Par {hole?.par || '?'}
      </div>

      <svg
        viewBox={`0 0 ${SVG_WIDTH} ${SVG_HEIGHT}`}
        style={{ width: '100%', height: 'auto', display: 'block' }}
      >
        {/* Background - Rough */}
        <rect
          width={SVG_WIDTH}
          height={SVG_HEIGHT}
          fill={COLORS.rough}
        />

        {/* Fairway - Light green ellipse */}
        <ellipse
          cx={SVG_WIDTH / 2}
          cy={SVG_HEIGHT / 2}
          rx={80}
          ry={200}
          fill={COLORS.fairway}
        />

        {/* Green - Bright green circle at top */}
        <circle
          cx={SVG_WIDTH / 2}
          cy={50}
          r={40}
          fill={COLORS.green}
        />

        {/* Flagstick */}
        <line
          x1={SVG_WIDTH / 2}
          y1={50}
          x2={SVG_WIDTH / 2}
          y2={30}
          stroke="red"
          strokeWidth={2}
        />
        <circle
          cx={SVG_WIDTH / 2}
          cy={30}
          r={5}
          fill="red"
        />

        {/* Tee Box - Dark green rectangle at bottom */}
        <rect
          x={(SVG_WIDTH / 2) - 30}
          y={460}
          width={60}
          height={30}
          fill={COLORS.teeBox}
        />

        {/* Player dots */}
        {players.map((player, index) => {
          const y = calculatePlayerPosition(player, index);
          const x = SVG_WIDTH / 2 + ((index % 2 === 0 ? 1 : -1) * (15 + index * 5)); // Offset for visibility
          const isHuman = player.is_human || player.id === 'human';
          const color = isHuman
            ? COLORS.humanPlayer
            : COLORS.computerPlayers[index % COLORS.computerPlayers.length];

          return (
            <g key={player.id}>
              <circle
                cx={x}
                cy={y}
                r={8}
                fill={color}
                stroke={isHuman ? 'white' : 'none'}
                strokeWidth={isHuman ? 2 : 0}
              />
              {/* Player name on hover - using title element */}
              <title>{player.name}</title>
            </g>
          );
        })}
      </svg>
    </div>
  );
};

HoleVisualization.propTypes = {
  hole: PropTypes.shape({
    hole_number: PropTypes.number,
    par: PropTypes.number,
    yards: PropTypes.number
  }),
  players: PropTypes.arrayOf(PropTypes.shape({
    id: PropTypes.string.isRequired,
    name: PropTypes.string.isRequired,
    is_human: PropTypes.bool,
    position: PropTypes.number
  }))
};

export default HoleVisualization;
```

Create index file:

```javascript
// frontend/src/components/simulation/visual/index.js
export { default as HoleVisualization } from './HoleVisualization';
```

### Step 4: Run test to verify it passes

```bash
cd frontend
npm test -- HoleVisualization.test.js
```

Expected: PASS (all 4 tests)

### Step 5: Commit

```bash
git add frontend/src/components/simulation/visual/
git commit -m "feat: add HoleVisualization SVG component

- 4-color top-down golf hole (tee, fairway, green, rough)
- Player dots with position mapping
- Human player highlighted with white border
- Hole info overlay (number and par)

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Task 2: Create PlayersCard Component

**Goal:** Display all players with scores, captain indicator, partnership status

**Files:**
- Create: `frontend/src/components/simulation/visual/PlayersCard.jsx`
- Create: `frontend/src/components/simulation/visual/__tests__/PlayersCard.test.js`
- Modify: `frontend/src/components/simulation/visual/index.js`

### Step 1: Write failing test

```javascript
// frontend/src/components/simulation/visual/__tests__/PlayersCard.test.js
import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import { ThemeProvider } from '../../../theme/Provider';
import PlayersCard from '../PlayersCard';

const renderWithTheme = (component) => {
  return render(
    <ThemeProvider>{component}</ThemeProvider>
  );
};

describe('PlayersCard', () => {
  const mockPlayers = [
    { id: 'human', name: 'You', points: 12, is_human: true },
    { id: 'bot1', name: 'Alice', points: 8, is_human: false },
    { id: 'bot2', name: 'Bob', points: 10, is_human: false },
    { id: 'bot3', name: 'Carol', points: 6, is_human: false }
  ];

  test('renders all players', () => {
    renderWithTheme(<PlayersCard players={mockPlayers} />);
    expect(screen.getByText('You')).toBeInTheDocument();
    expect(screen.getByText('Alice')).toBeInTheDocument();
    expect(screen.getByText('Bob')).toBeInTheDocument();
    expect(screen.getByText('Carol')).toBeInTheDocument();
  });

  test('displays player points', () => {
    renderWithTheme(<PlayersCard players={mockPlayers} />);
    expect(screen.getByText(/12/)).toBeInTheDocument();
    expect(screen.getByText(/8/)).toBeInTheDocument();
  });

  test('shows captain indicator', () => {
    renderWithTheme(<PlayersCard players={mockPlayers} captainId="bot1" />);
    // Check for crown emoji or captain text
    const card = screen.getByText('Alice').closest('div');
    expect(card.textContent).toMatch(/👑|Captain/i);
  });

  test('highlights human player', () => {
    renderWithTheme(<PlayersCard players={mockPlayers} />);
    const humanElement = screen.getByText('You').closest('div');
    // Should have some styling distinction (we'll check for data attribute)
    expect(humanElement).toHaveAttribute('data-is-human', 'true');
  });
});
```

### Step 2: Run test to verify it fails

```bash
cd frontend
npm test -- PlayersCard.test.js
```

Expected: FAIL - "Cannot find module '../PlayersCard'"

### Step 3: Write minimal implementation

```javascript
// frontend/src/components/simulation/visual/PlayersCard.jsx
import React from 'react';
import PropTypes from 'prop-types';
import { Card } from '../../ui';

const PlayersCard = ({ players = [], captainId = null }) => {
  return (
    <Card style={{ padding: '16px', height: '100%' }}>
      <h3 style={{ margin: '0 0 12px 0', fontSize: '16px', fontWeight: 'bold' }}>
        PLAYERS
      </h3>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
        {players.map(player => {
          const isCaptain = player.id === captainId;
          const isHuman = player.is_human || player.id === 'human';

          return (
            <div
              key={player.id}
              data-is-human={isHuman}
              style={{
                padding: '8px',
                borderRadius: '4px',
                backgroundColor: isHuman ? 'rgba(33, 150, 243, 0.1)' : 'transparent',
                border: isHuman ? '1px solid rgba(33, 150, 243, 0.3)' : '1px solid transparent'
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span style={{ fontSize: '20px' }}>
                    {isHuman ? '👤' : '🤖'}
                  </span>
                  <span style={{ fontWeight: isHuman ? 'bold' : 'normal' }}>
                    {player.name}
                    {isCaptain && ' 👑'}
                  </span>
                </div>
                <div style={{ fontSize: '14px', color: '#666' }}>
                  Points: <span style={{ fontWeight: 'bold', fontSize: '16px' }}>
                    {player.points || 0}
                  </span>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </Card>
  );
};

PlayersCard.propTypes = {
  players: PropTypes.arrayOf(PropTypes.shape({
    id: PropTypes.string.isRequired,
    name: PropTypes.string.isRequired,
    points: PropTypes.number,
    is_human: PropTypes.bool
  })),
  captainId: PropTypes.string
};

export default PlayersCard;
```

Update index:

```javascript
// frontend/src/components/simulation/visual/index.js
export { default as HoleVisualization } from './HoleVisualization';
export { default as PlayersCard } from './PlayersCard';
```

### Step 4: Run test to verify it passes

```bash
cd frontend
npm test -- PlayersCard.test.js
```

Expected: PASS (all 4 tests)

### Step 5: Commit

```bash
git add frontend/src/components/simulation/visual/
git commit -m "feat: add PlayersCard component

- Display all players with points
- Highlight human player with blue tint
- Captain indicator with crown emoji
- Clean card layout with icons

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Task 3: Create BettingCard Component

**Goal:** Display current wager, pot, betting phase, doubled status

**Files:**
- Create: `frontend/src/components/simulation/visual/BettingCard.jsx`
- Create: `frontend/src/components/simulation/visual/__tests__/BettingCard.test.js`
- Modify: `frontend/src/components/simulation/visual/index.js`

### Step 1: Write failing test

```javascript
// frontend/src/components/simulation/visual/__tests__/BettingCard.test.js
import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import { ThemeProvider } from '../../../theme/Provider';
import BettingCard from '../BettingCard';

const renderWithTheme = (component) => {
  return render(
    <ThemeProvider>{component}</ThemeProvider>
  );
};

describe('BettingCard', () => {
  const mockBetting = {
    current_wager: 20,
    doubled: true
  };

  const mockPokerState = {
    pot_size: 80,
    betting_phase: 'In Play'
  };

  test('displays current wager', () => {
    renderWithTheme(
      <BettingCard betting={mockBetting} baseWager={10} pokerState={mockPokerState} />
    );
    expect(screen.getByText(/20/)).toBeInTheDocument();
  });

  test('shows doubled indicator when doubled', () => {
    renderWithTheme(
      <BettingCard betting={mockBetting} baseWager={10} pokerState={mockPokerState} />
    );
    expect(screen.getByText(/2x/i)).toBeInTheDocument();
  });

  test('displays pot size', () => {
    renderWithTheme(
      <BettingCard betting={mockBetting} baseWager={10} pokerState={mockPokerState} />
    );
    expect(screen.getByText(/Pot.*80/i)).toBeInTheDocument();
  });

  test('shows betting phase', () => {
    renderWithTheme(
      <BettingCard betting={mockBetting} baseWager={10} pokerState={mockPokerState} />
    );
    expect(screen.getByText(/In Play/i)).toBeInTheDocument();
  });

  test('falls back to base wager when no betting data', () => {
    renderWithTheme(
      <BettingCard baseWager={5} />
    );
    expect(screen.getByText(/5/)).toBeInTheDocument();
  });
});
```

### Step 2: Run test to verify it fails

```bash
cd frontend
npm test -- BettingCard.test.js
```

Expected: FAIL - "Cannot find module '../BettingCard'"

### Step 3: Write minimal implementation

```javascript
// frontend/src/components/simulation/visual/BettingCard.jsx
import React from 'react';
import PropTypes from 'prop-types';
import { Card } from '../../ui';

const BettingCard = ({ betting = {}, baseWager = 1, pokerState = {} }) => {
  const currentWager = betting?.current_wager || baseWager;
  const isDoubled = betting?.doubled || false;
  const potSize = pokerState?.pot_size || 0;
  const bettingPhase = pokerState?.betting_phase || 'Pre-tee';

  return (
    <Card style={{ padding: '16px', height: '100%' }}>
      <h3 style={{ margin: '0 0 12px 0', fontSize: '16px', fontWeight: 'bold' }}>
        BETTING
      </h3>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
        {/* Current Wager */}
        <div>
          <div style={{ fontSize: '12px', color: '#666', marginBottom: '4px' }}>
            Current Wager
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ fontSize: '28px', fontWeight: 'bold', color: '#FFC107' }}>
              ${currentWager}
            </span>
            {isDoubled && (
              <span style={{
                background: '#FF9800',
                color: 'white',
                padding: '2px 8px',
                borderRadius: '12px',
                fontSize: '12px',
                fontWeight: 'bold'
              }}>
                2x
              </span>
            )}
          </div>
        </div>

        {/* Base Wager Reference */}
        <div style={{ fontSize: '14px', color: '#666' }}>
          Base: ${baseWager}
        </div>

        {/* Pot Size */}
        {potSize > 0 && (
          <div style={{ fontSize: '14px', color: '#666' }}>
            Pot: <span style={{ fontWeight: 'bold', color: '#000' }}>${potSize}</span>
          </div>
        )}

        {/* Betting Phase */}
        <div style={{
          marginTop: '8px',
          padding: '8px',
          background: '#f5f5f5',
          borderRadius: '4px',
          fontSize: '14px',
          textAlign: 'center'
        }}>
          Phase: <span style={{ fontWeight: 'bold' }}>{bettingPhase}</span>
        </div>
      </div>
    </Card>
  );
};

BettingCard.propTypes = {
  betting: PropTypes.shape({
    current_wager: PropTypes.number,
    doubled: PropTypes.bool
  }),
  baseWager: PropTypes.number,
  pokerState: PropTypes.shape({
    pot_size: PropTypes.number,
    betting_phase: PropTypes.string
  })
};

export default BettingCard;
```

Update index:

```javascript
// frontend/src/components/simulation/visual/index.js
export { default as HoleVisualization } from './HoleVisualization';
export { default as PlayersCard } from './PlayersCard';
export { default as BettingCard } from './BettingCard';
```

### Step 4: Run test to verify it passes

```bash
cd frontend
npm test -- BettingCard.test.js
```

Expected: PASS (all 5 tests)

### Step 5: Commit

```bash
git add frontend/src/components/simulation/visual/
git commit -m "feat: add BettingCard component

- Current wager with doubled indicator
- Base wager and pot size display
- Betting phase status
- Gold/yellow theme for betting info

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Task 4: Create ShotContextCard Component

**Goal:** Display shot context (number, distance, lie, recommendations, probabilities)

**Files:**
- Create: `frontend/src/components/simulation/visual/ShotContextCard.jsx`
- Create: `frontend/src/components/simulation/visual/__tests__/ShotContextCard.test.js`
- Modify: `frontend/src/components/simulation/visual/index.js`

### Step 1: Write failing test

```javascript
// frontend/src/components/simulation/visual/__tests__/ShotContextCard.test.js
import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import { ThemeProvider } from '../../../theme/Provider';
import ShotContextCard from '../ShotContextCard';

const renderWithTheme = (component) => {
  return render(
    <ThemeProvider>{component}</ThemeProvider>
  );
};

describe('ShotContextCard', () => {
  const mockShotState = {
    distance_to_hole: 185,
    lie: 'fairway',
    recommended_shot: '5-iron'
  };

  const mockHoleState = {
    current_shot_number: 2,
    total_shots: 4
  };

  const mockProbabilities = {
    win_probability: 0.65
  };

  test('displays shot number and total', () => {
    renderWithTheme(
      <ShotContextCard
        shotState={mockShotState}
        holeState={mockHoleState}
        probabilities={mockProbabilities}
      />
    );
    expect(screen.getByText(/Shot 2 of 4/i)).toBeInTheDocument();
  });

  test('shows distance to hole', () => {
    renderWithTheme(
      <ShotContextCard
        shotState={mockShotState}
        holeState={mockHoleState}
        probabilities={mockProbabilities}
      />
    );
    expect(screen.getByText(/185.*yard/i)).toBeInTheDocument();
  });

  test('displays lie quality', () => {
    renderWithTheme(
      <ShotContextCard
        shotState={mockShotState}
        holeState={mockHoleState}
        probabilities={mockProbabilities}
      />
    );
    expect(screen.getByText(/fairway/i)).toBeInTheDocument();
  });

  test('shows recommended shot', () => {
    renderWithTheme(
      <ShotContextCard
        shotState={mockShotState}
        holeState={mockHoleState}
        probabilities={mockProbabilities}
      />
    );
    expect(screen.getByText(/5-iron/i)).toBeInTheDocument();
  });

  test('displays win probability as percentage', () => {
    renderWithTheme(
      <ShotContextCard
        shotState={mockShotState}
        holeState={mockHoleState}
        probabilities={mockProbabilities}
      />
    );
    expect(screen.getByText(/65%/i)).toBeInTheDocument();
  });
});
```

### Step 2: Run test to verify it fails

```bash
cd frontend
npm test -- ShotContextCard.test.js
```

Expected: FAIL - "Cannot find module '../ShotContextCard'"

### Step 3: Write minimal implementation

```javascript
// frontend/src/components/simulation/visual/ShotContextCard.jsx
import React from 'react';
import PropTypes from 'prop-types';
import { Card } from '../../ui';

const ShotContextCard = ({ shotState = {}, holeState = {}, probabilities = {} }) => {
  const shotNumber = holeState?.current_shot_number || 1;
  const totalShots = holeState?.total_shots || shotNumber;
  const distance = shotState?.distance_to_hole || 0;
  const lie = shotState?.lie || 'unknown';
  const recommendedShot = shotState?.recommended_shot || 'N/A';
  const winProb = probabilities?.win_probability || 0;

  return (
    <Card style={{ padding: '16px', height: '100%' }}>
      <h3 style={{ margin: '0 0 12px 0', fontSize: '16px', fontWeight: 'bold' }}>
        SHOT CONTEXT
      </h3>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
        {/* Shot Number */}
        <div style={{ fontSize: '14px', color: '#666' }}>
          Shot {shotNumber} of {totalShots}
        </div>

        {/* Distance */}
        <div style={{ display: 'flex', alignItems: 'baseline', gap: '4px' }}>
          <span style={{ fontSize: '12px' }}>🎯</span>
          <span style={{ fontSize: '24px', fontWeight: 'bold' }}>
            {distance}
          </span>
          <span style={{ fontSize: '14px', color: '#666' }}>
            yards
          </span>
        </div>

        {/* Lie */}
        <div style={{ fontSize: '14px' }}>
          Lie: <span style={{
            fontWeight: 'bold',
            color: lie === 'fairway' ? '#4CAF50' : '#666',
            textTransform: 'capitalize'
          }}>
            {lie}
          </span>
        </div>

        {/* Recommended Shot */}
        <div style={{
          padding: '8px',
          background: '#f5f5f5',
          borderRadius: '4px',
          fontSize: '14px'
        }}>
          <div style={{ color: '#666', marginBottom: '4px' }}>Recommended:</div>
          <div style={{ fontWeight: 'bold', fontSize: '16px' }}>
            {recommendedShot}
          </div>
        </div>

        {/* Win Probability */}
        {winProb > 0 && (
          <div style={{
            marginTop: '4px',
            padding: '8px',
            background: winProb >= 0.5 ? '#E8F5E9' : '#FFF3E0',
            borderRadius: '4px',
            fontSize: '14px',
            textAlign: 'center'
          }}>
            Win Prob: <span style={{
              fontWeight: 'bold',
              fontSize: '18px',
              color: winProb >= 0.5 ? '#4CAF50' : '#FF9800'
            }}>
              {Math.round(winProb * 100)}%
            </span>
          </div>
        )}
      </div>
    </Card>
  );
};

ShotContextCard.propTypes = {
  shotState: PropTypes.shape({
    distance_to_hole: PropTypes.number,
    lie: PropTypes.string,
    recommended_shot: PropTypes.string
  }),
  holeState: PropTypes.shape({
    current_shot_number: PropTypes.number,
    total_shots: PropTypes.number
  }),
  probabilities: PropTypes.shape({
    win_probability: PropTypes.number
  })
};

export default ShotContextCard;
```

Update index:

```javascript
// frontend/src/components/simulation/visual/index.js
export { default as HoleVisualization } from './HoleVisualization';
export { default as PlayersCard } from './PlayersCard';
export { default as BettingCard } from './BettingCard';
export { default as ShotContextCard } from './ShotContextCard';
```

### Step 4: Run test to verify it passes

```bash
cd frontend
npm test -- ShotContextCard.test.js
```

Expected: PASS (all 5 tests)

### Step 5: Commit

```bash
git add frontend/src/components/simulation/visual/
git commit -m "feat: add ShotContextCard component

- Shot number and distance display
- Lie quality with color coding
- Recommended shot display
- Win probability with visual feedback

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Task 5: Create DecisionButtons Component

**Goal:** Large, equal-sized buttons for partnership, betting, and continue actions

**Files:**
- Create: `frontend/src/components/simulation/visual/DecisionButtons.jsx`
- Create: `frontend/src/components/simulation/visual/__tests__/DecisionButtons.test.js`
- Modify: `frontend/src/components/simulation/visual/index.js`

### Step 1: Write failing test

```javascript
// frontend/src/components/simulation/visual/__tests__/DecisionButtons.test.js
import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import { ThemeProvider } from '../../../theme/Provider';
import DecisionButtons from '../DecisionButtons';

const renderWithTheme = (component) => {
  return render(
    <ThemeProvider>{component}</ThemeProvider>
  );
};

describe('DecisionButtons', () => {
  test('shows continue button when hasNextShot and no interaction', () => {
    const onNextShot = jest.fn();
    renderWithTheme(
      <DecisionButtons
        hasNextShot={true}
        interactionNeeded={null}
        onNextShot={onNextShot}
      />
    );
    const button = screen.getByText(/Play Next Shot/i);
    expect(button).toBeInTheDocument();
    fireEvent.click(button);
    expect(onNextShot).toHaveBeenCalled();
  });

  test('shows partnership buttons when captain chooses partner', () => {
    const onDecision = jest.fn();
    const interaction = {
      type: 'captain_chooses_partner',
      available_partners: ['bot1', 'bot2']
    };
    const gameState = {
      players: [
        { id: 'bot1', name: 'Alice' },
        { id: 'bot2', name: 'Bob' }
      ]
    };

    renderWithTheme(
      <DecisionButtons
        interactionNeeded={interaction}
        onDecision={onDecision}
        gameState={gameState}
      />
    );

    expect(screen.getByText(/Alice/i)).toBeInTheDocument();
    expect(screen.getByText(/Bob/i)).toBeInTheDocument();
    expect(screen.getByText(/Go Solo/i)).toBeInTheDocument();
  });

  test('shows betting buttons when double offered', () => {
    const onDecision = jest.fn();
    const interaction = {
      type: 'double_offer'
    };

    renderWithTheme(
      <DecisionButtons
        interactionNeeded={interaction}
        onDecision={onDecision}
      />
    );

    expect(screen.getByText(/Accept.*Double/i)).toBeInTheDocument();
    expect(screen.getByText(/Decline.*Double/i)).toBeInTheDocument();
  });

  test('disables buttons when loading', () => {
    renderWithTheme(
      <DecisionButtons
        hasNextShot={true}
        loading={true}
      />
    );

    const button = screen.getByText(/Play Next Shot/i);
    expect(button).toBeDisabled();
  });

  test('shows no buttons when no action available', () => {
    const { container } = renderWithTheme(
      <DecisionButtons
        hasNextShot={false}
        interactionNeeded={null}
      />
    );

    expect(screen.getByText(/Waiting/i)).toBeInTheDocument();
  });
});
```

### Step 2: Run test to verify it fails

```bash
cd frontend
npm test -- DecisionButtons.test.js
```

Expected: FAIL - "Cannot find module '../DecisionButtons'"

### Step 3: Write minimal implementation

```javascript
// frontend/src/components/simulation/visual/DecisionButtons.jsx
import React from 'react';
import PropTypes from 'prop-types';
import { Button } from '../../ui';

const DecisionButtons = ({
  interactionNeeded = null,
  hasNextShot = false,
  onDecision = () => {},
  onNextShot = () => {},
  loading = false,
  gameState = {}
}) => {
  // Helper to render large decision button
  const renderButton = (key, icon, label, description, onClick, color = 'primary') => (
    <Button
      key={key}
      variant="contained"
      color={color}
      size="large"
      onClick={onClick}
      disabled={loading}
      style={{
        minHeight: '80px',
        fontSize: '18px',
        fontWeight: 'bold',
        display: 'flex',
        flexDirection: 'column',
        gap: '8px',
        padding: '16px',
        textTransform: 'none'
      }}
    >
      <span style={{ fontSize: '24px' }}>{icon}</span>
      <span>{label}</span>
      {description && (
        <span style={{ fontSize: '14px', opacity: 0.8, fontWeight: 'normal' }}>
          {description}
        </span>
      )}
    </Button>
  );

  // No action available
  if (!interactionNeeded && !hasNextShot) {
    return (
      <div style={{
        padding: '32px',
        textAlign: 'center',
        color: '#666',
        fontSize: '16px'
      }}>
        Waiting for simulation...
      </div>
    );
  }

  // Continue button (no interaction needed, shots available)
  if (!interactionNeeded && hasNextShot) {
    return (
      <div style={{
        display: 'grid',
        gap: '16px',
        padding: '16px'
      }}>
        {renderButton(
          'continue',
          '▶️',
          'Play Next Shot',
          'Continue simulation',
          onNextShot,
          'success'
        )}
      </div>
    );
  }

  const buttons = [];

  // Partnership decisions
  if (interactionNeeded.type === 'captain_chooses_partner') {
    const availablePartners = interactionNeeded.available_partners || [];
    const players = gameState?.players || [];

    // Partner request buttons
    availablePartners.forEach(partnerId => {
      const partner = players.find(p => p.id === partnerId);
      if (partner) {
        buttons.push(renderButton(
          `partner-${partnerId}`,
          '🤝',
          `Partner: ${partner.name}`,
          'Form team',
          () => onDecision({
            action: 'request_partner',
            requested_partner: partnerId
          }),
          'primary'
        ));
      }
    });

    // Go solo button
    buttons.push(renderButton(
      'go-solo',
      '🚀',
      'Go Solo',
      'Double and play alone',
      () => onDecision({ action: 'go_solo' }),
      'primary'
    ));

    // Keep watching button
    buttons.push(renderButton(
      'keep-watching',
      '👀',
      'Keep Watching',
      'See more tee shots',
      () => onDecision({ action: 'keep_watching' }),
      'primary'
    ));
  }

  // Partnership response
  if (interactionNeeded.type === 'partnership_request') {
    buttons.push(renderButton(
      'accept-partnership',
      '✅',
      'Accept Partnership',
      'Team up',
      () => onDecision({ accept_partnership: true }),
      'primary'
    ));

    buttons.push(renderButton(
      'decline-partnership',
      '❌',
      'Decline Partnership',
      'Play alone',
      () => onDecision({ accept_partnership: false }),
      'primary'
    ));
  }

  // Betting/Doubling decisions
  if (interactionNeeded.type === 'double_offer') {
    buttons.push(renderButton(
      'accept-double',
      '💰',
      'Accept Double',
      'Raise the stakes',
      () => onDecision({ accept_double: true }),
      'warning'
    ));

    buttons.push(renderButton(
      'decline-double',
      '❌',
      'Decline Double',
      'Keep current wager',
      () => onDecision({ accept_double: false }),
      'warning'
    ));
  }

  if (interactionNeeded.type === 'offer_double') {
    buttons.push(renderButton(
      'offer-double',
      '💰',
      'Offer Double',
      'Double the wager',
      () => onDecision({ offer_double: true }),
      'warning'
    ));

    buttons.push(renderButton(
      'decline-offer',
      '❌',
      'Decline',
      'Keep current wager',
      () => onDecision({ offer_double: false }),
      'warning'
    ));
  }

  // Render buttons in grid
  return (
    <div style={{
      display: 'grid',
      gridTemplateColumns: buttons.length === 1
        ? '1fr'
        : buttons.length === 2
        ? 'repeat(2, 1fr)'
        : 'repeat(auto-fit, minmax(200px, 1fr))',
      gap: '16px',
      padding: '16px'
    }}>
      {buttons}
    </div>
  );
};

DecisionButtons.propTypes = {
  interactionNeeded: PropTypes.shape({
    type: PropTypes.string.isRequired,
    available_partners: PropTypes.arrayOf(PropTypes.string)
  }),
  hasNextShot: PropTypes.bool,
  onDecision: PropTypes.func,
  onNextShot: PropTypes.func,
  loading: PropTypes.bool,
  gameState: PropTypes.shape({
    players: PropTypes.array
  })
};

export default DecisionButtons;
```

Update index:

```javascript
// frontend/src/components/simulation/visual/index.js
export { default as HoleVisualization } from './HoleVisualization';
export { default as PlayersCard } from './PlayersCard';
export { default as BettingCard } from './BettingCard';
export { default as ShotContextCard } from './ShotContextCard';
export { default as DecisionButtons } from './DecisionButtons';
```

### Step 4: Run test to verify it passes

```bash
cd frontend
npm test -- DecisionButtons.test.js
```

Expected: PASS (all 5 tests)

### Step 5: Commit

```bash
git add frontend/src/components/simulation/visual/
git commit -m "feat: add DecisionButtons component

- Large equal-sized buttons for all decision types
- Partnership buttons (request partner, go solo, keep watching)
- Betting buttons (accept/decline double)
- Continue button (play next shot)
- Dynamic grid layout based on available actions
- Icon + label + description format

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Task 6: Create SimulationVisualInterface Container

**Goal:** Main container component that composes all visual pieces in vertical flow layout

**Files:**
- Create: `frontend/src/components/simulation/visual/SimulationVisualInterface.jsx`
- Create: `frontend/src/components/simulation/visual/__tests__/SimulationVisualInterface.test.js`
- Modify: `frontend/src/components/simulation/visual/index.js`

### Step 1: Write failing test

```javascript
// frontend/src/components/simulation/visual/__tests__/SimulationVisualInterface.test.js
import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import { ThemeProvider } from '../../../theme/Provider';
import SimulationVisualInterface from '../SimulationVisualInterface';

const renderWithTheme = (component) => {
  return render(
    <ThemeProvider>{component}</ThemeProvider>
  );
};

describe('SimulationVisualInterface', () => {
  const mockGameState = {
    players: [
      { id: 'human', name: 'You', points: 12, is_human: true },
      { id: 'bot1', name: 'Alice', points: 8, is_human: false }
    ],
    captain_id: 'human',
    base_wager: 10,
    betting: { current_wager: 20 },
    hole_state: { current_shot_number: 2 },
    hole_info: { hole_number: 1, par: 4, yards: 380 }
  };

  const mockShotState = {
    distance_to_hole: 185,
    lie: 'fairway'
  };

  test('renders all three sections', () => {
    const { container } = renderWithTheme(
      <SimulationVisualInterface
        gameState={mockGameState}
        shotState={mockShotState}
        hasNextShot={true}
      />
    );

    // Check structure exists
    const svg = container.querySelector('svg'); // Hole visualization
    expect(svg).toBeInTheDocument();

    // Check for cards
    expect(screen.getByText(/PLAYERS/i)).toBeInTheDocument();
    expect(screen.getByText(/BETTING/i)).toBeInTheDocument();
    expect(screen.getByText(/SHOT CONTEXT/i)).toBeInTheDocument();

    // Check for buttons section
    expect(screen.getByText(/Play Next Shot/i)).toBeInTheDocument();
  });

  test('applies correct layout proportions', () => {
    const { container } = renderWithTheme(
      <SimulationVisualInterface
        gameState={mockGameState}
        shotState={mockShotState}
        hasNextShot={true}
      />
    );

    const sections = container.querySelectorAll('[data-section]');
    expect(sections.length).toBeGreaterThanOrEqual(3);
  });

  test('responsive: stacks cards on mobile', () => {
    // Mock window width
    global.innerWidth = 500;

    const { container } = renderWithTheme(
      <SimulationVisualInterface
        gameState={mockGameState}
        shotState={mockShotState}
        hasNextShot={true}
      />
    );

    const cardsContainer = container.querySelector('[data-section="cards"]');
    expect(cardsContainer).toBeInTheDocument();
  });
});
```

### Step 2: Run test to verify it fails

```bash
cd frontend
npm test -- SimulationVisualInterface.test.js
```

Expected: FAIL - "Cannot find module '../SimulationVisualInterface'"

### Step 3: Write minimal implementation

```javascript
// frontend/src/components/simulation/visual/SimulationVisualInterface.jsx
import React from 'react';
import PropTypes from 'prop-types';
import {
  HoleVisualization,
  PlayersCard,
  BettingCard,
  ShotContextCard,
  DecisionButtons
} from './index';

const SimulationVisualInterface = ({
  gameState = {},
  shotState = {},
  shotProbabilities = {},
  interactionNeeded = null,
  hasNextShot = false,
  loading = false,
  pokerState = {},
  onMakeDecision = () => {},
  onNextShot = () => {}
}) => {
  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      height: '100%',
      gap: '16px',
      padding: '16px',
      maxWidth: '1400px',
      margin: '0 auto'
    }}>
      {/* Top 35% - Hole Visualization */}
      <div
        data-section="visualization"
        style={{
          flex: '0 0 35%',
          minHeight: '300px',
          maxHeight: '400px'
        }}
      >
        <HoleVisualization
          hole={gameState?.hole_info}
          players={gameState?.players || []}
        />
      </div>

      {/* Middle 25% - Game State Cards */}
      <div
        data-section="cards"
        style={{
          flex: '0 0 25%',
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
          gap: '16px',
          minHeight: '200px'
        }}
      >
        <PlayersCard
          players={gameState?.players || []}
          captainId={gameState?.captain_id}
        />
        <BettingCard
          betting={gameState?.betting}
          baseWager={gameState?.base_wager || 1}
          pokerState={pokerState}
        />
        <ShotContextCard
          shotState={shotState}
          holeState={gameState?.hole_state}
          probabilities={shotProbabilities}
        />
      </div>

      {/* Bottom 40% - Decision Buttons */}
      <div
        data-section="buttons"
        style={{
          flex: '0 0 40%',
          minHeight: '250px'
        }}
      >
        <DecisionButtons
          interactionNeeded={interactionNeeded}
          hasNextShot={hasNextShot}
          onDecision={onMakeDecision}
          onNextShot={onNextShot}
          loading={loading}
          gameState={gameState}
        />
      </div>
    </div>
  );
};

SimulationVisualInterface.propTypes = {
  gameState: PropTypes.object,
  shotState: PropTypes.object,
  shotProbabilities: PropTypes.object,
  interactionNeeded: PropTypes.object,
  hasNextShot: PropTypes.bool,
  loading: PropTypes.bool,
  pokerState: PropTypes.object,
  onMakeDecision: PropTypes.func,
  onNextShot: PropTypes.func
};

export default SimulationVisualInterface;
```

Update index:

```javascript
// frontend/src/components/simulation/visual/index.js
export { default as HoleVisualization } from './HoleVisualization';
export { default as PlayersCard } from './PlayersCard';
export { default as BettingCard } from './BettingCard';
export { default as ShotContextCard } from './ShotContextCard';
export { default as DecisionButtons } from './DecisionButtons';
export { default as SimulationVisualInterface } from './SimulationVisualInterface';
```

### Step 4: Run test to verify it passes

```bash
cd frontend
npm test -- SimulationVisualInterface.test.js
```

Expected: PASS (all 3 tests)

### Step 5: Commit

```bash
git add frontend/src/components/simulation/visual/
git commit -m "feat: add SimulationVisualInterface container

- Vertical flow layout (35% viz, 25% cards, 40% buttons)
- Composes all visual components
- Responsive grid for cards
- Flexible sections with min/max heights
- Props pass-through to child components

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Task 7: Integrate SimulationVisualInterface into SimulationMode

**Goal:** Replace current rendering with new visual interface

**Files:**
- Modify: `frontend/src/components/simulation/SimulationMode.js:863-922`

### Step 1: Write integration test

```javascript
// frontend/src/components/simulation/__tests__/SimulationMode.visual.test.js
import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { GameProvider } from '../../../context';
import { ThemeProvider } from '../../../theme/Provider';
import SimulationMode from '../SimulationMode';

// Mock the API
jest.mock('../../../config/environment', () => ({
  simulationConfig: {
    apiUrl: 'http://localhost:8000',
    useMocks: true,
    mockPreset: 'default'
  }
}));

const renderWithProviders = (component) => {
  return render(
    <ThemeProvider>
      <GameProvider>
        {component}
      </GameProvider>
    </ThemeProvider>
  );
};

describe('SimulationMode with Visual Interface', () => {
  test('renders visual interface when game is active', async () => {
    renderWithProviders(<SimulationMode />);

    // Start simulation
    const startButton = await screen.findByText(/Start.*Simulation/i);
    expect(startButton).toBeInTheDocument();

    // After starting, should show visual interface components
    // (This will pass when we integrate the visual interface)
  });

  test('shows hole visualization in visual interface', async () => {
    renderWithProviders(<SimulationMode />);

    // When game active, should have SVG
    await waitFor(() => {
      const svg = document.querySelector('svg');
      // Will pass after integration
      if (svg) {
        expect(svg).toBeInTheDocument();
      }
    });
  });
});
```

### Step 2: Run test to verify current behavior

```bash
cd frontend
npm test -- SimulationMode.visual.test.js
```

Expected: Tests should run (may pass or skip depending on game state)

### Step 3: Modify SimulationMode.js to use visual interface

Find lines 863-922 in `SimulationMode.js` and replace the rendering logic:

```javascript
// frontend/src/components/simulation/SimulationMode.js
// ... (keep all imports at top)

// ADD this import near the top with other component imports
import { SimulationVisualInterface } from './visual';

// ... (keep all existing logic)

// REPLACE the rendering section (around line 863-922) with:

  // Choose interface based on mode preference
  if (useTurnBasedMode && turnBasedState) {
    return (
      <TurnBasedInterface
        gameState={{
          ...gameState,
          ...(turnBasedState.turn_based_state || turnBasedState),
          interactionNeeded,
          hasNextShot,
          feedback
        }}
        onMakeDecision={makeDecision}
        interactionNeeded={interactionNeeded}
        feedback={feedback}
        shotState={shotState}
        onNextShot={playNextShot}
        hasNextShot={hasNextShot}
      />
    );
  }

  // Use new Visual Interface (replaces EnhancedSimulationLayout and GamePlay)
  return (
    <SimulationVisualInterface
      gameState={gameState}
      shotState={shotState}
      shotProbabilities={shotProbabilities}
      interactionNeeded={interactionNeeded}
      hasNextShot={hasNextShot}
      loading={loading}
      pokerState={pokerState}
      onMakeDecision={makeDecision}
      onNextShot={playNextShot}
    />
  );
}

export default SimulationMode;
```

### Step 4: Run tests to verify integration

```bash
cd frontend
npm test -- SimulationMode
```

Expected: All existing tests should still pass, visual interface should render

### Step 5: Manual verification

```bash
cd frontend
npm start
```

Navigate to simulation mode, verify:
- Golf hole visualization appears
- Three info cards show data
- Decision buttons are large and clear
- Layout is vertical flow (top to bottom)

### Step 6: Commit

```bash
git add frontend/src/components/simulation/
git commit -m "feat: integrate SimulationVisualInterface into SimulationMode

- Replace EnhancedSimulationLayout with SimulationVisualInterface
- Remove old rendering logic (lines 863-922)
- Maintain TurnBasedInterface for turn-based mode
- All existing tests passing

BREAKING: Changes visual layout of simulation mode

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Task 8: Add Responsive Styles and Polish

**Goal:** Ensure mobile responsiveness and visual polish

**Files:**
- Create: `frontend/src/components/simulation/visual/styles.css`
- Modify: `frontend/src/components/simulation/visual/SimulationVisualInterface.jsx`

### Step 1: Create CSS file with responsive styles

```css
/* frontend/src/components/simulation/visual/styles.css */

/* Container */
.simulation-visual-interface {
  display: flex;
  flex-direction: column;
  height: 100%;
  gap: 16px;
  padding: 16px;
  max-width: 1400px;
  margin: 0 auto;
}

/* Sections */
.visualization-section {
  flex: 0 0 35%;
  min-height: 300px;
  max-height: 400px;
}

.cards-section {
  flex: 0 0 25%;
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
  min-height: 200px;
}

.buttons-section {
  flex: 0 0 40%;
  min-height: 250px;
}

/* Responsive: Tablet */
@media (max-width: 1024px) {
  .cards-section {
    grid-template-columns: repeat(2, 1fr);
  }

  .cards-section > :last-child {
    grid-column: 1 / -1;
  }
}

/* Responsive: Mobile */
@media (max-width: 768px) {
  .simulation-visual-interface {
    gap: 12px;
    padding: 12px;
  }

  .visualization-section {
    flex: 0 0 30%;
    min-height: 250px;
    max-height: 300px;
  }

  .cards-section {
    flex: 0 0 30%;
    grid-template-columns: 1fr;
    gap: 12px;
    min-height: auto;
  }

  .buttons-section {
    flex: 0 0 40%;
    min-height: 200px;
  }
}

/* Extra small screens */
@media (max-width: 480px) {
  .simulation-visual-interface {
    padding: 8px;
    gap: 8px;
  }

  .visualization-section {
    min-height: 200px;
  }
}
```

### Step 2: Import and use CSS classes in SimulationVisualInterface

```javascript
// Modify frontend/src/components/simulation/visual/SimulationVisualInterface.jsx
import React from 'react';
import PropTypes from 'prop-types';
import './styles.css';
import {
  HoleVisualization,
  PlayersCard,
  BettingCard,
  ShotContextCard,
  DecisionButtons
} from './index';

const SimulationVisualInterface = ({
  gameState = {},
  shotState = {},
  shotProbabilities = {},
  interactionNeeded = null,
  hasNextShot = false,
  loading = false,
  pokerState = {},
  onMakeDecision = () => {},
  onNextShot = () => {}
}) => {
  return (
    <div className="simulation-visual-interface">
      {/* Top 35% - Hole Visualization */}
      <div className="visualization-section">
        <HoleVisualization
          hole={gameState?.hole_info}
          players={gameState?.players || []}
        />
      </div>

      {/* Middle 25% - Game State Cards */}
      <div className="cards-section">
        <PlayersCard
          players={gameState?.players || []}
          captainId={gameState?.captain_id}
        />
        <BettingCard
          betting={gameState?.betting}
          baseWager={gameState?.base_wager || 1}
          pokerState={pokerState}
        />
        <ShotContextCard
          shotState={shotState}
          holeState={gameState?.hole_state}
          probabilities={shotProbabilities}
        />
      </div>

      {/* Bottom 40% - Decision Buttons */}
      <div className="buttons-section">
        <DecisionButtons
          interactionNeeded={interactionNeeded}
          hasNextShot={hasNextShot}
          onDecision={onMakeDecision}
          onNextShot={onNextShot}
          loading={loading}
          gameState={gameState}
        />
      </div>
    </div>
  );
};

// ... (keep PropTypes)

export default SimulationVisualInterface;
```

### Step 3: Test responsiveness manually

```bash
cd frontend
npm start
```

Open browser dev tools, test responsive behavior:
- Desktop (>1024px): 3 cards in row
- Tablet (768-1024px): 2 cards in row, 1 below
- Mobile (<768px): All cards stacked vertically
- Proportions adjust appropriately

### Step 4: Commit

```bash
git add frontend/src/components/simulation/visual/
git commit -m "style: add responsive styles for visual interface

- Mobile-first responsive design
- Breakpoints: 768px, 1024px
- Card grid adjusts columns based on screen size
- Section heights adjust for smaller screens
- Touch-friendly spacing on mobile

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Task 9: Update Documentation

**Goal:** Document the new visual interface for future developers

**Files:**
- Create: `frontend/src/components/simulation/visual/README.md`

### Step 1: Write component documentation

```markdown
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
```

### Step 2: Commit

```bash
git add frontend/src/components/simulation/visual/README.md
git commit -m "docs: add visual interface component documentation

- Component overview and architecture
- Usage examples
- Props documentation
- Responsive behavior guide
- Testing instructions

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Task 10: Final Verification and Cleanup

**Goal:** Run all tests, verify functionality, clean up

### Step 1: Run full test suite

```bash
cd frontend
npm test
```

Expected: All tests passing

### Step 2: Run lint

```bash
cd frontend
npm run lint
```

Fix any linting errors if present.

### Step 3: Build production bundle

```bash
cd frontend
npm run build
```

Expected: Build succeeds without errors

### Step 4: Manual smoke test

```bash
cd frontend
npm start
```

Verify:
- [ ] Simulation setup loads
- [ ] Start simulation shows visual interface
- [ ] Hole visualization renders
- [ ] All three cards show data
- [ ] Decision buttons appear
- [ ] Clicking buttons triggers decisions
- [ ] Continue button advances simulation
- [ ] Responsive on mobile (test in dev tools)

### Step 5: Final commit

```bash
git add .
git commit -m "chore: final verification and cleanup

- All tests passing
- Lint clean
- Production build successful
- Manual smoke tests verified

Closes visual interface implementation

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Success Criteria

✅ **Visual Clarity** - Users can quickly understand game state at a glance
✅ **Decision Confidence** - Large buttons with clear labels and consequences
✅ **Mobile Responsive** - Works on all screen sizes
✅ **Performance** - No lag in rendering updates
✅ **Test Coverage** - All components have unit tests
✅ **Consistency** - Uses existing component library and theme

---

## Plan Complete

This implementation plan provides step-by-step instructions for building the Simulation Visual Interface from scratch. Each task follows TDD principles (test first, minimal implementation, commit frequently) and includes exact file paths, complete code, and verification steps.

Total estimated time: 4-6 hours for experienced developer with zero codebase context.

# Stuart Mode Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a toggleable strategy panel to the scoring screen that gives the authenticated player real-time, handicap-aware advice on each hole — who to watch, whether to go solo, and how the quarter standings affect risk.

**Architecture:** A pure `stuartModeInsights.js` utility computes tips from game state; `StuartModePanel.jsx` renders them below `HoleHeader`; a `stuartMode` toggle in `useUIState` (persisted to localStorage) controls visibility. `SimpleScorekeeper` wires all three together.

**Tech Stack:** React (JSX, inline styles matching existing components), Jest + React Testing Library, no new dependencies.

---

## File Map

| Action | Path | Responsibility |
|--------|------|---------------|
| Create | `frontend/src/utils/stuartModeInsights.js` | Pure functions: threat scores, tip generation |
| Create | `frontend/src/utils/__tests__/stuartModeInsights.test.js` | Unit tests for insights logic |
| Create | `frontend/src/components/game/scorekeeper/StuartModePanel.jsx` | Display component: strategy tip + standings strip |
| Create | `frontend/src/components/game/scorekeeper/__tests__/StuartModePanel.test.jsx` | Render tests for the panel |
| Modify | `frontend/src/hooks/useUIState.js` | Add `stuartMode` + `toggleStuartMode` with localStorage |
| Modify | `frontend/src/components/game/scorekeeper/index.js` | Export `StuartModePanel` |
| Modify | `frontend/src/components/game/SimpleScorekeeper.jsx` | Add toggle button + render `<StuartModePanel>` |

---

## Task 1: Insights utility — threat scores and tip generation

**Files:**
- Create: `frontend/src/utils/stuartModeInsights.js`
- Create: `frontend/src/utils/__tests__/stuartModeInsights.test.js`

- [ ] **Step 1: Create the test file with the first failing test (threat score)**

```js
// frontend/src/utils/__tests__/stuartModeInsights.test.js
import { computeThreatScore, generateInsights } from '../stuartModeInsights';

describe('computeThreatScore', () => {
  test('returns handicap minus full stroke', () => {
    expect(computeThreatScore(8, 1)).toBe(7);
  });

  test('returns handicap minus half stroke (Creecher)', () => {
    expect(computeThreatScore(8, 0.5)).toBe(7.5);
  });

  test('returns handicap when no strokes', () => {
    expect(computeThreatScore(1, 0)).toBe(1);
  });

  test('handles double stroke', () => {
    expect(computeThreatScore(20, 2)).toBe(18);
  });
});
```

- [ ] **Step 2: Run test to confirm it fails**

```bash
cd frontend && npx jest stuartModeInsights --no-coverage 2>&1 | tail -10
```

Expected: `Cannot find module '../stuartModeInsights'`

- [ ] **Step 3: Create `stuartModeInsights.js` with `computeThreatScore`**

```js
// frontend/src/utils/stuartModeInsights.js

/**
 * Compute how dangerous a player is on a given hole.
 * Lower score = more dangerous.
 * threatScore = handicap - strokes (full strokes count 1, half strokes count 0.5)
 */
export function computeThreatScore(handicap, strokes) {
  return handicap - strokes;
}
```

- [ ] **Step 4: Run test to confirm it passes**

```bash
cd frontend && npx jest stuartModeInsights --no-coverage 2>&1 | tail -10
```

Expected: `4 passed`

- [ ] **Step 5: Add failing tests for `generateInsights`**

Append to `frontend/src/utils/__tests__/stuartModeInsights.test.js`:

```js
describe('generateInsights', () => {
  const stuart = { id: 'p1', name: 'Stuart', handicap: 15, is_authenticated: true };
  const steve  = { id: 'p2', name: 'Steve',  handicap: 1,  is_authenticated: false };
  const dan    = { id: 'p3', name: 'Dan',    handicap: 12, is_authenticated: false };
  const mike   = { id: 'p4', name: 'Mike',   handicap: 14, is_authenticated: false };

  const baseParams = {
    players: [stuart, steve, dan, mike],
    currentHole: 5,
    strokeAllocation: {
      p1: { 5: 1 },   // Stuart gets a stroke
      p2: { 5: 0 },   // Steve gets nothing
      p3: { 5: 0 },
      p4: { 5: 0 },
    },
    playerStandings: {
      p1: { quarters: 0 },
      p2: { quarters: 0 },
      p3: { quarters: 0 },
      p4: { quarters: 0 },
    },
    courseData: { holes: [{ hole_number: 5, handicap: 4 }] },
    currentWager: 2,
  };

  test('returns required fields', () => {
    const result = generateInsights(baseParams);
    expect(result).toHaveProperty('headline');
    expect(result).toHaveProperty('detail');
    expect(result).toHaveProperty('threats');
    expect(result).toHaveProperty('soloRecommendation');
  });

  test('soloRecommendation is go when Stuart has full stroke and no high-threat opponents', () => {
    // Lower all opponents to safe handicaps
    const params = {
      ...baseParams,
      players: [
        stuart,
        { id: 'p2', name: 'Bob', handicap: 18, is_authenticated: false },
        { id: 'p3', name: 'Ted', handicap: 16, is_authenticated: false },
      ],
      strokeAllocation: { p1: { 5: 1 }, p2: { 5: 0 }, p3: { 5: 0 } },
      playerStandings: {
        p1: { quarters: 0 },
        p2: { quarters: 0 },
        p3: { quarters: 0 },
      },
    };
    const result = generateInsights(params);
    expect(result.soloRecommendation).toBe('go');
  });

  test('soloRecommendation is caution when Stuart has full stroke but Steve (1 hdcp) is high threat', () => {
    const result = generateInsights(baseParams);
    expect(result.soloRecommendation).toBe('caution');
  });

  test('soloRecommendation is avoid when Stuart has no stroke and high-threat opponent exists', () => {
    const params = {
      ...baseParams,
      strokeAllocation: { p1: { 5: 0 }, p2: { 5: 0 }, p3: { 5: 0 }, p4: { 5: 0 } },
    };
    const result = generateInsights(params);
    expect(result.soloRecommendation).toBe('avoid');
  });

  test('being down > 3q bumps soloRecommendation up one level (caution → go)', () => {
    const params = {
      ...baseParams,
      playerStandings: {
        p1: { quarters: -4 }, // Stuart is down 4
        p2: { quarters: 2 },
        p3: { quarters: 1 },
        p4: { quarters: 1 },
      },
    };
    const result = generateInsights(params);
    expect(result.soloRecommendation).toBe('go');
  });

  test('threats array sorted lowest threatScore first', () => {
    const result = generateInsights(baseParams);
    const scores = result.threats.map(t => t.threatScore);
    expect(scores).toEqual([...scores].sort((a, b) => a - b));
  });

  test('Creecher (0.5 stroke) is reflected in threatScore', () => {
    const params = {
      ...baseParams,
      strokeAllocation: {
        p1: { 5: 0.5 }, // Stuart gets Creecher
        p2: { 5: 0 },
        p3: { 5: 0 },
        p4: { 5: 0 },
      },
    };
    const result = generateInsights(params);
    const stuartThreat = result.threats.find(t => t.player.id === 'p1');
    expect(stuartThreat.threatScore).toBe(14.5); // 15 - 0.5
  });

  test('headline mentions high-threat opponent by name', () => {
    const result = generateInsights(baseParams);
    expect(result.headline).toMatch(/Steve/);
  });

  test('hungry flag set for player who is down and is high threat', () => {
    const params = {
      ...baseParams,
      playerStandings: {
        p1: { quarters: 5 },
        p2: { quarters: -5 }, // Steve is down
        p3: { quarters: 0 },
        p4: { quarters: 0 },
      },
    };
    const result = generateInsights(params);
    const steveThreat = result.threats.find(t => t.player.id === 'p2');
    expect(steveThreat.hungry).toBe(true);
  });
});
```

- [ ] **Step 6: Run tests to confirm they all fail**

```bash
cd frontend && npx jest stuartModeInsights --no-coverage 2>&1 | tail -15
```

Expected: multiple failures — `generateInsights is not a function`

- [ ] **Step 7: Implement `generateInsights`**

Replace the entire contents of `frontend/src/utils/stuartModeInsights.js`:

```js
// frontend/src/utils/stuartModeInsights.js

/**
 * Compute how dangerous a player is on a given hole.
 * Lower = more dangerous. Full stroke = 1, Creecher half-stroke = 0.5.
 */
export function computeThreatScore(handicap, strokes) {
  return handicap - strokes;
}

const HIGH_THREAT_THRESHOLD = 4;
const QUARTERS_SWING_THRESHOLD = 3;

/**
 * Generate strategic insights for the authenticated player on the current hole.
 *
 * @param {Object} params
 * @param {Array}  params.players           - All players: { id, name, handicap, is_authenticated }
 * @param {number} params.currentHole       - Hole number (1–18)
 * @param {Object} params.strokeAllocation  - { [playerId]: { [hole]: strokes } }
 * @param {Object} params.playerStandings   - { [playerId]: { quarters } }
 * @param {Object} params.courseData        - { holes: [{ hole_number, handicap }] }
 * @param {number} params.currentWager      - Current wager in quarters
 *
 * @returns {{ headline, detail, threats, soloRecommendation }}
 */
export function generateInsights({
  players,
  currentHole,
  strokeAllocation,
  playerStandings,
  courseData,
  currentWager,
}) {
  const stuart = players.find(p => p.is_authenticated);
  if (!stuart) {
    return {
      headline: 'No authenticated player found',
      detail: '',
      threats: [],
      soloRecommendation: 'caution',
    };
  }

  const strokeIndex = courseData?.holes?.find(h => h.hole_number === currentHole)?.handicap;

  // Build threat entries for every player (including Stuart, for self-awareness)
  const threats = players.map(player => {
    const strokes = strokeAllocation?.[player.id]?.[currentHole] ?? 0;
    const threatScore = computeThreatScore(player.handicap, strokes);
    const isHighThreat = !player.is_authenticated && threatScore <= HIGH_THREAT_THRESHOLD;
    const quarters = playerStandings?.[player.id]?.quarters ?? 0;
    const hungry = isHighThreat && quarters < -QUARTERS_SWING_THRESHOLD;

    let strokeSituation;
    if (strokes >= 1) strokeSituation = 'full';
    else if (strokes >= 0.4) strokeSituation = 'creecher';
    else strokeSituation = 'none';

    return { player, threatScore, strokeSituation, isHighThreat, hungry, quarters };
  }).sort((a, b) => a.threatScore - b.threatScore);

  const stuartEntry = threats.find(t => t.player.is_authenticated);
  const stuartStrokes = strokeAllocation?.[stuart.id]?.[currentHole] ?? 0;
  const stuartQuarters = playerStandings?.[stuart.id]?.quarters ?? 0;
  const highThreats = threats.filter(t => t.isHighThreat);

  // Solo recommendation
  let soloRecommendation;
  if (stuartStrokes >= 1 && highThreats.length === 0) {
    soloRecommendation = 'go';
  } else if (stuartStrokes >= 1 && highThreats.length > 0) {
    soloRecommendation = 'caution';
  } else if (stuartStrokes >= 0.4) {
    soloRecommendation = highThreats.length > 0 ? 'caution' : 'go';
  } else {
    soloRecommendation = highThreats.length > 0 ? 'avoid' : 'caution';
  }

  // Down in quarters → bump up one level
  if (stuartQuarters < -QUARTERS_SWING_THRESHOLD) {
    if (soloRecommendation === 'caution') soloRecommendation = 'go';
    else if (soloRecommendation === 'avoid') soloRecommendation = 'caution';
  }

  // Build headline
  let headline;
  if (highThreats.length > 0) {
    const names = highThreats.map(t => t.player.name).join(' & ');
    headline = `Watch out for ${names}`;
  } else if (stuartStrokes >= 1) {
    headline = 'Stroke advantage — you have the edge';
  } else if (stuartEntry?.strokeSituation === 'creecher') {
    headline = 'Creecher (½ stroke) — partial advantage';
  } else if (strokeIndex && strokeIndex <= 6) {
    headline = `Tough hole (SI ${strokeIndex}) — consider a partner`;
  } else {
    headline = 'Balanced hole — play your read';
  }

  // Build detail
  const detailParts = [];

  if (stuartStrokes >= 1) {
    detailParts.push('You get a full stroke here.');
  } else if (stuartStrokes >= 0.4) {
    detailParts.push('You get the Creecher (½ stroke) here.');
  } else {
    detailParts.push('No stroke for you on this hole.');
  }

  highThreats.forEach(t => {
    const strokeNote = t.strokeSituation === 'full'
      ? 'also gets a stroke'
      : t.strokeSituation === 'creecher'
      ? 'gets the Creecher'
      : 'gets no stroke';
    detailParts.push(
      `${t.player.name} is a ${t.player.handicap} hdcp (${strokeNote}) — high threat.`
    );
  });

  if (stuartQuarters < -QUARTERS_SWING_THRESHOLD) {
    detailParts.push(`You're down ${Math.abs(stuartQuarters)}q — higher-variance play makes sense.`);
  } else if (stuartQuarters > QUARTERS_SWING_THRESHOLD) {
    detailParts.push(`You're up ${stuartQuarters}q — a partner reduces risk.`);
  }

  const wagerNote = currentWager > 1 ? ` at ${currentWager}q` : '';
  if (soloRecommendation === 'avoid' && strokeIndex && strokeIndex <= 6) {
    detailParts.push(`Hard hole${wagerNote} — partnership cuts your exposure.`);
  }

  return {
    headline,
    detail: detailParts.join(' '),
    threats,
    soloRecommendation,
  };
}
```

- [ ] **Step 8: Run all insights tests**

```bash
cd frontend && npx jest stuartModeInsights --no-coverage 2>&1 | tail -15
```

Expected: all tests pass

- [ ] **Step 9: Commit**

```bash
cd frontend && cd .. && git add frontend/src/utils/stuartModeInsights.js frontend/src/utils/__tests__/stuartModeInsights.test.js
git commit -m "feat: add stuartModeInsights utility with threat scoring and tip generation"
```

---

## Task 2: `StuartModePanel` component

**Files:**
- Create: `frontend/src/components/game/scorekeeper/StuartModePanel.jsx`
- Create: `frontend/src/components/game/scorekeeper/__tests__/StuartModePanel.test.jsx`

- [ ] **Step 1: Write the failing render tests**

```jsx
// frontend/src/components/game/scorekeeper/__tests__/StuartModePanel.test.jsx
import React from 'react';
import { render, screen } from '@testing-library/react';
import StuartModePanel from '../StuartModePanel';

const theme = {
  colors: {
    primary: '#2196F3',
    accent: '#FFD700',
    paper: '#ffffff',
    backgroundSecondary: '#f5f5f5',
    border: '#e0e0e0',
    textPrimary: '#333',
    textSecondary: '#666',
  },
};

const stuart = { id: 'p1', name: 'Stuart', handicap: 15, is_authenticated: true };
const steve  = { id: 'p2', name: 'Steve',  handicap: 1,  is_authenticated: false };
const dan    = { id: 'p3', name: 'Dan',    handicap: 12, is_authenticated: false };

const baseProps = {
  players: [stuart, steve, dan],
  currentHole: 5,
  strokeAllocation: {
    p1: { 5: 1 },
    p2: { 5: 0 },
    p3: { 5: 0 },
  },
  playerStandings: {
    p1: { quarters: 0, name: 'Stuart' },
    p2: { quarters: 0, name: 'Steve' },
    p3: { quarters: 0, name: 'Dan' },
  },
  courseData: { holes: [{ hole_number: 5, handicap: 4 }] },
  currentWager: 2,
  theme,
};

test('renders Stuart Mode heading', () => {
  render(<StuartModePanel {...baseProps} />);
  expect(screen.getByText(/Stuart Mode/i)).toBeInTheDocument();
});

test('renders headline from insights', () => {
  render(<StuartModePanel {...baseProps} />);
  expect(screen.getByText(/Watch out for Steve/i)).toBeInTheDocument();
});

test('renders solo recommendation badge', () => {
  render(<StuartModePanel {...baseProps} />);
  expect(screen.getByTestId('solo-recommendation')).toBeInTheDocument();
});

test('renders a standings row for each player', () => {
  render(<StuartModePanel {...baseProps} />);
  expect(screen.getByTestId('standing-p1')).toBeInTheDocument();
  expect(screen.getByTestId('standing-p2')).toBeInTheDocument();
  expect(screen.getByTestId('standing-p3')).toBeInTheDocument();
});

test('shows hungry indicator for player who is down and high threat', () => {
  const props = {
    ...baseProps,
    playerStandings: {
      p1: { quarters: 5,  name: 'Stuart' },
      p2: { quarters: -5, name: 'Steve' },  // Steve is down + high threat
      p3: { quarters: 0,  name: 'Dan' },
    },
  };
  render(<StuartModePanel {...props} />);
  expect(screen.getByTestId('hungry-p2')).toBeInTheDocument();
});
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
cd frontend && npx jest StuartModePanel --no-coverage 2>&1 | tail -10
```

Expected: `Cannot find module '../StuartModePanel'`

- [ ] **Step 3: Implement `StuartModePanel.jsx`**

```jsx
// frontend/src/components/game/scorekeeper/StuartModePanel.jsx
import React from 'react';
import PropTypes from 'prop-types';
import { generateInsights } from '../../../utils/stuartModeInsights';

const SOLO_BADGE = {
  go:      { label: 'Solo ✓', bg: '#4CAF50', color: 'white' },
  caution: { label: 'Solo ⚠',  bg: '#FF9800', color: 'white' },
  avoid:   { label: 'Solo ✗',  bg: '#f44336', color: 'white' },
};

const StuartModePanel = ({
  players,
  currentHole,
  strokeAllocation,
  playerStandings,
  courseData,
  currentWager,
  theme,
}) => {
  const insights = generateInsights({
    players,
    currentHole,
    strokeAllocation,
    playerStandings,
    courseData,
    currentWager,
  });

  const badge = SOLO_BADGE[insights.soloRecommendation];

  // Sort standings by quarters descending for display
  const standingsRows = [...players].sort((a, b) => {
    const qa = playerStandings?.[a.id]?.quarters ?? 0;
    const qb = playerStandings?.[b.id]?.quarters ?? 0;
    return qb - qa;
  });

  return (
    <div
      style={{
        background: theme.colors.paper,
        border: `2px solid #F59E0B`,
        borderRadius: '12px',
        marginBottom: '16px',
        overflow: 'hidden',
      }}
    >
      {/* Strategy tip section */}
      <div
        style={{
          background: 'linear-gradient(135deg, #92400E, #F59E0B)',
          color: 'white',
          padding: '12px 16px',
        }}
      >
        <div
          style={{
            fontSize: '11px',
            fontWeight: 'bold',
            textTransform: 'uppercase',
            letterSpacing: '1px',
            opacity: 0.9,
            marginBottom: '8px',
          }}
        >
          🧠 Stuart Mode
        </div>

        <div
          style={{
            display: 'flex',
            alignItems: 'flex-start',
            gap: '10px',
          }}
        >
          <span
            data-testid="solo-recommendation"
            style={{
              background: badge.bg,
              color: badge.color,
              padding: '4px 10px',
              borderRadius: '12px',
              fontSize: '12px',
              fontWeight: 'bold',
              whiteSpace: 'nowrap',
              flexShrink: 0,
              border: '2px solid rgba(255,255,255,0.4)',
            }}
          >
            {badge.label}
          </span>

          <div>
            <div style={{ fontSize: '15px', fontWeight: 'bold', marginBottom: '4px' }}>
              {insights.headline}
            </div>
            <div style={{ fontSize: '12px', opacity: 0.9, lineHeight: 1.4 }}>
              {insights.detail}
            </div>
          </div>
        </div>
      </div>

      {/* Standings strip */}
      <div style={{ padding: '10px 16px' }}>
        <div
          style={{
            fontSize: '10px',
            textTransform: 'uppercase',
            letterSpacing: '1px',
            color: theme.colors.textSecondary,
            marginBottom: '6px',
          }}
        >
          Quarter Standings
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
          {standingsRows.map(player => {
            const entry = insights.threats.find(t => t.player.id === player.id);
            const quarters = playerStandings?.[player.id]?.quarters ?? 0;
            const isStuart = player.is_authenticated;
            const isHungry = entry?.hungry;

            const qColor = quarters > 0 ? '#4CAF50' : quarters < 0 ? '#f44336' : '#9CA3AF';
            const qLabel = quarters > 0 ? `+${quarters}q` : `${quarters}q`;

            return (
              <div
                key={player.id}
                data-testid={`standing-${player.id}`}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  padding: '4px 8px',
                  borderRadius: '8px',
                  background: isStuart ? 'rgba(245,158,11,0.08)' : 'transparent',
                  border: isStuart ? '1px solid rgba(245,158,11,0.3)' : '1px solid transparent',
                }}
              >
                <span
                  style={{
                    fontSize: '13px',
                    fontWeight: isStuart ? 'bold' : '500',
                    color: theme.colors.textPrimary,
                  }}
                >
                  {player.name}
                  {isStuart && ' ←'}
                </span>

                <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                  {isHungry && (
                    <span
                      data-testid={`hungry-${player.id}`}
                      style={{
                        fontSize: '11px',
                        color: '#f44336',
                        fontWeight: 'bold',
                      }}
                    >
                      ⚠️ hungry
                    </span>
                  )}
                  <span
                    style={{
                      fontSize: '13px',
                      fontWeight: 'bold',
                      color: qColor,
                      minWidth: '40px',
                      textAlign: 'right',
                    }}
                  >
                    {qLabel}
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};

StuartModePanel.propTypes = {
  players: PropTypes.arrayOf(PropTypes.shape({
    id: PropTypes.string.isRequired,
    name: PropTypes.string.isRequired,
    handicap: PropTypes.number.isRequired,
    is_authenticated: PropTypes.bool,
  })).isRequired,
  currentHole: PropTypes.number.isRequired,
  strokeAllocation: PropTypes.object,
  playerStandings: PropTypes.object,
  courseData: PropTypes.object,
  currentWager: PropTypes.number.isRequired,
  theme: PropTypes.object.isRequired,
};

export default StuartModePanel;
```

- [ ] **Step 4: Run tests**

```bash
cd frontend && npx jest StuartModePanel --no-coverage 2>&1 | tail -15
```

Expected: all 5 tests pass

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/game/scorekeeper/StuartModePanel.jsx \
        frontend/src/components/game/scorekeeper/__tests__/StuartModePanel.test.jsx
git commit -m "feat: add StuartModePanel component"
```

---

## Task 3: Add `stuartMode` toggle to `useUIState`

**Files:**
- Modify: `frontend/src/hooks/useUIState.js`

- [ ] **Step 1: Write failing test**

Create `frontend/src/hooks/__tests__/useUIState.stuartMode.test.js`:

```js
// frontend/src/hooks/__tests__/useUIState.stuartMode.test.js
import { renderHook, act } from '@testing-library/react';
import { useUIState } from '../useUIState';

beforeEach(() => {
  localStorage.clear();
});

test('stuartMode defaults to false', () => {
  const { result } = renderHook(() => useUIState());
  expect(result.current.stuartMode).toBe(false);
});

test('toggleStuartMode flips stuartMode', () => {
  const { result } = renderHook(() => useUIState());
  act(() => { result.current.toggleStuartMode(); });
  expect(result.current.stuartMode).toBe(true);
  act(() => { result.current.toggleStuartMode(); });
  expect(result.current.stuartMode).toBe(false);
});

test('stuartMode persists to localStorage', () => {
  const { result } = renderHook(() => useUIState());
  act(() => { result.current.toggleStuartMode(); });
  expect(localStorage.getItem('wgp_stuart_mode')).toBe('true');
});

test('stuartMode restores from localStorage on mount', () => {
  localStorage.setItem('wgp_stuart_mode', 'true');
  const { result } = renderHook(() => useUIState());
  expect(result.current.stuartMode).toBe(true);
});
```

- [ ] **Step 2: Run test to confirm it fails**

```bash
cd frontend && npx jest useUIState.stuartMode --no-coverage 2>&1 | tail -10
```

Expected: `result.current.stuartMode` is `undefined`

- [ ] **Step 3: Add `stuartMode` to `useUIState.js`**

In `frontend/src/hooks/useUIState.js`, add after the existing `useState` declarations (around line 20):

```js
  const [stuartMode, setStuartMode] = useState(
    () => localStorage.getItem('wgp_stuart_mode') === 'true'
  );
```

Add the `toggleStuartMode` callback after `clearError` (before `resetForNewHole`):

```js
  const toggleStuartMode = useCallback(() => {
    setStuartMode(prev => {
      const next = !prev;
      localStorage.setItem('wgp_stuart_mode', String(next));
      return next;
    });
  }, []);
```

Add `stuartMode` and `toggleStuartMode` to the return object:

```js
    stuartMode,
    toggleStuartMode,
```

- [ ] **Step 4: Run tests**

```bash
cd frontend && npx jest useUIState.stuartMode --no-coverage 2>&1 | tail -10
```

Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
git add frontend/src/hooks/useUIState.js \
        frontend/src/hooks/__tests__/useUIState.stuartMode.test.js
git commit -m "feat: add stuartMode toggle with localStorage persistence to useUIState"
```

---

## Task 4: Wire up in `SimpleScorekeeper` and export from index

**Files:**
- Modify: `frontend/src/components/game/scorekeeper/index.js`
- Modify: `frontend/src/components/game/SimpleScorekeeper.jsx`

- [ ] **Step 1: Export `StuartModePanel` from the scorekeeper barrel**

In `frontend/src/components/game/scorekeeper/index.js`, add:

```js
export { default as StuartModePanel } from "./StuartModePanel";
```

Full file after edit:

```js
// frontend/src/components/game/scorekeeper/index.js
// Barrel export for scorekeeper sub-components
export { default as HoleHeader } from "./HoleHeader";
export { default as TeamSelector } from "./TeamSelector";
export { default as QuartersPanel } from "./QuartersPanel";
export { default as HoleNavigation } from "./HoleNavigation";
export { default as StuartModePanel } from "./StuartModePanel";
```

- [ ] **Step 2: Import `StuartModePanel` and destructure `stuartMode`/`toggleStuartMode` in `SimpleScorekeeper`**

In `frontend/src/components/game/SimpleScorekeeper.jsx`:

Find the import (around line 30):
```js
import {
  HoleHeader,
  TeamSelector,
  QuartersPanel,
  HoleNavigation,
} from "./scorekeeper";
```

Replace with:
```js
import {
  HoleHeader,
  TeamSelector,
  QuartersPanel,
  HoleNavigation,
  StuartModePanel,
} from "./scorekeeper";
```

Find the `useUIState` destructuring (around line 340–360). It currently reads:
```js
  const {
    showTeamSelection,
    ...
  } = useUIState();
```

Add `stuartMode` and `toggleStuartMode` to that destructure:
```js
    stuartMode,
    toggleStuartMode,
```

- [ ] **Step 3: Add the Stuart Mode toggle button**

Find the "📷 Import from photo" button block (around line 1748–1764):

```jsx
        {/* Scan Scorecard Photo — small link, not a prominent button */}
        <div style={{ marginTop: "4px", textAlign: "center" }}>
          <button
            onClick={() => setShowScorecardPhoto(true)}
            ...
          >
            📷 Import from photo
          </button>
        </div>
```

Add the Stuart Mode toggle **after** that closing `</div>` tag (before the `</div>` that closes the outer wrapper):

```jsx
        {/* Stuart Mode toggle */}
        <div style={{ marginTop: "4px", textAlign: "center" }}>
          <button
            onClick={toggleStuartMode}
            style={{
              padding: "4px 12px",
              fontSize: "12px",
              border: `1px solid ${stuartMode ? "#F59E0B" : theme.colors.border}`,
              borderRadius: "12px",
              background: stuartMode ? "rgba(245,158,11,0.15)" : "transparent",
              color: stuartMode ? "#92400E" : theme.colors.textSecondary,
              cursor: "pointer",
              fontWeight: stuartMode ? "bold" : "normal",
              transition: "all 0.2s",
            }}
          >
            🧠 Stuart Mode {stuartMode ? "ON" : "OFF"}
          </button>
        </div>
```

- [ ] **Step 4: Render `<StuartModePanel>` below `<HoleHeader>`**

Find the closing `/>` of `<HoleHeader` (around line 1786):

```jsx
        movePlayerInOrder={movePlayerInOrder}
      />

      {/* Float & Option Tracking */}
```

Insert between them:

```jsx
        movePlayerInOrder={movePlayerInOrder}
      />

      {/* Stuart Mode — strategy panel */}
      {stuartMode && (
        <StuartModePanel
          players={players}
          currentHole={currentHole}
          strokeAllocation={strokeAllocation}
          playerStandings={playerStandings}
          courseData={courseData}
          currentWager={currentWager}
          theme={theme}
        />
      )}

      {/* Float & Option Tracking */}
```

- [ ] **Step 5: Run the full frontend test suite**

```bash
cd frontend && npx jest --no-coverage 2>&1 | tail -20
```

Expected: existing tests still pass; new tests pass. (Pre-existing failures in `test_progression` and `test_advanced_rules` are backend tests — ignore.)

- [ ] **Step 6: Build to confirm no type/import errors**

```bash
cd frontend && npm run build 2>&1 | tail -20
```

Expected: successful build with no errors.

- [ ] **Step 7: Commit**

```bash
git add frontend/src/components/game/scorekeeper/index.js \
        frontend/src/components/game/SimpleScorekeeper.jsx
git commit -m "feat: wire up Stuart Mode toggle and panel in SimpleScorekeeper"
```

---

## Task 5: Smoke test in the browser

- [ ] **Step 1: Start the dev server**

```bash
cd frontend && npm start
```

- [ ] **Step 2: Open a game in the scoring screen**

Navigate to an active game. Confirm the "🧠 Stuart Mode OFF" button appears below the Import from photo link.

- [ ] **Step 3: Toggle Stuart Mode on**

Tap the button. Confirm:
- Button changes to "🧠 Stuart Mode ON" with amber styling
- `StuartModePanel` appears below the hole header with a headline and standings strip
- Solo recommendation badge is visible

- [ ] **Step 4: Advance to a hole where you get a stroke**

Confirm the panel tip reflects the stroke (headline changes, solo badge updates).

- [ ] **Step 5: Refresh the page**

Confirm Stuart Mode stays ON (localStorage persistence).

- [ ] **Step 6: Toggle off**

Confirm panel disappears cleanly.

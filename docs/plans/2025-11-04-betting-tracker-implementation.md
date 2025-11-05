# Betting Action Tracker Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a real-time betting action tracker integrated into the Game Page that tracks doubles, presses, team formations, and maintains full betting history with client-side state management and batch backend syncing.

**Architecture:** Event-sourced hybrid (event log + state snapshots) with client-side React state, expandable UI panel, and batch POST sync to backend at hole completion or every 5 events.

**Tech Stack:** React (frontend), FastAPI (backend), WebSocket (real-time sync), Material-UI patterns for mobile responsiveness

---

## Task 1: Create Betting Event Types and Constants

**Files:**
- Create: `frontend/src/constants/bettingEvents.js`
- Test: `frontend/src/constants/__tests__/bettingEvents.test.js`

**Step 1: Write the failing test**

```javascript
// frontend/src/constants/__tests__/bettingEvents.test.js
import { BettingEventTypes, createBettingEvent, isValidEventType } from '../bettingEvents';

describe('BettingEventTypes', () => {
  test('should have all required event types', () => {
    expect(BettingEventTypes.DOUBLE_OFFERED).toBe('DOUBLE_OFFERED');
    expect(BettingEventTypes.DOUBLE_ACCEPTED).toBe('DOUBLE_ACCEPTED');
    expect(BettingEventTypes.DOUBLE_DECLINED).toBe('DOUBLE_DECLINED');
    expect(BettingEventTypes.PRESS_OFFERED).toBe('PRESS_OFFERED');
    expect(BettingEventTypes.PRESS_ACCEPTED).toBe('PRESS_ACCEPTED');
    expect(BettingEventTypes.PRESS_DECLINED).toBe('PRESS_DECLINED');
    expect(BettingEventTypes.TEAMS_FORMED).toBe('TEAMS_FORMED');
    expect(BettingEventTypes.HOLE_COMPLETE).toBe('HOLE_COMPLETE');
  });

  test('should create valid betting event', () => {
    const event = createBettingEvent({
      gameId: 'game-123',
      holeNumber: 5,
      eventType: BettingEventTypes.DOUBLE_OFFERED,
      actor: 'Player1',
      data: { currentMultiplier: 2, proposedMultiplier: 4 }
    });

    expect(event.eventId).toBeDefined();
    expect(event.gameId).toBe('game-123');
    expect(event.holeNumber).toBe(5);
    expect(event.eventType).toBe('DOUBLE_OFFERED');
    expect(event.actor).toBe('Player1');
    expect(event.timestamp).toBeDefined();
    expect(event.data.currentMultiplier).toBe(2);
  });

  test('should validate event types', () => {
    expect(isValidEventType('DOUBLE_OFFERED')).toBe(true);
    expect(isValidEventType('INVALID_TYPE')).toBe(false);
  });
});
```

**Step 2: Run test to verify it fails**

Run: `cd frontend && npm test -- bettingEvents.test.js`
Expected: FAIL with "Cannot find module '../bettingEvents'"

**Step 3: Write minimal implementation**

```javascript
// frontend/src/constants/bettingEvents.js
import { v4 as uuidv4 } from 'uuid';

export const BettingEventTypes = {
  DOUBLE_OFFERED: 'DOUBLE_OFFERED',
  DOUBLE_ACCEPTED: 'DOUBLE_ACCEPTED',
  DOUBLE_DECLINED: 'DOUBLE_DECLINED',
  PRESS_OFFERED: 'PRESS_OFFERED',
  PRESS_ACCEPTED: 'PRESS_ACCEPTED',
  PRESS_DECLINED: 'PRESS_DECLINED',
  TEAMS_FORMED: 'TEAMS_FORMED',
  HOLE_COMPLETE: 'HOLE_COMPLETE'
};

export const createBettingEvent = ({ gameId, holeNumber, eventType, actor, data }) => {
  return {
    eventId: uuidv4(),
    gameId,
    holeNumber,
    timestamp: new Date().toISOString(),
    eventType,
    actor,
    data
  };
};

export const isValidEventType = (type) => {
  return Object.values(BettingEventTypes).includes(type);
};
```

**Step 4: Install uuid dependency**

Run: `cd frontend && npm install uuid`
Expected: Package installed successfully

**Step 5: Run test to verify it passes**

Run: `cd frontend && npm test -- bettingEvents.test.js`
Expected: PASS (all tests green)

**Step 6: Commit**

```bash
git add frontend/src/constants/bettingEvents.js frontend/src/constants/__tests__/bettingEvents.test.js package.json package-lock.json
git commit -m "feat: add betting event types and factory function"
```

---

## Task 2: Create Betting State Reducer

**Files:**
- Create: `frontend/src/hooks/useBettingState.js`
- Test: `frontend/src/hooks/__tests__/useBettingState.test.js`

**Step 1: Write the failing test**

```javascript
// frontend/src/hooks/__tests__/useBettingState.test.js
import { renderHook, act } from '@testing-library/react';
import useBettingState from '../useBettingState';
import { BettingEventTypes } from '../../constants/bettingEvents';

describe('useBettingState', () => {
  test('should initialize with default state', () => {
    const { result } = renderHook(() => useBettingState('game-123', 1));

    expect(result.current.state.currentMultiplier).toBe(1);
    expect(result.current.state.baseAmount).toBe(1.00);
    expect(result.current.state.currentBet).toBe(1.00);
    expect(result.current.state.pendingAction).toBeNull();
    expect(result.current.eventHistory.currentHole).toEqual([]);
  });

  test('should handle DOUBLE_OFFERED event', () => {
    const { result } = renderHook(() => useBettingState('game-123', 1));

    act(() => {
      result.current.actions.offerDouble('Player1', 2);
    });

    expect(result.current.state.pendingAction).toEqual({
      type: 'DOUBLE_OFFERED',
      by: 'Player1',
      proposedMultiplier: 2
    });
    expect(result.current.eventHistory.currentHole.length).toBe(1);
    expect(result.current.eventHistory.currentHole[0].eventType).toBe(BettingEventTypes.DOUBLE_OFFERED);
  });

  test('should handle DOUBLE_ACCEPTED event', () => {
    const { result } = renderHook(() => useBettingState('game-123', 1));

    act(() => {
      result.current.actions.offerDouble('Player1', 2);
    });

    act(() => {
      result.current.actions.acceptDouble('Player2');
    });

    expect(result.current.state.currentMultiplier).toBe(2);
    expect(result.current.state.currentBet).toBe(2.00);
    expect(result.current.state.pendingAction).toBeNull();
  });

  test('should handle DOUBLE_DECLINED event', () => {
    const { result } = renderHook(() => useBettingState('game-123', 1));

    act(() => {
      result.current.actions.offerDouble('Player1', 2);
    });

    act(() => {
      result.current.actions.declineDouble('Player2');
    });

    expect(result.current.state.currentMultiplier).toBe(1);
    expect(result.current.state.pendingAction).toBeNull();
  });
});
```

**Step 2: Run test to verify it fails**

Run: `cd frontend && npm test -- useBettingState.test.js`
Expected: FAIL with "Cannot find module '../useBettingState'"

**Step 3: Write minimal implementation**

```javascript
// frontend/src/hooks/useBettingState.js
import { useState, useCallback } from 'react';
import { BettingEventTypes, createBettingEvent } from '../constants/bettingEvents';

const useBettingState = (gameId, holeNumber) => {
  const [state, setState] = useState({
    holeNumber,
    currentMultiplier: 1,
    baseAmount: 1.00,
    currentBet: 1.00,
    teams: [],
    pendingAction: null,
    presses: []
  });

  const [eventHistory, setEventHistory] = useState({
    currentHole: [],
    lastHole: [],
    gameHistory: []
  });

  const addEvent = useCallback((eventType, actor, data) => {
    const event = createBettingEvent({
      gameId,
      holeNumber,
      eventType,
      actor,
      data
    });

    setEventHistory(prev => ({
      ...prev,
      currentHole: [...prev.currentHole, event],
      gameHistory: [...prev.gameHistory, event]
    }));

    return event;
  }, [gameId, holeNumber]);

  const offerDouble = useCallback((playerId, proposedMultiplier) => {
    addEvent(BettingEventTypes.DOUBLE_OFFERED, playerId, {
      currentMultiplier: state.currentMultiplier,
      proposedMultiplier
    });

    setState(prev => ({
      ...prev,
      pendingAction: {
        type: 'DOUBLE_OFFERED',
        by: playerId,
        proposedMultiplier
      }
    }));
  }, [addEvent, state.currentMultiplier]);

  const acceptDouble = useCallback((playerId) => {
    if (!state.pendingAction || state.pendingAction.type !== 'DOUBLE_OFFERED') return;

    const newMultiplier = state.pendingAction.proposedMultiplier;

    addEvent(BettingEventTypes.DOUBLE_ACCEPTED, playerId, {
      previousMultiplier: state.currentMultiplier,
      newMultiplier
    });

    setState(prev => ({
      ...prev,
      currentMultiplier: newMultiplier,
      currentBet: prev.baseAmount * newMultiplier,
      pendingAction: null
    }));
  }, [addEvent, state.pendingAction, state.currentMultiplier]);

  const declineDouble = useCallback((playerId) => {
    if (!state.pendingAction || state.pendingAction.type !== 'DOUBLE_OFFERED') return;

    addEvent(BettingEventTypes.DOUBLE_DECLINED, playerId, {
      declinedMultiplier: state.pendingAction.proposedMultiplier
    });

    setState(prev => ({
      ...prev,
      pendingAction: null
    }));
  }, [addEvent, state.pendingAction]);

  return {
    state,
    eventHistory,
    actions: {
      offerDouble,
      acceptDouble,
      declineDouble
    }
  };
};

export default useBettingState;
```

**Step 4: Run test to verify it passes**

Run: `cd frontend && npm test -- useBettingState.test.js`
Expected: PASS (all tests green)

**Step 5: Commit**

```bash
git add frontend/src/hooks/useBettingState.js frontend/src/hooks/__tests__/useBettingState.test.js
git commit -m "feat: add betting state reducer hook with event sourcing"
```

---

## Task 3: Create BettingTracker Component Shell

**Files:**
- Create: `frontend/src/components/game/BettingTracker.jsx`
- Test: `frontend/src/components/game/__tests__/BettingTracker.test.js`

**Step 1: Write the failing test**

```javascript
// frontend/src/components/game/__tests__/BettingTracker.test.js
import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import BettingTracker from '../BettingTracker';

describe('BettingTracker', () => {
  const mockGameState = {
    id: 'game-123',
    current_hole: 5,
    players: [
      { id: 'p1', name: 'Player1' },
      { id: 'p2', name: 'Player2' }
    ]
  };

  test('should render collapsed by default', () => {
    render(<BettingTracker gameState={mockGameState} />);

    expect(screen.getByText(/Bet:/)).toBeInTheDocument();
    expect(screen.queryByText(/Current Bet Status/)).not.toBeInTheDocument();
  });

  test('should expand when clicked', () => {
    render(<BettingTracker gameState={mockGameState} />);

    const collapseBar = screen.getByText(/Bet:/);
    fireEvent.click(collapseBar);

    expect(screen.getByText(/Current Bet Status/)).toBeInTheDocument();
  });

  test('should show pending action indicator', () => {
    render(<BettingTracker gameState={mockGameState} hasPendingAction={true} />);

    expect(screen.getByTestId('pending-indicator')).toBeInTheDocument();
  });
});
```

**Step 2: Run test to verify it fails**

Run: `cd frontend && npm test -- BettingTracker.test.js`
Expected: FAIL with "Cannot find module '../BettingTracker'"

**Step 3: Write minimal implementation**

```javascript
// frontend/src/components/game/BettingTracker.jsx
import React, { useState } from 'react';
import { useTheme } from '../../theme/Provider';
import useBettingState from '../../hooks/useBettingState';

const BettingTracker = ({ gameState, hasPendingAction = false }) => {
  const theme = useTheme();
  const [isExpanded, setIsExpanded] = useState(false);
  const { state, eventHistory, actions } = useBettingState(
    gameState.id,
    gameState.current_hole
  );

  const collapsedStyle = {
    padding: theme.spacing[3],
    background: theme.colors.paper,
    borderRadius: theme.borderRadius.md,
    cursor: 'pointer',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: theme.spacing[3],
    border: `2px solid ${theme.colors.border}`,
  };

  const expandedContainerStyle = {
    ...collapsedStyle,
    flexDirection: 'column',
    cursor: 'default'
  };

  if (!isExpanded) {
    return (
      <div style={collapsedStyle} onClick={() => setIsExpanded(true)}>
        <span>
          Bet: ${state.currentBet.toFixed(2)} ({state.currentMultiplier}x)
        </span>
        {hasPendingAction && (
          <span
            data-testid="pending-indicator"
            style={{
              background: theme.colors.error,
              color: 'white',
              borderRadius: theme.borderRadius.full,
              padding: `${theme.spacing[1]} ${theme.spacing[2]}`,
              fontSize: theme.typography.xs
            }}
          >
            Action Required
          </span>
        )}
      </div>
    );
  }

  return (
    <div style={expandedContainerStyle}>
      <div
        style={{
          width: '100%',
          display: 'flex',
          justifyContent: 'space-between',
          marginBottom: theme.spacing[3],
          cursor: 'pointer'
        }}
        onClick={() => setIsExpanded(false)}
      >
        <h3 style={{ margin: 0 }}>Current Bet Status</h3>
        <button style={{ ...theme.buttonStyle, padding: theme.spacing[1] }}>
          Collapse
        </button>
      </div>

      <div style={{ width: '100%' }}>
        <p>Multiplier: {state.currentMultiplier}x</p>
        <p>Base Amount: ${state.baseAmount.toFixed(2)}</p>
        <p>Current Bet: ${state.currentBet.toFixed(2)}</p>
      </div>
    </div>
  );
};

export default BettingTracker;
```

**Step 4: Run test to verify it passes**

Run: `cd frontend && npm test -- BettingTracker.test.js`
Expected: PASS (all tests green)

**Step 5: Commit**

```bash
git add frontend/src/components/game/BettingTracker.jsx frontend/src/components/game/__tests__/BettingTracker.test.js
git commit -m "feat: add BettingTracker component shell with expand/collapse"
```

---

## Task 4: Add CurrentBetStatus Subcomponent

**Files:**
- Modify: `frontend/src/components/game/BettingTracker.jsx`
- Create: `frontend/src/components/game/CurrentBetStatus.jsx`
- Test: `frontend/src/components/game/__tests__/CurrentBetStatus.test.js`

**Step 1: Write the failing test**

```javascript
// frontend/src/components/game/__tests__/CurrentBetStatus.test.js
import React from 'react';
import { render, screen } from '@testing-library/react';
import CurrentBetStatus from '../CurrentBetStatus';

describe('CurrentBetStatus', () => {
  const mockState = {
    currentMultiplier: 4,
    baseAmount: 1.00,
    currentBet: 4.00,
    teams: [
      { players: ['Player1', 'Player2'], betAmount: 4.00, score: 0 },
      { players: ['Player3', 'Player4'], betAmount: 4.00, score: 0 }
    ]
  };

  test('should display current multiplier', () => {
    render(<CurrentBetStatus state={mockState} />);
    expect(screen.getByText(/4x/)).toBeInTheDocument();
  });

  test('should display base amount', () => {
    render(<CurrentBetStatus state={mockState} />);
    expect(screen.getByText(/\$1\.00/)).toBeInTheDocument();
  });

  test('should display total bet', () => {
    render(<CurrentBetStatus state={mockState} />);
    expect(screen.getByText(/\$4\.00/)).toBeInTheDocument();
  });

  test('should display team compositions', () => {
    render(<CurrentBetStatus state={mockState} />);
    expect(screen.getByText(/Player1/)).toBeInTheDocument();
    expect(screen.getByText(/Player2/)).toBeInTheDocument();
    expect(screen.getByText(/Player3/)).toBeInTheDocument();
    expect(screen.getByText(/Player4/)).toBeInTheDocument();
  });
});
```

**Step 2: Run test to verify it fails**

Run: `cd frontend && npm test -- CurrentBetStatus.test.js`
Expected: FAIL with "Cannot find module '../CurrentBetStatus'"

**Step 3: Write minimal implementation**

```javascript
// frontend/src/components/game/CurrentBetStatus.jsx
import React from 'react';
import { useTheme } from '../../theme/Provider';

const CurrentBetStatus = ({ state }) => {
  const theme = useTheme();

  const containerStyle = {
    background: '#f0f7ff',
    padding: theme.spacing[4],
    borderRadius: theme.borderRadius.md,
    marginBottom: theme.spacing[3]
  };

  const multiplierBadgeStyle = {
    display: 'inline-block',
    background: theme.colors.primary,
    color: 'white',
    padding: `${theme.spacing[2]} ${theme.spacing[3]}`,
    borderRadius: theme.borderRadius.full,
    fontSize: theme.typography.xl,
    fontWeight: theme.typography.bold,
    marginRight: theme.spacing[2]
  };

  const teamContainerStyle = {
    display: 'grid',
    gridTemplateColumns: 'repeat(2, 1fr)',
    gap: theme.spacing[3],
    marginTop: theme.spacing[3]
  };

  const teamCardStyle = {
    background: 'white',
    padding: theme.spacing[3],
    borderRadius: theme.borderRadius.md,
    border: `2px solid ${theme.colors.border}`
  };

  return (
    <div style={containerStyle}>
      <div style={{ marginBottom: theme.spacing[3] }}>
        <span style={multiplierBadgeStyle}>{state.currentMultiplier}x</span>
        <span style={{ fontSize: theme.typography.lg }}>
          Base: ${state.baseAmount.toFixed(2)} = Total: ${state.currentBet.toFixed(2)}
        </span>
      </div>

      {state.teams && state.teams.length > 0 && (
        <div style={teamContainerStyle}>
          {state.teams.map((team, idx) => (
            <div key={idx} style={teamCardStyle}>
              <div style={{ fontWeight: theme.typography.bold, marginBottom: theme.spacing[2] }}>
                Team {idx + 1}
              </div>
              <div>
                {team.players.map((player, pIdx) => (
                  <div key={pIdx}>{player}</div>
                ))}
              </div>
              <div style={{ marginTop: theme.spacing[2], fontSize: theme.typography.sm, color: theme.colors.textSecondary }}>
                Bet: ${team.betAmount.toFixed(2)}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default CurrentBetStatus;
```

**Step 4: Update BettingTracker to use CurrentBetStatus**

```javascript
// frontend/src/components/game/BettingTracker.jsx (update)
import CurrentBetStatus from './CurrentBetStatus';

// ... inside expanded view, replace the simple bet display with:
<CurrentBetStatus state={state} />
```

**Step 5: Run test to verify it passes**

Run: `cd frontend && npm test -- CurrentBetStatus.test.js`
Expected: PASS (all tests green)

**Step 6: Commit**

```bash
git add frontend/src/components/game/CurrentBetStatus.jsx frontend/src/components/game/__tests__/CurrentBetStatus.test.js frontend/src/components/game/BettingTracker.jsx
git commit -m "feat: add CurrentBetStatus component with team display"
```

---

## Task 5: Add BettingControls Component

**Files:**
- Create: `frontend/src/components/game/BettingControls.jsx`
- Test: `frontend/src/components/game/__tests__/BettingControls.test.js`

**Step 1: Write the failing test**

```javascript
// frontend/src/components/game/__tests__/BettingControls.test.js
import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import BettingControls from '../BettingControls';

describe('BettingControls', () => {
  const mockActions = {
    offerDouble: jest.fn(),
    acceptDouble: jest.fn(),
    declineDouble: jest.fn(),
    offerPress: jest.fn()
  };

  const mockState = {
    pendingAction: null
  };

  test('should show offer double button when no pending action', () => {
    render(<BettingControls state={mockState} actions={mockActions} currentPlayer="Player1" />);
    expect(screen.getByText(/Offer Double/)).toBeInTheDocument();
  });

  test('should call offerDouble when button clicked', () => {
    render(<BettingControls state={mockState} actions={mockActions} currentPlayer="Player1" />);

    fireEvent.click(screen.getByText(/Offer Double/));
    expect(mockActions.offerDouble).toHaveBeenCalledWith('Player1', 2);
  });

  test('should show accept/decline buttons when double offered', () => {
    const pendingState = {
      pendingAction: {
        type: 'DOUBLE_OFFERED',
        by: 'Player1',
        proposedMultiplier: 2
      }
    };

    render(<BettingControls state={pendingState} actions={mockActions} currentPlayer="Player2" />);

    expect(screen.getByText(/Accept Double/)).toBeInTheDocument();
    expect(screen.getByText(/Decline/)).toBeInTheDocument();
  });

  test('should call acceptDouble when accept clicked', () => {
    const pendingState = {
      pendingAction: {
        type: 'DOUBLE_OFFERED',
        by: 'Player1',
        proposedMultiplier: 2
      }
    };

    render(<BettingControls state={pendingState} actions={mockActions} currentPlayer="Player2" />);

    fireEvent.click(screen.getByText(/Accept Double/));
    expect(mockActions.acceptDouble).toHaveBeenCalledWith('Player2');
  });
});
```

**Step 2: Run test to verify it fails**

Run: `cd frontend && npm test -- BettingControls.test.js`
Expected: FAIL with "Cannot find module '../BettingControls'"

**Step 3: Write minimal implementation**

```javascript
// frontend/src/components/game/BettingControls.jsx
import React from 'react';
import { useTheme } from '../../theme/Provider';

const BettingControls = ({ state, actions, currentPlayer }) => {
  const theme = useTheme();

  const buttonStyle = {
    ...theme.buttonStyle,
    padding: `${theme.spacing[3]} ${theme.spacing[4]}`,
    margin: theme.spacing[2],
    fontSize: theme.typography.md,
    minWidth: 120
  };

  const acceptButtonStyle = {
    ...buttonStyle,
    background: theme.colors.success
  };

  const declineButtonStyle = {
    ...buttonStyle,
    background: theme.colors.error
  };

  const containerStyle = {
    display: 'flex',
    flexDirection: 'column',
    gap: theme.spacing[2],
    padding: theme.spacing[3],
    background: theme.colors.paper,
    borderRadius: theme.borderRadius.md
  };

  const hasPendingAction = state.pendingAction !== null;
  const isPendingDouble = state.pendingAction?.type === 'DOUBLE_OFFERED';

  return (
    <div style={containerStyle}>
      {!hasPendingAction && (
        <>
          <button
            style={buttonStyle}
            onClick={() => actions.offerDouble(currentPlayer, (state.currentMultiplier || 1) * 2)}
          >
            Offer Double
          </button>
          <button
            style={buttonStyle}
            onClick={() => actions.offerPress(currentPlayer, state.baseAmount)}
          >
            Offer Press
          </button>
        </>
      )}

      {isPendingDouble && (
        <>
          <div style={{ marginBottom: theme.spacing[2], fontSize: theme.typography.md }}>
            {state.pendingAction.by} offered to double to {state.pendingAction.proposedMultiplier}x
          </div>
          <div style={{ display: 'flex', gap: theme.spacing[2] }}>
            <button
              style={acceptButtonStyle}
              onClick={() => actions.acceptDouble(currentPlayer)}
            >
              Accept Double
            </button>
            <button
              style={declineButtonStyle}
              onClick={() => actions.declineDouble(currentPlayer)}
            >
              Decline
            </button>
          </div>
        </>
      )}
    </div>
  );
};

export default BettingControls;
```

**Step 4: Run test to verify it passes**

Run: `cd frontend && npm test -- BettingControls.test.js`
Expected: PASS (all tests green)

**Step 5: Commit**

```bash
git add frontend/src/components/game/BettingControls.jsx frontend/src/components/game/__tests__/BettingControls.test.js
git commit -m "feat: add BettingControls component with double offer/accept/decline"
```

---

## Task 6: Add BettingHistory Component with Tabs

**Files:**
- Create: `frontend/src/components/game/BettingHistory.jsx`
- Test: `frontend/src/components/game/__tests__/BettingHistory.test.js`

**Step 1: Write the failing test**

```javascript
// frontend/src/components/game/__tests__/BettingHistory.test.js
import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import BettingHistory from '../BettingHistory';
import { BettingEventTypes } from '../../../constants/bettingEvents';

describe('BettingHistory', () => {
  const mockEventHistory = {
    currentHole: [
      {
        eventId: '1',
        eventType: BettingEventTypes.DOUBLE_OFFERED,
        actor: 'Player1',
        timestamp: '2025-11-04T10:00:00Z',
        data: { proposedMultiplier: 2 }
      },
      {
        eventId: '2',
        eventType: BettingEventTypes.DOUBLE_ACCEPTED,
        actor: 'Player2',
        timestamp: '2025-11-04T10:01:00Z',
        data: { newMultiplier: 2 }
      }
    ],
    lastHole: [],
    gameHistory: []
  };

  test('should show current hole tab by default', () => {
    render(<BettingHistory eventHistory={mockEventHistory} />);
    expect(screen.getByRole('tab', { name: /Current Hole/ })).toHaveAttribute('aria-selected', 'true');
  });

  test('should display events from current hole', () => {
    render(<BettingHistory eventHistory={mockEventHistory} />);
    expect(screen.getByText(/Player1/)).toBeInTheDocument();
    expect(screen.getByText(/DOUBLE_OFFERED/)).toBeInTheDocument();
  });

  test('should switch to last hole tab when clicked', () => {
    render(<BettingHistory eventHistory={mockEventHistory} />);

    fireEvent.click(screen.getByRole('tab', { name: /Last Hole/ }));
    expect(screen.getByRole('tab', { name: /Last Hole/ })).toHaveAttribute('aria-selected', 'true');
  });
});
```

**Step 2: Run test to verify it fails**

Run: `cd frontend && npm test -- BettingHistory.test.js`
Expected: FAIL with "Cannot find module '../BettingHistory'"

**Step 3: Write minimal implementation**

```javascript
// frontend/src/components/game/BettingHistory.jsx
import React, { useState } from 'react';
import { useTheme } from '../../theme/Provider';

const BettingHistory = ({ eventHistory }) => {
  const theme = useTheme();
  const [activeTab, setActiveTab] = useState('current');

  const tabContainerStyle = {
    display: 'flex',
    borderBottom: `2px solid ${theme.colors.border}`,
    marginBottom: theme.spacing[3]
  };

  const tabStyle = (isActive) => ({
    padding: `${theme.spacing[2]} ${theme.spacing[4]}`,
    background: isActive ? theme.colors.primary : 'transparent',
    color: isActive ? 'white' : theme.colors.textPrimary,
    border: 'none',
    cursor: 'pointer',
    fontSize: theme.typography.md,
    borderRadius: `${theme.borderRadius.md} ${theme.borderRadius.md} 0 0`
  });

  const eventListStyle = {
    maxHeight: 300,
    overflowY: 'auto'
  };

  const eventItemStyle = {
    padding: theme.spacing[3],
    background: theme.colors.paper,
    borderRadius: theme.borderRadius.md,
    marginBottom: theme.spacing[2],
    borderLeft: `4px solid ${theme.colors.primary}`
  };

  const getEvents = () => {
    switch (activeTab) {
      case 'current':
        return eventHistory.currentHole;
      case 'last':
        return eventHistory.lastHole;
      case 'game':
        return eventHistory.gameHistory;
      default:
        return [];
    }
  };

  const events = getEvents();

  return (
    <div>
      <div style={tabContainerStyle}>
        <button
          role="tab"
          aria-selected={activeTab === 'current'}
          style={tabStyle(activeTab === 'current')}
          onClick={() => setActiveTab('current')}
        >
          Current Hole
        </button>
        <button
          role="tab"
          aria-selected={activeTab === 'last'}
          style={tabStyle(activeTab === 'last')}
          onClick={() => setActiveTab('last')}
        >
          Last Hole
        </button>
        <button
          role="tab"
          aria-selected={activeTab === 'game'}
          style={tabStyle(activeTab === 'game')}
          onClick={() => setActiveTab('game')}
        >
          Game History
        </button>
      </div>

      <div style={eventListStyle}>
        {events.length === 0 && (
          <div style={{ textAlign: 'center', color: theme.colors.textSecondary }}>
            No events yet
          </div>
        )}
        {events.map((event) => (
          <div key={event.eventId} style={eventItemStyle}>
            <div style={{ fontWeight: theme.typography.bold, marginBottom: theme.spacing[1] }}>
              {event.eventType}
            </div>
            <div style={{ fontSize: theme.typography.sm, color: theme.colors.textSecondary }}>
              {event.actor} at {new Date(event.timestamp).toLocaleTimeString()}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default BettingHistory;
```

**Step 4: Run test to verify it passes**

Run: `cd frontend && npm test -- BettingHistory.test.js`
Expected: PASS (all tests green)

**Step 5: Commit**

```bash
git add frontend/src/components/game/BettingHistory.jsx frontend/src/components/game/__tests__/BettingHistory.test.js
git commit -m "feat: add BettingHistory component with tabbed interface"
```

---

## Task 7: Integrate All Components into BettingTracker

**Files:**
- Modify: `frontend/src/components/game/BettingTracker.jsx`

**Step 1: Update BettingTracker to include all subcomponents**

```javascript
// frontend/src/components/game/BettingTracker.jsx (complete version)
import React, { useState } from 'react';
import { useTheme } from '../../theme/Provider';
import useBettingState from '../../hooks/useBettingState';
import CurrentBetStatus from './CurrentBetStatus';
import BettingControls from './BettingControls';
import BettingHistory from './BettingHistory';

const BettingTracker = ({ gameState, currentPlayer = 'Player1' }) => {
  const theme = useTheme();
  const [isExpanded, setIsExpanded] = useState(false);
  const { state, eventHistory, actions } = useBettingState(
    gameState.id,
    gameState.current_hole
  );

  const hasPendingAction = state.pendingAction !== null;

  const collapsedStyle = {
    padding: theme.spacing[3],
    background: theme.colors.paper,
    borderRadius: theme.borderRadius.md,
    cursor: 'pointer',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: theme.spacing[3],
    border: `2px solid ${theme.colors.border}`,
  };

  const expandedContainerStyle = {
    ...collapsedStyle,
    flexDirection: 'column',
    cursor: 'default',
    border: `2px solid ${theme.colors.primary}`
  };

  if (!isExpanded) {
    return (
      <div style={collapsedStyle} onClick={() => setIsExpanded(true)}>
        <span>
          Bet: ${state.currentBet.toFixed(2)} ({state.currentMultiplier}x)
        </span>
        {hasPendingAction && (
          <span
            data-testid="pending-indicator"
            style={{
              background: theme.colors.error,
              color: 'white',
              borderRadius: theme.borderRadius.full,
              padding: `${theme.spacing[1]} ${theme.spacing[2]}`,
              fontSize: theme.typography.xs,
              animation: 'pulse 2s infinite'
            }}
          >
            Action Required
          </span>
        )}
      </div>
    );
  }

  return (
    <div style={expandedContainerStyle}>
      <div
        style={{
          width: '100%',
          display: 'flex',
          justifyContent: 'space-between',
          marginBottom: theme.spacing[3],
          cursor: 'pointer'
        }}
        onClick={() => setIsExpanded(false)}
      >
        <h3 style={{ margin: 0, fontSize: theme.typography.xl }}>Betting Tracker</h3>
        <button style={{
          ...theme.buttonStyle,
          padding: theme.spacing[1],
          background: 'transparent',
          color: theme.colors.textSecondary
        }}>
          ▼ Collapse
        </button>
      </div>

      <CurrentBetStatus state={state} />
      <BettingControls state={state} actions={actions} currentPlayer={currentPlayer} />
      <BettingHistory eventHistory={eventHistory} />
    </div>
  );
};

export default BettingTracker;
```

**Step 2: Run integration test**

Run: `cd frontend && npm test -- BettingTracker.test.js`
Expected: PASS (all tests green)

**Step 3: Commit**

```bash
git add frontend/src/components/game/BettingTracker.jsx
git commit -m "feat: integrate all betting components into BettingTracker"
```

---

## Task 8: Add BettingTracker to GamePage

**Files:**
- Modify: `frontend/src/pages/GamePage.js:416-425`

**Step 1: Import BettingTracker**

```javascript
// frontend/src/pages/GamePage.js (add to imports at top)
import BettingTracker from '../components/game/BettingTracker';
```

**Step 2: Add BettingTracker to page layout**

Insert after line 419 (after `{bettingTipsCard}`):

```javascript
        {/* Betting Action Tracker */}
        <BettingTracker
          gameState={gameState}
          currentPlayer={gameState.players[0]?.name || 'Player1'}
        />
```

**Step 3: Test manually**

Run: `cd frontend && npm start`
Expected: BettingTracker appears on GamePage, can expand/collapse

**Step 4: Commit**

```bash
git add frontend/src/pages/GamePage.js
git commit -m "feat: add BettingTracker to GamePage"
```

---

## Task 9: Create Backend Betting Events Endpoint

**Files:**
- Create: `backend/app/routes/betting_events.py`
- Modify: `backend/app/main.py:15-20`
- Test: `backend/tests/test_betting_events.py`

**Step 1: Write the failing test**

```python
# backend/tests/test_betting_events.py
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_create_betting_events():
    game_id = "test-game-123"
    payload = {
        "holeNumber": 5,
        "events": [
            {
                "eventId": "event-1",
                "eventType": "DOUBLE_OFFERED",
                "actor": "Player1",
                "data": {"proposedMultiplier": 2},
                "timestamp": "2025-11-04T10:00:00Z"
            }
        ],
        "clientTimestamp": "2025-11-04T10:00:00Z"
    }

    response = client.post(f"/api/games/{game_id}/betting-events", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert len(data["confirmedEvents"]) == 1
    assert data["confirmedEvents"][0] == "event-1"

def test_invalid_event_type():
    game_id = "test-game-123"
    payload = {
        "holeNumber": 5,
        "events": [
            {
                "eventId": "event-1",
                "eventType": "INVALID_TYPE",
                "actor": "Player1",
                "data": {},
                "timestamp": "2025-11-04T10:00:00Z"
            }
        ],
        "clientTimestamp": "2025-11-04T10:00:00Z"
    }

    response = client.post(f"/api/games/{game_id}/betting-events", json=payload)

    assert response.status_code == 400
```

**Step 2: Run test to verify it fails**

Run: `cd backend && pytest tests/test_betting_events.py -v`
Expected: FAIL with "404 Not Found"

**Step 3: Write minimal implementation**

```python
# backend/app/routes/betting_events.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Any, Dict

router = APIRouter()

VALID_EVENT_TYPES = {
    "DOUBLE_OFFERED",
    "DOUBLE_ACCEPTED",
    "DOUBLE_DECLINED",
    "PRESS_OFFERED",
    "PRESS_ACCEPTED",
    "PRESS_DECLINED",
    "TEAMS_FORMED",
    "HOLE_COMPLETE"
}

class BettingEvent(BaseModel):
    eventId: str
    eventType: str
    actor: str
    data: Dict[str, Any]
    timestamp: str

class BettingEventsPayload(BaseModel):
    holeNumber: int
    events: List[BettingEvent]
    clientTimestamp: str

class BettingEventsResponse(BaseModel):
    success: bool
    confirmedEvents: List[str]
    corrections: List[Dict[str, Any]] = []

@router.post("/api/games/{game_id}/betting-events", response_model=BettingEventsResponse)
async def create_betting_events(game_id: str, payload: BettingEventsPayload):
    """
    Store betting events for a game.
    Validates event types and returns confirmed event IDs.
    """
    confirmed = []

    for event in payload.events:
        if event.eventType not in VALID_EVENT_TYPES:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid event type: {event.eventType}"
            )
        confirmed.append(event.eventId)

    # TODO: Persist to database
    # For now, just confirm receipt

    return BettingEventsResponse(
        success=True,
        confirmedEvents=confirmed,
        corrections=[]
    )
```

**Step 4: Register router in main.py**

```python
# backend/app/main.py (add to imports)
from app.routes.betting_events import router as betting_events_router

# backend/app/main.py (add after other routers)
app.include_router(betting_events_router)
```

**Step 5: Run test to verify it passes**

Run: `cd backend && pytest tests/test_betting_events.py -v`
Expected: PASS (all tests green)

**Step 6: Commit**

```bash
git add backend/app/routes/betting_events.py backend/app/main.py backend/tests/test_betting_events.py
git commit -m "feat: add betting events API endpoint"
```

---

## Task 10: Add Batch Sync Logic to Frontend

**Files:**
- Modify: `frontend/src/hooks/useBettingState.js`
- Create: `frontend/src/api/bettingApi.js`
- Test: `frontend/src/api/__tests__/bettingApi.test.js`

**Step 1: Write the failing test**

```javascript
// frontend/src/api/__tests__/bettingApi.test.js
import { syncBettingEvents } from '../bettingApi';
import { BettingEventTypes } from '../../constants/bettingEvents';

global.fetch = jest.fn();

describe('bettingApi', () => {
  afterEach(() => {
    jest.clearAllMocks();
  });

  test('should sync events successfully', async () => {
    const mockResponse = {
      success: true,
      confirmedEvents: ['event-1'],
      corrections: []
    };

    global.fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockResponse
    });

    const events = [{
      eventId: 'event-1',
      eventType: BettingEventTypes.DOUBLE_OFFERED,
      actor: 'Player1',
      data: {},
      timestamp: '2025-11-04T10:00:00Z'
    }];

    const result = await syncBettingEvents('game-123', 5, events);

    expect(result.success).toBe(true);
    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining('/api/games/game-123/betting-events'),
      expect.objectContaining({
        method: 'POST'
      })
    );
  });

  test('should handle sync failure', async () => {
    global.fetch.mockResolvedValueOnce({
      ok: false,
      status: 400
    });

    const events = [{
      eventId: 'event-1',
      eventType: 'INVALID',
      actor: 'Player1',
      data: {},
      timestamp: '2025-11-04T10:00:00Z'
    }];

    await expect(syncBettingEvents('game-123', 5, events)).rejects.toThrow();
  });
});
```

**Step 2: Run test to verify it fails**

Run: `cd frontend && npm test -- bettingApi.test.js`
Expected: FAIL with "Cannot find module '../bettingApi'"

**Step 3: Write minimal implementation**

```javascript
// frontend/src/api/bettingApi.js
const API_URL = process.env.REACT_APP_API_URL || "";

export const syncBettingEvents = async (gameId, holeNumber, events) => {
  const payload = {
    holeNumber,
    events,
    clientTimestamp: new Date().toISOString()
  };

  const response = await fetch(`${API_URL}/api/games/${gameId}/betting-events`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });

  if (!response.ok) {
    throw new Error(`Sync failed: ${response.status}`);
  }

  return await response.json();
};

export const syncWithRetry = async (gameId, holeNumber, events, maxRetries = 3) => {
  let lastError;

  for (let attempt = 0; attempt < maxRetries; attempt++) {
    try {
      return await syncBettingEvents(gameId, holeNumber, events);
    } catch (error) {
      lastError = error;
      const delay = Math.min(1000 * Math.pow(2, attempt), 30000);
      await new Promise(resolve => setTimeout(resolve, delay));
    }
  }

  throw lastError;
};
```

**Step 4: Update useBettingState to trigger batch sync**

```javascript
// frontend/src/hooks/useBettingState.js (add)
import { syncBettingEvents } from '../api/bettingApi';

// Add state for sync tracking
const [syncStatus, setSyncStatus] = useState('synced'); // 'synced' | 'pending' | 'error'
const [unsyncedEvents, setUnsyncedEvents] = useState([]);

// Add effect to sync every 5 events
useEffect(() => {
  if (unsyncedEvents.length >= 5) {
    const performSync = async () => {
      setSyncStatus('pending');
      try {
        await syncBettingEvents(gameId, holeNumber, unsyncedEvents);
        setUnsyncedEvents([]);
        setSyncStatus('synced');
      } catch (error) {
        console.error('Sync failed:', error);
        setSyncStatus('error');
      }
    };
    performSync();
  }
}, [unsyncedEvents, gameId, holeNumber]);

// Modify addEvent to track unsynced events
const addEvent = useCallback((eventType, actor, data) => {
  const event = createBettingEvent({ gameId, holeNumber, eventType, actor, data });

  setEventHistory(prev => ({
    ...prev,
    currentHole: [...prev.currentHole, event],
    gameHistory: [...prev.gameHistory, event]
  }));

  setUnsyncedEvents(prev => [...prev, event]);

  return event;
}, [gameId, holeNumber]);

// Return sync status
return {
  state,
  eventHistory,
  actions: { offerDouble, acceptDouble, declineDouble },
  syncStatus
};
```

**Step 5: Run test to verify it passes**

Run: `cd frontend && npm test -- bettingApi.test.js`
Expected: PASS (all tests green)

**Step 6: Commit**

```bash
git add frontend/src/api/bettingApi.js frontend/src/api/__tests__/bettingApi.test.js frontend/src/hooks/useBettingState.js
git commit -m "feat: add batch sync logic with retry mechanism"
```

---

## Task 11: Add Hole Completion Sync Trigger

**Files:**
- Modify: `frontend/src/hooks/useBettingState.js`

**Step 1: Add hole completion handler**

```javascript
// frontend/src/hooks/useBettingState.js (add)

const completeHole = useCallback(async () => {
  // Create HOLE_COMPLETE event
  addEvent(BettingEventTypes.HOLE_COMPLETE, 'system', {
    finalMultiplier: state.currentMultiplier,
    finalBet: state.currentBet
  });

  // Force sync all unsynced events
  if (unsyncedEvents.length > 0) {
    setSyncStatus('pending');
    try {
      await syncBettingEvents(gameId, holeNumber, unsyncedEvents);
      setUnsyncedEvents([]);
      setSyncStatus('synced');
    } catch (error) {
      console.error('Hole completion sync failed:', error);
      setSyncStatus('error');
      throw error;
    }
  }

  // Move current hole events to last hole
  setEventHistory(prev => ({
    ...prev,
    lastHole: prev.currentHole,
    currentHole: []
  }));

  // Reset betting state for next hole
  setState({
    holeNumber: holeNumber + 1,
    currentMultiplier: 1,
    baseAmount: 1.00,
    currentBet: 1.00,
    teams: [],
    pendingAction: null,
    presses: []
  });
}, [addEvent, state, unsyncedEvents, gameId, holeNumber]);

// Add to returned actions
return {
  state,
  eventHistory,
  actions: {
    offerDouble,
    acceptDouble,
    declineDouble,
    completeHole  // New action
  },
  syncStatus
};
```

**Step 2: Add test for hole completion**

```javascript
// frontend/src/hooks/__tests__/useBettingState.test.js (add test)
test('should complete hole and sync events', async () => {
  const { result } = renderHook(() => useBettingState('game-123', 1));

  act(() => {
    result.current.actions.offerDouble('Player1', 2);
    result.current.actions.acceptDouble('Player2');
  });

  await act(async () => {
    await result.current.actions.completeHole();
  });

  expect(result.current.state.holeNumber).toBe(2);
  expect(result.current.state.currentMultiplier).toBe(1);
  expect(result.current.eventHistory.currentHole).toEqual([]);
  expect(result.current.eventHistory.lastHole.length).toBeGreaterThan(0);
});
```

**Step 3: Run test to verify it passes**

Run: `cd frontend && npm test -- useBettingState.test.js`
Expected: PASS (all tests green)

**Step 4: Commit**

```bash
git add frontend/src/hooks/useBettingState.js frontend/src/hooks/__tests__/useBettingState.test.js
git commit -m "feat: add hole completion with forced sync"
```

---

## Task 12: Add Mobile Responsiveness

**Files:**
- Modify: `frontend/src/components/game/BettingTracker.jsx`

**Step 1: Add responsive styles**

```javascript
// frontend/src/components/game/BettingTracker.jsx (update styles)

const BettingTracker = ({ gameState, currentPlayer = 'Player1' }) => {
  const theme = useTheme();
  const [isExpanded, setIsExpanded] = useState(false);

  // Detect mobile
  const [isMobile, setIsMobile] = useState(window.innerWidth < 768);

  useEffect(() => {
    const handleResize = () => {
      setIsMobile(window.innerWidth < 768);
    };

    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  // Mobile bottom sheet styles
  const mobileExpandedStyle = {
    position: 'fixed',
    bottom: 0,
    left: 0,
    right: 0,
    background: theme.colors.paper,
    borderTopLeftRadius: theme.borderRadius.lg,
    borderTopRightRadius: theme.borderRadius.lg,
    boxShadow: theme.shadows.lg,
    maxHeight: '80vh',
    overflowY: 'auto',
    padding: theme.spacing[4],
    zIndex: 1000,
    animation: 'slideUp 0.3s ease-out'
  };

  // Use mobile styles on small screens
  const expandedStyle = isMobile ? mobileExpandedStyle : expandedContainerStyle;

  // ... rest of component
};

// Add slideUp animation
const styleSheet = document.createElement("style");
styleSheet.textContent = `
  @keyframes slideUp {
    from {
      transform: translateY(100%);
    }
    to {
      transform: translateY(0);
    }
  }

  @keyframes pulse {
    0%, 100% {
      opacity: 1;
    }
    50% {
      opacity: 0.5;
    }
  }
`;
document.head.appendChild(styleSheet);
```

**Step 2: Test on mobile viewport**

Run: `cd frontend && npm start`
Test: Resize browser to mobile width, verify bottom sheet behavior

**Step 3: Commit**

```bash
git add frontend/src/components/game/BettingTracker.jsx
git commit -m "feat: add mobile responsive bottom sheet for betting tracker"
```

---

## Task 13: Integration Testing

**Files:**
- Create: `frontend/src/components/game/__tests__/BettingTracker.integration.test.js`

**Step 1: Write integration test**

```javascript
// frontend/src/components/game/__tests__/BettingTracker.integration.test.js
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import BettingTracker from '../BettingTracker';

describe('BettingTracker Integration', () => {
  const mockGameState = {
    id: 'game-123',
    current_hole: 5,
    players: [
      { id: 'p1', name: 'Player1' },
      { id: 'p2', name: 'Player2' }
    ]
  };

  test('complete double offer and accept workflow', async () => {
    render(<BettingTracker gameState={mockGameState} currentPlayer="Player1" />);

    // Expand tracker
    fireEvent.click(screen.getByText(/Bet:/));

    // Offer double
    fireEvent.click(screen.getByText(/Offer Double/));

    // Should show pending action
    await waitFor(() => {
      expect(screen.getByText(/Player1 offered to double/)).toBeInTheDocument();
    });

    // Accept double
    fireEvent.click(screen.getByText(/Accept Double/));

    // Should update multiplier
    await waitFor(() => {
      expect(screen.getByText(/2x/)).toBeInTheDocument();
    });

    // Should show in history
    expect(screen.getByText(/DOUBLE_ACCEPTED/)).toBeInTheDocument();
  });
});
```

**Step 2: Run integration test**

Run: `cd frontend && npm test -- BettingTracker.integration.test.js`
Expected: PASS (all tests green)

**Step 3: Commit**

```bash
git add frontend/src/components/game/__tests__/BettingTracker.integration.test.js
git commit -m "test: add integration tests for betting tracker workflow"
```

---

## Task 14: Documentation and Cleanup

**Files:**
- Create: `docs/BETTING_TRACKER.md`

**Step 1: Create user documentation**

```markdown
# Betting Action Tracker

## Overview

The Betting Action Tracker provides real-time visibility into betting actions during each hole, including doubles, presses, team formations, and complete betting history.

## Features

- **Expandable Panel**: Collapsed by default, expands to show full betting controls
- **Current Bet Status**: Always visible multiplier and bet amount
- **Team Display**: Shows current partnerships and bet amounts
- **Betting Controls**: Offer/accept/decline doubles and presses
- **Event History**: Three tabs - Current Hole, Last Hole, Game History
- **Mobile Responsive**: Bottom sheet UI on mobile devices
- **Auto-sync**: Batches events and syncs to backend every 5 events or at hole completion

## Usage

### Offering a Double

1. Expand the betting tracker
2. Click "Offer Double"
3. Other players will see accept/decline buttons
4. Multiplier updates when accepted

### Viewing History

1. Expand the betting tracker
2. Navigate between tabs: Current Hole / Last Hole / Game History
3. See chronological list of all betting actions

### Mobile

- Swipe up to expand (bottom sheet)
- Swipe down to collapse
- Touch-friendly large buttons

## Architecture

- **Client-side**: React hooks manage state with event sourcing
- **Backend**: FastAPI endpoint receives batched events
- **Sync**: Batch POST every 5 events or hole completion
- **Retry**: Exponential backoff on failures (1s, 2s, 4s, max 30s)
```

**Step 2: Add component documentation**

```javascript
// frontend/src/components/game/BettingTracker.jsx (add JSDoc)
/**
 * BettingTracker - Main betting action tracker component
 *
 * Displays current bet status, betting controls, and event history.
 * Manages client-side state with event sourcing and batch syncs to backend.
 *
 * @param {Object} gameState - Current game state from GamePage
 * @param {string} currentPlayer - ID of current player for action context
 *
 * Features:
 * - Expandable panel (collapsed by default)
 * - Real-time betting actions (double, press, teams)
 * - Event history with tabs (current hole, last hole, game)
 * - Mobile responsive (bottom sheet)
 * - Auto-sync (every 5 events or hole completion)
 */
```

**Step 3: Commit documentation**

```bash
git add docs/BETTING_TRACKER.md frontend/src/components/game/BettingTracker.jsx
git commit -m "docs: add betting tracker user and developer documentation"
```

---

## Summary

This implementation plan creates a complete betting action tracker with:

1. **Event-sourced state management** (Tasks 1-2)
2. **Expandable UI components** (Tasks 3-7)
3. **Integration with GamePage** (Task 8)
4. **Backend API endpoint** (Task 9)
5. **Batch sync with retry** (Tasks 10-11)
6. **Mobile responsiveness** (Task 12)
7. **Testing and documentation** (Tasks 13-14)

Each task follows TDD with clear verification steps. Commit frequently after each passing test.

**Total estimated time**: 6-8 hours for experienced developer

**Dependencies**: uuid package (installed in Task 1)

**Testing strategy**: Unit tests for all components, integration tests for workflows, manual testing for mobile responsiveness

# Test Utilities Documentation

This directory contains comprehensive testing utilities for the Wolf Goat Pig application. These tools help maintain consistent test patterns, reduce boilerplate code, and improve test maintainability.

## Table of Contents

- [Overview](#overview)
- [Test Helpers](#test-helpers)
- [Mock Factories](#mock-factories)
- [Game Fixtures](#game-fixtures)
- [Common Patterns](#common-patterns)
- [Best Practices](#best-practices)

## Overview

The test utilities are organized into three main files:

1. **testHelpers.js** - General-purpose testing utilities (wrappers, mocks, async utils)
2. **mockFactories.js** - Factory functions for creating test mocks with sensible defaults
3. **gameFixtures.js** - Pre-built game data fixtures for common test scenarios

## Test Helpers

### Rendering Components

#### TestWrapper
Provides all necessary context providers for component testing.

```javascript
import { TestWrapper } from '../test-utils/testHelpers';

<TestWrapper tutorialState={{ isActive: true }} theme="default">
  <YourComponent />
</TestWrapper>
```

#### renderWithContext
Convenience function that wraps `render` with TestWrapper.

```javascript
import { renderWithContext } from '../test-utils/testHelpers';

const { getByText } = renderWithContext(
  <YourComponent />,
  {
    tutorialState: { isActive: true },
    theme: 'dark'
  }
);
```

### Browser API Mocks

#### mockFetch
Mock fetch with customizable responses by endpoint.

```javascript
import { mockFetch } from '../test-utils/testHelpers';

mockFetch({
  'GET /api/players': { players: [...] },
  'POST /api/game': { game_id: '123' }
});
```

#### mockLocalStorage / mockSessionStorage
Fully functional storage mocks with proper API.

```javascript
import { mockLocalStorage } from '../test-utils/testHelpers';

const storage = mockLocalStorage();
storage.setItem('key', 'value');
expect(storage.getItem('key')).toBe('value');
```

#### mockWindowDialogs
Mock window.confirm, alert, and prompt.

```javascript
import { mockWindowDialogs } from '../test-utils/testHelpers';

const { confirmMock, alertMock } = mockWindowDialogs();
confirmMock.mockReturnValue(true); // User clicks OK
```

#### mockResizeObserver / mockIntersectionObserver
Mock observer APIs for responsive components.

```javascript
import { mockResizeObserver } from '../test-utils/testHelpers';

mockResizeObserver();
// Now your components using ResizeObserver will work in tests
```

### Async Utilities

#### waitForCondition
Wait for a custom condition to be true.

```javascript
import { asyncUtils } from '../test-utils/testHelpers';

await asyncUtils.waitForCondition(
  () => document.querySelector('.loaded') !== null,
  5000 // timeout in ms
);
```

#### flushPromises
Flush all pending promises in the microtask queue.

```javascript
import { asyncUtils } from '../test-utils/testHelpers';

await asyncUtils.flushPromises();
// All pending promises have now resolved
```

### Form Testing

#### fillForm
Automatically fill form fields with data.

```javascript
import { formUtils } from '../test-utils/testHelpers';
import userEvent from '@testing-library/user-event';

const user = userEvent.setup();
await formUtils.fillForm(form, {
  username: 'testuser',
  email: 'test@example.com',
  acceptTerms: true
}, user);
```

#### expectFormErrors
Validate form error messages.

```javascript
import { formUtils } from '../test-utils/testHelpers';

formUtils.expectFormErrors(form, {
  username: 'Username is required',
  email: null // No error expected
});
```

### Setup and Teardown

#### setupTestEnvironment
One-line setup for common test environment configuration.

```javascript
import { setupTestEnvironment } from '../test-utils/testHelpers';

beforeEach(() => {
  const cleanup = setupTestEnvironment();
  return cleanup; // Returns cleanup function
});
```

## Mock Factories

Mock factories provide consistent, customizable test data with sensible defaults.

### Theme Mocks

#### createMockTheme
Create a complete theme object for testing themed components.

```javascript
import { createMockTheme } from '../test-utils/mockFactories';

const theme = createMockTheme({
  colors: {
    primary: '#FF0000' // Override just what you need
  }
});
```

#### createMockUseTheme
Create a mock useTheme hook.

```javascript
import { createMockUseTheme } from '../test-utils/mockFactories';

jest.mock('../../theme/Provider', () => ({
  useTheme: createMockUseTheme()
}));
```

### Game State Mocks

#### createMockPlayers
Generate realistic player objects.

```javascript
import { createMockPlayers } from '../test-utils/mockFactories';

// Create 4 players with defaults
const players = createMockPlayers(4);

// Create players with custom properties
const customPlayers = createMockPlayers(2, {
  handicap: 10,
  current_score: 35
});
```

#### createMockGameState
Create game states for different scenarios.

```javascript
import { createMockGameState } from '../test-utils/mockFactories';

// Initial game state (hole 1, no scores)
const initialGame = createMockGameState('initial');

// Mid-game state (hole 8, some scores)
const midGame = createMockGameState('mid_game');

// Final hole
const finalHole = createMockGameState('final_hole');

// Completed game
const completed = createMockGameState('completed');

// Custom overrides
const customGame = createMockGameState('mid_game', {
  current_hole: 10,
  current_wager: 5.0
});
```

#### createMockHoleHistory
Generate hole-by-hole scoring history.

```javascript
import { createMockHoleHistory } from '../test-utils/mockFactories';

const history = createMockHoleHistory(
  8, // 8 holes completed
  ['player_1', 'player_2', 'player_3', 'player_4']
);
```

#### createMockCourseHoles
Generate course hole data.

```javascript
import { createMockCourseHoles } from '../test-utils/mockFactories';

const holes = createMockCourseHoles(18); // Full 18-hole course
const nineHoles = createMockCourseHoles(9); // 9-hole course
```

### Betting Mocks

#### createMockOddsResponse
Generate odds calculation responses.

```javascript
import { createMockOddsResponse } from '../test-utils/mockFactories';

const odds = createMockOddsResponse({
  confidence_level: 0.95,
  calculation_time_ms: 100
});
```

#### createMockBettingScenario
Create specific betting scenarios.

```javascript
import { createMockBettingScenario } from '../test-utils/mockFactories';

const doubleDown = createMockBettingScenario('double_down');
const sideBet = createMockBettingScenario('side_bet');
const pressBet = createMockBettingScenario('press_bet');
```

### Event Handler Mocks

#### createMockEventHandlers
Create a complete set of jest mock functions.

```javascript
import { createMockEventHandlers } from '../test-utils/mockFactories';

const handlers = createMockEventHandlers();
// handlers.onClick, handlers.onSubmit, handlers.onBettingAction, etc.

<Component onClick={handlers.onClick} onSave={handlers.onSave} />

expect(handlers.onClick).toHaveBeenCalledWith(expectedArg);
```

### API Mocks

#### createMockFetchResponse
Mock successful API responses.

```javascript
import { createMockFetchResponse } from '../test-utils/mockFactories';

global.fetch = jest.fn(() =>
  createMockFetchResponse({ data: 'success' })
);
```

#### createMockFetchError
Mock HTTP error responses.

```javascript
import { createMockFetchError } from '../test-utils/mockFactories';

global.fetch = jest.fn(() =>
  createMockFetchError(404, 'Not Found')
);
```

## Game Fixtures

Pre-built, realistic game data for common test scenarios.

### mockPlayerProfiles
Array of 4 detailed player profiles with stats, preferences, and history.

```javascript
import { mockPlayerProfiles } from '../__tests__/fixtures/gameFixtures';

const alice = mockPlayerProfiles[0]; // Experienced player
const bob = mockPlayerProfiles[1];   // Aggressive player
```

### mockGameStates
Complete game states for different scenarios.

```javascript
import { mockGameStates } from '../__tests__/fixtures/gameFixtures';

const initialGame = mockGameStates.initial;
const midGame = mockGameStates.mid_game;
const finalHole = mockGameStates.final_hole;
const completed = mockGameStates.completed;
```

### mockOddsResponses
Realistic odds calculation responses.

```javascript
import { mockOddsResponses } from '../__tests__/fixtures/gameFixtures';

const basicOdds = mockOddsResponses.basic;
const complexOdds = mockOddsResponses.complex;
```

### Utility Functions

The fixtures include helper functions:

```javascript
import { testUtils } from '../__tests__/fixtures/gameFixtures';

// Create custom player
const player = testUtils.createPlayer({ name: 'Custom', handicap: 10 });

// Create custom game state
const game = testUtils.createGameState('mid_game', { current_hole: 12 });

// Generate random score
const score = testUtils.generateRandomScore(4, 18); // par, handicap

// Deep clone for mutation testing
const cloned = testUtils.deepClone(mockGameStates.mid_game);

// Generate time series data for charts
const chartData = testUtils.generateTimeSeriesData(30, 100, 0.1);
```

## Common Patterns

### Testing a Component with Theme

```javascript
import { renderWithContext, createMockTheme } from '../test-utils';

test('renders with custom theme', () => {
  const customTheme = createMockTheme({
    colors: { primary: '#FF0000' }
  });

  renderWithContext(<YourComponent />, { theme: customTheme });
  // Test themed rendering
});
```

### Testing Game Components

```javascript
import { renderWithContext } from '../test-utils/testHelpers';
import { createMockGameState, createMockPlayers } from '../test-utils/mockFactories';

test('displays current game state', () => {
  const gameState = createMockGameState('mid_game', {
    current_hole: 10
  });

  const { getByText } = renderWithContext(
    <GameComponent gameState={gameState} />
  );

  expect(getByText(/Hole 10/)).toBeInTheDocument();
});
```

### Testing Betting Components

```javascript
import { renderWithContext } from '../test-utils/testHelpers';
import {
  createMockOddsResponse,
  createMockEventHandlers
} from '../test-utils/mockFactories';

test('handles betting action', async () => {
  const handlers = createMockEventHandlers();
  const odds = createMockOddsResponse();

  const { getByText } = renderWithContext(
    <BettingPanel odds={odds} onBettingAction={handlers.onBettingAction} />
  );

  await userEvent.click(getByText('Place Bet'));
  expect(handlers.onBettingAction).toHaveBeenCalled();
});
```

### Testing with Async Data

```javascript
import { renderWithContext, asyncUtils } from '../test-utils/testHelpers';
import { createMockFetchResponse } from '../test-utils/mockFactories';

test('loads and displays data', async () => {
  global.fetch = jest.fn(() =>
    createMockFetchResponse({ players: createMockPlayers(4) })
  );

  renderWithContext(<PlayerList />);

  await asyncUtils.waitForCondition(
    () => screen.queryByText('Alice') !== null
  );

  expect(screen.getByText('Alice')).toBeInTheDocument();
});
```

### Testing Forms

```javascript
import { renderWithContext, formUtils } from '../test-utils/testHelpers';
import userEvent from '@testing-library/user-event';

test('validates form submission', async () => {
  const user = userEvent.setup();
  const onSubmit = jest.fn();

  const { container } = renderWithContext(
    <YourForm onSubmit={onSubmit} />
  );

  await formUtils.fillForm(container, {
    username: 'test',
    email: 'invalid-email'
  }, user);

  await user.click(screen.getByText('Submit'));

  formUtils.expectFormErrors(container, {
    email: 'Invalid email format'
  });
});
```

## Best Practices

### 1. Use Mock Factories for Consistency
Always use factory functions instead of creating mocks inline. This ensures consistent test data and makes updates easier.

```javascript
// ❌ Don't
const player = { id: '1', name: 'Test', handicap: 10, ... };

// ✅ Do
const player = createMockPlayers(1)[0];
```

### 2. Override Only What You Need
Factory functions provide sensible defaults. Only override properties relevant to your test.

```javascript
// ✅ Clear and focused
const highHandicapPlayer = createMockPlayers(1, { handicap: 25 })[0];
```

### 3. Use Fixtures for Complex Scenarios
For rich, realistic data, use the pre-built fixtures.

```javascript
import { mockGameStates } from '../__tests__/fixtures/gameFixtures';

const midGameScenario = mockGameStates.mid_game;
```

### 4. Clean Up After Tests
Use setupTestEnvironment for automatic cleanup.

```javascript
beforeEach(() => {
  const cleanup = setupTestEnvironment();
  return cleanup;
});
```

### 5. Combine Utilities Effectively
Leverage multiple utilities together for comprehensive tests.

```javascript
import { renderWithContext } from '../test-utils/testHelpers';
import { createMockGameState, createMockEventHandlers } from '../test-utils/mockFactories';
import { mockOddsResponses } from '../__tests__/fixtures/gameFixtures';

test('complete betting flow', async () => {
  const gameState = createMockGameState('mid_game');
  const handlers = createMockEventHandlers();
  const odds = mockOddsResponses.basic;

  renderWithContext(
    <BettingSystem
      gameState={gameState}
      odds={odds}
      onAction={handlers.onBettingAction}
    />
  );

  // Test implementation
});
```

### 6. Document Custom Mocks
When creating test-specific mocks, add comments explaining why.

```javascript
// Mock WebSocket for real-time game updates test
const mockWebSocket = createMockWebSocket();
mockWebSocket.simulateMessage({ type: 'score_update', data: {...} });
```

### 7. Test Edge Cases with Minimal Data
Use factories with minimal overrides to test edge cases.

```javascript
// Test with no players
const emptyGame = createMockGameState('initial', { players: [] });

// Test with maximum players
const fullGame = createMockGameState('initial', {
  players: createMockPlayers(6)
});
```

## Examples

### Complete Component Test Example

```javascript
import React from 'react';
import { screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { renderWithContext } from '../test-utils/testHelpers';
import {
  createMockGameState,
  createMockOddsResponse,
  createMockEventHandlers
} from '../test-utils/mockFactories';
import BettingOddsPanel from '../BettingOddsPanel';

describe('BettingOddsPanel', () => {
  let gameState;
  let oddsResponse;
  let handlers;

  beforeEach(() => {
    gameState = createMockGameState('mid_game');
    oddsResponse = createMockOddsResponse();
    handlers = createMockEventHandlers();

    global.fetch = jest.fn(() =>
      Promise.resolve({
        ok: true,
        json: async () => oddsResponse
      })
    );
  });

  test('displays odds and handles betting action', async () => {
    const user = userEvent.setup();

    renderWithContext(
      <BettingOddsPanel
        gameState={gameState}
        onBettingAction={handlers.onBettingAction}
      />
    );

    // Wait for odds to load
    expect(await screen.findByText(/65.0%/)).toBeInTheDocument();

    // Click betting action
    await user.click(screen.getByText('Take Action'));

    expect(handlers.onBettingAction).toHaveBeenCalledWith(
      expect.objectContaining({
        scenario_type: 'double_down'
      })
    );
  });
});
```

## Summary

This testing toolkit provides:

- **Consistency** - Standardized mocks and fixtures across all tests
- **DRY** - Reusable factory functions eliminate duplication
- **Maintainability** - Central location for test data makes updates easy
- **Realism** - Pre-built fixtures provide realistic game scenarios
- **Flexibility** - Override only what you need for each test
- **Speed** - Less boilerplate means faster test writing

For questions or to add new utilities, update the relevant file and this documentation.

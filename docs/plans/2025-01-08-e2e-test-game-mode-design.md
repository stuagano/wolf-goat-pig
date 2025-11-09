# E2E Testing Design: Test Game Mode Happy Path

**Date**: January 8, 2025
**Status**: Design Approved
**Related Issue**: #118

## Overview

Implement comprehensive end-to-end testing for the Wolf Goat Pig test game mode using Playwright. The test suite will validate the complete user journey from homepage navigation through game creation, scorekeeper interaction, and final game completion.

## Approach: Hybrid with Fixtures

We're using a hybrid approach that balances thoroughness with execution speed:
- **Page Object Model (POM)** for maintainability and reusability
- **Strategic UI testing** for critical user-facing flows (holes 1-3, 16-18)
- **API shortcuts** for repetitive middle game (holes 4-15)
- **Test fixtures** for predictable, reusable test data
- **Multiple player counts** to test 4-man and 5-man game modes

## Architecture

### Directory Structure

```
frontend/tests/e2e/
├── playwright.config.js          # Playwright configuration
├── fixtures/
│   ├── game-fixtures.js          # Test data (player names, scores, etc.)
│   └── api-helpers.js            # Backend API shortcuts
├── page-objects/
│   ├── HomePage.js               # Homepage interactions
│   ├── GameCreationPage.js       # Test game creation flow
│   ├── ScorekeeperPage.js        # Scorekeeper UI interactions
│   └── GameCompletionPage.js     # Final standings/summary
├── tests/
│   ├── test-game-happy-path.spec.js    # Main full game test
│   ├── test-game-4-man.spec.js         # 4-player specific
│   ├── test-game-5-man.spec.js         # 5-player specific
│   └── test-game-shortcuts.spec.js     # Quick smoke test
└── utils/
    ├── test-helpers.js           # Common utilities
    └── assertions.js             # Custom assertions
```

## Test Flow

### Main Happy Path Test (4-man Game)

```javascript
test('complete 4-man test game from homepage to final standings', async ({ page }) => {
  // 1. Homepage Navigation
  const homePage = new HomePage(page);
  await homePage.goto();
  await homePage.clickTestGameButton();

  // 2. Game Creation
  const gameCreation = new GameCreationPage(page);
  const gameData = await gameCreation.createTestGame({
    playerCount: 4,
    courseName: 'Wing Point'
  });

  // 3. Enter Scorekeeper
  const scorekeeper = new ScorekeeperPage(page);
  await scorekeeper.verifyGameLoaded(gameData.gameId);

  // 4. Play Holes 1-3 (UI - verify critical paths)
  await scorekeeper.playHole(1, fixtures.hole1Scores);
  await scorekeeper.playHole(2, fixtures.hole2Scores);
  await scorekeeper.playHole(3, fixtures.hole3Scores);

  // 5. Complete Holes 4-15 (API - fast forward)
  await apiHelpers.completeHoles(gameData.gameId, 4, 15, fixtures.middleGameScores);
  await page.reload(); // Verify state persists

  // 6. Play Holes 16-18 (UI - test double points, Hoepfinger)
  await scorekeeper.playHole(16, fixtures.hole16Scores);
  await scorekeeper.playHole(17, fixtures.hole17Scores);
  await scorekeeper.playHole(18, fixtures.hole18Scores);

  // 7. Verify Game Completion
  const completion = new GameCompletionPage(page);
  await completion.verifyFinalStandings();
  await completion.verifyPointsBalanceToZero();
});
```

### Why This Flow?

- **Holes 1-3**: Test critical UI paths (game creation, initial scorekeeper interaction, team formation)
- **Holes 4-15**: Fast-forward via API (repetitive, same logic as holes 1-3)
- **Holes 16-18**: Test special rules (double points on 17-18, Hoepfinger phase)
- **Validation**: Verify game state persists after reload, points balance to zero

## Page Objects

### ScorekeeperPage Example

```javascript
class ScorekeeperPage {
  constructor(page) {
    this.page = page;
  }

  async playHole(holeNumber, scoreData) {
    // Enter scores for all players
    for (const [playerId, score] of Object.entries(scoreData.scores)) {
      await this.enterScore(playerId, score);
    }

    // Handle team formation (captain picks partner or goes solo)
    if (scoreData.partnership) {
      await this.selectPartner(scoreData.partnership);
    } else {
      await this.goSolo();
    }

    // Submit hole
    await this.clickCompleteHole();
    await this.verifyHoleCompleted(holeNumber);
  }

  async enterScore(playerId, score) {
    await this.page.fill(`[data-testid="score-input-${playerId}"]`, score.toString());
  }

  async selectPartner(partnership) {
    await this.page.click(`[data-testid="partner-${partnership.partner}"]`);
  }

  async goSolo() {
    await this.page.click('[data-testid="go-solo-button"]');
  }

  async clickCompleteHole() {
    await this.page.click('[data-testid="complete-hole-button"]');

    // Wait for API call to complete
    await this.page.waitForResponse(
      response => response.url().includes('/complete-hole') && response.status() === 200
    );

    // Wait for UI to update
    await this.page.waitForSelector('[data-testid="hole-completed-indicator"]');
  }

  async verifyHoleCompleted(holeNumber) {
    await expect(this.page.locator('[data-testid="current-hole"]'))
      .toHaveText((holeNumber + 1).toString());
  }

  async verifyGameLoaded(gameId) {
    // Wait for game state to load
    await this.page.waitForFunction(
      (id) => window.localStorage.getItem('wgp_current_game') === id,
      gameId,
      { timeout: 10000 }
    );
  }
}
```

## Test Fixtures

### Game Data Structure

```javascript
// fixtures/game-fixtures.js
export const testGames = {
  standard4Man: {
    playerCount: 4,
    courseName: 'Wing Point',
    players: [
      { id: 'test-player-1', name: 'Test Player 1', handicap: 18 },
      { id: 'test-player-2', name: 'Test Player 2', handicap: 15 },
      { id: 'test-player-3', name: 'Test Player 3', handicap: 12 },
      { id: 'test-player-4', name: 'Test Player 4', handicap: 20 }
    ],
    holes: {
      // Hole 1 - Simple partnership
      1: {
        scores: {
          'test-player-1': 4,
          'test-player-2': 5,
          'test-player-3': 6,
          'test-player-4': 7
        },
        captain: 'test-player-1',
        partnership: {
          captain: 'test-player-1',
          partner: 'test-player-2'
        },
        expectedPoints: {
          'test-player-1': 3,
          'test-player-2': 3,
          'test-player-3': -3,
          'test-player-4': -3
        }
      },
      // Hole 2 - Captain goes solo
      2: {
        scores: {
          'test-player-1': 3,
          'test-player-2': 5,
          'test-player-3': 5,
          'test-player-4': 6
        },
        captain: 'test-player-2',
        solo: true,
        expectedPoints: {
          'test-player-1': -3,
          'test-player-2': 9,
          'test-player-3': -3,
          'test-player-4': -3
        }
      },
      // Hole 17 - Hoepfinger (2x points)
      17: {
        scores: { /* ... */ },
        captain: 'test-player-4',
        hoepfinger: true,
        joesSpecialWager: 8,
        doublePoints: true
      },
      // Hole 18 - Final hole (2x points)
      18: {
        scores: { /* ... */ },
        captain: 'test-player-1',
        doublePoints: true
      }
      // ... holes 3-16 defined similarly
    }
  },

  standard5Man: {
    playerCount: 5,
    // 5-player specific data with Aardvark mechanics
    holes: {
      1: {
        scores: { /* 5 players */ },
        captain: 'test-player-1',
        partnership: { captain: 'test-player-1', partner: 'test-player-2' },
        aardvark_requested_team: 'team1',
        aardvark_tossed: false
      }
      // ... 5-man specific holes
    }
  }
};
```

### API Helpers

```javascript
// fixtures/api-helpers.js
export class APIHelpers {
  constructor(baseURL = 'http://localhost:8000') {
    this.baseURL = baseURL;
  }

  async completeHoles(gameId, startHole, endHole, scoresData) {
    for (let hole = startHole; hole <= endHole; hole++) {
      const holeData = scoresData[hole];

      await fetch(`${this.baseURL}/games/${gameId}/complete-hole`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          hole_number: hole,
          scores: holeData.scores,
          captain_id: holeData.captain,
          partner_id: holeData.partnership?.partner || null,
          solo: holeData.solo || false,
          float_invoked_by: holeData.floatInvokedBy || null,
          option_invoked_by: holeData.optionInvokedBy || null,
          joes_special_wager: holeData.joesSpecialWager || null
        })
      });
    }
  }

  async deleteGame(gameId) {
    await fetch(`${this.baseURL}/games/${gameId}`, {
      method: 'DELETE'
    });
  }
}
```

## Reliability & Error Handling

### Playwright Configuration

```javascript
// playwright.config.js
export default {
  testDir: './tests/e2e',
  timeout: 120000, // 2 minutes per test
  retries: 2, // Retry flaky tests
  workers: 1, // Run tests serially (avoid port conflicts)

  use: {
    baseURL: 'http://localhost:3000',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
    trace: 'retain-on-failure'
  },

  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] }
    }
  ],

  webServer: [
    {
      command: 'cd backend && uvicorn app.main:app --reload',
      port: 8000,
      timeout: 120000,
      reuseExistingServer: !process.env.CI
    },
    {
      command: 'cd frontend && npm start',
      port: 3000,
      timeout: 120000,
      reuseExistingServer: !process.env.CI
    }
  ],

  reporter: [
    ['html', { outputFolder: 'playwright-report' }],
    ['junit', { outputFile: 'test-results/junit.xml' }],
    ['list']
  ]
};
```

### Waiting Strategies

**Always use explicit waits, never arbitrary sleeps:**

```javascript
// ✅ Good - Wait for specific condition
await page.waitForResponse(
  response => response.url().includes('/complete-hole') && response.status() === 200
);

// ✅ Good - Wait for element state
await page.waitForSelector('[data-testid="hole-completed"]', { state: 'visible' });

// ✅ Good - Wait for function
await page.waitForFunction(
  () => document.querySelector('[data-testid="total-points"]').textContent !== '0'
);

// ❌ Bad - Arbitrary timeout
await page.waitForTimeout(3000);
```

### Test Cleanup

```javascript
// utils/test-helpers.js
export async function cleanupTestGame(page, gameId) {
  // Cleanup localStorage
  await page.evaluate(() => {
    localStorage.removeItem('wgp_current_game');
    Object.keys(localStorage)
      .filter(key => key.startsWith('wgp_session_'))
      .forEach(key => localStorage.removeItem(key));
  });

  // Optional: Delete test game from backend
  const apiHelpers = new APIHelpers();
  await apiHelpers.deleteGame(gameId);
}

// In test file
let currentGameId;

test.afterEach(async ({ page }) => {
  if (currentGameId) {
    await cleanupTestGame(page, currentGameId);
  }
});
```

### Custom Assertions

```javascript
// utils/assertions.js
export async function assertPointsBalanceToZero(page) {
  const playerPoints = await page.locator('[data-testid="player-points"]').allTextContents();
  const total = playerPoints
    .map(pts => parseInt(pts))
    .reduce((sum, pts) => sum + pts, 0);

  expect(total).toBe(0); // Zero-sum game validation
}

export async function assertHoleHistory(page, expectedHoleCount) {
  const holes = await page.locator('[data-testid="hole-history-row"]').count();
  expect(holes).toBe(expectedHoleCount);
}

export async function assertGameCompleted(page) {
  await expect(page.locator('[data-testid="game-status"]'))
    .toHaveText('Completed');

  await expect(page.locator('[data-testid="final-standings"]'))
    .toBeVisible();
}
```

## Test Execution

### Local Development

```bash
# Run all E2E tests
npm run test:e2e

# Run with UI (interactive mode)
npm run test:e2e:ui

# Run in debug mode (step through)
npm run test:e2e:debug

# Run in headed mode (see browser)
npm run test:e2e:headed

# View HTML report
npm run test:e2e:report
```

### Test Organization by Speed

```javascript
// tests/test-game-happy-path.spec.js
test.describe('Full Game E2E Tests', () => {
  test.describe.configure({ mode: 'serial' });

  test('4-man game - full 18 holes @slow', async ({ page }) => {
    // Full UI test - takes ~3-5 minutes
  });

  test('5-man game - full 18 holes @slow', async ({ page }) => {
    // Full UI test with Aardvark mechanics - takes ~4-6 minutes
  });
});

// tests/test-game-shortcuts.spec.js
test.describe('Quick Smoke Tests', () => {
  test('4-man game - quick validation @smoke', async ({ page }) => {
    // First 3 holes UI, rest via API - takes ~30 seconds
  });

  test('5-man game - quick validation @smoke', async ({ page }) => {
    // First 3 holes UI with Aardvark, rest via API - takes ~45 seconds
  });
});
```

### Running Specific Tests

```bash
# Run only smoke tests
npm run test:e2e -- --grep @smoke

# Run only slow tests
npm run test:e2e -- --grep @slow

# Run specific test file
npm run test:e2e -- test-game-4-man.spec.js
```

## CI/CD Integration

### GitHub Actions Workflow

```yaml
# .github/workflows/e2e-tests.yml
name: E2E Tests

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  e2e:
    runs-on: ubuntu-latest
    timeout-minutes: 30

    steps:
      - uses: actions/checkout@v3

      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'
          cache: 'npm'
          cache-dependency-path: frontend/package-lock.json

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
          cache: 'pip'

      - name: Install backend dependencies
        run: |
          cd backend
          pip install -r requirements.txt

      - name: Install frontend dependencies
        run: |
          cd frontend
          npm ci

      - name: Install Playwright
        run: |
          cd frontend
          npx playwright install --with-deps chromium

      - name: Run smoke tests (PR)
        if: github.event_name == 'pull_request'
        run: |
          cd frontend
          npm run test:e2e -- --grep @smoke

      - name: Run full E2E tests (main branch)
        if: github.ref == 'refs/heads/main'
        run: |
          cd frontend
          npm run test:e2e

      - name: Upload test results
        uses: actions/upload-artifact@v3
        if: always()
        with:
          name: playwright-report
          path: frontend/playwright-report/
          retention-days: 30

      - name: Upload test videos
        uses: actions/upload-artifact@v3
        if: failure()
        with:
          name: playwright-videos
          path: frontend/test-results/
          retention-days: 7
```

### Strategy

- **Pull Requests**: Run smoke tests only (~1-2 minutes) for fast feedback
- **Main Branch**: Run full test suite (~10-15 minutes) for comprehensive validation
- **Artifacts**: Save HTML reports always, videos/screenshots only on failure

## Success Criteria

### Test Coverage

- ✅ Homepage navigation to test game mode
- ✅ Test game creation with 4 and 5 players
- ✅ Game state persistence (localStorage + backend)
- ✅ Score entry and validation
- ✅ Team formation (partnerships and solo)
- ✅ Special rules (Float, Option, Hoepfinger, double points)
- ✅ 5-man mechanics (Aardvark team selection)
- ✅ Game completion and final standings
- ✅ Zero-sum point validation

### Performance Targets

- **Smoke test**: < 1 minute execution time
- **Full 4-man test**: < 5 minutes execution time
- **Full 5-man test**: < 6 minutes execution time
- **CI/CD smoke tests**: < 2 minutes total (including setup)
- **CI/CD full tests**: < 15 minutes total

### Reliability Targets

- **Flakiness**: < 1% test failure rate on main branch
- **Retry success**: 90%+ of flaky tests pass on first retry
- **Zero sleeps**: All waits are condition-based

## Implementation Timeline

1. **Phase 1: Setup & Infrastructure** (1-2 hours)
   - Configure Playwright
   - Create directory structure
   - Set up basic page objects

2. **Phase 2: Test Fixtures** (2-3 hours)
   - Define 4-man and 5-man game fixtures
   - Build API helper utilities
   - Create custom assertions

3. **Phase 3: 4-Man Happy Path** (3-4 hours)
   - Implement HomePage and GameCreationPage
   - Build ScorekeeperPage with full interactions
   - Write complete 4-man test

4. **Phase 4: 5-Man Game Support** (2-3 hours)
   - Extend fixtures for Aardvark mechanics
   - Add 5-man specific page object methods
   - Write complete 5-man test

5. **Phase 5: Smoke Tests & CI/CD** (1-2 hours)
   - Create fast smoke test variants
   - Set up GitHub Actions workflow
   - Verify CI/CD execution

**Total Estimated Effort**: 9-14 hours

## Future Enhancements

### Additional Test Scenarios (Out of Scope for Initial Implementation)

- **Special Rules Combinations**: Test Float + Option on same hole, Duncan mechanics
- **Error Scenarios**: Invalid scores, network failures, concurrent access
- **Browser Compatibility**: Test on Firefox, Safari, mobile browsers
- **Accessibility**: Test keyboard navigation, screen reader compatibility
- **Performance**: Load testing, stress testing with multiple concurrent games
- **6-Man Games**: When 6-player support is implemented

### Test Data Variations

- Different score patterns (ties, large margins, close games)
- Different partnership strategies (always solo, always partner, mixed)
- Edge cases (hole-in-one, maximum scores, push scenarios)

## References

- GitHub Issue: #118
- Playwright Documentation: https://playwright.dev/
- Backend API: `/games/create-test` endpoint
- Frontend: `HomePage.js`, `SimpleScorekeeper.jsx`

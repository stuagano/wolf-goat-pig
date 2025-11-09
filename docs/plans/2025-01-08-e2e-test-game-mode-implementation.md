# E2E Test Game Mode Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implement comprehensive Playwright E2E tests for the test game mode, covering the full user journey from homepage through 18-hole game completion.

**Architecture:** Hybrid approach using Page Object Model for maintainability, strategic UI testing for critical paths (holes 1-3, 16-18), API shortcuts for middle game (holes 4-15), and reusable test fixtures.

**Tech Stack:** Playwright 1.56.1, JavaScript, Node.js, FastAPI backend

---

## Task 1: Playwright Configuration & Directory Structure

**Files:**
- Create: `frontend/tests/e2e/playwright.config.js`
- Create: `frontend/tests/e2e/fixtures/.gitkeep`
- Create: `frontend/tests/e2e/page-objects/.gitkeep`
- Create: `frontend/tests/e2e/tests/.gitkeep`
- Create: `frontend/tests/e2e/utils/.gitkeep`
- Modify: `frontend/package.json`

**Step 1: Create Playwright configuration**

Create `frontend/tests/e2e/playwright.config.js`:

```javascript
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './tests',
  timeout: 120000, // 2 minutes per test
  retries: 2,
  workers: 1, // Run serially to avoid port conflicts

  use: {
    baseURL: 'http://localhost:3000',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
    trace: 'retain-on-failure',
  },

  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],

  webServer: [
    {
      command: 'cd ../../backend && uvicorn app.main:app --reload',
      port: 8000,
      timeout: 120000,
      reuseExistingServer: !process.env.CI,
    },
    {
      command: 'cd .. && npm start',
      port: 3000,
      timeout: 120000,
      reuseExistingServer: !process.env.CI,
    },
  ],

  reporter: [
    ['html', { outputFolder: 'playwright-report' }],
    ['junit', { outputFile: 'test-results/junit.xml' }],
    ['list'],
  ],
});
```

**Step 2: Create directory structure**

```bash
mkdir -p frontend/tests/e2e/{fixtures,page-objects,tests,utils}
touch frontend/tests/e2e/fixtures/.gitkeep
touch frontend/tests/e2e/page-objects/.gitkeep
touch frontend/tests/e2e/tests/.gitkeep
touch frontend/tests/e2e/utils/.gitkeep
```

**Step 3: Add npm scripts**

Modify `frontend/package.json` - add to "scripts" section:

```json
{
  "scripts": {
    "test:e2e": "playwright test",
    "test:e2e:ui": "playwright test --ui",
    "test:e2e:debug": "playwright test --debug",
    "test:e2e:headed": "playwright test --headed",
    "test:e2e:report": "playwright show-report"
  }
}
```

**Step 4: Verify Playwright is installed**

Run: `cd frontend && npm list @playwright/test`
Expected: Should show version 1.56.1

**Step 5: Commit**

```bash
git add frontend/tests/e2e frontend/package.json
git commit -m "feat(e2e): add Playwright configuration and directory structure

- Configure Playwright with webServer for backend/frontend
- Create directory structure for page objects, fixtures, tests, utils
- Add npm scripts for E2E test execution
- Set 2 minute timeout, 2 retries, serial execution"
```

---

## Task 2: Test Fixtures & API Helpers

**Files:**
- Create: `frontend/tests/e2e/fixtures/game-fixtures.js`
- Create: `frontend/tests/e2e/fixtures/api-helpers.js`

**Step 1: Create 4-man game fixtures**

Create `frontend/tests/e2e/fixtures/game-fixtures.js`:

```javascript
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
      3: {
        scores: {
          'test-player-1': 5,
          'test-player-2': 4,
          'test-player-3': 5,
          'test-player-4': 6
        },
        captain: 'test-player-3',
        partnership: {
          captain: 'test-player-3',
          partner: 'test-player-4'
        },
        expectedPoints: {
          'test-player-1': -3,
          'test-player-2': -3,
          'test-player-3': 3,
          'test-player-4': 3
        }
      },
      // Middle holes (4-15) - will be completed via API
      4: { scores: { 'test-player-1': 4, 'test-player-2': 5, 'test-player-3': 5, 'test-player-4': 6 }, captain: 'test-player-4', solo: true },
      5: { scores: { 'test-player-1': 5, 'test-player-2': 4, 'test-player-3': 6, 'test-player-4': 5 }, captain: 'test-player-1', partnership: { captain: 'test-player-1', partner: 'test-player-3' } },
      6: { scores: { 'test-player-1': 4, 'test-player-2': 5, 'test-player-3': 5, 'test-player-4': 6 }, captain: 'test-player-2', solo: true },
      7: { scores: { 'test-player-1': 6, 'test-player-2': 4, 'test-player-3': 5, 'test-player-4': 5 }, captain: 'test-player-3', partnership: { captain: 'test-player-3', partner: 'test-player-1' } },
      8: { scores: { 'test-player-1': 4, 'test-player-2': 5, 'test-player-3': 6, 'test-player-4': 5 }, captain: 'test-player-4', partnership: { captain: 'test-player-4', partner: 'test-player-2' } },
      9: { scores: { 'test-player-1': 5, 'test-player-2': 4, 'test-player-3': 5, 'test-player-4': 6 }, captain: 'test-player-1', solo: true },
      10: { scores: { 'test-player-1': 4, 'test-player-2': 5, 'test-player-3': 6, 'test-player-4': 5 }, captain: 'test-player-2', partnership: { captain: 'test-player-2', partner: 'test-player-4' } },
      11: { scores: { 'test-player-1': 5, 'test-player-2': 4, 'test-player-3': 5, 'test-player-4': 6 }, captain: 'test-player-3', solo: true },
      12: { scores: { 'test-player-1': 4, 'test-player-2': 6, 'test-player-3': 5, 'test-player-4': 5 }, captain: 'test-player-4', partnership: { captain: 'test-player-4', partner: 'test-player-3' } },
      13: { scores: { 'test-player-1': 5, 'test-player-2': 4, 'test-player-3': 6, 'test-player-4': 5 }, captain: 'test-player-1', partnership: { captain: 'test-player-1', partner: 'test-player-2' } },
      14: { scores: { 'test-player-1': 4, 'test-player-2': 5, 'test-player-3': 5, 'test-player-4': 6 }, captain: 'test-player-2', solo: true },
      15: { scores: { 'test-player-1': 5, 'test-player-2': 4, 'test-player-3': 6, 'test-player-4': 5 }, captain: 'test-player-3', partnership: { captain: 'test-player-3', partner: 'test-player-4' } },
      // Final holes (16-18) - UI testing for special rules
      16: {
        scores: {
          'test-player-1': 4,
          'test-player-2': 5,
          'test-player-3': 6,
          'test-player-4': 5
        },
        captain: 'test-player-4',
        partnership: {
          captain: 'test-player-4',
          partner: 'test-player-1'
        }
      },
      17: {
        scores: {
          'test-player-1': 3,
          'test-player-2': 5,
          'test-player-3': 5,
          'test-player-4': 6
        },
        captain: 'test-player-1',
        hoepfinger: true,
        joesSpecialWager: 8,
        doublePoints: true // Hole 17 has 2x points
      },
      18: {
        scores: {
          'test-player-1': 4,
          'test-player-2': 5,
          'test-player-3': 5,
          'test-player-4': 6
        },
        captain: 'test-player-2',
        solo: true,
        doublePoints: true // Hole 18 has 2x points
      }
    }
  }
};
```

**Step 2: Create API helper utilities**

Create `frontend/tests/e2e/fixtures/api-helpers.js`:

```javascript
export class APIHelpers {
  constructor(baseURL = 'http://localhost:8000') {
    this.baseURL = baseURL;
  }

  async completeHoles(gameId, startHole, endHole, holesData) {
    for (let hole = startHole; hole <= endHole; hole++) {
      const holeData = holesData[hole];
      if (!holeData) continue;

      const response = await fetch(`${this.baseURL}/games/${gameId}/complete-hole`, {
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
          joes_special_wager: holeData.joesSpecialWager || null,
          hole_par: 4 // Default par
        })
      });

      if (!response.ok) {
        throw new Error(`Failed to complete hole ${hole}: ${response.statusText}`);
      }
    }
  }

  async deleteGame(gameId) {
    await fetch(`${this.baseURL}/games/${gameId}`, {
      method: 'DELETE'
    });
  }

  async createTestGame(playerCount = 4, courseName = 'Wing Point') {
    const response = await fetch(`${this.baseURL}/games/create-test`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        player_count: playerCount,
        course_name: courseName
      })
    });

    if (!response.ok) {
      throw new Error(`Failed to create test game: ${response.statusText}`);
    }

    return response.json();
  }
}
```

**Step 3: Commit**

```bash
git add frontend/tests/e2e/fixtures/
git commit -m "feat(e2e): add test fixtures and API helpers

- Add 4-man game fixtures with all 18 holes
- Include expected scores, partnerships, and points for validation
- Add API helper class for fast-forwarding holes and game cleanup
- Support Hoepfinger and double points on holes 17-18"
```

---

## Task 3: Custom Assertions & Test Helpers

**Files:**
- Create: `frontend/tests/e2e/utils/assertions.js`
- Create: `frontend/tests/e2e/utils/test-helpers.js`

**Step 1: Create custom assertions**

Create `frontend/tests/e2e/utils/assertions.js`:

```javascript
import { expect } from '@playwright/test';

export async function assertPointsBalanceToZero(page) {
  const playerPoints = await page.locator('[data-testid="player-points"]').allTextContents();
  const total = playerPoints
    .map(pts => parseInt(pts.replace(/[^0-9-]/g, '')))
    .reduce((sum, pts) => sum + pts, 0);

  expect(total).toBe(0);
}

export async function assertHoleHistory(page, expectedHoleCount) {
  const holes = await page.locator('[data-testid="hole-history-row"]').count();
  expect(holes).toBe(expectedHoleCount);
}

export async function assertGameCompleted(page) {
  await expect(page.locator('[data-testid="game-status"]'))
    .toHaveText(/completed/i);

  await expect(page.locator('[data-testid="final-standings"]'))
    .toBeVisible();
}

export async function assertPlayerPoints(page, expectedPoints) {
  for (const [playerId, expectedPts] of Object.entries(expectedPoints)) {
    const actualPts = await page.locator(`[data-testid="player-${playerId}-points"]`).textContent();
    const points = parseInt(actualPts.replace(/[^0-9-]/g, ''));
    expect(points).toBe(expectedPts);
  }
}
```

**Step 2: Create test helper utilities**

Create `frontend/tests/e2e/utils/test-helpers.js`:

```javascript
import { APIHelpers } from '../fixtures/api-helpers.js';

export async function cleanupTestGame(page, gameId) {
  if (!gameId) return;

  // Cleanup localStorage
  await page.evaluate(() => {
    localStorage.removeItem('wgp_current_game');
    Object.keys(localStorage)
      .filter(key => key.startsWith('wgp_session_'))
      .forEach(key => localStorage.removeItem(key));
  });

  // Delete test game from backend
  const apiHelpers = new APIHelpers();
  try {
    await apiHelpers.deleteGame(gameId);
  } catch (error) {
    console.warn(`Failed to delete test game ${gameId}:`, error.message);
  }
}

export async function waitForGameState(page, gameId, timeout = 10000) {
  await page.waitForFunction(
    (id) => window.localStorage.getItem('wgp_current_game') === id,
    gameId,
    { timeout }
  );
}

export async function waitForHoleCompletion(page, holeNumber) {
  // Wait for API response
  await page.waitForResponse(
    response => response.url().includes('/complete-hole') && response.status() === 200,
    { timeout: 10000 }
  );

  // Wait for UI to update to next hole
  await page.waitForSelector(`[data-testid="current-hole"][data-hole="${holeNumber + 1}"]`, {
    timeout: 5000
  });
}
```

**Step 3: Commit**

```bash
git add frontend/tests/e2e/utils/
git commit -m "feat(e2e): add custom assertions and test helpers

- Add custom assertions for zero-sum validation, hole history, game completion
- Add test helpers for cleanup, waiting strategies, and state verification
- Use condition-based waits instead of arbitrary timeouts"
```

---

## Task 4: HomePage Page Object

**Files:**
- Create: `frontend/tests/e2e/page-objects/HomePage.js`

**Step 1: Create HomePage page object**

Create `frontend/tests/e2e/page-objects/HomePage.js`:

```javascript
export class HomePage {
  constructor(page) {
    this.page = page;
  }

  async goto() {
    await this.page.goto('/');
    await this.page.waitForLoadState('networkidle');
  }

  async clickMultiplayerGame() {
    await this.page.click('text=/Create Game/i');
  }

  async clickPracticeMode() {
    await this.page.click('text=/Start Practice/i');
  }

  async clickTestGame() {
    // Open hamburger menu
    await this.page.click('button:has-text("☰")');

    // Click "Test Multiplayer (Dev)" menu item
    await this.page.click('text=/Test Multiplayer/i');
  }

  async verifyHomepageLoaded() {
    await this.page.waitForSelector('text=/Wolf Goat Pig/i');
    await this.page.waitForSelector('text=/Multiplayer Game/i');
  }
}
```

**Step 2: Commit**

```bash
git add frontend/tests/e2e/page-objects/HomePage.js
git commit -m "feat(e2e): add HomePage page object

- Add methods for navigation to different game modes
- Support hamburger menu interaction for test game mode
- Include homepage load verification"
```

---

## Task 5: GameCreationPage Page Object

**Files:**
- Create: `frontend/tests/e2e/page-objects/GameCreationPage.js`

**Step 1: Create GameCreationPage page object**

Create `frontend/tests/e2e/page-objects/GameCreationPage.js`:

```javascript
export class GameCreationPage {
  constructor(page) {
    this.page = page;
  }

  async createTestGame(options = {}) {
    const { playerCount = 4, courseName = 'Wing Point' } = options;

    // Wait for test game creation page to load
    await this.page.waitForSelector('[data-testid="create-test-game-button"]', {
      timeout: 10000
    });

    // Select player count if dropdown exists
    const playerCountSelector = await this.page.$('[data-testid="player-count-select"]');
    if (playerCountSelector) {
      await this.page.selectOption('[data-testid="player-count-select"]', playerCount.toString());
    }

    // Select course if dropdown exists
    const courseSelector = await this.page.$('[data-testid="course-select"]');
    if (courseSelector) {
      await this.page.selectOption('[data-testid="course-select"]', courseName);
    }

    // Click create button
    await this.page.click('[data-testid="create-test-game-button"]');

    // Wait for game to be created and redirected
    await this.page.waitForURL(/\/game\/.+/, { timeout: 15000 });

    // Extract game ID from URL
    const url = this.page.url();
    const gameId = url.match(/\/game\/([^\/]+)/)?.[1];

    if (!gameId) {
      throw new Error('Failed to extract game ID from URL');
    }

    return {
      gameId,
      playerCount,
      courseName
    };
  }

  async verifyGameCreated(gameId) {
    await this.page.waitForSelector(`[data-testid="game-id"][data-game="${gameId}"]`, {
      timeout: 5000
    });
  }
}
```

**Step 2: Commit**

```bash
git add frontend/tests/e2e/page-objects/GameCreationPage.js
git commit -m "feat(e2e): add GameCreationPage page object

- Add createTestGame method with player count and course selection
- Extract game ID from URL after creation
- Add verification for successful game creation"
```

---

## Task 6: ScorekeeperPage Page Object

**Files:**
- Create: `frontend/tests/e2e/page-objects/ScorekeeperPage.js`

**Step 1: Create ScorekeeperPage page object**

Create `frontend/tests/e2e/page-objects/ScorekeeperPage.js`:

```javascript
import { waitForHoleCompletion } from '../utils/test-helpers.js';

export class ScorekeeperPage {
  constructor(page) {
    this.page = page;
  }

  async verifyGameLoaded(gameId) {
    await this.page.waitForFunction(
      (id) => window.localStorage.getItem('wgp_current_game') === id,
      gameId,
      { timeout: 10000 }
    );

    await this.page.waitForSelector('[data-testid="scorekeeper-container"]', {
      timeout: 10000
    });
  }

  async playHole(holeNumber, scoreData) {
    // Verify we're on the correct hole
    await this.page.waitForSelector(`[data-testid="current-hole"]`, {
      timeout: 5000
    });

    const currentHole = await this.page.locator('[data-testid="current-hole"]').textContent();
    if (parseInt(currentHole) !== holeNumber) {
      throw new Error(`Expected hole ${holeNumber}, but on hole ${currentHole}`);
    }

    // Enter scores for all players
    for (const [playerId, score] of Object.entries(scoreData.scores)) {
      await this.enterScore(playerId, score);
    }

    // Handle team formation
    if (scoreData.solo) {
      await this.goSolo();
    } else if (scoreData.partnership) {
      await this.selectPartner(scoreData.partnership.partner);
    }

    // Handle special rules
    if (scoreData.floatInvokedBy) {
      await this.invokeFloat(scoreData.floatInvokedBy);
    }

    if (scoreData.joesSpecialWager) {
      await this.setJoesSpecialWager(scoreData.joesSpecialWager);
    }

    // Complete hole
    await this.clickCompleteHole();
    await waitForHoleCompletion(this.page, holeNumber);
  }

  async enterScore(playerId, score) {
    const selector = `[data-testid="score-input-${playerId}"]`;
    await this.page.fill(selector, score.toString());
  }

  async selectPartner(partnerId) {
    await this.page.click(`[data-testid="partner-${partnerId}"]`);
  }

  async goSolo() {
    await this.page.click('[data-testid="go-solo-button"]');
  }

  async invokeFloat(playerId) {
    await this.page.click(`[data-testid="float-button-${playerId}"]`);
  }

  async setJoesSpecialWager(wager) {
    await this.page.fill('[data-testid="joes-special-wager-input"]', wager.toString());
  }

  async clickCompleteHole() {
    await this.page.click('[data-testid="complete-hole-button"]');
  }

  async verifyHoleCompleted(holeNumber) {
    const nextHole = holeNumber + 1;
    await this.page.waitForSelector(`[data-testid="current-hole"]`, {
      timeout: 5000
    });

    const currentHole = await this.page.locator('[data-testid="current-hole"]').textContent();
    if (parseInt(currentHole) !== nextHole) {
      throw new Error(`Expected to advance to hole ${nextHole}, but on hole ${currentHole}`);
    }
  }

  async getCurrentHole() {
    const holeText = await this.page.locator('[data-testid="current-hole"]').textContent();
    return parseInt(holeText);
  }

  async getPlayerPoints(playerId) {
    const pointsText = await this.page.locator(`[data-testid="player-${playerId}-points"]`).textContent();
    return parseInt(pointsText.replace(/[^0-9-]/g, ''));
  }
}
```

**Step 2: Commit**

```bash
git add frontend/tests/e2e/page-objects/ScorekeeperPage.js
git commit -m "feat(e2e): add ScorekeeperPage page object

- Add playHole method for complete hole workflow (scores, teams, submit)
- Support solo, partnership, and special rules (Float, Joe's Special)
- Add score entry, team selection, and hole completion methods
- Include verification for hole advancement and current state"
```

---

## Task 7: GameCompletionPage Page Object

**Files:**
- Create: `frontend/tests/e2e/page-objects/GameCompletionPage.js`

**Step 1: Create GameCompletionPage page object**

Create `frontend/tests/e2e/page-objects/GameCompletionPage.js`:

```javascript
import { assertPointsBalanceToZero, assertGameCompleted } from '../utils/assertions.js';

export class GameCompletionPage {
  constructor(page) {
    this.page = page;
  }

  async verifyFinalStandings() {
    await this.page.waitForSelector('[data-testid="final-standings"]', {
      timeout: 10000
    });

    await assertGameCompleted(this.page);
  }

  async verifyPointsBalanceToZero() {
    await assertPointsBalanceToZero(this.page);
  }

  async getFinalStandings() {
    const standings = [];
    const playerRows = await this.page.locator('[data-testid="player-standing-row"]').all();

    for (const row of playerRows) {
      const name = await row.locator('[data-testid="player-name"]').textContent();
      const points = await row.locator('[data-testid="player-total-points"]').textContent();

      standings.push({
        name: name.trim(),
        points: parseInt(points.replace(/[^0-9-]/g, ''))
      });
    }

    return standings;
  }

  async verifyWinner(expectedWinnerName) {
    const standings = await this.getFinalStandings();
    const winner = standings[0]; // Assuming sorted by points descending

    if (winner.name !== expectedWinnerName) {
      throw new Error(`Expected winner ${expectedWinnerName}, but got ${winner.name}`);
    }
  }

  async verifyGameStatus() {
    const status = await this.page.locator('[data-testid="game-status"]').textContent();
    return status.toLowerCase().includes('completed');
  }
}
```

**Step 2: Commit**

```bash
git add frontend/tests/e2e/page-objects/GameCompletionPage.js
git commit -m "feat(e2e): add GameCompletionPage page object

- Add final standings verification
- Support zero-sum point validation
- Include methods to get standings and verify winner
- Add game completion status check"
```

---

## Task 8: 4-Man Happy Path Test (Holes 1-3 UI)

**Files:**
- Create: `frontend/tests/e2e/tests/test-game-4-man.spec.js`

**Step 1: Write the test structure**

Create `frontend/tests/e2e/tests/test-game-4-man.spec.js`:

```javascript
import { test, expect } from '@playwright/test';
import { HomePage } from '../page-objects/HomePage.js';
import { GameCreationPage } from '../page-objects/GameCreationPage.js';
import { ScorekeeperPage } from '../page-objects/ScorekeeperPage.js';
import { GameCompletionPage } from '../page-objects/GameCompletionPage.js';
import { testGames } from '../fixtures/game-fixtures.js';
import { APIHelpers } from '../fixtures/api-helpers.js';
import { cleanupTestGame } from '../utils/test-helpers.js';

test.describe('4-Man Test Game - Full Happy Path', () => {
  let currentGameId;

  test.afterEach(async ({ page }) => {
    await cleanupTestGame(page, currentGameId);
  });

  test('complete 4-man test game from homepage to final standings', async ({ page }) => {
    const fixture = testGames.standard4Man;
    const apiHelpers = new APIHelpers();

    // 1. Homepage Navigation
    const homePage = new HomePage(page);
    await homePage.goto();
    await homePage.verifyHomepageLoaded();
    await homePage.clickTestGame();

    // 2. Game Creation
    const gameCreation = new GameCreationPage(page);
    const gameData = await gameCreation.createTestGame({
      playerCount: 4,
      courseName: 'Wing Point'
    });
    currentGameId = gameData.gameId;

    // 3. Enter Scorekeeper
    const scorekeeper = new ScorekeeperPage(page);
    await scorekeeper.verifyGameLoaded(gameData.gameId);

    // 4. Play Holes 1-3 (UI - verify critical paths)
    await scorekeeper.playHole(1, fixture.holes[1]);
    await scorekeeper.verifyHoleCompleted(1);

    await scorekeeper.playHole(2, fixture.holes[2]);
    await scorekeeper.verifyHoleCompleted(2);

    await scorekeeper.playHole(3, fixture.holes[3]);
    await scorekeeper.verifyHoleCompleted(3);

    // 5. Complete Holes 4-15 (API - fast forward)
    await apiHelpers.completeHoles(gameData.gameId, 4, 15, fixture.holes);

    // 6. Reload page to verify state persists
    await page.reload();
    await scorekeeper.verifyGameLoaded(gameData.gameId);

    // Verify we're on hole 16
    const currentHole = await scorekeeper.getCurrentHole();
    expect(currentHole).toBe(16);

    // 7. Play Holes 16-18 (UI - test double points, Hoepfinger)
    await scorekeeper.playHole(16, fixture.holes[16]);
    await scorekeeper.verifyHoleCompleted(16);

    await scorekeeper.playHole(17, fixture.holes[17]);
    await scorekeeper.verifyHoleCompleted(17);

    await scorekeeper.playHole(18, fixture.holes[18]);

    // 8. Verify Game Completion
    const completion = new GameCompletionPage(page);
    await completion.verifyFinalStandings();
    await completion.verifyPointsBalanceToZero();

    const isCompleted = await completion.verifyGameStatus();
    expect(isCompleted).toBe(true);
  });
});
```

**Step 2: Run test to verify it fails (expected - need data-testid attributes)**

Run: `cd frontend && npm run test:e2e -- test-game-4-man.spec.js`
Expected: FAIL - selectors not found (need to add data-testid attributes to components)

**Step 3: Document what data-testid attributes are needed**

The test will fail because the UI components don't have the required `data-testid` attributes. Here's what needs to be added to the frontend components:

**Required in `HomePage.js`:**
- Hamburger menu button
- "Test Multiplayer (Dev)" menu item

**Required in test game creation flow:**
- `data-testid="create-test-game-button"`
- `data-testid="player-count-select"` (if exists)
- `data-testid="course-select"` (if exists)

**Required in `SimpleScorekeeper.jsx`:**
- `data-testid="scorekeeper-container"`
- `data-testid="current-hole"`
- `data-testid="score-input-{playerId}"`
- `data-testid="partner-{partnerId}"`
- `data-testid="go-solo-button"`
- `data-testid="complete-hole-button"`
- `data-testid="player-{playerId}-points"`
- `data-testid="float-button-{playerId}"` (if exists)
- `data-testid="joes-special-wager-input"` (if exists)

**Required in game completion view:**
- `data-testid="final-standings"`
- `data-testid="game-status"`
- `data-testid="player-standing-row"`
- `data-testid="player-name"`
- `data-testid="player-total-points"`
- `data-testid="player-points"`

**Step 4: Commit test (even though it fails - we'll fix UI next)**

```bash
git add frontend/tests/e2e/tests/test-game-4-man.spec.js
git commit -m "test(e2e): add 4-man happy path test (WIP - needs UI data-testid)

- Add complete 18-hole test from homepage to game completion
- Test holes 1-3 and 16-18 via UI, holes 4-15 via API
- Verify game state persistence after reload
- Verify zero-sum points and game completion

Note: Test will fail until data-testid attributes added to UI components"
```

---

## Task 9: Add data-testid Attributes to UI Components

**Files:**
- Modify: `frontend/src/components/game/SimpleScorekeeper.jsx`
- Modify: `frontend/src/pages/HomePage.js`

**Step 1: Add data-testid to SimpleScorekeeper**

Modify `frontend/src/components/game/SimpleScorekeeper.jsx`:

Find the main container and add `data-testid="scorekeeper-container"`:

```jsx
<div data-testid="scorekeeper-container" style={{ /* existing styles */ }}>
```

Find the current hole display and add `data-testid="current-hole"`:

```jsx
<div data-testid="current-hole" style={{ /* existing styles */ }}>
  Hole {currentHole}
</div>
```

Find score inputs and add `data-testid` for each player:

```jsx
<input
  data-testid={`score-input-${player.id}`}
  type="number"
  // ... existing props
/>
```

Find partner selection buttons and add `data-testid`:

```jsx
<button
  data-testid={`partner-${player.id}`}
  onClick={() => handlePartnerSelect(player.id)}
  // ... existing props
>
```

Find go solo button and add `data-testid`:

```jsx
<button
  data-testid="go-solo-button"
  onClick={handleGoSolo}
  // ... existing props
>
```

Find complete hole button and add `data-testid`:

```jsx
<button
  data-testid="complete-hole-button"
  onClick={handleCompleteHole}
  // ... existing props
>
```

Find player points display and add `data-testid`:

```jsx
<div data-testid={`player-${player.id}-points`}>
  {player.points || 0}
</div>
```

**Step 2: Add data-testid to HomePage**

Modify `frontend/src/pages/HomePage.js`:

Find the hamburger menu button:

```jsx
<button
  data-testid="hamburger-menu-button"
  onClick={() => setMenuOpen(!menuOpen)}
  // ... existing props
>
```

Find the Test Multiplayer menu item:

```jsx
<button
  data-testid="test-multiplayer-menu-item"
  onClick={() => {
    navigate('/test-multiplayer');
    setMenuOpen(false);
  }}
  // ... existing props
>
```

**Step 3: Run test again to see progress**

Run: `cd frontend && npm run test:e2e -- test-game-4-man.spec.js`
Expected: Should get further, may still fail on game completion view

**Step 4: Commit UI changes**

```bash
git add frontend/src/components/game/SimpleScorekeeper.jsx frontend/src/pages/HomePage.js
git commit -m "feat(ui): add data-testid attributes for E2E testing

- Add test identifiers to SimpleScorekeeper for E2E automation
- Include score inputs, partner selection, solo button, complete hole
- Add identifiers to HomePage hamburger menu and test game navigation
- Enable reliable element selection in Playwright tests"
```

---

## Task 10: Add Game Completion UI (if missing)

**Note:** This task assumes the game completion UI exists. If it doesn't, we'll need to create it.

**Step 1: Check if game completion view exists**

Run: `grep -r "final.*standings" frontend/src/components/`
Expected: Should find components or create them

**Step 2: Add data-testid to game completion components**

If the components exist, add these `data-testid` attributes:

```jsx
<div data-testid="final-standings">
  {/* standings content */}
</div>

<div data-testid="game-status">
  {gameStatus}
</div>

{players.map(player => (
  <div key={player.id} data-testid="player-standing-row">
    <span data-testid="player-name">{player.name}</span>
    <span data-testid="player-total-points">{player.points}</span>
  </div>
))}
```

**Step 3: Commit changes**

```bash
git add frontend/src/components/game/
git commit -m "feat(ui): add data-testid to game completion view

- Add test identifiers for final standings display
- Include game status and player points for E2E validation
- Enable E2E verification of game completion"
```

---

## Task 11: Run and Debug E2E Test

**Step 1: Run test in headed mode**

Run: `cd frontend && npm run test:e2e:headed -- test-game-4-man.spec.js`
Expected: Browser opens, watch test execute

**Step 2: Debug any failures**

If test fails, run in debug mode:
Run: `npm run test:e2e:debug -- test-game-4-man.spec.js`

Common issues to check:
- Missing data-testid attributes
- Incorrect selectors
- Timing issues (add waits)
- API endpoint not responding
- Backend not running

**Step 3: Fix any issues found**

Make necessary adjustments to:
- Page objects (selectors, methods)
- Test fixtures (data)
- UI components (data-testid)

**Step 4: Run until test passes**

Run: `npm run test:e2e -- test-game-4-man.spec.js`
Expected: PASS - all assertions green

**Step 5: Commit fixes**

```bash
git add .
git commit -m "fix(e2e): resolve test failures and timing issues

- Fix selector issues in page objects
- Add missing waits for async operations
- Correct test data in fixtures
- Ensure UI components have all required test IDs"
```

---

## Task 12: Add Quick Smoke Test

**Files:**
- Create: `frontend/tests/e2e/tests/test-game-smoke.spec.js`

**Step 1: Create smoke test**

Create `frontend/tests/e2e/tests/test-game-smoke.spec.js`:

```javascript
import { test, expect } from '@playwright/test';
import { HomePage } from '../page-objects/HomePage.js';
import { GameCreationPage } from '../page-objects/GameCreationPage.js';
import { ScorekeeperPage } from '../page-objects/ScorekeeperPage.js';
import { testGames } from '../fixtures/game-fixtures.js';
import { APIHelpers } from '../fixtures/api-helpers.js';
import { cleanupTestGame } from '../utils/test-helpers.js';

test.describe('Quick Smoke Tests @smoke', () => {
  let currentGameId;

  test.afterEach(async ({ page }) => {
    await cleanupTestGame(page, currentGameId);
  });

  test('4-man game - quick validation', async ({ page }) => {
    const fixture = testGames.standard4Man;
    const apiHelpers = new APIHelpers();

    // Create game
    const homePage = new HomePage(page);
    await homePage.goto();
    await homePage.clickTestGame();

    const gameCreation = new GameCreationPage(page);
    const gameData = await gameCreation.createTestGame({ playerCount: 4 });
    currentGameId = gameData.gameId;

    // Play first 3 holes via UI
    const scorekeeper = new ScorekeeperPage(page);
    await scorekeeper.verifyGameLoaded(gameData.gameId);

    await scorekeeper.playHole(1, fixture.holes[1]);
    await scorekeeper.playHole(2, fixture.holes[2]);
    await scorekeeper.playHole(3, fixture.holes[3]);

    // Fast-forward remaining holes via API
    await apiHelpers.completeHoles(gameData.gameId, 4, 18, fixture.holes);

    // Reload and verify completion
    await page.reload();

    const currentHole = await scorekeeper.getCurrentHole();
    expect(currentHole).toBeGreaterThan(18); // Should be completed
  });
});
```

**Step 2: Run smoke test**

Run: `npm run test:e2e -- test-game-smoke.spec.js`
Expected: PASS in under 1 minute

**Step 3: Commit**

```bash
git add frontend/tests/e2e/tests/test-game-smoke.spec.js
git commit -m "test(e2e): add quick smoke test for 4-man game

- Test first 3 holes via UI, remaining via API
- Verify game creation and basic hole completion
- Tagged @smoke for fast CI/CD execution
- Execution time: ~30 seconds"
```

---

## Task 13: Add GitHub Actions CI/CD Workflow

**Files:**
- Create: `.github/workflows/e2e-tests.yml`

**Step 1: Create workflow file**

Create `.github/workflows/e2e-tests.yml`:

```yaml
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

**Step 2: Commit**

```bash
git add .github/workflows/e2e-tests.yml
git commit -m "ci: add GitHub Actions workflow for E2E tests

- Run smoke tests on PRs for fast feedback
- Run full E2E suite on main branch
- Upload HTML reports and videos on failure
- Set 30 minute timeout for complete test suite"
```

---

## Task 14: Update Documentation

**Files:**
- Create: `frontend/tests/e2e/README.md`
- Modify: `docs/plans/2025-01-08-e2e-test-game-mode-design.md`

**Step 1: Create E2E README**

Create `frontend/tests/e2e/README.md`:

```markdown
# E2E Testing - Test Game Mode

Playwright E2E tests for the Wolf Goat Pig test game mode.

## Quick Start

```bash
# Run all E2E tests
npm run test:e2e

# Run with UI (interactive)
npm run test:e2e:ui

# Run in debug mode
npm run test:e2e:debug

# Run only smoke tests
npm run test:e2e -- --grep @smoke

# View test report
npm run test:e2e:report
```

## Test Structure

- `fixtures/` - Test data and API helpers
- `page-objects/` - Page Object Model classes
- `tests/` - Test specs
- `utils/` - Custom assertions and helpers

## Test Coverage

- ✅ Homepage navigation to test game mode
- ✅ Test game creation (4-man)
- ✅ Score entry and team formation
- ✅ Special rules (Hoepfinger, double points)
- ✅ Game completion and final standings
- ✅ Zero-sum point validation

## CI/CD

- **PRs**: Smoke tests (~1 minute)
- **Main branch**: Full test suite (~10 minutes)
- **Artifacts**: HTML reports, screenshots, videos on failure

## Adding New Tests

1. Create test data in `fixtures/game-fixtures.js`
2. Add page object methods if needed
3. Write test in `tests/` directory
4. Use `@smoke` tag for fast tests

## Debugging

```bash
# Run in headed mode (see browser)
npm run test:e2e:headed

# Run specific test
npm run test:e2e -- test-game-4-man.spec.js

# Debug with breakpoints
npm run test:e2e:debug
```

## References

- Design Doc: `docs/plans/2025-01-08-e2e-test-game-mode-design.md`
- Playwright Docs: https://playwright.dev/
```

**Step 2: Update design doc with implementation status**

Modify `docs/plans/2025-01-08-e2e-test-game-mode-design.md` - add at top:

```markdown
**Status**: ✅ Implemented
**Implementation Plan**: `docs/plans/2025-01-08-e2e-test-game-mode-implementation.md`
**Completion Date**: [Today's date]
```

**Step 3: Commit**

```bash
git add frontend/tests/e2e/README.md docs/plans/2025-01-08-e2e-test-game-mode-design.md
git commit -m "docs: add E2E testing README and update design doc status

- Add comprehensive README for E2E test suite
- Include quick start, structure, coverage, and debugging info
- Update design doc with implementation status
- Reference implementation plan"
```

---

## Task 15: Final Verification & Cleanup

**Step 1: Run full test suite**

Run: `npm run test:e2e`
Expected: All tests pass

**Step 2: Verify smoke tests are fast**

Run: `time npm run test:e2e -- --grep @smoke`
Expected: Complete in under 2 minutes

**Step 3: Check test report**

Run: `npm run test:e2e:report`
Expected: HTML report opens with all green

**Step 4: Remove .gitkeep files**

```bash
rm frontend/tests/e2e/fixtures/.gitkeep
rm frontend/tests/e2e/page-objects/.gitkeep
rm frontend/tests/e2e/tests/.gitkeep
rm frontend/tests/e2e/utils/.gitkeep
```

**Step 5: Final commit**

```bash
git add .
git commit -m "chore: remove .gitkeep files from E2E test directories

All directories now contain actual files, .gitkeep no longer needed"
```

---

## Success Criteria Checklist

- [ ] Playwright configured with webServer for backend/frontend
- [ ] Directory structure created (fixtures, page-objects, tests, utils)
- [ ] Test fixtures for 4-man game with all 18 holes
- [ ] API helpers for fast-forwarding and cleanup
- [ ] Custom assertions for zero-sum validation
- [ ] Page objects for HomePage, GameCreation, Scorekeeper, Completion
- [ ] 4-man happy path test (holes 1-3, 16-18 UI, 4-15 API)
- [ ] Quick smoke test tagged @smoke
- [ ] UI components have data-testid attributes
- [ ] GitHub Actions workflow for CI/CD
- [ ] Documentation (README, design doc updated)
- [ ] All tests passing
- [ ] Smoke tests complete in < 2 minutes
- [ ] Full test suite complete in < 10 minutes

---

## Next Steps (Future Enhancements)

1. **5-Man Game Tests** - Extend fixtures and add 5-man test spec
2. **Error Scenarios** - Test invalid inputs, network failures
3. **Browser Compatibility** - Test on Firefox, Safari
4. **Accessibility Tests** - Keyboard navigation, screen reader
5. **Performance Tests** - Load testing, stress testing

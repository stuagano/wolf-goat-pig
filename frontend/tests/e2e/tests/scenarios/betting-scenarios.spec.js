import { test, expect } from '@playwright/test';
import { APIHelpers } from '../../fixtures/api-helpers.js';
import { cleanupTestGame } from '../../utils/test-helpers.js';
import { ScorekeeperPage } from '../../page-objects/ScorekeeperPage.js';

/**
 * Betting E2E — carry-over only (matches live quarters scorekeeper).
 *
 * Implemented: push → 2× next hole, carry badge, consecutive-push limit, reload.
 *
 * Skipped below: doubling/redouble/The Option/Ackerley — either Stuart-mode-only
 * or never wired to manual quarters entry. Those tests pre-date the current UI
 * and assumed golf scores auto-calculated quarters.
 */

const API_BASE = 'http://localhost:8333';
const FRONTEND_BASE = 'http://localhost:3000';

test.describe('Betting Mechanics Scenarios', () => {
  let apiHelpers;
  let gameId;
  let players;
  let scorekeeperPage;

  test.beforeEach(async ({ page }) => {
    apiHelpers = new APIHelpers(API_BASE);
    scorekeeperPage = new ScorekeeperPage(page);
  });

  test.afterEach(async ({ page }) => {
    if (gameId) {
      await cleanupTestGame(page, gameId);
    }
  });

  test.describe('Carry-over', () => {
    test('from tied hole - quarters roll to next hole', async ({ page }) => {
      const gameData = await apiHelpers.createTestGame(4, 'Wing Point');
      gameId = gameData.game_id;
      players = gameData.players;

      await page.goto(`${FRONTEND_BASE}/game/${gameId}`);
      await scorekeeperPage.verifyGameLoaded(gameId);

      const p1 = players[0].id;
      const p2 = players[1].id;
      const p3 = players[2].id;
      const p4 = players[3].id;

      await scorekeeperPage.playHole(1, {
        push: true,
        captain: p1,
        partnership: { captain: p1, partner: p2 },
      });

      const p1After1 = await scorekeeperPage.getPlayerPoints(p1);
      expect(p1After1).toBe(0);

      await page.waitForSelector('[data-testid="carry-over-badge"]', { timeout: 5000 });
      await expect(page.locator('[data-testid="current-wager"]')).toHaveText('2q');

      await scorekeeperPage.playHole(2, {
        quarters: {
          [p1]: 3,
          [p2]: 3,
          [p3]: -3,
          [p4]: -3,
        },
        captain: p2,
        partnership: { captain: p2, partner: p1 },
      });

      const p1After2 = await scorekeeperPage.getPlayerPoints(p1);
      const p2After2 = await scorekeeperPage.getPlayerPoints(p2);

      expect(p1After2).toBe(3);
      expect(p2After2).toBe(3);
    });

    test('limit - consecutive carries blocked', async ({ page }) => {
      const gameData = await apiHelpers.createTestGame(4, 'Wing Point');
      gameId = gameData.game_id;
      players = gameData.players;

      await page.goto(`${FRONTEND_BASE}/game/${gameId}`);
      await scorekeeperPage.verifyGameLoaded(gameId);

      const p1 = players[0].id;
      const p2 = players[1].id;
      const p3 = players[2].id;
      const p4 = players[3].id;

      await scorekeeperPage.playHole(1, {
        push: true,
        partnership: { captain: p1, partner: p2 },
      });

      await scorekeeperPage.expectCarryOverBadge(true);
      expect(await scorekeeperPage.getCurrentWager()).toBe(2);

      await scorekeeperPage.playHole(2, {
        push: true,
        partnership: { captain: p2, partner: p1 },
      });

      await scorekeeperPage.expectCarryOverBadge(false);
      expect(await scorekeeperPage.getCurrentWager()).toBe(2);

      await scorekeeperPage.playHole(3, {
        quarters: {
          [p1]: 3,
          [p2]: 3,
          [p3]: -3,
          [p4]: -3,
        },
        partnership: { captain: p1, partner: p2 },
      });

      const p1After3 = await scorekeeperPage.getPlayerPoints(p1);
      const p2After3 = await scorekeeperPage.getPlayerPoints(p2);

      expect(p1After3).toBe(3);
      expect(p2After3).toBe(3);
      expect(p1After3).not.toBe(6);
    });

    test('survives page reload after hole 1 push', async ({ page }) => {
      const gameData = await apiHelpers.createTestGame(4, 'Wing Point');
      gameId = gameData.game_id;
      players = gameData.players;

      await page.goto(`${FRONTEND_BASE}/game/${gameId}`);
      await scorekeeperPage.verifyGameLoaded(gameId);

      const p1 = players[0].id;
      const p2 = players[1].id;

      await scorekeeperPage.playHole(1, {
        push: true,
        partnership: { captain: p1, partner: p2 },
      });

      await page.reload();
      await scorekeeperPage.verifyGameLoaded(gameId);

      expect(await scorekeeperPage.getCurrentHole()).toBe(2);
      await scorekeeperPage.expectCarryOverBadge(true);
      expect(await scorekeeperPage.getCurrentWager()).toBe(2);
      expect(await scorekeeperPage.getPlayerPoints(p1)).toBe(0);
    });
  });

  // Pre-2026 scaffold — not wired to manual quarters entry; do not run in CI.
  test.describe.skip('Unimplemented betting mechanics', () => {
    test('Doubling - team can double the wager when winning position', async ({ page }) => {
      const gameData = await apiHelpers.createTestGame(4, 'Wing Point');
      gameId = gameData.game_id;
      players = gameData.players;

      await page.goto(`${FRONTEND_BASE}/game/${gameId}`);
      await scorekeeperPage.verifyGameLoaded(gameId);

      const p1 = players[0].id;
      const p2 = players[1].id;
      const p3 = players[2].id;
      const p4 = players[3].id;

      await scorekeeperPage.playHole(1, {
        scores: { [p1]: 4, [p2]: 8, [p3]: 5, [p4]: 6 },
        captain: p1,
        partnership: { captain: p1, partner: p2 },
      });

      const p1Points = await scorekeeperPage.getPlayerPoints(p1);
      expect(p1Points).toBeGreaterThan(0);
    });

    test('Redoubling - opponent can redouble after initial double', async ({ page }) => {
      const gameData = await apiHelpers.createTestGame(4, 'Wing Point');
      gameId = gameData.game_id;
      players = gameData.players;

      await page.goto(`${FRONTEND_BASE}/game/${gameId}`);
      await scorekeeperPage.verifyGameLoaded(gameId);

      const p1 = players[0].id;
      const p2 = players[1].id;
      const p3 = players[2].id;
      const p4 = players[3].id;

      await scorekeeperPage.playHole(1, {
        scores: { [p1]: 5, [p2]: 8, [p3]: 4, [p4]: 6 },
        captain: p1,
        partnership: { captain: p1, partner: p2 },
      });

      expect(await scorekeeperPage.getPlayerPoints(p3)).toBeGreaterThan(0);
    });

    test('The Option - automatic double when team furthest down', async ({ page }) => {
      const gameData = await apiHelpers.createTestGame(4, 'Wing Point');
      gameId = gameData.game_id;
      players = gameData.players;

      await page.goto(`${FRONTEND_BASE}/game/${gameId}`);
      await scorekeeperPage.verifyGameLoaded(gameId);

      const p1 = players[0].id;
      const p2 = players[1].id;
      const p3 = players[2].id;
      const p4 = players[3].id;

      for (let i = 0; i < 2; i++) {
        await scorekeeperPage.playHole(i + 1, {
          scores: [
            { [p1]: 7, [p2]: 8, [p3]: 4, [p4]: 5 },
            { [p1]: 6, [p2]: 7, [p3]: 3, [p4]: 4 },
          ][i],
          captain: p1,
          partnership: { captain: p1, partner: p2 },
        });
      }

      await scorekeeperPage.playHole(3, {
        scores: { [p1]: 4, [p2]: 8, [p3]: 6, [p4]: 7 },
        captain: p1,
        partnership: { captain: p1, partner: p2 },
      });

      expect(await scorekeeperPage.getPlayerPoints(p1)).toBeDefined();
    });

    test('Ackerley Gambit - opt-in to higher wager within team', async ({ page }) => {
      const gameData = await apiHelpers.createTestGame(4, 'Wing Point');
      gameId = gameData.game_id;
      players = gameData.players;

      await page.goto(`${FRONTEND_BASE}/game/${gameId}`);
      await scorekeeperPage.verifyGameLoaded(gameId);

      const p1 = players[0].id;
      const p2 = players[1].id;
      const p3 = players[2].id;
      const p4 = players[3].id;

      await scorekeeperPage.playHole(1, {
        scores: { [p1]: 4, [p2]: 8, [p3]: 6, [p4]: 7 },
        captain: p1,
        partnership: { captain: p1, partner: p2 },
      });

      expect(await scorekeeperPage.getPlayerPoints(p1)).toBeGreaterThan(0);
      expect(await scorekeeperPage.getPlayerPoints(p2)).toBeGreaterThan(0);
    });

    test('Betting mechanics preserve zero-sum across multiple holes', async ({ page }) => {
      const gameData = await apiHelpers.createTestGame(4, 'Wing Point');
      gameId = gameData.game_id;
      players = gameData.players;

      await page.goto(`${FRONTEND_BASE}/game/${gameId}`);
      await scorekeeperPage.verifyGameLoaded(gameId);

      const p1 = players[0].id;
      const p2 = players[1].id;
      const p3 = players[2].id;
      const p4 = players[3].id;

      const scenarios = [
        { [p1]: 4, [p2]: 8, [p3]: 5, [p4]: 7 },
        { [p1]: 3, [p2]: 7, [p3]: 6, [p4]: 5 },
        { [p1]: 4, [p2]: 5, [p3]: 6, [p4]: 7 },
        { [p1]: 5, [p2]: 6, [p3]: 4, [p4]: 8 },
        { [p1]: 3, [p2]: 7, [p3]: 8, [p4]: 6 },
      ];

      for (let hole = 1; hole <= 5; hole++) {
        const isSolo = hole === 3 || hole === 5;
        await scorekeeperPage.playHole(hole, {
          scores: scenarios[hole - 1],
          captain: p1,
          ...(isSolo
            ? { solo: true }
            : { partnership: { captain: p1, partner: hole % 2 === 0 ? p2 : p3 } }),
        });

        const pts = [p1, p2, p3, p4].map((id) => scorekeeperPage.getPlayerPoints(id));
        const values = await Promise.all(pts);
        const holeTotal = values.reduce((a, b) => a + b, 0);
        expect(Math.abs(holeTotal)).toBeLessThan(0.01);
      }
    });

    test('Complex betting sequence - double, redouble, carry-over', async ({ page }) => {
      const gameData = await apiHelpers.createTestGame(4, 'Wing Point');
      gameId = gameData.game_id;
      players = gameData.players;

      await page.goto(`${FRONTEND_BASE}/game/${gameId}`);
      await scorekeeperPage.verifyGameLoaded(gameId);

      const p1 = players[0].id;
      const p2 = players[1].id;
      const p3 = players[2].id;
      const p4 = players[3].id;

      await scorekeeperPage.playHole(1, {
        scores: { [p1]: 5, [p2]: 8, [p3]: 4, [p4]: 6 },
        captain: p1,
        partnership: { captain: p1, partner: p2 },
      });
      await scorekeeperPage.playHole(2, {
        scores: { [p1]: 4, [p2]: 7, [p3]: 5, [p4]: 6 },
        captain: p3,
        partnership: { captain: p3, partner: p4 },
      });
      await scorekeeperPage.playHole(3, {
        scores: { [p1]: 4, [p2]: 8, [p3]: 4, [p4]: 9 },
        captain: p1,
        partnership: { captain: p1, partner: p2 },
      });

      const totals = await Promise.all(
        [p1, p2, p3, p4].map((id) => scorekeeperPage.getPlayerPoints(id)),
      );
      expect(Math.abs(totals.reduce((a, b) => a + b, 0))).toBeLessThan(0.01);
    });
  });
});

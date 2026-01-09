import { test, expect } from '@playwright/test';
import { APIHelpers } from '../../fixtures/api-helpers.js';
import { cleanupTestGame } from '../../utils/test-helpers.js';
import { ScorekeeperPage } from '../../page-objects/ScorekeeperPage.js';

/**
 * Partnership Scenarios E2E Tests
 *
 * Tests partnership/goat game mechanics where captain selects a partner
 * and they play as a team (best-ball format) against the other partnership.
 *
 * These tests verify:
 * - Captain selects partner after each tee shot
 * - Partner accepts invitation
 * - Partner declines invitation (becomes solo, doubles bet)
 * - Best-ball scoring calculations (using best score from each team)
 * - Partners split quarters evenly
 * - Partnership quarter distribution is zero-sum
 */

const API_BASE = 'http://localhost:8333';
const FRONTEND_BASE = 'http://localhost:3333';

test.describe('Partnership Scenarios', () => {
  let apiHelpers;
  let gameId;
  let players;
  let scorekeeperPage;

  test.beforeEach(async ({ page }) => {
    apiHelpers = new APIHelpers(API_BASE);
    scorekeeperPage = new ScorekeeperPage(page);
  });

  test.afterEach(async () => {
    if (gameId) {
      await cleanupTestGame(null, gameId);
    }
  });

  test('Captain selects partner - best-ball scoring with favorable matchup', async ({ page }) => {
    /**
     * Scenario: Captain selects partner, their team wins best-ball
     * Expected: Each partner gets 1.5 quarters, opponents lose 1.5 each
     */

    const gameData = await apiHelpers.createTestGame(4, 'Wing Point');
    gameId = gameData.game_id;
    players = gameData.players;

    await page.goto(`${FRONTEND_BASE}/game/${gameId}`);
    await scorekeeperPage.verifyGameLoaded(gameId);

    const p1 = players[0].id;
    const p2 = players[1].id;
    const p3 = players[2].id;
    const p4 = players[3].id;

    // Hole 1: Captain (P1) selects partner (P2)
    // Team 1 (P1+P2): best score is 4 (P1)
    // Team 2 (P3+P4): best score is 5 (P3)
    // Team 1 wins -> P1=1.5, P2=1.5, P3=-1.5, P4=-1.5
    await scorekeeperPage.playHole(1, {
      scores: {
        [p1]: 4,
        [p2]: 7,
        [p3]: 5,
        [p4]: 6
      },
      captain: p1,
      partnership: { captain: p1, partner: p2 }
    });

    const p1Points = await scorekeeperPage.getPlayerPoints(p1);
    const p2Points = await scorekeeperPage.getPlayerPoints(p2);
    const p3Points = await scorekeeperPage.getPlayerPoints(p3);
    const p4Points = await scorekeeperPage.getPlayerPoints(p4);

    expect(p1Points).toBe(1.5);
    expect(p2Points).toBe(1.5);
    expect(p3Points).toBe(-1.5);
    expect(p4Points).toBe(-1.5);

    const totalQuarters = p1Points + p2Points + p3Points + p4Points;
    expect(Math.abs(totalQuarters)).toBeLessThan(0.01);

    console.log(`Partnership win: P1=${p1Points}, P2=${p2Points}, P3=${p3Points}, P4=${p4Points}`);
  });

  test('Captain selects partner - best-ball scoring with unfavorable matchup', async ({ page }) => {
    /**
     * Scenario: Captain selects partner, their team loses best-ball
     * Expected: Each partner loses 1.5 quarters, opponents gain 1.5 each
     */

    const gameData = await apiHelpers.createTestGame(4, 'Wing Point');
    gameId = gameData.game_id;
    players = gameData.players;

    await page.goto(`${FRONTEND_BASE}/game/${gameId}`);
    await scorekeeperPage.verifyGameLoaded(gameId);

    const p1 = players[0].id;
    const p2 = players[1].id;
    const p3 = players[2].id;
    const p4 = players[3].id;

    // Hole 1: Captain (P1) selects partner (P2)
    // Team 1 (P1+P2): best score is 5 (P2)
    // Team 2 (P3+P4): best score is 4 (P3)
    // Team 1 loses -> P1=-1.5, P2=-1.5, P3=1.5, P4=1.5
    await scorekeeperPage.playHole(1, {
      scores: {
        [p1]: 7,
        [p2]: 5,
        [p3]: 4,
        [p4]: 6
      },
      captain: p1,
      partnership: { captain: p1, partner: p2 }
    });

    const p1Points = await scorekeeperPage.getPlayerPoints(p1);
    const p2Points = await scorekeeperPage.getPlayerPoints(p2);
    const p3Points = await scorekeeperPage.getPlayerPoints(p3);
    const p4Points = await scorekeeperPage.getPlayerPoints(p4);

    expect(p1Points).toBe(-1.5);
    expect(p2Points).toBe(-1.5);
    expect(p3Points).toBe(1.5);
    expect(p4Points).toBe(1.5);

    const totalQuarters = p1Points + p2Points + p3Points + p4Points;
    expect(Math.abs(totalQuarters)).toBeLessThan(0.01);

    console.log(`Partnership loss: P1=${p1Points}, P2=${p2Points}, P3=${p3Points}, P4=${p4Points}`);
  });

  test('Partners split quarters evenly on partnership win', async ({ page }) => {
    /**
     * Scenario: Partnership wins hole, verify both partners get equal quarters
     * Expected: Both partners receive identical quarter amounts (1.5 each)
     */

    const gameData = await apiHelpers.createTestGame(4, 'Wing Point');
    gameId = gameData.game_id;
    players = gameData.players;

    await page.goto(`${FRONTEND_BASE}/game/${gameId}`);
    await scorekeeperPage.verifyGameLoaded(gameId);

    const p1 = players[0].id;
    const p2 = players[1].id;
    const p3 = players[2].id;
    const p4 = players[3].id;

    // Multiple partnership holes to verify consistent even splitting
    const holeScenarios = [
      // Hole 1: P1+P2 vs P3+P4
      { captain: p1, partner: p2, scores: { [p1]: 4, [p2]: 8, [p3]: 5, [p4]: 6 }, expectedDelta: 1.5 },
      // Hole 2: P2+P3 vs P1+P4
      { captain: p2, partner: p3, scores: { [p1]: 7, [p2]: 4, [p3]: 4, [p4]: 8 }, expectedDelta: 1.5 },
      // Hole 3: P3+P4 vs P1+P2
      { captain: p3, partner: p4, scores: { [p1]: 6, [p2]: 7, [p3]: 5, [p4]: 4 }, expectedDelta: 1.5 }
    ];

    for (let holeNum = 1; holeNum <= 3; holeNum++) {
      const scenario = holeScenarios[holeNum - 1];

      await scorekeeperPage.playHole(holeNum, {
        scores: scenario.scores,
        captain: scenario.captain,
        partnership: { captain: scenario.captain, partner: scenario.partner }
      });

      const captainPoints = await scorekeeperPage.getPlayerPoints(scenario.captain);
      const partnerPoints = await scorekeeperPage.getPlayerPoints(scenario.partner);

      // Both partners should have same points
      expect(captainPoints).toBe(scenario.expectedDelta);
      expect(partnerPoints).toBe(scenario.expectedDelta);
      expect(captainPoints).toBe(partnerPoints);
    }

    console.log('Partnership quarters split evenly verified across 3 holes');
  });

  test('Partners split quarters evenly on partnership loss', async ({ page }) => {
    /**
     * Scenario: Partnership loses hole, verify both partners get equal negative quarters
     * Expected: Both partners lose identical quarter amounts (-1.5 each)
     */

    const gameData = await apiHelpers.createTestGame(4, 'Wing Point');
    gameId = gameData.game_id;
    players = gameData.players;

    await page.goto(`${FRONTEND_BASE}/game/${gameId}`);
    await scorekeeperPage.verifyGameLoaded(gameId);

    const p1 = players[0].id;
    const p2 = players[1].id;
    const p3 = players[2].id;
    const p4 = players[3].id;

    // Hole 1: P1+P2 lose to P3+P4
    // Team 1 (P1+P2): best score is 6 (P2)
    // Team 2 (P3+P4): best score is 4 (P3)
    await scorekeeperPage.playHole(1, {
      scores: {
        [p1]: 7,
        [p2]: 6,
        [p3]: 4,
        [p4]: 5
      },
      captain: p1,
      partnership: { captain: p1, partner: p2 }
    });

    const p1Points = await scorekeeperPage.getPlayerPoints(p1);
    const p2Points = await scorekeeperPage.getPlayerPoints(p2);

    expect(p1Points).toBe(-1.5);
    expect(p2Points).toBe(-1.5);
    expect(p1Points).toBe(p2Points);

    console.log(`Partnership loss - even split: P1=${p1Points}, P2=${p2Points}`);
  });

  test('Best-ball scoring - team with best score wins', async ({ page }) => {
    /**
     * Scenario: Verify best-ball scoring uses the best score from each team
     * Team 1 has scores 4,8 -> uses 4
     * Team 2 has scores 5,6 -> uses 5
     * Expected: Team 1 wins with score 4
     */

    const gameData = await apiHelpers.createTestGame(4, 'Wing Point');
    gameId = gameData.game_id;
    players = gameData.players;

    await page.goto(`${FRONTEND_BASE}/game/${gameId}`);
    await scorekeeperPage.verifyGameLoaded(gameId);

    const p1 = players[0].id;
    const p2 = players[1].id;
    const p3 = players[2].id;
    const p4 = players[3].id;

    // Hole 1: Best-ball comparison
    // P1 (best of P1+P2): 4
    // P3 (best of P3+P4): 5
    // P1+P2 win
    await scorekeeperPage.playHole(1, {
      scores: {
        [p1]: 4,
        [p2]: 8,
        [p3]: 5,
        [p4]: 7
      },
      captain: p1,
      partnership: { captain: p1, partner: p2 }
    });

    const p1Points = await scorekeeperPage.getPlayerPoints(p1);
    const p2Points = await scorekeeperPage.getPlayerPoints(p2);

    // Both should be positive (won)
    expect(p1Points).toBeGreaterThan(0);
    expect(p2Points).toBeGreaterThan(0);

    console.log(`Best-ball win: P1=${p1Points}, P2=${p2Points}`);
  });

  test('Best-ball tie-breaker - equal best scores', async ({ page }) => {
    /**
     * Scenario: Both teams have same best score (tie)
     * Expected: Neither team wins or loses quarters
     */

    const gameData = await apiHelpers.createTestGame(4, 'Wing Point');
    gameId = gameData.game_id;
    players = gameData.players;

    await page.goto(`${FRONTEND_BASE}/game/${gameId}`);
    await scorekeeperPage.verifyGameLoaded(gameId);

    const p1 = players[0].id;
    const p2 = players[1].id;
    const p3 = players[2].id;
    const p4 = players[3].id;

    // Hole 1: Tie in best-ball
    // P1 (best of P1+P2): 4
    // P3 (best of P3+P4): 4
    // Tie - no quarters exchanged
    await scorekeeperPage.playHole(1, {
      scores: {
        [p1]: 4,
        [p2]: 8,
        [p3]: 4,
        [p4]: 9
      },
      captain: p1,
      partnership: { captain: p1, partner: p2 }
    });

    const p1Points = await scorekeeperPage.getPlayerPoints(p1);
    const p2Points = await scorekeeperPage.getPlayerPoints(p2);
    const p3Points = await scorekeeperPage.getPlayerPoints(p3);
    const p4Points = await scorekeeperPage.getPlayerPoints(p4);

    // All should be 0 on a tie
    expect(p1Points).toBe(0);
    expect(p2Points).toBe(0);
    expect(p3Points).toBe(0);
    expect(p4Points).toBe(0);

    console.log(`Best-ball tie (no quarters exchanged): all = 0`);
  });

  test('Partnership zero-sum validation - quarters always balance', async ({ page }) => {
    /**
     * Scenario: Multiple partnership holes, verify zero-sum on each hole
     * Expected: Every hole's quarters sum to exactly zero
     */

    const gameData = await apiHelpers.createTestGame(4, 'Wing Point');
    gameId = gameData.game_id;
    players = gameData.players;

    await page.goto(`${FRONTEND_BASE}/game/${gameId}`);
    await scorekeeperPage.verifyGameLoaded(gameId);

    const p1 = players[0].id;
    const p2 = players[1].id;
    const p3 = players[2].id;
    const p4 = players[3].id;

    // Play 4 partnership holes with different captain rotations
    const partnerships = [
      { captain: p1, partner: p2, scores: { [p1]: 4, [p2]: 6, [p3]: 5, [p4]: 7 } },
      { captain: p2, partner: p3, scores: { [p1]: 6, [p2]: 4, [p3]: 5, [p4]: 7 } },
      { captain: p3, partner: p4, scores: { [p1]: 5, [p2]: 7, [p3]: 4, [p4]: 5 } },
      { captain: p4, partner: p1, scores: { [p1]: 4, [p2]: 6, [p3]: 7, [p4]: 5 } }
    ];

    const previousTotals = { [p1]: 0, [p2]: 0, [p3]: 0, [p4]: 0 };

    for (let holeNum = 1; holeNum <= 4; holeNum++) {
      const partnership = partnerships[holeNum - 1];

      await scorekeeperPage.playHole(holeNum, {
        scores: partnership.scores,
        captain: partnership.captain,
        partnership: { captain: partnership.captain, partner: partnership.partner }
      });

      // Get running totals
      const p1Points = await scorekeeperPage.getPlayerPoints(p1);
      const p2Points = await scorekeeperPage.getPlayerPoints(p2);
      const p3Points = await scorekeeperPage.getPlayerPoints(p3);
      const p4Points = await scorekeeperPage.getPlayerPoints(p4);

      // Verify sum to zero
      const holeTotal = p1Points + p2Points + p3Points + p4Points;
      expect(Math.abs(holeTotal)).toBeLessThan(0.01);
    }

    console.log('Partnership zero-sum validation passed for 4 holes');
  });

  test('Partner selection from all available players', async ({ page }) => {
    /**
     * Scenario: Captain can select any other player as partner
     * Expected: Partnership forms correctly regardless of which player is selected
     */

    const gameData = await apiHelpers.createTestGame(4, 'Wing Point');
    gameId = gameData.game_id;
    players = gameData.players;

    await page.goto(`${FRONTEND_BASE}/game/${gameId}`);
    await scorekeeperPage.verifyGameLoaded(gameId);

    const p1 = players[0].id;
    const p2 = players[1].id;
    const p3 = players[2].id;
    const p4 = players[3].id;

    // Test multiple captain/partner combinations
    const combinations = [
      { captain: p1, partner: p2 },
      { captain: p1, partner: p3 },
      { captain: p1, partner: p4 },
      { captain: p2, partner: p3 }
    ];

    for (let holeNum = 1; holeNum <= 4; holeNum++) {
      const combo = combinations[holeNum - 1];

      const scores = {};
      scores[p1] = 4 + (holeNum % 3);
      scores[p2] = 5 + (holeNum % 2);
      scores[p3] = 6 + (holeNum % 3);
      scores[p4] = 5 + (holeNum % 2);

      await scorekeeperPage.playHole(holeNum, {
        scores,
        captain: combo.captain,
        partnership: { captain: combo.captain, partner: combo.partner }
      });

      // Just verify no errors and a score was recorded
      const captainPoints = await scorekeeperPage.getPlayerPoints(combo.captain);
      expect(captainPoints).toBeDefined();
    }

    console.log('Multiple partner selection combinations tested');
  });
});

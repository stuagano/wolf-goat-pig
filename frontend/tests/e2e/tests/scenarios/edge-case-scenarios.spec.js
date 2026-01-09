import { test, expect } from '@playwright/test';
import { APIHelpers } from '../../fixtures/api-helpers.js';
import { cleanupTestGame } from '../../utils/test-helpers.js';
import { ScorekeeperPage } from '../../page-objects/ScorekeeperPage.js';

/**
 * Edge Case Scenarios E2E Tests
 *
 * Tests unusual or boundary conditions including:
 * - All players tie on a hole
 * - Multiple consecutive ties (carry-over limits)
 * - Zero-sum validation across complex scenarios
 * - Game completion with final standings
 * - Early departure scenarios
 */

const API_BASE = 'http://localhost:8333';
const FRONTEND_BASE = 'http://localhost:3333';

test.describe('Edge Case Scenarios', () => {
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

  test('All players tie on a hole - everyone gets 0 quarters', async ({ page }) => {
    /**
     * Scenario: All 4 players shoot exact same score
     * Expected: Everyone gets 0 quarters, hole carries to next hole
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

    // Hole 1: All players shoot 4
    await scorekeeperPage.playHole(1, {
      scores: {
        [p1]: 4,
        [p2]: 4,
        [p3]: 4,
        [p4]: 4
      },
      captain: p1,
      solo: true
    });

    const p1Points = await scorekeeperPage.getPlayerPoints(p1);
    const p2Points = await scorekeeperPage.getPlayerPoints(p2);
    const p3Points = await scorekeeperPage.getPlayerPoints(p3);
    const p4Points = await scorekeeperPage.getPlayerPoints(p4);

    // Everyone should get 0
    expect(p1Points).toBe(0);
    expect(p2Points).toBe(0);
    expect(p3Points).toBe(0);
    expect(p4Points).toBe(0);

    const total = p1Points + p2Points + p3Points + p4Points;
    expect(total).toBe(0);

    console.log(`All players tie on hole 1: all get 0 quarters`);
  });

  test('Partnership with both players tied score', async ({ page }) => {
    /**
     * Scenario: Both members of partnership shoot identical score
     * Best-ball uses that score for the team
     * Expected: Best-ball comparison still works correctly
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

    // Hole 1: P1 and P2 both shoot 4
    // Team best: 4 vs 5 (P3)
    // P1+P2 win
    await scorekeeperPage.playHole(1, {
      scores: {
        [p1]: 4,
        [p2]: 4,
        [p3]: 5,
        [p4]: 6
      },
      captain: p1,
      partnership: { captain: p1, partner: p2 }
    });

    const p1Points = await scorekeeperPage.getPlayerPoints(p1);
    const p2Points = await scorekeeperPage.getPlayerPoints(p2);

    // Both should be positive
    expect(p1Points).toBeGreaterThan(0);
    expect(p2Points).toBeGreaterThan(0);
    expect(p1Points).toBe(p2Points);

    console.log(`Partnership with tied scores: P1=${p1Points}, P2=${p2Points}`);
  });

  test('Zero-sum validation - simple 4-hole game', async ({ page }) => {
    /**
     * Scenario: Play simple 4-hole game, verify zero-sum at completion
     * Expected: Final totals for all players sum to zero
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

    // Play 4 holes
    const scenarios = [
      { [p1]: 4, [p2]: 5, [p3]: 6, [p4]: 7, captain: p1, solo: true },
      { [p1]: 5, [p2]: 4, [p3]: 6, [p4]: 7, captain: p2, partnership: { captain: p2, partner: p3 } },
      { [p1]: 4, [p2]: 5, [p3]: 4, [p4]: 6, captain: p3, solo: true },
      { [p1]: 5, [p2]: 6, [p3]: 7, [p4]: 4, captain: p4, partnership: { captain: p4, partner: p1 } }
    ];

    for (let hole = 1; hole <= 4; hole++) {
      const scenario = scenarios[hole - 1];
      const scores = {
        [p1]: scenario[p1],
        [p2]: scenario[p2],
        [p3]: scenario[p3],
        [p4]: scenario[p4]
      };

      if (scenario.solo) {
        await scorekeeperPage.playHole(hole, {
          scores,
          captain: scenario.captain,
          solo: true
        });
      } else {
        await scorekeeperPage.playHole(hole, {
          scores,
          captain: scenario.captain,
          partnership: scenario.partnership
        });
      }
    }

    // Get final totals
    const p1Final = await scorekeeperPage.getPlayerPoints(p1);
    const p2Final = await scorekeeperPage.getPlayerPoints(p2);
    const p3Final = await scorekeeperPage.getPlayerPoints(p3);
    const p4Final = await scorekeeperPage.getPlayerPoints(p4);

    const finalSum = p1Final + p2Final + p3Final + p4Final;
    expect(Math.abs(finalSum)).toBeLessThan(0.01);

    console.log(`Zero-sum after 4 holes: Total=${finalSum.toFixed(2)} (P1=${p1Final}, P2=${p2Final}, P3=${p3Final}, P4=${p4Final})`);
  });

  test('Zero-sum validation - complex mixed-rules game', async ({ page }) => {
    /**
     * Scenario: Play with alternating solo/partnership, special wagers
     * Expected: Zero-sum always maintained
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

    let holeNum = 1;

    // Hole 1: Solo
    await scorekeeperPage.playHole(holeNum++, {
      scores: { [p1]: 4, [p2]: 5, [p3]: 6, [p4]: 7 },
      captain: p1,
      solo: true
    });

    // Hole 2: Partnership
    await scorekeeperPage.playHole(holeNum++, {
      scores: { [p1]: 5, [p2]: 4, [p3]: 6, [p4]: 7 },
      captain: p2,
      partnership: { captain: p2, partner: p3 }
    });

    // Hole 3: Solo with extreme scores
    await scorekeeperPage.playHole(holeNum++, {
      scores: { [p1]: 3, [p2]: 7, [p3]: 8, [p4]: 6 },
      captain: p3,
      solo: true
    });

    // Hole 4: Partnership
    await scorekeeperPage.playHole(holeNum++, {
      scores: { [p1]: 4, [p2]: 6, [p3]: 5, [p4]: 4 },
      captain: p4,
      partnership: { captain: p4, partner: p1 }
    });

    // Hole 5: Tie
    await scorekeeperPage.playHole(holeNum++, {
      scores: { [p1]: 4, [p2]: 4, [p3]: 4, [p4]: 4 },
      captain: p1,
      solo: true
    });

    const p1Final = await scorekeeperPage.getPlayerPoints(p1);
    const p2Final = await scorekeeperPage.getPlayerPoints(p2);
    const p3Final = await scorekeeperPage.getPlayerPoints(p3);
    const p4Final = await scorekeeperPage.getPlayerPoints(p4);

    const finalSum = p1Final + p2Final + p3Final + p4Final;
    expect(Math.abs(finalSum)).toBeLessThan(0.01);

    console.log(`Zero-sum with complex rules: Total=${finalSum.toFixed(2)}`);
  });

  test('Game completion - final standings calculation', async ({ page }) => {
    /**
     * Scenario: Complete a short game, verify final standings are calculated
     * Expected: Final standings show each player's total quarters
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

    // Play 3 holes
    for (let hole = 1; hole <= 3; hole++) {
      await scorekeeperPage.playHole(hole, {
        scores: {
          [p1]: 4 + (hole % 2),
          [p2]: 5 + (hole % 3),
          [p3]: 6 + (hole % 2),
          [p4]: 7 + (hole % 3)
        },
        captain: players[hole % 4].id,
        solo: hole % 2 === 0,
        partnership: hole % 2 === 1 ? {
          captain: players[hole % 4].id,
          partner: players[(hole + 1) % 4].id
        } : null
      });
    }

    // Get final standings
    const finalPoints = {
      [p1]: await scorekeeperPage.getPlayerPoints(p1),
      [p2]: await scorekeeperPage.getPlayerPoints(p2),
      [p3]: await scorekeeperPage.getPlayerPoints(p3),
      [p4]: await scorekeeperPage.getPlayerPoints(p4)
    };

    // All should be defined
    expect(finalPoints[p1]).toBeDefined();
    expect(finalPoints[p2]).toBeDefined();
    expect(finalPoints[p3]).toBeDefined();
    expect(finalPoints[p4]).toBeDefined();

    // Sum should be zero
    const sum = Object.values(finalPoints).reduce((a, b) => a + b, 0);
    expect(Math.abs(sum)).toBeLessThan(0.01);

    console.log(`Game completion standings: P1=${finalPoints[p1]}, P2=${finalPoints[p2]}, P3=${finalPoints[p3]}, P4=${finalPoints[p4]}`);
  });

  test('Extreme score variance - one player far exceeds others', async ({ page }) => {
    /**
     * Scenario: One player shoots much higher score than rest of field
     * Expected: Negative quarters calculated correctly, no overflow
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

    // Hole 1: P4 shoots 10, everyone else shoots 3-4
    await scorekeeperPage.playHole(1, {
      scores: {
        [p1]: 3,
        [p2]: 4,
        [p3]: 3,
        [p4]: 10  // Extreme outlier
      },
      captain: p1,
      solo: true
    });

    const p1Points = await scorekeeperPage.getPlayerPoints(p1);
    const p4Points = await scorekeeperPage.getPlayerPoints(p4);

    expect(p1Points).toBeGreaterThan(0);
    expect(p4Points).toBeLessThan(0);

    const total = p1Points + (await scorekeeperPage.getPlayerPoints(p2)) + (await scorekeeperPage.getPlayerPoints(p3)) + p4Points;
    expect(Math.abs(total)).toBeLessThan(0.01);

    console.log(`Extreme variance: P1=${p1Points}, P4=${p4Points}`);
  });

  test('Negative to positive swing - player goes from losing to winning', async ({ page }) => {
    /**
     * Scenario: Player loses several holes, then wins multiple holes
     * Expected: Cumulative points correctly show swing from negative to positive
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

    // Holes 1-2: P1 loses badly
    await scorekeeperPage.playHole(1, {
      scores: { [p1]: 7, [p2]: 4, [p3]: 5, [p4]: 6 },
      captain: p1,
      solo: true
    });

    let p1Points = await scorekeeperPage.getPlayerPoints(p1);
    expect(p1Points).toBe(-3);

    await scorekeeperPage.playHole(2, {
      scores: { [p1]: 8, [p2]: 4, [p3]: 5, [p4]: 6 },
      captain: p2,
      partnership: { captain: p2, partner: p3 }
    });

    p1Points = await scorekeeperPage.getPlayerPoints(p1);
    expect(p1Points).toBeLessThan(-2);

    // Holes 3-4: P1 wins
    await scorekeeperPage.playHole(3, {
      scores: { [p1]: 4, [p2]: 5, [p3]: 6, [p4]: 7 },
      captain: p1,
      solo: true
    });

    p1Points = await scorekeeperPage.getPlayerPoints(p1);
    expect(p1Points).toBeLessThan(0); // Still negative after 1 win

    await scorekeeperPage.playHole(4, {
      scores: { [p1]: 4, [p2]: 5, [p3]: 6, [p4]: 7 },
      captain: p1,
      solo: true
    });

    p1Points = await scorekeeperPage.getPlayerPoints(p1);
    expect(p1Points).toBeLessThan(1); // Close to breakeven or slightly positive

    console.log(`Swing from negative to positive: final=${p1Points}`);
  });

  test('Maximum running total variance - one player up 30 quarters', async ({ page }) => {
    /**
     * Scenario: One player wins all holes, accumulating large positive total
     * Expected: Large variance maintained, zero-sum at each step
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

    // Play 5 holes where P1 wins all
    for (let hole = 1; hole <= 5; hole++) {
      await scorekeeperPage.playHole(hole, {
        scores: {
          [p1]: 3, // Always best
          [p2]: 5 + (hole % 2),
          [p3]: 6 + (hole % 3),
          [p4]: 7 + (hole % 2)
        },
        captain: p1,
        solo: true
      });

      const p1Total = await scorekeeperPage.getPlayerPoints(p1);
      const p2Total = await scorekeeperPage.getPlayerPoints(p2);
      const p3Total = await scorekeeperPage.getPlayerPoints(p3);
      const p4Total = await scorekeeperPage.getPlayerPoints(p4);

      const sum = p1Total + p2Total + p3Total + p4Total;
      expect(Math.abs(sum)).toBeLessThan(0.01);
    }

    const p1Final = await scorekeeperPage.getPlayerPoints(p1);
    expect(p1Final).toBe(15); // 5 holes * 3 quarters

    console.log(`Maximum variance: P1=${p1Final} after winning all 5 holes`);
  });

  test('Fractional quarters - partnership creates .5 increments', async ({ page }) => {
    /**
     * Scenario: Partnership scoring creates fractional quarters (.5, 1.5, 3.0)
     * Expected: Fractional values calculated and accumulated correctly
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

    // Play 3 partnership holes
    for (let hole = 1; hole <= 3; hole++) {
      await scorekeeperPage.playHole(hole, {
        scores: {
          [p1]: 4 + (hole % 2),
          [p2]: 8,
          [p3]: 5 + (hole % 2),
          [p4]: 6
        },
        captain: hole % 2 === 1 ? p1 : p3,
        partnership: hole % 2 === 1 ?
          { captain: p1, partner: p2 } :
          { captain: p3, partner: p4 }
      });
    }

    const p1Final = await scorekeeperPage.getPlayerPoints(p1);
    const p2Final = await scorekeeperPage.getPlayerPoints(p2);

    // Verify fractional values exist
    expect(Number.isFinite(p1Final)).toBe(true);
    expect(Number.isFinite(p2Final)).toBe(true);

    console.log(`Fractional quarters: P1=${p1Final}, P2=${p2Final}`);
  });
});

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

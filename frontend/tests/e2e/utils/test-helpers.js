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
    response => response.url().includes('/holes/complete') && response.status() === 200,
    { timeout: 10000 }
  );

  // Wait for UI to update to next hole (verify text content changed)
  await page.waitForFunction(
    (nextHole) => {
      const elem = document.querySelector('[data-testid="current-hole"]');
      return elem && parseInt(elem.textContent.replace(/[^0-9]/g, '')) === nextHole;
    },
    holeNumber + 1,
    { timeout: 5000 }
  );
}

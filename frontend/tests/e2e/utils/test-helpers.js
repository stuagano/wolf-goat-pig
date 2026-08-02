import { APIHelpers } from '../fixtures/api-helpers.js';

export async function cleanupTestGame(page, gameId) {
  if (!gameId) return;

  if (page) {
    // Cleanup localStorage
    await page.evaluate(() => {
      localStorage.removeItem('wgp_current_game');
      Object.keys(localStorage)
        .filter(key => key.startsWith('wgp_session_'))
        .forEach(key => localStorage.removeItem(key));
    });
  }

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
  // Frontend syncs via POST /scores (offline-first), not /holes/complete.
  await page.waitForResponse(
    (response) =>
      response.url().includes('/scores') &&
      response.request().method() === 'POST' &&
      response.status() === 200,
    { timeout: 15000 }
  ).catch(() => {
    // Offline queue path — no network POST; UI still advances locally.
  });

  await page.waitForFunction(
    (nextHole) => {
      const elem = document.querySelector('[data-testid="current-hole"]');
      return elem && parseInt(elem.textContent.replace(/[^0-9]/g, ''), 10) === nextHole;
    },
    holeNumber + 1,
    { timeout: 10000 }
  );
}

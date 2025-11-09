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

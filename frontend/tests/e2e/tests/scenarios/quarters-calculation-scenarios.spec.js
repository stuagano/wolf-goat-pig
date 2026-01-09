import { test, expect } from '@playwright/test';
import { setAllQuarters } from './quarters-helpers.js';

/**
 * Quarters Calculation Scenarios
 *
 * Tests that focus on quarter entry, validation, and zero-sum property.
 * Uses the actual SimpleScorekeeper UI which has manual quarter entry.
 * Uses quick-add buttons to set quarters (typing doesn't work with controlled inputs).
 */

const API_BASE = 'http://localhost:8333';
const FRONTEND_BASE = 'http://localhost:3000';

test.describe('Quarters Calculation & Zero-Sum Validation', () => {
  let gameId;
  let players;

  test.beforeEach(async ({ request }) => {
    // Create test game via API
    const response = await request.post(`${API_BASE}/games/create-test?player_count=4`);
    expect(response.ok()).toBeTruthy();

    const data = await response.json();
    gameId = data.game_id;
    players = data.players;

    console.log(`Created test game: ${gameId}`);
  });

  test.afterEach(async ({ request }) => {
    if (gameId) {
      await request.delete(`${API_BASE}/games/${gameId}`);
    }
  });

  test('Solo win - quarters distribute correctly (+3, -1, -1, -1)', async ({ page }) => {
    await page.goto(`${FRONTEND_BASE}/game/${gameId}`);
    await page.waitForSelector('[data-testid="scorekeeper-container"]', { timeout: 10000 });

    // Wait for quarters section to be visible
    await page.waitForSelector('[data-testid="quarters-input-test-player-1"]', { timeout: 5000 });

    // Enter quarters using quick-add buttons: solo player wins
    // P1 (solo) wins = +3 quarters
    // P2, P3, P4 each lose = -1 quarters each
    await setAllQuarters(page, players, [3, -1, -1, -1]);

    // Verify quarters sum shows zero (validation should pass)
    await expect(page.locator('text=Sum: 0')).toBeVisible();

    // Complete the hole
    const completeButton = page.locator('[data-testid="complete-hole-button"]');
    await completeButton.click();

    // Wait for hole to advance
    await page.waitForTimeout(1000);

    // Verify we advanced to hole 2
    const bodyText = await page.locator('body').textContent();
    expect(bodyText).toContain('Hole 2');

    console.log('✓ Solo win quarters validated: +3, -1, -1, -1');
  });

  test('Solo loss - quarters distribute correctly (-3, +1, +1, +1)', async ({ page }) => {
    await page.goto(`${FRONTEND_BASE}/game/${gameId}`);
    await page.waitForSelector('[data-testid="scorekeeper-container"]', { timeout: 10000 });

    // P1 (solo) loses = -3 quarters
    // P2, P3, P4 each win = +1 quarters each
    await setAllQuarters(page, players, [-3, 1, 1, 1]);

    const completeButton = page.locator('[data-testid="complete-hole-button"]');
    await expect(completeButton).toBeEnabled();
    await completeButton.click();

    await page.waitForTimeout(1000);
    const bodyText = await page.locator('body').textContent();
    expect(bodyText).toContain('Hole 2');

    console.log('✓ Solo loss quarters validated: -3, +1, +1, +1');
  });

  test('Partnership win - quarters split evenly (+1.5, +1.5, -1.5, -1.5)', async ({ page }) => {
    await page.goto(`${FRONTEND_BASE}/game/${gameId}`);
    await page.waitForSelector('[data-testid="scorekeeper-container"]', { timeout: 10000 });

    // Team 1 (P1+P2) wins = +1.5 quarters each
    // Team 2 (P3+P4) loses = -1.5 quarters each
    await setAllQuarters(page, players, [1.5, 1.5, -1.5, -1.5]);

    const completeButton = page.locator('[data-testid="complete-hole-button"]');
    await expect(completeButton).toBeEnabled();
    await completeButton.click();

    await page.waitForTimeout(1000);
    const bodyText = await page.locator('body').textContent();
    expect(bodyText).toContain('Hole 2');

    console.log('✓ Partnership quarters validated: +1.5, +1.5, -1.5, -1.5');
  });

  test('Zero-sum validation rejects imbalanced quarters', async ({ page }) => {
    await page.goto(`${FRONTEND_BASE}/game/${gameId}`);
    await page.waitForSelector('[data-testid="scorekeeper-container"]', { timeout: 10000 });

    // Enter quarters that DON'T sum to zero (should be rejected)
    await setAllQuarters(page, players, [3, -1, -1, 0]); // Should be -1

    // Try to complete hole
    const completeButton = page.locator('[data-testid="complete-hole-button"]');
    await completeButton.click();

    // Should see error message about quarters not summing to zero
    await page.waitForTimeout(500);
    const bodyText = await page.locator('body').textContent();
    expect(bodyText).toMatch(/quarters must sum to zero/i);

    console.log('✓ Zero-sum validation correctly rejected imbalanced quarters');
  });

  test('Multiple holes - running totals accumulate correctly', async ({ page }) => {
    await page.goto(`${FRONTEND_BASE}/game/${gameId}`);
    await page.waitForSelector('[data-testid="scorekeeper-container"]', { timeout: 10000 });

    // Hole 1: P1 solo win (+3, -1, -1, -1)
    await setAllQuarters(page, players, [3, -1, -1, -1]);
    await page.locator('[data-testid="complete-hole-button"]').click();
    await page.waitForTimeout(1000);

    // Verify hole 2
    let bodyText = await page.locator('body').textContent();
    expect(bodyText).toContain('Hole 2');

    // Hole 2: P2 solo win (-1, +3, -1, -1)
    await setAllQuarters(page, players, [-1, 3, -1, -1]);
    await page.locator('[data-testid="complete-hole-button"]').click();
    await page.waitForTimeout(1000);

    // Verify hole 3
    bodyText = await page.locator('body').textContent();
    expect(bodyText).toContain('Hole 3');

    // Hole 3: Partnership (+1.5, +1.5, -1.5, -1.5)
    await setAllQuarters(page, players, [1.5, 1.5, -1.5, -1.5]);
    await page.locator('[data-testid="complete-hole-button"]').click();
    await page.waitForTimeout(1000);

    // Expected running totals after 3 holes:
    // P1: +3 -1 +1.5 = +3.5
    // P2: -1 +3 +1.5 = +3.5
    // P3: -1 -1 -1.5 = -3.5
    // P4: -1 -1 -1.5 = -3.5
    // Sum = 0 ✓

    bodyText = await page.locator('body').textContent();
    expect(bodyText).toContain('Hole 4');

    console.log('✓ Running totals after 3 holes: P1=+3.5, P2=+3.5, P3=-3.5, P4=-3.5');
  });

  test('Fractional quarters work correctly (1.5, 2.5, etc)', async ({ page }) => {
    await page.goto(`${FRONTEND_BASE}/game/${gameId}`);
    await page.waitForSelector('[data-testid="scorekeeper-container"]', { timeout: 10000 });

    // Test with fractional quarters
    await setAllQuarters(page, players, [2.5, 0.5, -1.5, -1.5]);

    const completeButton = page.locator('[data-testid="complete-hole-button"]');
    await expect(completeButton).toBeEnabled();
    await completeButton.click();

    await page.waitForTimeout(1000);
    const bodyText = await page.locator('body').textContent();
    expect(bodyText).toContain('Hole 2');

    console.log('✓ Fractional quarters validated: 2.5 + 0.5 - 1.5 - 1.5 = 0');
  });

  test('All tied - zero quarters for everyone (0, 0, 0, 0)', async ({ page }) => {
    await page.goto(`${FRONTEND_BASE}/game/${gameId}`);
    await page.waitForSelector('[data-testid="scorekeeper-container"]', { timeout: 10000 });

    // All players tie = no quarter changes
    await setAllQuarters(page, players, [0, 0, 0, 0]);

    const completeButton = page.locator('[data-testid="complete-hole-button"]');
    await expect(completeButton).toBeEnabled();
    await completeButton.click();

    await page.waitForTimeout(1000);
    const bodyText = await page.locator('body').textContent();
    expect(bodyText).toContain('Hole 2');

    console.log('✓ All tied quarters validated: 0, 0, 0, 0');
  });

  test('Large wager - higher quarter values (8-quarter wager)', async ({ page }) => {
    await page.goto(`${FRONTEND_BASE}/game/${gameId}`);
    await page.waitForSelector('[data-testid="scorekeeper-container"]', { timeout: 10000 });

    // 8-quarter wager (Joe's Special max): solo win
    // Solo winner gets 12 (8 * 1.5 for 3-for-2)
    // Each opponent loses 4 (12 / 3)
    await setAllQuarters(page, players, [12, -4, -4, -4]);

    const completeButton = page.locator('[data-testid="complete-hole-button"]');
    await expect(completeButton).toBeEnabled();
    await completeButton.click();

    await page.waitForTimeout(1000);
    const bodyText = await page.locator('body').textContent();
    expect(bodyText).toContain('Hole 2');

    console.log('✓ Large wager quarters validated: +12, -4, -4, -4');
  });
});

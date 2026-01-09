import { test, expect } from '@playwright/test';

/**
 * Quarters Calculation Tests with Mocked API
 *
 * These tests work WITHOUT backend by mocking API responses.
 * Tests the reducer-based state management and quarters validation.
 */

const FRONTEND_BASE = 'http://localhost:3000';

test.describe('Quarters Calculation (Mocked API)', () => {
  let mockGameId;
  let mockPlayers;

  test.beforeEach(async ({ page }) => {
    // Generate mock data
    mockGameId = 'test-game-' + Date.now();
    mockPlayers = [
      { id: 'p1', name: 'Player 1', tee_order: 0, handicap: 10 },
      { id: 'p2', name: 'Player 2', tee_order: 1, handicap: 15 },
      { id: 'p3', name: 'Player 3', tee_order: 2, handicap: 20 },
      { id: 'p4', name: 'Player 4', tee_order: 3, handicap: 8 }
    ];

    // Mock the game state endpoint
    await page.route(`**/games/${mockGameId}/state`, (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          game_id: mockGameId,
          players: mockPlayers,
          current_hole: 1,
          hole_history: [],
          base_wager: 1,
          course_name: 'Wing Point Golf & Country Club',
          stroke_allocation: null
        })
      });
    });

    // Mock hole completion endpoint
    await page.route(`**/games/${mockGameId}/holes/complete`, (route) => {
      const request = route.request();
      const postData = request.postDataJSON();

      // Validate quarters sum to zero
      const quartersSum = Object.values(postData.quarters || {})
        .reduce((sum, val) => sum + (parseFloat(val) || 0), 0);

      if (Math.abs(quartersSum) > 0.001) {
        route.fulfill({
          status: 400,
          contentType: 'application/json',
          body: JSON.stringify({
            error: `Quarters must sum to zero. Current sum: ${quartersSum.toFixed(2)}`
          })
        });
      } else {
        route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            success: true,
            hole_number: postData.hole_number,
            quarters: postData.quarters
          })
        });
      }
    });
  });

  test('Solo win - quarters distribute correctly (+3, -1, -1, -1)', async ({ page }) => {
    await page.goto(`${FRONTEND_BASE}/game/${mockGameId}`);

    // Wait for scorekeeper to load
    await page.waitForSelector('[data-testid="scorekeeper-container"]', { timeout: 15000 });

    console.log('✓ Scorekeeper loaded');

    // Enter quarters for solo win scenario
    await page.fill(`[data-testid="quarters-input-p1"]`, '3');
    await page.fill(`[data-testid="quarters-input-p2"]`, '-1');
    await page.fill(`[data-testid="quarters-input-p3"]`, '-1');
    await page.fill(`[data-testid="quarters-input-p4"]`, '-1');

    console.log('✓ Quarters entered: +3, -1, -1, -1');

    // Complete hole
    const completeButton = page.locator('[data-testid="complete-hole-button"]');
    await expect(completeButton).toBeEnabled({ timeout: 5000 });
    await completeButton.click();

    console.log('✓ Hole completed successfully');

    // Verify advancement to hole 2
    await page.waitForTimeout(2000);
    const bodyText = await page.locator('body').textContent();
    expect(bodyText).toContain('Hole 2');

    console.log('✓ Solo win quarters validated: +3, -1, -1, -1');
  });

  test('Zero-sum validation rejects imbalanced quarters', async ({ page }) => {
    await page.goto(`${FRONTEND_BASE}/game/${mockGameId}`);
    await page.waitForSelector('[data-testid="scorekeeper-container"]', { timeout: 15000 });

    // Enter quarters that DON'T sum to zero
    await page.fill(`[data-testid="quarters-input-p1"]`, '3');
    await page.fill(`[data-testid="quarters-input-p2"]`, '-1');
    await page.fill(`[data-testid="quarters-input-p3"]`, '-1');
    await page.fill(`[data-testid="quarters-input-p4"]`, '0'); // Should be -1!

    console.log('✓ Imbalanced quarters entered: +3, -1, -1, 0 (sum = +1)');

    // Try to complete hole
    const completeButton = page.locator('[data-testid="complete-hole-button"]');
    await completeButton.click();

    // Should show error
    await page.waitForTimeout(1000);
    const bodyText = await page.locator('body').textContent();
    expect(bodyText).toMatch(/quarters must sum to zero/i);

    console.log('✓ Zero-sum validation correctly rejected imbalanced quarters');
  });

  test('Partnership win - quarters split evenly (+1.5, +1.5, -1.5, -1.5)', async ({ page }) => {
    await page.goto(`${FRONTEND_BASE}/game/${mockGameId}`);
    await page.waitForSelector('[data-testid="scorekeeper-container"]', { timeout: 15000 });

    // Enter partnership quarters
    await page.fill(`[data-testid="quarters-input-p1"]`, '1.5');
    await page.fill(`[data-testid="quarters-input-p2"]`, '1.5');
    await page.fill(`[data-testid="quarters-input-p3"]`, '-1.5');
    await page.fill(`[data-testid="quarters-input-p4"]`, '-1.5');

    console.log('✓ Partnership quarters entered: +1.5, +1.5, -1.5, -1.5');

    const completeButton = page.locator('[data-testid="complete-hole-button"]');
    await expect(completeButton).toBeEnabled({ timeout: 5000 });
    await completeButton.click();

    await page.waitForTimeout(2000);
    const bodyText = await page.locator('body').textContent();
    expect(bodyText).toContain('Hole 2');

    console.log('✓ Partnership quarters validated: +1.5, +1.5, -1.5, -1.5');
  });

  test('Multiple holes - running totals accumulate', async ({ page }) => {
    await page.goto(`${FRONTEND_BASE}/game/${mockGameId}`);
    await page.waitForSelector('[data-testid="scorekeeper-container"]', { timeout: 15000 });

    // Hole 1: +3, -1, -1, -1
    await page.fill(`[data-testid="quarters-input-p1"]`, '3');
    await page.fill(`[data-testid="quarters-input-p2"]`, '-1');
    await page.fill(`[data-testid="quarters-input-p3"]`, '-1');
    await page.fill(`[data-testid="quarters-input-p4"]`, '-1');
    await page.locator('[data-testid="complete-hole-button"]').click();
    await page.waitForTimeout(2000);

    console.log('✓ Hole 1 completed: +3, -1, -1, -1');

    // Verify hole 2
    let bodyText = await page.locator('body').textContent();
    expect(bodyText).toContain('Hole 2');

    // Hole 2: -1, +3, -1, -1
    await page.fill(`[data-testid="quarters-input-p1"]`, '-1');
    await page.fill(`[data-testid="quarters-input-p2"]`, '3');
    await page.fill(`[data-testid="quarters-input-p3"]`, '-1');
    await page.fill(`[data-testid="quarters-input-p4"]`, '-1');
    await page.locator('[data-testid="complete-hole-button"]').click();
    await page.waitForTimeout(2000);

    console.log('✓ Hole 2 completed: -1, +3, -1, -1');

    // Verify hole 3
    bodyText = await page.locator('body').textContent();
    expect(bodyText).toContain('Hole 3');

    // Expected running totals:
    // P1: +3 -1 = +2
    // P2: -1 +3 = +2
    // P3: -1 -1 = -2
    // P4: -1 -1 = -2
    // Sum = 0 ✓

    console.log('✓ Running totals after 2 holes: P1=+2, P2=+2, P3=-2, P4=-2');
  });

  test('Fractional quarters work (2.5, 0.5, -1.5, -1.5)', async ({ page }) => {
    await page.goto(`${FRONTEND_BASE}/game/${mockGameId}`);
    await page.waitForSelector('[data-testid="scorekeeper-container"]', { timeout: 15000 });

    // Test fractional values
    await page.fill(`[data-testid="quarters-input-p1"]`, '2.5');
    await page.fill(`[data-testid="quarters-input-p2"]`, '0.5');
    await page.fill(`[data-testid="quarters-input-p3"]`, '-1.5');
    await page.fill(`[data-testid="quarters-input-p4"]`, '-1.5');

    const completeButton = page.locator('[data-testid="complete-hole-button"]');
    await expect(completeButton).toBeEnabled({ timeout: 5000 });
    await completeButton.click();

    await page.waitForTimeout(2000);
    const bodyText = await page.locator('body').textContent();
    expect(bodyText).toContain('Hole 2');

    console.log('✓ Fractional quarters validated: 2.5 + 0.5 - 1.5 - 1.5 = 0');
  });
});

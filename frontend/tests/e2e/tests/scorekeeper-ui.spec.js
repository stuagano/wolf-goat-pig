/**
 * Scorekeeper UI Tests
 * 
 * Tests for scorekeeper form structure and basic interactions.
 * 
 * Run with: npx playwright test tests/scorekeeper-ui.spec.js
 */
import { test, expect } from '@playwright/test';

const API_BASE = 'http://localhost:8333';

// Helper to create a test game
async function createTestGame(request) {
  const response = await request.post(`${API_BASE}/games/create-test?player_count=4`);
  expect(response.ok()).toBeTruthy();
  return await response.json();
}

// Helper to cleanup
async function deleteGame(request, gameId) {
  await request.delete(`${API_BASE}/games/${gameId}`).catch(() => {});
}

test.describe('Scorekeeper UI - Structure', () => {
  let gameData;

  test.beforeAll(async ({ request }) => {
    gameData = await createTestGame(request);
  });

  test.afterAll(async ({ request }) => {
    if (gameData?.game_id) {
      await deleteGame(request, gameData.game_id);
    }
  });

  test('scorekeeper container loads', async ({ page }) => {
    await page.goto(`/game/${gameData.game_id}`);
    await page.waitForSelector('[data-testid="scorekeeper-container"]', { timeout: 10000 });
    
    const container = page.locator('[data-testid="scorekeeper-container"]');
    await expect(container).toBeVisible();
  });

  test('displays hole selector', async ({ page }) => {
    await page.goto(`/game/${gameData.game_id}`);
    await page.waitForSelector('[data-testid="scorekeeper-container"]', { timeout: 10000 });
    
    const holeSelector = page.locator('[data-testid="hole-selector"]');
    await expect(holeSelector).toBeVisible();
  });

  test('displays complete hole button', async ({ page }) => {
    await page.goto(`/game/${gameData.game_id}`);
    await page.waitForSelector('[data-testid="scorekeeper-container"]', { timeout: 10000 });
    
    const completeButton = page.locator('[data-testid="complete-hole-button"]');
    await expect(completeButton).toBeVisible();
  });

  test('displays solo mode button', async ({ page }) => {
    await page.goto(`/game/${gameData.game_id}`);
    await page.waitForSelector('[data-testid="scorekeeper-container"]', { timeout: 10000 });
    
    const soloButton = page.locator('[data-testid="go-solo-button"]');
    await expect(soloButton).toBeVisible();
  });

  test('displays quarters inputs for all 4 players', async ({ page }) => {
    await page.goto(`/game/${gameData.game_id}`);
    await page.waitForSelector('[data-testid="scorekeeper-container"]', { timeout: 10000 });
    
    for (const player of gameData.players) {
      const input = page.locator(`[data-testid="quarters-input-${player.id}"]`);
      await expect(input).toBeVisible();
    }
  });

  test('displays partner buttons for all 4 players', async ({ page }) => {
    await page.goto(`/game/${gameData.game_id}`);
    await page.waitForSelector('[data-testid="scorekeeper-container"]', { timeout: 10000 });
    
    for (const player of gameData.players) {
      const button = page.locator(`[data-testid="partner-${player.id}"]`).first();
      await expect(button).toBeVisible();
    }
  });
});

test.describe('Scorekeeper UI - Navigation', () => {
  let gameData;

  test.beforeEach(async ({ request }) => {
    gameData = await createTestGame(request);
  });

  test.afterEach(async ({ request }) => {
    if (gameData?.game_id) {
      await deleteGame(request, gameData.game_id);
    }
  });

  test('can change hole using selector', async ({ page }) => {
    await page.goto(`/game/${gameData.game_id}`);
    await page.waitForSelector('[data-testid="scorekeeper-container"]', { timeout: 10000 });
    
    const holeSelector = page.locator('[data-testid="hole-selector"]');
    await holeSelector.selectOption('5');
    
    const value = await holeSelector.inputValue();
    expect(value).toBe('5');
  });

  test('solo button can be clicked', async ({ page }) => {
    await page.goto(`/game/${gameData.game_id}`);
    await page.waitForSelector('[data-testid="scorekeeper-container"]', { timeout: 10000 });
    
    const soloButton = page.locator('[data-testid="go-solo-button"]');
    await soloButton.click();
    
    // Button should still be visible after click
    await expect(soloButton).toBeVisible();
  });

  test('partner buttons can be clicked', async ({ page }) => {
    await page.goto(`/game/${gameData.game_id}`);
    await page.waitForSelector('[data-testid="scorekeeper-container"]', { timeout: 10000 });
    
    const player = gameData.players[0];
    const button = page.locator(`[data-testid="partner-${player.id}"]`).first();
    await button.click();
    
    // Button should still be visible
    await expect(button).toBeVisible();
  });
});

test.describe('Scorekeeper UI - Responsive', () => {
  let gameData;

  test.beforeAll(async ({ request }) => {
    gameData = await createTestGame(request);
  });

  test.afterAll(async ({ request }) => {
    if (gameData?.game_id) {
      await deleteGame(request, gameData.game_id);
    }
  });

  test('works on mobile viewport', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto(`/game/${gameData.game_id}`);
    await page.waitForSelector('[data-testid="scorekeeper-container"]', { timeout: 10000 });
    
    await expect(page.locator('[data-testid="scorekeeper-container"]')).toBeVisible();
    await expect(page.locator('[data-testid="complete-hole-button"]')).toBeVisible();
  });

  test('works on tablet viewport', async ({ page }) => {
    await page.setViewportSize({ width: 768, height: 1024 });
    await page.goto(`/game/${gameData.game_id}`);
    await page.waitForSelector('[data-testid="scorekeeper-container"]', { timeout: 10000 });
    
    await expect(page.locator('[data-testid="scorekeeper-container"]')).toBeVisible();
  });

  test('works on desktop viewport', async ({ page }) => {
    await page.setViewportSize({ width: 1920, height: 1080 });
    await page.goto(`/game/${gameData.game_id}`);
    await page.waitForSelector('[data-testid="scorekeeper-container"]', { timeout: 10000 });
    
    await expect(page.locator('[data-testid="scorekeeper-container"]')).toBeVisible();
  });
});

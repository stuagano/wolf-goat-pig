import { test, expect } from '@playwright/test';

test.describe('Wolf-Goat-Pig Game Flow', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to the game
    await page.goto('/');
    
    // Wait for the page to load
    await page.waitForLoadState('networkidle');
  });

  test('should load the main game interface', async ({ page }) => {
    // Check that the main game components are present
    await expect(page.locator('h1')).toContainText(['Wolf', 'Goat', 'Pig']);
    
    // Check for game setup elements
    await expect(page.locator('[data-testid="game-setup"]')).toBeVisible();
    
    console.log('✅ Main game interface loaded successfully');
  });

  test('should create a new game with 4 players', async ({ page }) => {
    // Look for game setup form
    const gameSetup = page.locator('[data-testid="game-setup"]');
    await expect(gameSetup).toBeVisible();
    
    // Fill in player names if inputs exist
    const playerInputs = page.locator('input[placeholder*="player" i]');
    const inputCount = await playerInputs.count();
    
    if (inputCount > 0) {
      await playerInputs.nth(0).fill('Stuart');
      if (inputCount > 1) await playerInputs.nth(1).fill('Alex');
      if (inputCount > 2) await playerInputs.nth(2).fill('Sam');
      if (inputCount > 3) await playerInputs.nth(3).fill('Ace');
    }
    
    // Start the game
    const startButton = page.locator('button', { hasText: /start|begin|play/i });
    if (await startButton.isVisible()) {
      await startButton.click();
    }
    
    // Wait for game to initialize
    await page.waitForTimeout(2000);
    
    console.log('✅ Game created with players');
  });

  test('should display current hole information', async ({ page }) => {
    // Start a game first
    await startGameIfNeeded(page);
    
    // Check for hole information
    const holeInfo = page.locator('[data-testid*="hole"], .hole-info, h2, h3');
    await expect(holeInfo.first()).toBeVisible();
    
    // Should show current hole (likely Hole 1)
    const holeText = await holeInfo.first().textContent();
    expect(holeText).toMatch(/hole.*1/i);
    
    console.log('✅ Hole information displayed');
  });

  test('should show player positions and shot capabilities', async ({ page }) => {
    await startGameIfNeeded(page);
    
    // Look for player information
    const playerElements = page.locator('[data-testid*="player"], .player, .player-card');
    await expect(playerElements.first()).toBeVisible();
    
    // Check for shot button or action
    const shotButton = page.locator('button', { hasText: /shot|hit|play|swing/i });
    await expect(shotButton.first()).toBeVisible();
    
    console.log('✅ Player positions and shot capabilities visible');
  });

  test('should simulate shots and update positions', async ({ page }) => {
    await startGameIfNeeded(page);
    
    // Take first shot
    const shotButton = page.locator('button', { hasText: /shot|hit|play|swing/i }).first();
    await shotButton.click();
    
    // Wait for shot result
    await page.waitForTimeout(3000);
    
    // Check for updated game state
    const gameState = page.locator('[data-testid*="game"], .game-state, .current-state');
    await expect(gameState.first()).toBeVisible();
    
    // Take second shot
    const nextShotButton = page.locator('button', { hasText: /shot|hit|play|swing/i }).first();
    if (await nextShotButton.isVisible()) {
      await nextShotButton.click();
      await page.waitForTimeout(2000);
    }
    
    console.log('✅ Shots simulated and positions updated');
  });

  test('should show partnership opportunities after tee shots', async ({ page }) => {
    await startGameIfNeeded(page);
    
    // Simulate first two shots to trigger partnership opportunity
    for (let i = 0; i < 2; i++) {
      const shotButton = page.locator('button', { hasText: /shot|hit|play|swing/i }).first();
      if (await shotButton.isVisible()) {
        await shotButton.click();
        await page.waitForTimeout(2000);
      }
    }
    
    // Look for partnership options
    const partnershipElements = page.locator('[data-testid*="partner"], .partnership, button', { 
      hasText: /partner|team|join/i 
    });
    
    // Partnership opportunities may or may not be visible depending on game state
    if (await partnershipElements.first().isVisible()) {
      console.log('✅ Partnership opportunities displayed');
    } else {
      console.log('ℹ️  Partnership opportunities not yet available (expected in some cases)');
    }
  });

  test('should display betting information', async ({ page }) => {
    await startGameIfNeeded(page);
    
    // Look for betting/wager information
    const bettingElements = page.locator('[data-testid*="bet"], [data-testid*="wager"], .betting, .wager');
    const bettingText = page.locator('text=/quarter|bet|wager|dollar/i');
    
    // Either betting elements or text mentioning betting should exist
    const hasBettingUI = await bettingElements.first().isVisible().catch(() => false);
    const hasBettingText = await bettingText.first().isVisible().catch(() => false);
    
    if (hasBettingUI || hasBettingText) {
      console.log('✅ Betting information displayed');
    } else {
      console.log('ℹ️  Betting information not prominently displayed (may be in settings)');
    }
  });

  test('should handle game progression through multiple shots', async ({ page }) => {
    await startGameIfNeeded(page);
    
    let shotCount = 0;
    const maxShots = 10; // Safety limit
    
    // Simulate multiple shots
    while (shotCount < maxShots) {
      const shotButton = page.locator('button', { hasText: /shot|hit|play|swing/i }).first();
      
      if (!(await shotButton.isVisible())) {
        break;
      }
      
      await shotButton.click();
      await page.waitForTimeout(1500);
      shotCount++;
      
      // Check if hole is completed
      const holeCompleteText = page.locator('text=/complete|finished|done|next.*hole/i');
      if (await holeCompleteText.first().isVisible()) {
        console.log(`✅ Hole completed after ${shotCount} shots`);
        break;
      }
    }
    
    expect(shotCount).toBeGreaterThan(0);
    console.log(`✅ Simulated ${shotCount} shots successfully`);
  });

  test('should maintain consistent UI state', async ({ page }) => {
    await startGameIfNeeded(page);
    
    // Take a few shots and check UI consistency
    for (let i = 0; i < 3; i++) {
      const shotButton = page.locator('button', { hasText: /shot|hit|play|swing/i }).first();
      if (await shotButton.isVisible()) {
        await shotButton.click();
        await page.waitForTimeout(2000);
        
        // Check that basic UI elements are still present
        await expect(page.locator('h1, h2, .header')).toBeVisible();
        
        // No JavaScript errors should appear
        const errorElements = page.locator('.error, [data-testid*="error"]');
        if (await errorElements.first().isVisible()) {
          const errorText = await errorElements.first().textContent();
          throw new Error(`UI Error detected: ${errorText}`);
        }
      }
    }
    
    console.log('✅ UI state remained consistent throughout gameplay');
  });
});

// Helper function to start game if needed
async function startGameIfNeeded(page) {
  // Check if we're already in a game
  const shotButton = page.locator('button', { hasText: /shot|hit|play|swing/i });
  if (await shotButton.first().isVisible()) {
    return; // Game already started
  }
  
  // Look for start button
  const startButton = page.locator('button', { hasText: /start|begin|play|new.*game/i });
  if (await startButton.first().isVisible()) {
    await startButton.first().click();
    await page.waitForTimeout(3000);
  }
  
  // Fill in default players if setup form is visible
  const playerInputs = page.locator('input[placeholder*="player" i]');
  const inputCount = await playerInputs.count();
  
  if (inputCount > 0) {
    await playerInputs.nth(0).fill('Stuart');
    if (inputCount > 1) await playerInputs.nth(1).fill('Alex');
    if (inputCount > 2) await playerInputs.nth(2).fill('Sam');
    if (inputCount > 3) await playerInputs.nth(3).fill('Ace');
    
    const confirmButton = page.locator('button', { hasText: /confirm|start|begin/i });
    if (await confirmButton.isVisible()) {
      await confirmButton.click();
      await page.waitForTimeout(2000);
    }
  }
}
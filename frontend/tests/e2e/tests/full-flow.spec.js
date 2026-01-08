/**
 * Full Game Flow Test
 * Navigate: Enter Game -> Create New Game -> Score Holes
 */
import { test, expect } from '@playwright/test';

test.describe('Full Game Flow', () => {
  
  test.beforeEach(async ({ page }) => {
    page.on('console', msg => {
      if (msg.type() === 'error') {
        console.log('ERROR:', msg.text());
      }
    });
  });

  test('complete game creation and scoring flow', async ({ page }) => {
    // Step 1: Go to scorekeeper and enter
    await page.goto('/simple-scorekeeper');
    await page.waitForTimeout(2000);
    await page.screenshot({ path: 'test-results/flow-01-start.png', fullPage: true });
    
    // Click Enter Game
    const enterBtn = page.locator('button:has-text("Enter"), a:has-text("Enter")').first();
    if (await enterBtn.isVisible()) {
      await enterBtn.click();
      await page.waitForTimeout(2000);
    }
    
    await page.screenshot({ path: 'test-results/flow-02-after-enter.png', fullPage: true });
    
    // Step 2: Look for Create New Game button
    const createBtn = page.locator('button:has-text("Create New Game"), button:has-text("🎮Create")');
    if (await createBtn.first().isVisible()) {
      console.log('Found Create New Game button');
      await createBtn.first().click();
      await page.waitForTimeout(2000);
      await page.screenshot({ path: 'test-results/flow-03-create-clicked.png', fullPage: true });
      
      console.log('After create click URL:', page.url());
    }
    
    // Step 3: Check if we're on game creation page
    const currentUrl = page.url();
    console.log('Current URL:', currentUrl);
    
    // Look for player inputs
    const playerInputs = await page.locator('input').all();
    console.log('Inputs found:', playerInputs.length);
    
    // Fill player names if found
    for (let i = 0; i < Math.min(playerInputs.length, 4); i++) {
      const placeholder = await playerInputs[i].getAttribute('placeholder').catch(() => '');
      console.log(`Input ${i}: placeholder="${placeholder}"`);
      
      if (placeholder?.toLowerCase().includes('player') || placeholder?.toLowerCase().includes('name')) {
        await playerInputs[i].fill(['Alice', 'Bob', 'Charlie', 'Diana'][i]);
      }
    }
    
    await page.screenshot({ path: 'test-results/flow-04-players.png', fullPage: true });
    
    // Step 4: Look for Start/Create button to begin game
    const startBtn = page.locator('button:has-text("Start"), button:has-text("Create Game"), button[type="submit"]').first();
    if (await startBtn.isVisible()) {
      console.log('Found start button, clicking...');
      await startBtn.click();
      await page.waitForTimeout(3000);
      await page.screenshot({ path: 'test-results/flow-05-game-started.png', fullPage: true });
      
      console.log('After start URL:', page.url());
    }
    
    // Step 5: Check if we're in the game now
    const bodyText = await page.textContent('body');
    console.log('Page content:', bodyText?.slice(0, 600));
    
    // Look for hole indicator
    if (bodyText?.includes('Hole') || bodyText?.includes('hole')) {
      console.log('Found hole indicator - we are in the game!');
    }
    
    // Look for score entry buttons
    const scoreButtons = await page.locator('button').filter({ hasText: /^[1-9]$/ }).all();
    console.log('Score buttons (1-9):', scoreButtons.length);
  });

  test('test mode flow', async ({ page }) => {
    await page.goto('/simple-scorekeeper');
    await page.waitForTimeout(2000);
    
    // Click Enter Game first
    const enterBtn = page.locator('button:has-text("Enter")').first();
    if (await enterBtn.isVisible()) {
      await enterBtn.click();
      await page.waitForTimeout(2000);
    }
    
    // Look for Test Mode button
    const testModeBtn = page.locator('button:has-text("Test Mode"), button:has-text("🧪Test")');
    if (await testModeBtn.first().isVisible()) {
      console.log('Found Test Mode button');
      await testModeBtn.first().click();
      await page.waitForTimeout(2000);
      await page.screenshot({ path: 'test-results/flow-test-mode.png', fullPage: true });
      
      console.log('Test mode URL:', page.url());
      
      const bodyText = await page.textContent('body');
      console.log('Test mode content:', bodyText?.slice(0, 500));
    }
  });

  test('score rounds flow', async ({ page }) => {
    await page.goto('/simple-scorekeeper');
    await page.waitForTimeout(2000);
    
    // Click Enter Game first
    const enterBtn = page.locator('button:has-text("Enter")').first();
    if (await enterBtn.isVisible()) {
      await enterBtn.click();
      await page.waitForTimeout(2000);
    }
    
    // Look for Score Rounds button
    const scoreBtn = page.locator('button:has-text("Score Rounds"), button:has-text("⚽Score")');
    if (await scoreBtn.first().isVisible()) {
      console.log('Found Score Rounds button');
      await scoreBtn.first().click();
      await page.waitForTimeout(2000);
      await page.screenshot({ path: 'test-results/flow-score-rounds.png', fullPage: true });
      
      console.log('Score rounds URL:', page.url());
    }
  });
});

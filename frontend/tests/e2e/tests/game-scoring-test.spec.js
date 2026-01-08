/**
 * Game Scoring Flow Test
 * Tests the SimpleScorekeeper component functionality
 */
import { test, expect } from '@playwright/test';

test.describe('Game Scoring Tests', () => {
  
  test.beforeEach(async ({ page }) => {
    // Log console messages
    page.on('console', msg => {
      if (msg.type() === 'error') {
        console.log('Console ERROR:', msg.text());
      }
    });
    
    // Log network errors
    page.on('requestfailed', request => {
      console.log('Request failed:', request.url(), request.failure()?.errorText);
    });
  });

  test('simple scorekeeper loads and shows game UI', async ({ page }) => {
    await page.goto('/simple-scorekeeper');
    await page.waitForLoadState('networkidle');
    
    // Take initial screenshot
    await page.screenshot({ path: 'test-results/scorekeeper-initial.png', fullPage: true });
    
    // Check for key UI elements
    const bodyText = await page.textContent('body');
    console.log('Page content preview:', bodyText?.slice(0, 500));
    
    // Look for hole number display
    const holeText = await page.locator('text=/hole/i').first().textContent().catch(() => null);
    console.log('Hole text found:', holeText);
    
    // Look for player elements
    const playerElements = await page.locator('[class*="player"], [data-testid*="player"]').count();
    console.log('Player elements found:', playerElements);
  });

  test('inspect scorekeeper structure', async ({ page }) => {
    await page.goto('/simple-scorekeeper');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000); // Wait for React to render
    
    // Get all buttons
    const buttons = await page.locator('button').all();
    console.log('Total buttons:', buttons.length);
    
    for (let i = 0; i < Math.min(buttons.length, 10); i++) {
      const text = await buttons[i].textContent();
      const isVisible = await buttons[i].isVisible();
      if (isVisible && text?.trim()) {
        console.log(`Button ${i}: "${text.trim().slice(0, 50)}"`);
      }
    }
    
    // Get all input fields
    const inputs = await page.locator('input').all();
    console.log('Total inputs:', inputs.length);
    
    // Get all select dropdowns
    const selects = await page.locator('select').all();
    console.log('Total selects:', selects.length);
    
    // Look for score-related elements
    const scoreElements = await page.locator('[class*="score"], [data-testid*="score"]').count();
    console.log('Score-related elements:', scoreElements);
    
    await page.screenshot({ path: 'test-results/scorekeeper-structure.png', fullPage: true });
  });

  test('check for any error messages on page', async ({ page }) => {
    await page.goto('/simple-scorekeeper');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000);
    
    // Look for error elements
    const errorElements = await page.locator('[class*="error"], [role="alert"], .error, .alert-danger').all();
    console.log('Error elements found:', errorElements.length);
    
    for (const el of errorElements) {
      const text = await el.textContent();
      if (text?.trim()) {
        console.log('Error content:', text.trim());
      }
    }
    
    // Check for loading states
    const loadingElements = await page.locator('[class*="loading"], [class*="spinner"]').count();
    console.log('Loading elements:', loadingElements);
    
    await page.screenshot({ path: 'test-results/scorekeeper-errors.png', fullPage: true });
  });

  test('try to interact with game setup', async ({ page }) => {
    await page.goto('/simple-scorekeeper');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000);
    
    // Look for "New Game" or similar button
    const newGameBtn = await page.locator('button:has-text("New"), button:has-text("Create"), button:has-text("Start")').first();
    if (await newGameBtn.isVisible().catch(() => false)) {
      console.log('Found new game button');
      await newGameBtn.click();
      await page.waitForTimeout(1000);
      await page.screenshot({ path: 'test-results/after-new-game-click.png', fullPage: true });
    }
    
    // Look for player name inputs
    const playerInputs = await page.locator('input[placeholder*="player" i], input[placeholder*="name" i]').all();
    console.log('Player name inputs:', playerInputs.length);
    
    // Look for course selection
    const courseSelect = await page.locator('select, [class*="dropdown"]').first();
    if (await courseSelect.isVisible().catch(() => false)) {
      console.log('Found course/dropdown selector');
    }
    
    await page.screenshot({ path: 'test-results/game-setup.png', fullPage: true });
  });

  test('examine page for scoring controls', async ({ page }) => {
    await page.goto('/simple-scorekeeper');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(3000);
    
    // Screenshot the full page
    await page.screenshot({ path: 'test-results/full-scorekeeper.png', fullPage: true });
    
    // Get page HTML structure (first 5000 chars)
    const html = await page.content();
    
    // Look for common score-related patterns
    const patterns = [
      /hole.*\d/gi,
      /score/gi,
      /par/gi,
      /player/gi,
      /wager/gi,
      /quarter/gi,
      /complete/gi,
    ];
    
    for (const pattern of patterns) {
      const matches = html.match(pattern);
      if (matches) {
        console.log(`Pattern "${pattern}": ${matches.length} matches`);
      }
    }
    
    // Find clickable elements that might advance the hole
    const nextButtons = await page.locator('button:has-text("Next"), button:has-text("Complete"), button:has-text("Submit")').all();
    console.log('Next/Complete/Submit buttons:', nextButtons.length);
    
    for (const btn of nextButtons) {
      const text = await btn.textContent();
      const visible = await btn.isVisible();
      console.log(`  - "${text?.trim()}" visible: ${visible}`);
    }
  });
});

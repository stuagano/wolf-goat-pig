/**
 * Game Interaction Test - With Mock Auth
 * Full flow: Enter game -> Set up players -> Score holes
 */
import { test, expect } from '@playwright/test';

test.describe('Game Interaction Flow', () => {
  
  test.beforeEach(async ({ page }) => {
    page.on('console', msg => {
      if (msg.type() === 'error') {
        console.log('Console ERROR:', msg.text());
      }
    });
    
    page.on('requestfailed', request => {
      console.log('Request FAILED:', request.url());
    });
  });

  test('enter game and explore UI', async ({ page }) => {
    await page.goto('/simple-scorekeeper');
    await page.waitForTimeout(2000);
    
    await page.screenshot({ path: 'test-results/01-initial.png', fullPage: true });
    
    // Look for Enter Game button
    const enterGameBtn = page.locator('button:has-text("Enter Game"), a:has-text("Enter Game")');
    if (await enterGameBtn.isVisible()) {
      console.log('Found "Enter Game" button, clicking...');
      await enterGameBtn.click();
      await page.waitForTimeout(2000);
      await page.screenshot({ path: 'test-results/02-after-enter.png', fullPage: true });
    }
    
    // Check current page content
    const bodyText = await page.textContent('body');
    console.log('Page after click:', bodyText?.slice(0, 500));
    
    // List all buttons
    const buttons = await page.locator('button').all();
    console.log('\nAll buttons on page:');
    for (const btn of buttons) {
      const text = await btn.textContent().catch(() => '');
      const visible = await btn.isVisible().catch(() => false);
      if (visible && text?.trim()) {
        console.log(`  - "${text.trim().slice(0, 50)}"`);
      }
    }
  });

  test('browse without login', async ({ page }) => {
    await page.goto('/simple-scorekeeper');
    await page.waitForTimeout(2000);
    
    // Try "Browse Without Login"
    const browseBtn = page.locator('button:has-text("Browse"), a:has-text("Browse")');
    if (await browseBtn.isVisible()) {
      console.log('Found "Browse" button, clicking...');
      await browseBtn.click();
      await page.waitForTimeout(2000);
      await page.screenshot({ path: 'test-results/03-browse-mode.png', fullPage: true });
      
      const bodyText = await page.textContent('body');
      console.log('Browse mode content:', bodyText?.slice(0, 500));
    }
  });

  test('navigate to home and find game options', async ({ page }) => {
    await page.goto('/');
    await page.waitForTimeout(2000);
    await page.screenshot({ path: 'test-results/04-home.png', fullPage: true });
    
    const bodyText = await page.textContent('body');
    console.log('Home page:', bodyText?.slice(0, 800));
    
    // Look for game-related links
    const links = await page.locator('a').all();
    console.log('\nLinks on home:');
    for (const link of links.slice(0, 15)) {
      const text = await link.textContent().catch(() => '');
      const href = await link.getAttribute('href').catch(() => '');
      if (text?.trim()) {
        console.log(`  "${text.trim().slice(0, 30)}" -> ${href}`);
      }
    }
  });

  test('go to create game page', async ({ page }) => {
    await page.goto('/create-game');
    await page.waitForTimeout(2000);
    await page.screenshot({ path: 'test-results/05-create-game.png', fullPage: true });
    
    const bodyText = await page.textContent('body');
    console.log('Create game page:', bodyText?.slice(0, 600));
    
    // Check for form elements
    const inputs = await page.locator('input').all();
    console.log('\nInputs found:', inputs.length);
    for (const input of inputs) {
      const placeholder = await input.getAttribute('placeholder').catch(() => '');
      const name = await input.getAttribute('name').catch(() => '');
      const visible = await input.isVisible();
      if (visible) {
        console.log(`  Input: name="${name}" placeholder="${placeholder}"`);
      }
    }
    
    const selects = await page.locator('select').all();
    console.log('Selects found:', selects.length);
  });

  test('try active games page', async ({ page }) => {
    await page.goto('/active-games');
    await page.waitForTimeout(2000);
    await page.screenshot({ path: 'test-results/06-active-games.png', fullPage: true });
    
    const bodyText = await page.textContent('body');
    console.log('Active games:', bodyText?.slice(0, 500));
  });

  test('full game creation flow', async ({ page }) => {
    // Go to create game
    await page.goto('/create-game');
    await page.waitForTimeout(2000);
    
    await page.screenshot({ path: 'test-results/07-create-start.png', fullPage: true });
    
    // Try to fill in player names if inputs exist
    const playerInputs = await page.locator('input[placeholder*="Player"], input[placeholder*="Name"], input[name*="player"]').all();
    console.log('Player inputs found:', playerInputs.length);
    
    if (playerInputs.length >= 4) {
      await playerInputs[0].fill('Alice');
      await playerInputs[1].fill('Bob');
      await playerInputs[2].fill('Charlie');
      await playerInputs[3].fill('Diana');
      
      await page.screenshot({ path: 'test-results/08-players-filled.png', fullPage: true });
    }
    
    // Look for create/start button
    const createBtn = page.locator('button:has-text("Create"), button:has-text("Start"), button[type="submit"]').first();
    if (await createBtn.isVisible()) {
      console.log('Found create button');
      await createBtn.click();
      await page.waitForTimeout(3000);
      await page.screenshot({ path: 'test-results/09-after-create.png', fullPage: true });
      
      console.log('After create URL:', page.url());
    }
  });

  test('direct scorekeeper with game ID', async ({ page }) => {
    // Try to access scorekeeper directly
    await page.goto('/simple-scorekeeper/test-game-123');
    await page.waitForTimeout(2000);
    await page.screenshot({ path: 'test-results/10-direct-scorekeeper.png', fullPage: true });
    
    const url = page.url();
    console.log('Direct scorekeeper URL:', url);
    
    const bodyText = await page.textContent('body');
    console.log('Content:', bodyText?.slice(0, 500));
  });
});

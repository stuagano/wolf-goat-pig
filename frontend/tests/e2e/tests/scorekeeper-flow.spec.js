/**
 * SimpleScorekeeper Flow Test
 * Tests the full game scoring flow with mock auth enabled
 */
import { test, expect } from '@playwright/test';

test.describe('SimpleScorekeeper Full Flow', () => {
  
  test.beforeEach(async ({ page }) => {
    // Log all console messages
    page.on('console', msg => {
      const type = msg.type();
      if (type === 'error' || type === 'warning') {
        console.log(`Console ${type}:`, msg.text());
      }
    });
    
    // Log network errors
    page.on('requestfailed', request => {
      console.log('Request failed:', request.url(), request.failure()?.errorText);
    });
  });

  test('load scorekeeper and explore UI', async ({ page }) => {
    await page.goto('/simple-scorekeeper');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(3000);
    
    // Screenshot initial state
    await page.screenshot({ path: 'test-results/scorekeeper-loaded.png', fullPage: true });
    
    // Check current URL
    const url = page.url();
    console.log('Current URL:', url);
    
    // Get page title
    const title = await page.title();
    console.log('Page title:', title);
    
    // Check what's visible
    const bodyText = await page.textContent('body');
    console.log('Page text preview:', bodyText?.slice(0, 1000));
    
    // Check if we're past login
    const hasLoginButton = await page.locator('button:has-text("Log In")').isVisible().catch(() => false);
    console.log('Login button visible:', hasLoginButton);
    
    if (hasLoginButton) {
      console.log('Still on login page - mock auth may not be working');
      return;
    }
    
    // Look for hole number
    const holeIndicator = await page.locator('text=/Hole\\s*\\d/i').first().textContent().catch(() => null);
    console.log('Hole indicator:', holeIndicator);
    
    // Count buttons
    const buttons = await page.locator('button').all();
    console.log('Total buttons:', buttons.length);
    
    // List visible buttons
    for (const btn of buttons.slice(0, 15)) {
      const text = await btn.textContent().catch(() => '');
      const visible = await btn.isVisible().catch(() => false);
      if (visible && text?.trim()) {
        console.log(`  Button: "${text.trim().slice(0, 40)}"`);
      }
    }
  });

  test('navigate through app sections', async ({ page }) => {
    // Try home page first
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    await page.screenshot({ path: 'test-results/home-mockauth.png', fullPage: true });
    
    // Check for navigation elements
    const navLinks = await page.locator('nav a, header a, [role="navigation"] a').all();
    console.log('Navigation links found:', navLinks.length);
    
    for (const link of navLinks.slice(0, 10)) {
      const text = await link.textContent().catch(() => '');
      const href = await link.getAttribute('href').catch(() => '');
      console.log(`  Nav: "${text?.trim()}" -> ${href}`);
    }
    
    // Try to find and click scorekeeper link
    const scorekeeperLink = await page.locator('a:has-text("Score"), a:has-text("Game"), a[href*="score"]').first();
    if (await scorekeeperLink.isVisible().catch(() => false)) {
      console.log('Found scorekeeper link, clicking...');
      await scorekeeperLink.click();
      await page.waitForLoadState('networkidle');
      await page.waitForTimeout(2000);
      await page.screenshot({ path: 'test-results/after-nav-click.png', fullPage: true });
    }
  });

  test('check API connectivity from page', async ({ page }) => {
    await page.goto('/simple-scorekeeper');
    await page.waitForLoadState('networkidle');
    
    // Test API call from browser context
    const apiResult = await page.evaluate(async () => {
      const results = {};
      
      // Test courses endpoint
      try {
        const res = await fetch('http://localhost:8333/courses');
        results.courses = { status: res.status, ok: res.ok };
      } catch (e) {
        results.courses = { error: e.message };
      }
      
      // Test health endpoint
      try {
        const res = await fetch('http://localhost:8333/health');
        results.health = { status: res.status, data: await res.json() };
      } catch (e) {
        results.health = { error: e.message };
      }
      
      // Test games endpoint
      try {
        const res = await fetch('http://localhost:8333/games');
        results.games = { status: res.status };
      } catch (e) {
        results.games = { error: e.message };
      }
      
      return results;
    });
    
    console.log('API Results:', JSON.stringify(apiResult, null, 2));
  });

  test('interact with scorekeeper controls', async ({ page }) => {
    await page.goto('/simple-scorekeeper');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(3000);
    
    // Check if we can find player inputs or game controls
    const inputs = await page.locator('input').all();
    console.log('Input fields:', inputs.length);
    
    for (const input of inputs.slice(0, 10)) {
      const placeholder = await input.getAttribute('placeholder').catch(() => '');
      const type = await input.getAttribute('type').catch(() => '');
      const visible = await input.isVisible().catch(() => false);
      if (visible) {
        console.log(`  Input: type="${type}" placeholder="${placeholder}"`);
      }
    }
    
    // Look for score entry buttons (numbers)
    const numberButtons = await page.locator('button').filter({ hasText: /^[1-9]$/ }).all();
    console.log('Number buttons (for scores):', numberButtons.length);
    
    // Look for action buttons
    const actionButtons = await page.locator('button:has-text("Complete"), button:has-text("Next"), button:has-text("Save"), button:has-text("Submit")').all();
    console.log('Action buttons:', actionButtons.length);
    
    for (const btn of actionButtons) {
      const text = await btn.textContent();
      console.log(`  Action: "${text?.trim()}"`);
    }
    
    await page.screenshot({ path: 'test-results/scorekeeper-controls.png', fullPage: true });
  });

  test('try to start a new game', async ({ page }) => {
    await page.goto('/simple-scorekeeper');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(3000);
    
    await page.screenshot({ path: 'test-results/before-game-start.png', fullPage: true });
    
    // Look for "Create Game" or "New Game" or "Start" buttons
    const createButtons = await page.locator('button').filter({ 
      hasText: /create|new|start/i 
    }).all();
    
    console.log('Create/New/Start buttons:', createButtons.length);
    
    for (const btn of createButtons) {
      const text = await btn.textContent();
      const visible = await btn.isVisible();
      const disabled = await btn.isDisabled();
      console.log(`  "${text?.trim()}" - visible: ${visible}, disabled: ${disabled}`);
    }
    
    // If we find a visible create button, click it
    const visibleCreateBtn = await page.locator('button:has-text("Create"), button:has-text("New Game"), button:has-text("Start Game")').first();
    if (await visibleCreateBtn.isVisible().catch(() => false)) {
      console.log('Clicking create/start button...');
      await visibleCreateBtn.click();
      await page.waitForTimeout(2000);
      await page.screenshot({ path: 'test-results/after-create-click.png', fullPage: true });
      
      // Check for modal or new UI
      const modal = await page.locator('[role="dialog"], .modal, [class*="modal"]').first();
      if (await modal.isVisible().catch(() => false)) {
        console.log('Modal appeared');
        await page.screenshot({ path: 'test-results/create-game-modal.png' });
      }
    }
  });
});

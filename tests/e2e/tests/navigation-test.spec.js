import { test, expect } from '@playwright/test';

const navigationLinks = [
  { path: '/about', name: 'About' },
  { path: '/rules', name: 'Rules' },
  { path: '/sheets', name: 'Sheets' },
  { path: '/leaderboard', name: 'Leaderboard' },
  { path: '/live-sync', name: 'Live Sync' },
  { path: '/tutorial', name: 'Tutorial' },
  { path: '/analytics', name: 'Analytics' },
  { path: '/simulation', name: 'Simulation' },
  { path: '/analyzer', name: 'Analyzer' },
  { path: '/signup', name: 'Signup' }
];

test.describe('Navigation Links', () => {
  test.beforeEach(async ({ page }) => {
    // Disable authentication for testing
    await page.addInitScript(() => {
      window.localStorage.setItem('REACT_APP_USE_MOCK_AUTH', 'true');
    });
  });

  navigationLinks.forEach(({ path, name }) => {
    test(`${name} loads without error`, async ({ page }) => {
      // Go directly to the path
      await page.goto(`http://localhost:3000${path}`);
      
      // Wait for the page to load
      await page.waitForLoadState('networkidle');
      
      // Check that we don't get a 404 or error page
      const body = await page.textContent('body');
      expect(body).not.toContain('404');
      expect(body).not.toContain('Page not found');
      expect(body).not.toContain('Cannot GET');
      
      // Check that some content is present (not blank)
      expect(body.length).toBeGreaterThan(50);
      
      // Check that navigation is present
      const navElement = page.locator('nav');
      await expect(navElement).toBeVisible();
      
      // Check that the page title is reasonable
      const title = await page.title();
      expect(title).toBeTruthy();
    });
  });
});

test.describe('Navigation', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('http://localhost:3000/');
    // Skip splash screen if present
    const startButton = page.locator('button:has-text("Start New Game")');
    if (await startButton.isVisible()) {
      await startButton.click();
      await page.waitForTimeout(500);
    }
  });

  test('all navigation buttons are present', async ({ page }) => {
    const navButtons = [
      'Home',
      'Game', 
      'Practice',
      'Leaderboard',
      'Tutorial',
      'About',
      'Rules',
      'Sheets',
      'Analytics',
      'Analyzer',
      'Signup',
      'Live Sync'
    ];

    for (const buttonText of navButtons) {
      const button = page.locator(`button:has-text("${buttonText}")`);
      await expect(button).toBeVisible();
    }
  });

  test('navigation buttons are clickable', async ({ page }) => {
    // Test a few key navigation buttons
    const testButtons = [
      { text: 'About', expectedUrl: '/about' },
      { text: 'Rules', expectedUrl: '/rules' },
      { text: 'Leaderboard', expectedUrl: '/leaderboard' }
    ];

    for (const { text, expectedUrl } of testButtons) {
      const button = page.locator(`button:has-text("${text}")`);
      await button.click();
      await page.waitForTimeout(500);
      
      // Check that URL changed
      expect(page.url()).toContain(expectedUrl);
      
      // Go back to home for next test
      await page.goto('http://localhost:3000/');
      const startButton = page.locator('button:has-text("Start New Game")');
      if (await startButton.isVisible()) {
        await startButton.click();
        await page.waitForTimeout(500);
      }
    }
  });
});
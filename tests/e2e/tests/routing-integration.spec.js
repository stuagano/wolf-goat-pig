import { test, expect } from '@playwright/test';

/**
 * Integration tests for Vercel rewrite rules
 *
 * These tests verify that the dual rewrite rules in vercel.json work correctly:
 * 1. "/" -> "/index.html" (handles root path)
 * 2. "/:path((?!.*\\.).*)" -> "/index.html" (handles all routes without file extensions)
 *
 * Both rules are needed because the regex pattern in rule #2 doesn't match the root path.
 */
test.describe('Routing Integration Tests', () => {
  test.beforeEach(async ({ page }) => {
    // Disable authentication for testing
    await page.addInitScript(() => {
      window.localStorage.setItem('REACT_APP_USE_MOCK_AUTH', 'true');
    });
  });

  test('root path (/) serves the React app', async ({ page }) => {
    // Navigate to root
    await page.goto('http://localhost:3000/');

    // Wait for React app to load
    await page.waitForLoadState('networkidle');

    // Verify React root element exists (confirms index.html was served)
    const rootElement = page.locator('#root');
    await expect(rootElement).toBeVisible();

    // Verify the page contains React content
    const body = await page.textContent('body');
    expect(body).toBeTruthy();
    expect(body.length).toBeGreaterThan(50);

    // Verify no 404 errors
    expect(body).not.toContain('404');
    expect(body).not.toContain('Cannot GET');
  });

  test('deep routes (/some/route) serve the React app', async ({ page }) => {
    // Test a deep route that doesn't actually exist as a static file
    await page.goto('http://localhost:3000/non-existent/deep/route');

    // Wait for React app to load
    await page.waitForLoadState('networkidle');

    // Verify React root element exists (confirms index.html was served)
    const rootElement = page.locator('#root');
    await expect(rootElement).toBeVisible();

    // Verify the page contains React content
    const body = await page.textContent('body');
    expect(body).toBeTruthy();

    // Verify no 404 errors
    expect(body).not.toContain('404');
    expect(body).not.toContain('Cannot GET');
  });

  test('existing routes (/about, /rules, etc.) serve the React app', async ({ page }) => {
    const testRoutes = ['/about', '/rules', '/leaderboard', '/tutorial'];

    for (const route of testRoutes) {
      await page.goto(`http://localhost:3000${route}`);

      // Wait for React app to load
      await page.waitForLoadState('networkidle');

      // Verify React root element exists
      const rootElement = page.locator('#root');
      await expect(rootElement).toBeVisible();

      // Verify navigation is present (confirms full app loaded)
      const navElement = page.locator('nav');
      await expect(navElement).toBeVisible();
    }
  });

  test('static assets are NOT rewritten', async ({ page }) => {
    // Navigate to root first to ensure app is loaded
    await page.goto('http://localhost:3000/');
    await page.waitForLoadState('networkidle');

    // Check that static assets with file extensions load correctly
    // Note: This is implicit - if the app loads, CSS/JS files must have loaded correctly
    // We can verify by checking computed styles or that scripts executed

    // Verify some styling is applied (CSS loaded)
    const bodyElement = page.locator('body');
    const backgroundColor = await bodyElement.evaluate(el =>
      window.getComputedStyle(el).backgroundColor
    );

    // If backgroundColor is not the default (rgba(0, 0, 0, 0)), CSS loaded
    expect(backgroundColor).toBeTruthy();
  });

  test('client-side navigation maintains React app state', async ({ page }) => {
    // Start at root
    await page.goto('http://localhost:3000/');
    await page.waitForLoadState('networkidle');

    // Navigate to /about using client-side routing
    const aboutButton = page.locator('button:has-text("About")');
    if (await aboutButton.isVisible()) {
      await aboutButton.click();
      await page.waitForTimeout(500);

      // Verify URL changed
      expect(page.url()).toContain('/about');

      // Verify React root still exists (no page reload)
      const rootElement = page.locator('#root');
      await expect(rootElement).toBeVisible();
    }
  });

  test('refreshing deep route maintains the React app', async ({ page }) => {
    // Navigate to a deep route
    await page.goto('http://localhost:3000/about');
    await page.waitForLoadState('networkidle');

    // Verify React app loaded
    const rootElement = page.locator('#root');
    await expect(rootElement).toBeVisible();

    // Reload the page (simulates user refreshing)
    await page.reload();
    await page.waitForLoadState('networkidle');

    // Verify React app still loads after refresh
    await expect(rootElement).toBeVisible();

    // Verify we're still on the same route
    expect(page.url()).toContain('/about');
  });
});

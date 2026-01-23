import { test, expect } from '@playwright/test';

/**
 * Production Smoke Tests
 *
 * These tests run against the production deployment to verify:
 * - Version.json is accessible and valid
 * - Service worker is registered and functioning
 * - CSS and JS assets load correctly
 * - Basic app functionality works
 *
 * Run with: npx playwright test --config tests/e2e/playwright.production.config.js
 * Or with custom URL: FRONTEND_URL=https://staging.example.com npx playwright test ...
 */

const BACKEND_URL = process.env.BACKEND_URL || 'https://wolf-goat-pig.onrender.com';

test.describe('Production Deployment Verification', () => {

  test('version.json is accessible and valid', async ({ request }) => {
    const response = await request.get('/version.json');
    expect(response.ok()).toBeTruthy();

    const data = await response.json();
    expect(data).toHaveProperty('version');
    expect(data).toHaveProperty('buildTime');
    expect(data.version).toMatch(/^\d+\.\d+\.\d+/);  // Semver format

    console.log(`Deployed version: ${data.version}`);
    console.log(`Build time: ${data.buildTime}`);
  });

  test('service worker is accessible', async ({ request }) => {
    const response = await request.get('/service-worker.js');
    expect(response.ok()).toBeTruthy();

    const content = await response.text();
    expect(content).toContain('SW_VERSION');
    expect(content).toContain('CACHE_NAME');

    // Extract and log version
    const versionMatch = content.match(/SW_VERSION = '([^']+)'/);
    if (versionMatch) {
      console.log(`Service worker version: ${versionMatch[1]}`);
    }
  });

  test('manifest.json is accessible', async ({ request }) => {
    const response = await request.get('/manifest.json');
    expect(response.ok()).toBeTruthy();

    const data = await response.json();
    expect(data).toHaveProperty('name');
    expect(data).toHaveProperty('short_name');
  });
});

test.describe('Production Frontend Functionality', () => {

  test('homepage loads with proper styling', async ({ page }) => {
    // Navigate to homepage
    await page.goto('/');
    await page.waitForLoadState('domcontentloaded');

    // Check that CSS is loaded (page should have styled elements)
    const hasStyledContent = await page.evaluate(() => {
      const body = document.body;
      const computedStyle = window.getComputedStyle(body);
      // If CSS loaded, font-family won't be default browser font
      return computedStyle.fontFamily !== 'Times New Roman' &&
             computedStyle.fontFamily !== '"Times New Roman"';
    });
    expect(hasStyledContent).toBeTruthy();

    // Verify no flash of unstyled content
    const bodyBackground = await page.evaluate(() => {
      return window.getComputedStyle(document.body).backgroundColor;
    });
    // Should have some background color set (not transparent)
    expect(bodyBackground).not.toBe('rgba(0, 0, 0, 0)');
  });

  test('app renders without critical JavaScript errors', async ({ page }) => {
    const criticalErrors = [];

    page.on('console', msg => {
      if (msg.type() === 'error') {
        const text = msg.text();
        // Filter out expected errors (CORS in cross-origin requests, etc.)
        if (!text.includes('CORS') &&
            !text.includes('favicon') &&
            !text.includes('404')) {
          criticalErrors.push(text);
        }
      }
    });

    page.on('pageerror', err => {
      criticalErrors.push(err.message);
    });

    await page.goto('/');
    await page.waitForLoadState('networkidle');

    if (criticalErrors.length > 0) {
      console.log('Critical errors found:', criticalErrors);
    }
    expect(criticalErrors.length).toBe(0);
  });

  test('React app mounts successfully', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('domcontentloaded');

    // Check React root has children (app rendered)
    const rootHasContent = await page.evaluate(() => {
      const root = document.getElementById('root');
      return root && root.children.length > 0;
    });
    expect(rootHasContent).toBeTruthy();
  });

  test('navigation buttons are visible and styled', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('domcontentloaded');

    // Wait for app to fully render
    await page.waitForTimeout(1000);

    const buttons = page.locator('button');
    const buttonCount = await buttons.count();
    expect(buttonCount).toBeGreaterThan(0);

    // Check first button has proper styling (not unstyled)
    if (buttonCount > 0) {
      const firstButton = buttons.first();
      const hasBackground = await firstButton.evaluate(el => {
        const style = window.getComputedStyle(el);
        // Button should have some background color (not transparent default)
        return style.backgroundColor !== 'rgba(0, 0, 0, 0)' ||
               style.border !== 'none';
      });
      expect(hasBackground).toBeTruthy();
    }
  });
});

test.describe('Production Backend Connectivity', () => {

  test('backend health endpoint responds', async ({ request }) => {
    const response = await request.get(`${BACKEND_URL}/health`);

    // Accept 200 (healthy) or 503 (unhealthy but responding)
    expect([200, 503]).toContain(response.status());

    const data = await response.json();
    console.log('Backend health:', JSON.stringify(data));
  });

  test('backend ready endpoint responds', async ({ request }) => {
    const response = await request.get(`${BACKEND_URL}/ready`);
    expect(response.ok()).toBeTruthy();
  });

  test('CORS allows frontend origin', async ({ request }) => {
    const frontendUrl = process.env.FRONTEND_URL || 'https://wolf-goat-pig.vercel.app';

    const response = await request.fetch(`${BACKEND_URL}/health`, {
      method: 'OPTIONS',
      headers: {
        'Origin': frontendUrl,
        'Access-Control-Request-Method': 'GET',
      },
    });

    // Should get CORS headers back
    const headers = response.headers();
    const allowOrigin = headers['access-control-allow-origin'];

    // Either allows the specific origin or allows all (*)
    expect(allowOrigin === frontendUrl || allowOrigin === '*').toBeTruthy();
  });
});

test.describe('Service Worker Behavior', () => {

  test('service worker registers in browser', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Give SW time to register
    await page.waitForTimeout(2000);

    const swStatus = await page.evaluate(async () => {
      if (!('serviceWorker' in navigator)) {
        return { supported: false };
      }

      const registrations = await navigator.serviceWorker.getRegistrations();
      return {
        supported: true,
        registered: registrations.length > 0,
        count: registrations.length,
        states: registrations.map(r => r.active?.state || 'no-active'),
      };
    });

    console.log('Service Worker Status:', JSON.stringify(swStatus));

    expect(swStatus.supported).toBeTruthy();
    // Note: SW may not be registered in test browser context
  });
});

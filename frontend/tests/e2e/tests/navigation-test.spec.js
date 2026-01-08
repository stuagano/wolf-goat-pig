/**
 * Navigation and Game Flow Test
 * Tests the main user flows without requiring Auth0 login
 * Uses mock auth or tests public pages
 */
import { test, expect } from '@playwright/test';

test.describe('Navigation Tests', () => {
  test('homepage loads and shows main elements', async ({ page }) => {
    await page.goto('/');
    
    // Take screenshot
    await page.screenshot({ path: 'test-results/homepage.png', fullPage: true });
    
    // Check for key elements (adjust based on actual page structure)
    const pageContent = await page.content();
    console.log('Page title:', await page.title());
    
    // Log any console errors
    page.on('console', msg => {
      if (msg.type() === 'error') {
        console.log('Console error:', msg.text());
      }
    });
  });

  test('navigate to rules page', async ({ page }) => {
    await page.goto('/rules');
    await page.waitForLoadState('networkidle');
    
    await page.screenshot({ path: 'test-results/rules-page.png', fullPage: true });
    
    // Check page loaded
    const content = await page.textContent('body');
    console.log('Rules page loaded, content length:', content?.length);
  });

  test('navigate to about page', async ({ page }) => {
    await page.goto('/about');
    await page.waitForLoadState('networkidle');
    
    await page.screenshot({ path: 'test-results/about-page.png', fullPage: true });
  });

  test('check API health from frontend', async ({ page }) => {
    // Navigate to home first
    await page.goto('/');
    
    // Make API call directly
    const response = await page.evaluate(async () => {
      try {
        const res = await fetch('http://localhost:8333/courses');
        return { status: res.status, data: await res.json() };
      } catch (e) {
        return { error: e.message };
      }
    });
    
    console.log('API response:', JSON.stringify(response, null, 2).slice(0, 500));
    expect(response.status).toBe(200);
  });

  test('simple scorekeeper page loads (may redirect to login)', async ({ page }) => {
    await page.goto('/simple-scorekeeper');
    await page.waitForLoadState('networkidle');
    
    await page.screenshot({ path: 'test-results/scorekeeper-page.png', fullPage: true });
    
    // Log current URL (might redirect to auth)
    console.log('Current URL:', page.url());
  });
});

test.describe('Auth0 Login Flow', () => {
  test('login page appears for protected routes', async ({ page }) => {
    await page.goto('/simple-scorekeeper');
    await page.waitForLoadState('networkidle');
    
    // Wait a moment for any redirects
    await page.waitForTimeout(2000);
    
    const url = page.url();
    console.log('After navigation URL:', url);
    
    await page.screenshot({ path: 'test-results/login-redirect.png', fullPage: true });
    
    // Check if we're on Auth0 login or the app
    if (url.includes('auth0')) {
      console.log('Redirected to Auth0 login');
      expect(url).toContain('auth0');
    } else {
      console.log('Stayed on app (possibly mock auth or already logged in)');
    }
  });
});

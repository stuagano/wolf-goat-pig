import { test, expect } from '@playwright/test';

/**
 * Smoke Tests - Basic validation that the app is working
 *
 * These tests validate core functionality:
 * - Backend is running and responsive
 * - Frontend loads correctly
 * - Basic navigation works
 *
 * Run with: npx playwright test tests/smoke-test.spec.js
 */

const API_BASE = 'http://localhost:8333';

test.describe('Smoke Tests - Backend', () => {
  test('backend ready endpoint responds', async ({ request }) => {
    // Use /ready endpoint which is lightweight and always responds
    const response = await request.get(`${API_BASE}/ready`);
    expect(response.ok()).toBeTruthy();

    const data = await response.json();
    expect(data).toHaveProperty('status', 'ready');
  });

  test('backend health endpoint responds', async ({ request }) => {
    // Health check may return 503 in test environment, but should respond
    const response = await request.get(`${API_BASE}/health`);
    
    // Accept either success (200) or service unavailable (503)
    expect([200, 503]).toContain(response.status());
    
    const data = await response.json();
    // Either has status field (success) or detail field (error)
    const hasExpectedFields = data.status || data.detail;
    expect(hasExpectedFields).toBeTruthy();
  });

  test('create test game endpoint works', async ({ request }) => {
    // Create a test game without course (simpler)
    const response = await request.post(`${API_BASE}/games/create-test?player_count=4`);
    expect(response.ok()).toBeTruthy();

    const data = await response.json();
    expect(data).toHaveProperty('game_id');
    expect(data).toHaveProperty('players');
    expect(data.players).toHaveLength(4);
    expect(data).toHaveProperty('status', 'in_progress');

    // Cleanup
    const gameId = data.game_id;
    await request.delete(`${API_BASE}/games/${gameId}`);
  });

  test('courses endpoint responds', async ({ request }) => {
    const response = await request.get(`${API_BASE}/courses`);
    expect(response.ok()).toBeTruthy();

    const data = await response.json();
    // Courses endpoint returns object keyed by course name
    expect(typeof data).toBe('object');
    expect(Object.keys(data).length).toBeGreaterThan(0);
  });
});

test.describe('Smoke Tests - Frontend', () => {
  test('homepage loads and renders', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('domcontentloaded');

    // Check page has content
    const hasContent = await page.evaluate(() => document.body.textContent.length > 0);
    expect(hasContent).toBeTruthy();

    // Check for app title or branding
    const pageText = await page.textContent('body');
    expect(pageText).toMatch(/wolf|goat|pig|golf/i);
  });

  test('homepage has navigation buttons', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('domcontentloaded');

    // Should have at least one button
    const buttons = await page.locator('button').count();
    expect(buttons).toBeGreaterThan(0);
  });

  test('no critical JavaScript errors on load', async ({ page }) => {
    const errors = [];
    
    // Listen for console errors before navigation
    page.on('console', msg => {
      if (msg.type() === 'error') {
        const text = msg.text();
        // Ignore CORS and network errors (expected in test environment)
        if (!text.includes('CORS') && 
            !text.includes('net::ERR_FAILED') &&
            !text.includes('Failed to fetch') &&
            !text.includes('NetworkError')) {
          errors.push(text);
        }
      }
    });

    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Log any errors found for debugging
    if (errors.length > 0) {
      console.log('Critical errors found:', errors);
    }

    expect(errors.length).toBe(0);
  });
});

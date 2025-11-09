import { test, expect } from '@playwright/test';

/**
 * Smoke Tests - Quick API validation without full browser automation
 *
 * These tests validate core functionality through API calls:
 * - Backend is running and responsive
 * - Test game creation works
 * - Basic hole completion works
 * - Game state persists correctly
 *
 * Run with: npm run test:e2e -- smoke-test.spec.js
 */

const API_BASE = 'http://localhost:8000';

test.describe('Smoke Tests - API Health', () => {
  let testGameId;

  test.afterEach(async ({ request }) => {
    // Cleanup: delete test game if created
    if (testGameId) {
      try {
        await request.delete(`${API_BASE}/games/${testGameId}`);
      } catch (e) {
        console.warn(`Cleanup warning: Could not delete game ${testGameId}`);
      }
    }
  });

  test('backend health check', async ({ request }) => {
    // Verify backend is running
    const response = await request.get(`${API_BASE}/`);
    expect(response.ok()).toBeTruthy();

    // Backend root returns HTML, not JSON - just verify it's responding
    const text = await response.text();
    expect(text.length).toBeGreaterThan(0);
  });

  test('create test game via API', async ({ request }) => {
    // Create a 4-player test game using query parameters
    const response = await request.post(`${API_BASE}/games/create-test?player_count=4&course_name=Wing%20Point`);

    expect(response.ok()).toBeTruthy();

    const data = await response.json();
    expect(data).toHaveProperty('game_id');
    expect(data).toHaveProperty('players');
    expect(data.players).toHaveLength(4);

    testGameId = data.game_id;

    // Verify game state
    expect(data).toHaveProperty('status');
    expect(data.status).toBe('in_progress');
    expect(data).toHaveProperty('test_mode');
    expect(data.test_mode).toBe(true);
  });

  test('complete hole via API', async ({ request }) => {
    // Create game first using query parameters
    const createResponse = await request.post(`${API_BASE}/games/create-test?player_count=4&course_name=Wing%20Point`);

    const gameData = await createResponse.json();
    testGameId = gameData.game_id;

    const players = gameData.players;

    // Complete hole 1
    const completeResponse = await request.post(`${API_BASE}/games/${testGameId}/holes/complete`, {
      data: {
        hole_number: 1,
        scores: {
          [players[0].id]: 4,
          [players[1].id]: 5,
          [players[2].id]: 5,
          [players[3].id]: 6
        },
        captain_id: players[0].id,
        partnership: {
          captain_id: players[0].id,
          partner_id: players[1].id
        }
      }
    });

    expect(completeResponse.ok()).toBeTruthy();

    const holeResult = await completeResponse.json();
    expect(holeResult).toHaveProperty('hole_number', 1);
    expect(holeResult).toHaveProperty('points');

    // Verify zero-sum: all points should add up to 0
    const totalPoints = Object.values(holeResult.points).reduce((sum, pts) => sum + pts, 0);
    expect(totalPoints).toBe(0);
  });

  test('game state persistence', async ({ request }) => {
    // Create game using query parameters
    const createResponse = await request.post(`${API_BASE}/games/create-test?player_count=4&course_name=Wing%20Point`);

    const gameData = await createResponse.json();
    testGameId = gameData.game_id;

    // Fetch game state
    const getResponse = await request.get(`${API_BASE}/games/${testGameId}`);
    expect(getResponse.ok()).toBeTruthy();

    const fetchedGame = await getResponse.json();
    expect(fetchedGame.game_id).toBe(testGameId);
    expect(fetchedGame.current_hole).toBe(1);
    expect(fetchedGame.players).toHaveLength(4);
  });
});

test.describe('Smoke Tests - Frontend Rendering', () => {
  test('homepage loads without errors', async ({ page }) => {
    // Navigate to homepage
    await page.goto('/');

    // Wait for any network activity to settle
    await page.waitForLoadState('networkidle');

    // Check for basic page elements (non-blocking)
    const hasContent = await page.evaluate(() => {
      return document.body.textContent.length > 0;
    });

    expect(hasContent).toBeTruthy();

    // Check no console errors
    const logs = [];
    page.on('console', msg => {
      if (msg.type() === 'error') {
        logs.push(msg.text());
      }
    });

    // Reload to catch console errors
    await page.reload();
    await page.waitForLoadState('networkidle');

    // Allow some warnings but no critical errors
    const criticalErrors = logs.filter(log =>
      !log.includes('Deprecation') &&
      !log.includes('Warning')
    );

    expect(criticalErrors.length).toBe(0);
  });
});

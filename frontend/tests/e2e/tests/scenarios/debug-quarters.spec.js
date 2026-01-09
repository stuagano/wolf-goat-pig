import { test, expect } from '@playwright/test';

const API_BASE = 'http://localhost:8333';
const FRONTEND_BASE = 'http://localhost:3000';

test('Debug: Check quarter input testids', async ({ page, request }) => {
  // Create test game
  const response = await request.post(`${API_BASE}/games/create-test?player_count=4`);
  const data = await response.json();
  const gameId = data.game_id;

  console.log('Game ID:', gameId);
  console.log('Players from API:', data.players.map(p => ({ id: p.id, name: p.name })));

  // Navigate to game
  await page.goto(`${FRONTEND_BASE}/game/${gameId}`);
  await page.waitForSelector('[data-testid="scorekeeper-container"]', { timeout: 10000 });

  // Find all quarter inputs
  const inputs = await page.locator('input[data-testid^="quarters-input-"]').all();
  console.log(`Found ${inputs.length} quarter input elements`);

  // Get the testid of each input
  for (let i = 0; i < inputs.length; i++) {
    const testid = await inputs[i].getAttribute('data-testid');
    const value = await inputs[i].inputValue();
    console.log(`  Input ${i}: testid="${testid}", value="${value}"`);
  }

  // Try filling the first input
  console.log('\nTrying to fill first input with "3"...');
  const input1 = page.locator('[data-testid="quarters-input-test-player-1"]');
  await input1.click();
  await input1.fill('3');

  // Check if it worked
  const newValue1 = await input1.inputValue();
  console.log(`After fill: value="${newValue1}"`);

  // Try with pressSequentially
  console.log('\nTrying with pressSequentially...');
  await input1.click();
  await input1.clear();
  await input1.pressSequentially('3', { delay: 100 });

  const newValue2 = await input1.inputValue();
  console.log(`After pressSequentially: value="${newValue2}"`);

  // Try clicking the +1 button 3 times to get +3
  console.log('\nTrying to click +1 button 3 times...');
  // Find all buttons containing "+1" in the first quarters row
  const plusOneButtons = page.getByRole('button', { name: '+1' });
  const count = await plusOneButtons.count();
  console.log(`Found ${count} "+1" buttons`);

  // Click the first +1 button (for player 1) three times
  await plusOneButtons.first().click();
  await page.waitForTimeout(100);
  await plusOneButtons.first().click();
  await page.waitForTimeout(100);
  await plusOneButtons.first().click();
  await page.waitForTimeout(500);

  const newValue3 = await input1.inputValue();
  console.log(`After clicking +1 three times: value="${newValue3}"`);

  // Take a screenshot
  await page.screenshot({ path: 'test-results/debug-quarters.png', fullPage: true });
  console.log('Screenshot saved to test-results/debug-quarters.png');

  // Cleanup
  await request.delete(`${API_BASE}/games/${gameId}`);
});

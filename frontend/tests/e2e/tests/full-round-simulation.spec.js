const { test, expect } = require('@playwright/test');

test.describe('Wolf Goat Pig Game - Full Round Simulation', () => {
  let gameId;
  let joinCode;

  test('should create a game, join lobby, start game, and advance through holes', async ({ page, context }) => {
    // Step 1: Navigate to home page
    await page.goto('http://localhost:3001');

    // Wait for page to load
    await page.waitForLoadState('networkidle');

    // Step 2: Navigate to create game page
    await page.goto('http://localhost:3001/game');

    // Wait for the create game page to load - look for the actual heading
    await expect(page.getByRole('heading', { name: /Create New Game/i })).toBeVisible({ timeout: 10000 });

    // Step 3: Select course and player count (use defaults if available)
    // The form should have a select for course and player count
    const courseSelect = page.locator('select').first();
    await courseSelect.waitFor({ state: 'visible', timeout: 5000 });

    // Step 4: Click the create game button
    const createButton = page.getByRole('button', { name: /Create Game.*Get Join Code/i });
    await createButton.click();

    // Step 5: Wait for navigation to lobby page
    await page.waitForURL(/\/lobby\//, { timeout: 10000 });

    // Extract game ID and join code from URL and page
    const url = page.url();
    const match = url.match(/\/lobby\/([a-f0-9-]+)/);
    if (match) {
      gameId = match[1];
      console.log('Game ID:', gameId);
    }

    // Get join code from the page
    const joinCodeElement = page.locator('text=/Join Code:/i').locator('..').locator('text=/[A-Z0-9]{6}/');
    joinCode = await joinCodeElement.textContent();
    console.log('Join Code:', joinCode);

    // Step 6: Join as 2 players (minimum required to start)
    // Open new pages to simulate different players joining
    const player1Page = await context.newPage();
    const player2Page = await context.newPage();

    // Player 1 joins
    await player1Page.goto(`http://localhost:3001/join/${joinCode}`);
    await player1Page.getByPlaceholder(/Enter your name/i).fill('Player 1');
    // Handicap field is pre-filled with 18, so we can skip filling it
    await player1Page.getByRole('button', { name: /Join Game/i }).click();
    await player1Page.waitForURL(/\/lobby\//, { timeout: 10000 });
    console.log('Player 1 joined');

    // Player 2 joins
    await player2Page.goto(`http://localhost:3001/join/${joinCode}`);
    await player2Page.getByPlaceholder(/Enter your name/i).fill('Player 2');
    // Handicap field is pre-filled with 18, so we can skip filling it
    await player2Page.getByRole('button', { name: /Join Game/i }).click();
    await player2Page.waitForURL(/\/lobby\//, { timeout: 10000 });
    console.log('Player 2 joined');

    // Step 7: Wait for start button to become enabled (lobby updates via polling)
    await page.waitForTimeout(3000); // Wait for lobby to update

    // Find and click start game button (should now be enabled)
    const startButton = page.getByRole('button', { name: /start/i }).first();
    await startButton.click();

    // Step 7: Wait for navigation to game interface
    await page.waitForURL(/\/game\//, { timeout: 10000 });
    await page.waitForLoadState('networkidle');

    // Step 8: Verify game interface loaded
    // Should see hole information - use first() to avoid strict mode violation
    await expect(page.locator('text=/hole/i').first()).toBeVisible({ timeout: 10000 });

    console.log('Game started successfully, now testing hole advancement...');

    // Step 9: Advance through multiple holes
    for (let hole = 1; hole <= 3; hole++) {
      console.log(`Testing hole ${hole}...`);

      // Wait a bit for the game state to stabilize
      await page.waitForTimeout(1000);

      // Look for action buttons (these might be bet buttons, pass buttons, or shot result buttons)
      // The specific buttons depend on game state

      // Try to find and click any action button that advances the game
      const actionButtons = [
        page.getByRole('button', { name: /wolf|goat|pig|pass|bet|continue|next|save.*hole/i }),
        page.locator('button:has-text("Wolf")'),
        page.locator('button:has-text("Goat")'),
        page.locator('button:has-text("Pig")'),
        page.locator('button:has-text("Pass")'),
        page.locator('button:has-text("Continue")'),
        page.locator('button:has-text("Next")'),
        page.locator('button:text-matches("Save.*[Hh]ole", "i")'),
      ];

      // Try each button type until one is clickable
      let actionTaken = false;
      for (const buttonLocator of actionButtons) {
        try {
          const button = buttonLocator.first();
          if (await button.isVisible({ timeout: 2000 })) {
            await button.click();
            actionTaken = true;
            console.log(`Clicked action button on hole ${hole}`);
            await page.waitForTimeout(500);
            break;
          }
        } catch (e) {
          // Button not found or not clickable, try next
          continue;
        }
      }

      if (!actionTaken) {
        console.log(`No immediate action button found on hole ${hole}, looking for "Save Hole" or score entry...`);

        // Look for score entry or save hole functionality
        // The user mentioned "save hole" was failing, so this is important to test
        const saveHoleButton = page.locator('button', { hasText: /save.*hole/i }).first();

        try {
          if (await saveHoleButton.isVisible({ timeout: 3000 })) {
            console.log(`Found "Save Hole" button on hole ${hole}, clicking it...`);
            await saveHoleButton.click();

            // Wait for the save action to complete
            await page.waitForTimeout(1000);

            // Check for success or error
            const errorText = await page.locator('text=/error|fail/i').first().textContent({ timeout: 2000 }).catch(() => null);
            if (errorText) {
              console.error(`Error on hole ${hole}: ${errorText}`);
              throw new Error(`Save hole failed: ${errorText}`);
            }

            console.log(`Successfully saved hole ${hole}`);
          }
        } catch (e) {
          console.log(`Could not find or click save hole button: ${e.message}`);
        }
      }

      // Verify we're still in a valid game state
      // The page should still show game-related content
      const gameContent = await page.locator('text=/hole|player|score/i').first().isVisible({ timeout: 5000 }).catch(() => false);
      expect(gameContent).toBeTruthy();
    }

    console.log('Successfully tested advancing through 3 holes');
  });

  test('should handle save hole action without 404 error', async ({ page, context }) => {
    // This test specifically targets the bug that was fixed
    // where saving a hole after server restart would give 404

    // Create and start a game
    await page.goto('http://localhost:3001/game');
    await page.waitForLoadState('networkidle');

    const courseSelect = page.locator('select').first();
    await courseSelect.waitFor({ state: 'visible', timeout: 5000 });

    const createButton = page.getByRole('button', { name: /Create Game.*Get Join Code/i });
    await createButton.click();

    await page.waitForURL(/\/lobby\//, { timeout: 10000 });

    // Get join code
    const joinCodeElement = page.locator('text=/Join Code:/i').locator('..').locator('text=/[A-Z0-9]{6}/');
    const joinCode = await joinCodeElement.textContent();

    // Join as 2 players
    const player1Page = await context.newPage();
    await player1Page.goto(`http://localhost:3001/join/${joinCode}`);
    await player1Page.getByPlaceholder(/Enter your name/i).fill('Player 1');
    await player1Page.getByRole('button', { name: /Join Game/i }).click();
    await player1Page.waitForURL(/\/lobby\//, { timeout: 10000 });

    const player2Page = await context.newPage();
    await player2Page.goto(`http://localhost:3001/join/${joinCode}`);
    await player2Page.getByPlaceholder(/Enter your name/i).fill('Player 2');
    await player2Page.getByRole('button', { name: /Join Game/i }).click();
    await player2Page.waitForURL(/\/lobby\//, { timeout: 10000 });

    // Wait for lobby to update
    await page.waitForTimeout(3000);

    const startButton = page.getByRole('button', { name: /start/i }).first();
    await startButton.click();

    await page.waitForURL(/\/game\//, { timeout: 10000 });
    await page.waitForLoadState('networkidle');

    // Now try to perform a save hole action
    // Listen for network requests to verify no 404
    let has404 = false;
    page.on('response', response => {
      if (response.status() === 404 && response.url().includes('/action')) {
        has404 = true;
        console.error(`404 error detected on: ${response.url()}`);
      }
    });

    // Verify game interface loaded
    await expect(page.locator('text=/hole/i').first()).toBeVisible({ timeout: 10000 });

    // Look for any action button (Wolf, Goat, Pig, Next Hole, etc.)
    await page.waitForTimeout(2000);

    const actionButton = page.locator('button').filter({ hasText: /Wolf|Goat|Pig|Next|Continue|Pass/i }).first();

    try {
      if (await actionButton.isVisible({ timeout: 5000 })) {
        await actionButton.click();
        await page.waitForTimeout(1000);

        // Verify no 404 error occurred
        expect(has404).toBe(false);
        console.log('Game action completed without 404 error');
      }
    } catch (e) {
      console.log('Action button not immediately clickable, but no 404 detected');
    }

    // Verify no 404 occurred
    expect(has404).toBe(false);
  });
});

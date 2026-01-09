/**
 * Helper to set quarters for a player using quick-add buttons (integers) or direct value setting (decimals)
 * @param {Page} page - Playwright page object
 * @param {string} playerId - Player ID (e.g., "test-player-1")
 * @param {number} targetValue - Target quarter value (e.g., 3, -1, 1.5, -2.5)
 */
export async function setQuartersWithButtons(page, playerId, targetValue) {
  // Find the input for this player
  const input = page.locator(`[data-testid="quarters-input-${playerId}"]`);

  // For fractional or zero values, need special handling
  // React's controlled inputs require proper event simulation
  if (!Number.isInteger(targetValue) || targetValue === 0) {
    await input.click();
    await input.clear();

    // Use Playwright's evaluation to update React state directly
    await input.evaluate((el, value) => {
      // Get the React fiber node to update state directly
      const nativeInputValueSetter = Object.getOwnPropertyDescriptor(
        window.HTMLInputElement.prototype,
        'value'
      ).set;

      nativeInputValueSetter.call(el, value.toString());

      // Trigger React's onChange by dispatching a proper input event
      const inputEvent = new Event('input', { bubbles: true });
      el.dispatchEvent(inputEvent);
    }, targetValue);

    await page.waitForTimeout(150);
    return;
  }

  // For integer values, use quick-add buttons (more realistic user interaction)
  const container = input.locator('../..');

  if (targetValue > 0) {
    // Click +1 button for positive integers
    const plusButton = container.getByRole('button', { name: '+1', exact: true });
    for (let i = 0; i < targetValue; i++) {
      await plusButton.click();
      await page.waitForTimeout(50);
    }
  } else if (targetValue < 0) {
    // Click -1 button for negative integers
    const minusButton = container.getByRole('button', { name: '-1', exact: true });
    for (let i = 0; i < Math.abs(targetValue); i++) {
      await minusButton.click();
      await page.waitForTimeout(50);
    }
  }
  // If targetValue is 0, do nothing
}

/**
 * Set quarters for all players
 * @param {Page} page - Playwright page object
 * @param {Array} players - Array of player objects with id property
 * @param {Array<number>} values - Array of quarter values for each player (can include decimals)
 */
export async function setAllQuarters(page, players, values) {
  for (let i = 0; i < players.length; i++) {
    await setQuartersWithButtons(page, players[i].id, values[i]);
  }
  // Wait for state to settle
  await page.waitForTimeout(300);
}

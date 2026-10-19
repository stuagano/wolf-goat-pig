// iOS: going back to a hole you already played must open an editor you can use.
//
// Tapping ◀ on hole 2 opens the Edit Hole dialog for hole 1. On an iPhone the
// bottom hole-navigation bar painted over that dialog, so its Save/Cancel
// buttons sat under the bar and taps landed on the bar instead.
import { test, expect } from '@playwright/test';

const API = 'http://localhost:8333';
const AUTH = { Authorization: 'Bearer e2e' };

// True when a tap at the centre of `locator` would hit that element (or its children).
const isTappable = (locator) =>
  locator.evaluate((el) => {
    const r = el.getBoundingClientRect();
    const hit = document.elementFromPoint(r.left + r.width / 2, r.top + r.height / 2);
    return !!hit && (hit === el || el.contains(hit));
  });

test('back to a played hole opens an Edit Hole dialog that is on top and tappable', async ({ page, request }) => {
  const created = await request.post(`${API}/games/create-custom`, {
    headers: AUTH,
    data: {
      players: Array.from({ length: 4 }, (_, i) => ({
        name: `Test Player ${i + 1}`,
        handicap: 18,
        ...(i === 0 ? { user_id: 'auth0|123456789' } : {}),
      })),
    },
  });
  expect(created.ok(), await created.text()).toBeTruthy();
  const game = await created.json();
  const ids = game.players.map((p) => p.id);

  const quarters = Object.fromEntries(ids.map((id, i) => [id, i < 2 ? 1 : -1]));
  const saved = await request.post(`${API}/games/${game.game_id}/scores`, {
    headers: AUTH,
    data: { holes: [{ hole_number: 1, quarters }], current_hole: 2 },
  });
  expect(saved.ok(), await saved.text()).toBeTruthy();

  try {
    await page.goto(`/game/${game.game_id}`);
    await page.waitForSelector('[data-testid="scorekeeper-container"]');

    await page.getByRole('button', { name: 'Go to hole 1' }).tap();

    const dialog = page.getByRole('dialog', { name: 'Edit Hole 1' });
    await expect(dialog).toBeVisible();
    await page.screenshot({ path: 'test-results/ios-back-to-hole-1.png', fullPage: false });

    // Every control in the dialog — each player's strokes/quarters inputs and
    // Save/Cancel — must receive the tap, not something painted over it.
    const controls = dialog.locator('input, button');
    const count = await controls.count();
    expect(count).toBeGreaterThan(4);
    const covered = [];
    for (let i = 0; i < count; i += 1) {
      const control = controls.nth(i);
      await control.scrollIntoViewIfNeeded();
      if (!(await isTappable(control))) {
        covered.push(await control.evaluate((el) => el.getAttribute('aria-label') || el.textContent || el.name || el.tagName));
      }
    }
    expect(covered, 'dialog controls covered by another element').toEqual([]);
  } finally {
    await request.delete(`${API}/games/${game.game_id}`).catch(() => {});
  }
});

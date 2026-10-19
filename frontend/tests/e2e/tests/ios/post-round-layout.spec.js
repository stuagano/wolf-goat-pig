import { test, expect } from '@playwright/test';

const players = ['Alex', 'Christopher Montgomery-Wellington', 'AlexandertheVeryLongUnbrokenSurname', 'Sam', 'Jordan', 'Taylor'];

test.beforeEach(async ({ page }) => {
  // Same Auth0 cache seam as post-round-negative-quarters.spec.js.
  await page.addInitScript(() => {
    const clientId = 'test-e2e-client-id';
    const scope = 'openid profile email offline_access';
    const expiresAt = Math.floor(Date.now() / 1000) + 86400;
    const user = { sub: 'auth0|123456789', email: 'test@example.com', name: 'Test User' };
    localStorage.setItem(`@@auth0spajs@@::${clientId}::default::${scope}`, JSON.stringify({
      body: { access_token: 'e2e', token_type: 'Bearer', expires_in: 86400, scope, audience: 'default', client_id: clientId }, expiresAt,
    }));
    localStorage.setItem(`@@auth0spajs@@::${clientId}::@@user@@`, JSON.stringify({
      id_token: 'e2e', decodedToken: { claims: { ...user, __raw: 'e2e', exp: expiresAt }, user },
    }));
  });
  await page.route('http://localhost:8333/**', async route => {
    const path = new URL(route.request().url()).pathname;
    if (path === '/players/me') return route.fulfill({ json: { id: 1, name: 'Alex', legacy_name: players[0] } });
    if (path === '/legacy-players') return route.fulfill({ json: { players } });
    if (path === '/players/me/rounds') return route.fulfill({ json: [] });
    if (path === '/players/me/round') return route.fulfill({ json: { rounds: players.map((member, id) => ({ id, member })) } });
    return route.fulfill({ json: {} });
  });
});

async function expectContained(page) {
  const geometry = await page.locator('.post-round-page').evaluate(root => {
    const form = root.querySelector('.pr-form');
    const bounds = form.getBoundingClientRect();
    const overflow = [...form.querySelectorAll('input, button, label, fieldset, legend')].flatMap(el => {
      const rect = el.getBoundingClientRect();
      return rect.left < bounds.left - 1 || rect.right > bounds.right + 1 || el.scrollWidth > el.clientWidth + 1
        ? [{ element: el.tagName, text: el.textContent?.slice(0, 50), left: rect.left, right: rect.right, width: rect.width, scrollWidth: el.scrollWidth, clientWidth: el.clientWidth, minWidth: getComputedStyle(el).minWidth }]
        : [];
    });
    return { viewport: document.documentElement.clientWidth, pageWidth: document.documentElement.scrollWidth, formLeft: bounds.left, formRight: bounds.right, overflow };
  });
  expect.soft(geometry.overflow, JSON.stringify(geometry, null, 2)).toEqual([]);
  expect.soft(geometry.pageWidth).toBeLessThanOrEqual(geometry.viewport);
}

for (const width of [320, 375, 390, 1280]) {
  test(`Post a Score controls fit and remain usable at ${width}px`, async ({ page }, testInfo) => {
    test.skip(testInfo.project.name === 'desktop' ? width !== 1280 : width === 1280);
    await page.setViewportSize({ width, height: 844 });
    await page.goto('/rounds/post');
    await expect(page.getByText('Posting as Alex', { exact: true })).toBeVisible();
    await expectContained(page);
    await page.getByLabel('Date', { exact: true }).fill('2026-01-15');
    for (const name of players.slice(1)) {
      await page.getByRole('group', { name: 'Group members' }).getByRole('button', { name, exact: true }).click();
    }
    await expect(page.locator('fieldset input')).toHaveCount(6);
    await expectContained(page);
    for (const [index, name] of players.entries()) {
      const input = page.getByLabel(`${name} — quarters won/lost`);
      await input.click();
      await expect(input).toBeFocused();
      await page.keyboard.insertText(index === 0 ? '—3' : '0');
      await expect(input).toHaveValue(index === 0 ? '-3' : '0');
      await expectContained(page);
    }
    await page.getByPlaceholder('Wing Point').fill('A long golf course name');
    await page.getByPlaceholder('Morning game').fill('Morning game');
    await page.getByPlaceholder('18 holes').fill('18 holes');
    await testInfo.attach('six-player-form', { body: await page.screenshot({ fullPage: true }), contentType: 'image/png' });
    const posted = page.waitForRequest(request => request.url().endsWith('/players/me/round') && request.method() === 'POST');
    await page.getByRole('button', { name: 'Post foursome results', exact: true }).click();
    expect((await posted).postDataJSON()).toEqual({
      date: '2026-01-15', location: 'A long golf course name', group: 'Morning game', duration: '18 holes',
      results: players.map((member, index) => ({ member, score: index === 0 ? -3 : 0 })),
    });
    await expect(page.getByText('Results posted for all 6 players.', { exact: false })).toBeVisible();
    await expectContained(page);
  });
}

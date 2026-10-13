// iOS read-after-write: what a golfer types on an iPhone is what gets saved.
//
// Guards two shipped bugs:
//  - #383: quarters input used a numeric keypad, and the iOS keypad has no minus key.
//  - #392: iOS Smart Punctuation sends "—"/"–" for a typed minus, which failed validation.
//
// Emulated WebKit can't draw the iOS keyboard, so we assert the attributes that
// pick it, then insert the exact characters iOS emits and read the result back
// from the API.
import { test, expect } from '@playwright/test';

const API = 'http://localhost:8333';
const CLIENT_ID = 'test-e2e-client-id'; // matches playwright.config.js
const SCOPE = 'openid profile email offline_access'; // matches AuthContext.jsx
// The dev backend accepts any Bearer token as the fixed dev user.
const AUTH = { Authorization: 'Bearer e2e' };

// Keyboards with no minus key on iOS.
const NO_MINUS_INPUTMODES = ['numeric', 'decimal', 'tel'];

// Seed the auth0-spa-js localStorage cache so getAccessTokenSilently returns a
// token and the app is signed in, with no network calls to Auth0.
const seedAuth0Session = ({ clientId, scope }) => {
  const now = Math.floor(Date.now() / 1000);
  const user = { sub: 'auth0|123456789', email: 'test@example.com', name: 'Test User' };
  localStorage.setItem(
    `@@auth0spajs@@::${clientId}::default::${scope}`,
    JSON.stringify({
      body: { access_token: 'e2e', token_type: 'Bearer', expires_in: 86400, scope, audience: 'default', client_id: clientId },
      expiresAt: now + 86400,
    }),
  );
  localStorage.setItem(
    `@@auth0spajs@@::${clientId}::@@user@@`,
    JSON.stringify({ id_token: 'e2e', decodedToken: { claims: { ...user, __raw: 'e2e', exp: now + 86400 }, user } }),
  );
};

test('negative quarters typed the iOS way are saved as negative numbers', async ({ page, request }) => {
  const { players } = await (await request.get(`${API}/legacy-players`)).json();
  const [me, partner] = players;
  // Link the dev user to a roster name (the form requires it).
  const link = await request.put(`${API}/players/me/legacy-name`, { headers: AUTH, data: { legacy_name: me } });
  expect(link.ok(), await link.text()).toBeTruthy();

  // Unique past date so reruns don't hit the one-result-per-day 409.
  const date = new Date(Date.UTC(2000, 0, 1) + (Date.now() % 7_000) * 86_400_000).toISOString().slice(0, 10);

  await page.addInitScript(seedAuth0Session, { clientId: CLIENT_ID, scope: SCOPE });
  await page.goto('/rounds/post');

  await page.locator('input[type="date"]').fill(date);
  await page.getByRole('group', { name: 'Group members' }).getByRole('button', { name: partner, exact: true }).click();

  const myInput = page.getByLabel(`${me} — quarters won/lost`);
  const partnerInput = page.getByLabel(`${partner} — quarters won/lost`);

  // Keyboard contract (#383): every quarters field must offer a minus key.
  for (const input of [myInput, partnerInput]) {
    await expect(input).not.toHaveAttribute('type', 'number');
    expect(NO_MINUS_INPUTMODES).not.toContain(await input.getAttribute('inputmode'));
  }

  // What iOS actually sends (#392): Smart Punctuation em dash, long-press en dash.
  await myInput.focus();
  await page.keyboard.insertText('—3');
  await partnerInput.focus();
  await page.keyboard.insertText('–2');
  await expect(myInput).toHaveValue('-3');

  await page.getByRole('button', { name: 'Post foursome results', exact: true }).click();
  await expect(page.getByText(/Results posted for all 2 players/)).toBeVisible();

  // Read-after-write: the server stored what was typed.
  const rounds = await (await request.get(`${API}/players/me/rounds`, { headers: AUTH })).json();
  const saved = rounds.find((r) => r.date === date);
  expect(saved?.score).toBe(-3);
});

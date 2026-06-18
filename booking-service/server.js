/**
 * ForeTees Booking Microservice
 *
 * Lightweight HTTP server that exposes headless browser booking/cancel
 * for ForeTees v5. Called by the Python backend via HTTP.
 *
 * Endpoints:
 *   POST /book   — Book a tee time
 *   POST /cancel — Cancel a tee time
 *   GET  /health — Health check
 *
 * Request body (JSON):
 *   { username, password, date, time, transport_mode }
 *
 * Auth: Bearer token via BOOKING_SERVICE_SECRET env var
 */

const http = require('http');
const path = require('path');

// Ensure Playwright finds browsers installed into the project dir during build.
// render.yaml installs to ./.playwright-browsers; set the env var before
// requiring playwright so it doesn't fall back to ~/.cache/ms-playwright.
if (!process.env.PLAYWRIGHT_BROWSERS_PATH) {
  process.env.PLAYWRIGHT_BROWSERS_PATH = path.join(__dirname, '.playwright-browsers');
}

const { chromium } = require('playwright');

const PORT = process.env.PORT || 3001;
const SECRET = process.env.BOOKING_SERVICE_SECRET || '';
const WINGPOINT_BASE = 'https://www.wingpointgolf.com';
const LOGIN_PAGE = '/public/member-login-465.html';
const TEE_TIME_PAGE = '/members/golf/make-a-tee-time-703.html';
const FORETEES_BASE = 'https://ftapp.wingpointgolf.com/v5/wingpointgcc_flxrez0_m30';

// ── Auth helper ──────────────────────────────────────────────
function checkAuth(req) {
  if (!SECRET) return true; // No secret = no auth required
  const auth = req.headers['authorization'] || '';
  return auth === `Bearer ${SECRET}`;
}

// ── ForeTees login + SSO ─────────────────────────────────────
async function loginAndSSO(page, username, password) {
  await page.goto(`${WINGPOINT_BASE}${LOGIN_PAGE}`, { waitUntil: 'networkidle' });
  await page.fill('input[name="UserLOGIN"]', username);
  await page.fill('input[name="UserPWD"]', password);
  await page.click('input[name="btnLogon"]');
  await page.waitForLoadState('networkidle');

  await page.goto(`${WINGPOINT_BASE}${TEE_TIME_PAGE}`, { waitUntil: 'networkidle' });
  const ssoKey = await page.evaluate(() => {
    for (const s of document.querySelectorAll('script')) {
      const m = s.textContent.match(/ftSSOKey\s*=\s*'([^']+)'/);
      if (m) return m[1];
    }
    return null;
  });
  const ssoIV = await page.evaluate(() => {
    for (const s of document.querySelectorAll('script')) {
      const m = s.textContent.match(/ftSSOIV\s*=\s*'([^']+)'/);
      if (m) return m[1];
    }
    return null;
  });
  if (!ssoKey || !ssoIV) throw new Error('Could not find SSO params');

  await page.goto(
    `${FORETEES_BASE}/Member_select?sso_uid=${encodeURIComponent(ssoKey)}&sso_iv=${encodeURIComponent(ssoIV)}`,
    { waitUntil: 'networkidle' },
  );
}

// ── Navigate to slot ─────────────────────────────────────────
async function navigateToSlot(page, date, time) {
  const [yy, mm, dd] = date.split('-');
  const ftDate = `${mm}/${dd}/${yy}`;
  await page.goto(
    `${FORETEES_BASE}/Member_sheet?calDate=${encodeURIComponent(ftDate)}&course=&displayOpt=0`,
    { waitUntil: 'networkidle' },
  );
  await page.waitForTimeout(2000);

  const found = await page.evaluate((targetTime) => {
    for (const a of document.querySelectorAll('a')) {
      if (a.textContent.trim() === targetTime) {
        a.click();
        return true;
      }
    }
    return false;
  }, time);

  if (!found) {
    const available = await page.evaluate(() =>
      Array.from(document.querySelectorAll('a.teetime_button, a[data-ftjson]'))
        .slice(0, 20)
        .map((a) => a.textContent.trim()),
    );
    throw new Error(`Slot "${time}" not found. Available: ${available.join(', ')}`);
  }

  // Wait for form to render
  await page
    .waitForFunction(
      () =>
        document.body?.innerText?.includes('Submit') ||
        document.body?.innerText?.includes('Cancel Reservation') ||
        document.body?.innerText?.includes('Time remaining'),
      { timeout: 15000 },
    )
    .catch(() => {});
  await page.waitForTimeout(2000);

  // Check for "not allowed" error
  const bodyText = await page.evaluate(() => document.body?.innerText || '');
  if (bodyText.includes('Not Allowed') || bodyText.includes('not allowed')) {
    throw new Error('Tee Time Not Allowed — you may have another booking in-use. Wait 6 minutes and retry.');
  }
}

// ── Parse "Firstname Lastname" → best search term (last name) ─
function searchTermFor(fullName) {
  const parts = fullName.trim().split(/\s+/);
  // Use last name — more unique, and ForeTees shows "LastName, FirstName"
  return parts.length > 1 ? parts[parts.length - 1] : parts[0];
}

// ── Find best match in ftMs-listItem list ─────────────────────
async function pickBestMatch(page, fullName) {
  const nameLower = fullName.toLowerCase();
  const parts = nameLower.split(/\s+/);
  const items = page.locator('div.ftMs-listItem');
  const count = await items.count();
  if (count === 0) return null;

  for (let j = 0; j < count; j++) {
    const item = items.nth(j);
    const text = (await item.textContent().catch(() => '')).toLowerCase();
    // Match if ALL parts of the name appear in the item text
    if (parts.every((p) => text.includes(p))) return item;
  }
  // Fallback: first result
  return items.first();
}

// ── Fill co-player names into empty slots ────────────────────
// ForeTees v5 uses a "Select Player #N" modal:
//   1. Click the empty slot row to open the modal
//   2. Type the last name in the search input
//   3. Wait for ftMs-listItem results
//   4. Click the best match
async function fillCoPlayers(page, playerNames) {
  if (!playerNames || playerNames.length === 0) return;

  // Find visible empty slot rows (exclude locked/hidden ones)
  const emptyRows = page.locator(
    'div.slot_player_row.emptySlot:not(.ftS-noDisplay):not(.ftS-lockedPlayer)'
  );
  const count = await emptyRows.count();

  for (let i = 0; i < Math.min(playerNames.length, count); i++) {
    const name = playerNames[i];
    if (!name) continue;
    const row = emptyRows.nth(i);

    try {
      // Click anywhere on the empty row — ForeTees opens the member-select modal
      await row.click({ timeout: 3000 });

      // Wait for the modal to appear, then click the "Members" tab
      const membersTab = page.locator('button:has-text("Members"), a:has-text("Members")').first();
      await membersTab.waitFor({ state: 'visible', timeout: 4000 });
      await membersTab.click();

      // Wait for the modal search input to appear
      const searchInput = page.locator(
        'div[class*="ftMs"] input[type="text"], input.ftMs-searchInput'
      ).first();
      await searchInput.waitFor({ state: 'visible', timeout: 3000 });

      // Type last name — ForeTees shows "LastName, FirstName" in results
      const term = searchTermFor(name);
      await searchInput.fill(term);

      // Wait for results to populate
      await page.waitForSelector('div.ftMs-listItem', { timeout: 4000 });

      // Pick the best matching member and click
      const match = await pickBestMatch(page, name);
      if (match) {
        await match.click({ timeout: 3000 });
        console.log(`[co-player] slot ${i}: selected "${name}" (searched "${term}")`);
      } else {
        // Close modal without selecting if no match found
        const closeBtn = page.locator('button:has-text("Close"), button.ftMs-close').first();
        await closeBtn.click({ timeout: 2000 }).catch(() => {});
        console.warn(`[co-player] slot ${i}: no match found for "${name}", skipped`);
      }

      // Small pause to let ForeTees update the slot before moving to next
      await page.waitForTimeout(500);
    } catch (err) {
      console.warn(`[co-player] slot ${i} error for "${name}": ${err.message}`);
      // Try to close any open modal before moving on
      await page.locator('button:has-text("Close")').first().click({ timeout: 1000 }).catch(() => {});
    }
  }
}

// ── Book ─────────────────────────────────────────────────────
async function book(args) {
  const { username, password, date, time, transport_mode, players } = args;
  if (!username || !password || !date || !time)
    return { success: false, error: 'Missing required fields' };

  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();
  try {
    await loginAndSSO(page, username, password);
    await navigateToSlot(page, date, time);

    // Add co-players to empty slots before submitting
    await fillCoPlayers(page, players);

    // Set transport mode using Playwright's native selectOption so that
    // ForeTees v5's JS framework event handlers actually fire (plain
    // dispatchEvent is ignored by SPA frameworks).
    const mode = transport_mode || 'WLK';
    const transportSelects = page.locator('select');
    const selectCount = await transportSelects.count();
    for (let i = 0; i < selectCount; i++) {
      const sel = transportSelects.nth(i);
      const opts = await sel.evaluate((el) => Array.from(el.options).map((o) => o.value));
      if (opts.includes('WLK') || opts.includes('CRT') || opts.includes('PC')) {
        await sel.selectOption(mode).catch(() => {});
      }
    }

    // Click Submit Request / Submit Changes
    const respPromise = page
      .waitForResponse((r) => r.url().includes('Member_slot') && r.request().method() === 'POST', { timeout: 15000 })
      .catch(() => null);

    await page.evaluate(() => {
      for (const el of document.querySelectorAll('a, button')) {
        const t = (el.textContent || '').trim().toLowerCase();
        if (t.includes('submit request') || t.includes('submit changes')) {
          el.click();
          return;
        }
      }
    });

    const resp = await respPromise;
    if (resp) {
      const json = await resp.json().catch(() => null);
      if (json) {
        return {
          success: json.successful === true,
          title: json.title || '',
          messages: [...(json.message_list || []), ...(json.notice_list || []), ...(json.warning_list || [])],
        };
      }
    }
    return { success: false, error: 'No response from ForeTees' };
  } catch (err) {
    return { success: false, error: err.message };
  } finally {
    await browser.close();
  }
}

// ── Cancel ───────────────────────────────────────────────────
async function cancel(args) {
  const { username, password, date, time, ttdata } = args;
  if (!username || !password || (!ttdata && (!date || !time)))
    return { success: false, error: 'Missing required fields' };

  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();
  try {
    await loginAndSSO(page, username, password);

    if (ttdata) {
      // Navigate to the member's booking list, find the booking by ttdata, click it
      await page.goto(`${FORETEES_BASE}/Member_teelist_list`, { waitUntil: 'networkidle' });
      await page.waitForTimeout(2000);

      const found = await page.evaluate((targetTtdata) => {
        for (const el of document.querySelectorAll('[data-ftjson]')) {
          try {
            const data = JSON.parse(el.getAttribute('data-ftjson'));
            if (data.ttdata === targetTtdata) {
              el.click();
              return true;
            }
          } catch (e) {}
        }
        return false;
      }, ttdata);

      if (!found) {
        const snippet = await page.evaluate(() => (document.body?.innerText || '').slice(0, 400));
        throw new Error(`Booking not found in tee time list. Page: ${snippet}`);
      }

      // Wait for the slot detail page (cancel or booking form)
      await page.waitForFunction(
        () =>
          document.querySelector('a.cancel_request_button') ||
          document.body?.innerText?.includes('Cancel Reservation') ||
          document.body?.innerText?.includes('Submit'),
        { timeout: 15000 },
      ).catch(() => {});
      await page.waitForTimeout(1000);
    } else {
      await navigateToSlot(page, date, time);
    }

    const respPromise = page
      .waitForResponse((r) => r.url().includes('Member_slot') && r.request().method() === 'POST', { timeout: 15000 })
      .catch(() => null);

    // Try cancel button; fall back to text-based search
    const clicked = await page.evaluate(() => {
      const btn = document.querySelector('a.cancel_request_button');
      if (btn) { btn.click(); return true; }
      for (const el of document.querySelectorAll('a, button')) {
        if ((el.textContent || '').toLowerCase().includes('cancel reservation')) {
          el.click();
          return true;
        }
      }
      return false;
    });
    if (!clicked) {
      const bodySnippet = await page.evaluate(() => (document.body?.innerText || '').slice(0, 600));
      throw new Error(`Cancel button not found. Page content: ${bodySnippet}`);
    }

    const resp = await respPromise;
    if (resp) {
      const json = await resp.json().catch(() => null);
      if (json) {
        return {
          success: json.successful === true,
          title: json.title || '',
          messages: [...(json.message_list || []), ...(json.notice_list || []), ...(json.warning_list || [])],
        };
      }
    }
    return { success: false, error: 'No response from ForeTees' };
  } catch (err) {
    return { success: false, error: err.message };
  } finally {
    await browser.close();
  }
}

// ── HTTP Server ──────────────────────────────────────────────
const server = http.createServer(async (req, res) => {
  const sendJSON = (status, data) => {
    res.writeHead(status, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify(data));
  };

  if (req.method === 'GET' && req.url === '/health') {
    return sendJSON(200, { status: 'ok' });
  }

  if (!checkAuth(req)) {
    return sendJSON(401, { error: 'Unauthorized' });
  }

  if (req.method !== 'POST') {
    return sendJSON(405, { error: 'Method not allowed' });
  }

  // Read body
  let body = '';
  for await (const chunk of req) body += chunk;
  let args;
  try {
    args = JSON.parse(body);
  } catch {
    return sendJSON(400, { error: 'Invalid JSON' });
  }

  const path = req.url.split('?')[0];
  let result;
  try {
    if (path === '/book') {
      console.log(`[${new Date().toISOString()}] POST /book date=${args.date} time=${args.time}`);
      result = await book(args);
    } else if (path === '/cancel') {
      console.log(`[${new Date().toISOString()}] POST /cancel date=${args.date} time=${args.time}`);
      result = await cancel(args);
    } else {
      return sendJSON(404, { error: 'Not found' });
    }
  } catch (err) {
    console.error(`[${new Date().toISOString()}] Unhandled error:`, err.message);
    result = { success: false, error: err.message };
  }

  console.log(`[${new Date().toISOString()}] Result: success=${result.success}`);
  sendJSON(result.success ? 200 : 400, result);
});

server.listen(PORT, () => {
  console.log(`ForeTees booking service listening on port ${PORT}`);
});

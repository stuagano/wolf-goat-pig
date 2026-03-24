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

// ── Book ─────────────────────────────────────────────────────
async function book(args) {
  const { username, password, date, time, transport_mode } = args;
  if (!username || !password || !date || !time)
    return { success: false, error: 'Missing required fields' };

  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();
  try {
    await loginAndSSO(page, username, password);
    await navigateToSlot(page, date, time);

    // Set transport mode
    await page.evaluate((mode) => {
      for (const sel of document.querySelectorAll('select')) {
        const opts = Array.from(sel.options).map((o) => o.value);
        if (opts.includes('WLK') || opts.includes('CRT')) {
          sel.value = mode;
          sel.dispatchEvent(new Event('change', { bubbles: true }));
          return;
        }
      }
    }, transport_mode || 'WLK');

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
  const { username, password, date, time } = args;
  if (!username || !password || !date || !time)
    return { success: false, error: 'Missing required fields' };

  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();
  try {
    await loginAndSSO(page, username, password);
    await navigateToSlot(page, date, time);

    const respPromise = page
      .waitForResponse((r) => r.url().includes('Member_slot') && r.request().method() === 'POST', { timeout: 15000 })
      .catch(() => null);

    await page.click('a.cancel_request_button');

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
  if (path === '/book') {
    console.log(`[${new Date().toISOString()}] POST /book date=${args.date} time=${args.time}`);
    result = await book(args);
  } else if (path === '/cancel') {
    console.log(`[${new Date().toISOString()}] POST /cancel date=${args.date} time=${args.time}`);
    result = await cancel(args);
  } else {
    return sendJSON(404, { error: 'Not found' });
  }

  console.log(`[${new Date().toISOString()}] Result: success=${result.success}`);
  sendJSON(result.success ? 200 : 400, result);
});

server.listen(PORT, () => {
  console.log(`ForeTees booking service listening on port ${PORT}`);
});

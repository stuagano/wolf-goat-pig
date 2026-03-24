/**
 * ForeTees v5 Tee Time Booking via Headless Browser
 *
 * ForeTees v5 is a JavaScript SPA that populates booking form fields
 * (teecurr_id, id_hash) at runtime via JS. These values cannot be
 * extracted via HTTP alone. This script uses Playwright to:
 *
 * 1. Authenticate with ForeTees (Wing Point Golf Club)
 * 2. Navigate to the Member_slot page with the ttdata token
 * 3. Wait for JS to populate the form
 * 4. Fill in the booking (player name, transport mode)
 * 5. Submit and return the result
 *
 * Usage:
 *   node foretees_book.js <json_args>
 *
 * Args (JSON):
 *   username: ForeTees login username
 *   password: ForeTees login password
 *   date: Date in YYYY-MM-DD format
 *   time: Time string like "12:00 PM"
 *   transport_mode: WLK, CRT, or PC
 *
 * Output: JSON to stdout with {success, title, messages} or {success, error}
 */

const { chromium } = require('playwright');

const WINGPOINT_BASE = 'https://www.wingpointgolf.com';
const LOGIN_PAGE = '/public/member-login-465.html';
const TEE_TIME_PAGE = '/members/golf/make-a-tee-time-703.html';
const FORETEES_BASE = 'https://ftapp.wingpointgolf.com/v5/wingpointgcc_flxrez0_m30';

async function book(args) {
  const { username, password, date, time, transport_mode } = args;

  if (!username || !password || !date || !time) {
    return { success: false, error: 'Missing required arguments (username, password, date, time)' };
  }

  const browser = await chromium.launch({
    headless: true,
    channel: 'chromium',  // Uses headless shell if installed via --only-shell
  });
  const context = await browser.newContext({
    userAgent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36',
  });
  const page = await context.newPage();

  try {
    // Step 1: Login to Wing Point
    console.error('[foretees_book] Logging in...');
    await page.goto(`${WINGPOINT_BASE}${LOGIN_PAGE}`, { waitUntil: 'networkidle' });

    await page.fill('input[name="UserLOGIN"]', username);
    await page.fill('input[name="UserPWD"]', password);
    await page.click('input[name="btnLogon"]');
    await page.waitForLoadState('networkidle');

    // Step 2: Navigate to tee time page to get SSO params
    console.error('[foretees_book] Getting SSO params...');
    await page.goto(`${WINGPOINT_BASE}${TEE_TIME_PAGE}`, { waitUntil: 'networkidle' });

    // Extract SSO key and IV from the page JS
    const ssoKey = await page.evaluate(() => {
      // Look for ftSSOKey in inline scripts
      const scripts = document.querySelectorAll('script');
      for (const s of scripts) {
        const match = s.textContent.match(/ftSSOKey\s*=\s*'([^']+)'/);
        if (match) return match[1];
      }
      return null;
    });

    const ssoIV = await page.evaluate(() => {
      const scripts = document.querySelectorAll('script');
      for (const s of scripts) {
        const match = s.textContent.match(/ftSSOIV\s*=\s*'([^']+)'/);
        if (match) return match[1];
      }
      return null;
    });

    if (!ssoKey || !ssoIV) {
      return { success: false, error: 'Could not find SSO params on tee time page' };
    }

    // Step 3: SSO into ForeTees
    console.error('[foretees_book] SSO into ForeTees...');
    const ssoUrl = `${FORETEES_BASE}/Member_select?sso_uid=${encodeURIComponent(ssoKey)}&sso_iv=${encodeURIComponent(ssoIV)}`;
    await page.goto(ssoUrl, { waitUntil: 'networkidle' });

    // Step 4: Load the tee sheet to establish context, then navigate to slot
    console.error('[foretees_book] Loading tee sheet...');

    // Step 4: Load tee sheet for the target date and click the slot
    // Parse YYYY-MM-DD into MM/DD/YYYY for ForeTees
    const [yy, mm, dd] = date.split('-');
    const ftDate = `${mm}/${dd}/${yy}`;
    console.error(`[foretees_book] Loading tee sheet for ${ftDate}...`);

    const sheetUrl = `${FORETEES_BASE}/Member_sheet?calDate=${encodeURIComponent(ftDate)}&course=&displayOpt=0`;
    await page.goto(sheetUrl, { waitUntil: 'networkidle' });
    await page.waitForTimeout(2000);

    // Find and click the slot matching the target time
    console.error(`[foretees_book] Looking for ${time} slot...`);
    const slotFound = await page.evaluate((targetTime) => {
      // ForeTees tee sheet has links like <a class="teetime_button">11:20 AM</a>
      const links = document.querySelectorAll('a.teetime_button, a[data-ftjson], .rwdTr a');
      for (const link of links) {
        const linkText = link.textContent.trim();
        if (linkText === targetTime) {
          link.click();
          return { found: true, time: linkText };
        }
      }
      // Try partial match
      for (const link of links) {
        if (link.textContent.includes(targetTime)) {
          link.click();
          return { found: true, time: link.textContent.trim() };
        }
      }
      return {
        found: false,
        available: Array.from(links).slice(0, 15).map(l => l.textContent.trim()),
      };
    }, time);

    if (!slotFound.found) {
      return {
        success: false,
        error: `Tee time slot "${time}" not found on ${date}`,
        debug: { available_times: slotFound.available },
      };
    }
    console.error(`[foretees_book] Clicked slot: ${slotFound.time}`);

    // Wait for the booking form to render (v5 SPA uses client-side routing)
    // The slot_container or booking form appears after JS processes the click
    try {
      await page.waitForSelector('.slot_container, .slot_form, [data-ftjson]', { timeout: 10000 });
      console.error('[foretees_book] Slot container appeared');
    } catch {
      // Fallback: wait for "Submit Request" text or "Time remaining" indicator
      try {
        await page.waitForFunction(
          () => document.body?.innerText?.includes('Submit Request') ||
                document.body?.innerText?.includes('Time remaining') ||
                document.body?.innerText?.includes('Add players'),
          { timeout: 10000 }
        );
        console.error('[foretees_book] Booking form text detected');
      } catch {
        console.error('[foretees_book] Form did not appear, waiting extra...');
        await page.waitForTimeout(5000);
      }
    }
    await page.waitForTimeout(2000);

    // Debug: log page state
    const formState = await page.evaluate(() => ({
      title: document.title,
      url: window.location.href,
      bodyPreview: document.body?.innerText?.substring(0, 300),
      hasSlotContainer: !!document.querySelector('.slot_container'),
      inputCount: document.querySelectorAll('input').length,
      selectCount: document.querySelectorAll('select').length,
    }));
    console.error(`[foretees_book] Form state: ${JSON.stringify(formState)}`);

    // Step 5: The booking form is now rendered with player 1 = current user.
    // ForeTees v5 auto-populates player 1. We just need to set transport
    // mode and click "Submit Request".
    console.error('[foretees_book] Setting transport mode and submitting...');

    // Set transport mode for player 1
    // ForeTees v5 has selects for transport — try all possible selector patterns
    const transportSet = await page.evaluate((mode) => {
      // Try all selects that might be transport mode
      const selects = document.querySelectorAll('select');
      for (const sel of selects) {
        const name = sel.name || '';
        // Transport selects are named p1cw, p2cw, etc. or similar
        if (name.match(/p\d*cw|tmode|transport/i) ||
            Array.from(sel.options).some(o => ['WLK', 'CRT', 'PC'].includes(o.value))) {
          // This is a transport select — set it for player 1
          if (name === 'p1cw' || name.includes('1') || !name.match(/p[2-5]cw/)) {
            sel.value = mode;
            sel.dispatchEvent(new Event('change', { bubbles: true }));
            return { set: true, method: 'select', name: sel.name, options: Array.from(sel.options).map(o => o.value) };
          }
        }
      }

      // If no named select found, try the first select with WLK/CRT/PC options
      for (const sel of selects) {
        const opts = Array.from(sel.options).map(o => o.value);
        if (opts.includes('WLK') || opts.includes('CRT') || opts.includes('PC')) {
          sel.value = mode;
          sel.dispatchEvent(new Event('change', { bubbles: true }));
          return { set: true, method: 'fallback-select', name: sel.name, options: opts };
        }
      }

      return {
        set: false,
        selectNames: Array.from(selects).map(s => s.name),
        selectOptions: Array.from(selects).map(s => ({ name: s.name, opts: Array.from(s.options).map(o => o.value).slice(0, 5) })),
      };
    }, transport_mode || 'WLK');
    console.error(`[foretees_book] Transport: ${JSON.stringify(transportSet)}`);

    // Find and click "Submit Request" button
    // Listen for navigation or AJAX response
    const responsePromise = page.waitForResponse(
      resp => resp.url().includes('Member_slot') && resp.request().method() === 'POST',
      { timeout: 15000 }
    ).catch(() => null);

    const submitClicked = await page.evaluate(() => {
      // Look for submit button by text
      const allButtons = document.querySelectorAll('button, input[type="button"], input[type="submit"], a, div[role="button"]');
      for (const btn of allButtons) {
        const text = (btn.textContent || btn.value || '').trim().toLowerCase();
        if (text.includes('submit request') || text.includes('submit')) {
          btn.click();
          return { clicked: true, text: text.substring(0, 50) };
        }
      }

      // Try finding by class/id patterns
      const submitBtn = document.querySelector('.submitButton, #submitButton, [data-action="submit"], .slot_submit');
      if (submitBtn) {
        submitBtn.click();
        return { clicked: true, text: submitBtn.textContent?.substring(0, 50) || 'class match' };
      }

      return {
        clicked: false,
        buttons: Array.from(allButtons).slice(0, 10).map(b => (b.textContent || b.value || '').trim().substring(0, 40)),
      };
    });

    console.error(`[foretees_book] Submit: ${JSON.stringify(submitClicked)}`);

    if (!submitClicked.clicked) {
      return {
        success: false,
        error: 'No submit button found on booking page',
        debug: submitClicked,
      };
    }

    // Wait for the booking response
    const postResponse = await responsePromise;
    if (postResponse) {
      const respText = await postResponse.text();
      console.error(`[foretees_book] POST response: ${postResponse.status()} ${respText.substring(0, 200)}`);

      // Try to parse JSON response
      try {
        const jsonResp = JSON.parse(respText);
        const success = jsonResp.successful === true;
        const messages = [
          ...(jsonResp.message_list || []),
          ...(jsonResp.notice_list || []),
          ...(jsonResp.warning_list || []),
        ];
        return {
          success,
          title: jsonResp.title || '',
          messages: messages.length > 0 ? messages : [success ? 'Booking confirmed' : 'Booking failed'],
        };
      } catch {
        // Non-JSON response — check page content
      }
    }

    // Wait for page to update after submission
    await page.waitForTimeout(3000);

    // Check the page for success/error messages
    const result = await page.evaluate(() => {
      const bodyText = document.body?.innerText || '';
      const title = document.title || '';

      if (bodyText.includes('Confirmation') || bodyText.includes('confirmed') ||
          bodyText.includes('successfully') || bodyText.includes('booked')) {
        return { success: true, title: 'Booking Confirmed', messages: [bodyText.substring(0, 500)] };
      }

      return { success: false, title, messages: [bodyText.substring(0, 500)] };
    });

    return result;

  } catch (err) {
    return { success: false, error: `Browser error: ${err.message}` };
  } finally {
    await browser.close();
  }
}

// Main: read args from command line
const args = JSON.parse(process.argv[2] || '{}');
book(args)
  .then(result => {
    console.log(JSON.stringify(result));
    process.exit(result.success ? 0 : 1);
  })
  .catch(err => {
    console.log(JSON.stringify({ success: false, error: err.message }));
    process.exit(1);
  });

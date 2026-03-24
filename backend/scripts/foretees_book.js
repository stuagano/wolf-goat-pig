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
 *   ttdata: Encrypted tee time slot identifier
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
  const { username, password, ttdata, transport_mode } = args;

  if (!username || !password || !ttdata) {
    return { success: false, error: 'Missing required arguments' };
  }

  const browser = await chromium.launch({ headless: true });
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

    // Step 4: Navigate to the slot booking page
    console.error('[foretees_book] Loading slot page...');
    const slotUrl = `${FORETEES_BASE}/Member_slot?ttdata=${encodeURIComponent(ttdata)}`;
    await page.goto(slotUrl, { waitUntil: 'networkidle' });

    // Wait for the v5 SPA to render the form
    // The slot_container div gets populated by JS
    await page.waitForTimeout(3000);

    // Step 5: Extract teecurr_id and id_hash from the rendered DOM
    console.error('[foretees_book] Extracting form data...');
    const formData = await page.evaluate(() => {
      const fields = {};

      // Try getting values from input fields (if they exist after JS render)
      document.querySelectorAll('input[name]').forEach(input => {
        fields[input.name] = input.value;
      });

      // Also try select elements
      document.querySelectorAll('select[name]').forEach(select => {
        fields[select.name] = select.value;
      });

      return {
        fields,
        fieldCount: Object.keys(fields).length,
        teecurr_id1: fields.teecurr_id1 || '',
        id_hash: fields.id_hash || '',
        pageTitle: document.title,
        bodyPreview: document.body?.innerText?.substring(0, 500) || '',
      };
    });

    console.error(`[foretees_book] Found ${formData.fieldCount} form fields, teecurr_id1=${formData.teecurr_id1 ? 'yes' : 'no'}, id_hash=${formData.id_hash ? 'yes' : 'no'}`);

    if (!formData.teecurr_id1 || formData.teecurr_id1 === '0') {
      // Return debug info
      return {
        success: false,
        error: 'Could not extract teecurr_id from rendered page',
        debug: {
          pageTitle: formData.pageTitle,
          fieldCount: formData.fieldCount,
          fieldNames: Object.keys(formData.fields).slice(0, 20),
          bodyPreview: formData.bodyPreview,
        },
      };
    }

    // Step 6: Set transport mode and submit the form
    console.error('[foretees_book] Submitting booking...');

    // Set the transport mode for player 1
    const transportSelect = await page.$('select[name="p1cw"]');
    if (transportSelect) {
      await transportSelect.selectOption(transport_mode || 'WLK');
    }

    // Click the submit/update button
    // ForeTees v5 uses a button or link to submit
    const submitResult = await page.evaluate(async (transport) => {
      // Find and fill the form programmatically
      const form = document.querySelector('form') ||
        document.querySelector('[data-ftjson]')?.closest('form');

      // Set transport mode directly
      const cwSelect = document.querySelector('select[name="p1cw"]');
      if (cwSelect) cwSelect.value = transport;

      // Find the submit button
      const submitBtn = document.querySelector('input[name="submitForm"]') ||
        document.querySelector('button[type="submit"]') ||
        document.querySelector('[data-action="submit"]') ||
        document.querySelector('.submit_button') ||
        document.querySelector('#submitButton');

      if (submitBtn) {
        submitBtn.click();
        return { clicked: true, buttonText: submitBtn.textContent || submitBtn.value };
      }

      // Try clicking any visible "Submit" or "Confirm" button
      const buttons = document.querySelectorAll('button, input[type="button"], input[type="submit"], a.button');
      for (const btn of buttons) {
        const text = (btn.textContent || btn.value || '').toLowerCase();
        if (text.includes('submit') || text.includes('confirm') || text.includes('book')) {
          btn.click();
          return { clicked: true, buttonText: text };
        }
      }

      return { clicked: false, error: 'No submit button found' };
    }, transport_mode || 'WLK');

    console.error(`[foretees_book] Submit result: ${JSON.stringify(submitResult)}`);

    if (!submitResult.clicked) {
      return { success: false, error: 'No submit button found on page', debug: submitResult };
    }

    // Wait for the response
    await page.waitForTimeout(3000);

    // Check for success/error messages
    const result = await page.evaluate(() => {
      const bodyText = document.body?.innerText || '';
      const title = document.title || '';

      // Look for success indicators
      if (bodyText.includes('confirmed') || bodyText.includes('Confirmed') ||
          bodyText.includes('successfully') || bodyText.includes('booked')) {
        return { success: true, title: 'Booking Confirmed', messages: [bodyText.substring(0, 500)] };
      }

      // Look for error indicators
      if (bodyText.includes('Error') || bodyText.includes('error') ||
          bodyText.includes('Unable') || bodyText.includes('Sorry')) {
        return { success: false, title: title, messages: [bodyText.substring(0, 500)] };
      }

      return { success: false, title: title, messages: ['Unknown result: ' + bodyText.substring(0, 500)] };
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

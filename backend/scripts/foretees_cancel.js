/**
 * ForeTees v5 Tee Time Cancellation via Headless Browser
 *
 * Navigates to an existing booking and cancels it.
 *
 * Usage:
 *   node foretees_cancel.js <json_args>
 *
 * Args: { username, password, date (YYYY-MM-DD), time ("1:30 PM") }
 */

const { chromium } = require('playwright');

const WINGPOINT_BASE = 'https://www.wingpointgolf.com';
const LOGIN_PAGE = '/public/member-login-465.html';
const TEE_TIME_PAGE = '/members/golf/make-a-tee-time-703.html';
const FORETEES_BASE = 'https://ftapp.wingpointgolf.com/v5/wingpointgcc_flxrez0_m30';

async function cancel(args) {
  const { username, password, date, time } = args;
  if (!username || !password || !date || !time) {
    return { success: false, error: 'Missing required arguments' };
  }

  const browser = await chromium.launch({
    headless: true,
    channel: 'chromium',
  });
  const context = await browser.newContext({
    userAgent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
  });
  const page = await context.newPage();

  try {
    // Login
    console.error('[cancel] Logging in...');
    await page.goto(`${WINGPOINT_BASE}${LOGIN_PAGE}`, { waitUntil: 'networkidle' });
    await page.fill('input[name="UserLOGIN"]', username);
    await page.fill('input[name="UserPWD"]', password);
    await page.click('input[name="btnLogon"]');
    await page.waitForLoadState('networkidle');

    // Get SSO
    console.error('[cancel] Getting SSO...');
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
    if (!ssoKey || !ssoIV) return { success: false, error: 'No SSO params' };

    // SSO into ForeTees
    console.error('[cancel] SSO into ForeTees...');
    await page.goto(`${FORETEES_BASE}/Member_select?sso_uid=${encodeURIComponent(ssoKey)}&sso_iv=${encodeURIComponent(ssoIV)}`, { waitUntil: 'networkidle' });

    // Load tee sheet
    const [yy, mm, dd] = date.split('-');
    const ftDate = `${mm}/${dd}/${yy}`;
    console.error(`[cancel] Loading tee sheet for ${ftDate}...`);
    await page.goto(`${FORETEES_BASE}/Member_sheet?calDate=${encodeURIComponent(ftDate)}&course=&displayOpt=0`, { waitUntil: 'networkidle' });
    await page.waitForTimeout(2000);

    // Click the slot
    console.error(`[cancel] Looking for ${time} slot...`);
    const slotFound = await page.evaluate((targetTime) => {
      const links = document.querySelectorAll('a.teetime_button, a[data-ftjson], .rwdTr a');
      for (const link of links) {
        if (link.textContent.trim() === targetTime) {
          link.click();
          return { found: true };
        }
      }
      return { found: false, available: Array.from(links).slice(0, 15).map(l => l.textContent.trim()) };
    }, time);

    if (!slotFound.found) {
      return { success: false, error: `Slot "${time}" not found`, debug: slotFound };
    }

    // Wait for booking form
    console.error('[cancel] Waiting for booking form...');
    try {
      await page.waitForSelector('.slot_container', { timeout: 10000 });
    } catch {
      try {
        await page.waitForFunction(
          () => document.body?.innerText?.includes('Submit Changes') ||
                document.body?.innerText?.includes('Cancel'),
          { timeout: 10000 }
        );
      } catch {
        await page.waitForTimeout(5000);
      }
    }
    await page.waitForTimeout(2000);

    // Look for cancel/remove buttons
    console.error('[cancel] Looking for cancel button...');

    // Listen for POST response
    const responsePromise = page.waitForResponse(
      resp => resp.url().includes('Member_slot') && resp.request().method() === 'POST',
      { timeout: 15000 }
    ).catch(() => null);

    const cancelResult = await page.evaluate(() => {
      // Look for cancel/remove/delete buttons
      const allEls = document.querySelectorAll('button, input[type="button"], input[type="submit"], a, div[role="button"], span');
      for (const el of allEls) {
        const text = (el.textContent || el.value || '').trim().toLowerCase();
        if (text.includes('cancel') && !text.includes('cancel changes') ||
            text.includes('remove') || text.includes('delete')) {
          // Check it's not a navigation "Cancel" but a booking cancel
          if (el.closest('.slot_container, .slot_form, #content, .rwdContent')) {
            el.click();
            return { clicked: true, text: text.substring(0, 50), method: 'slot-scoped' };
          }
        }
      }
      // Try broader search
      for (const el of allEls) {
        const text = (el.textContent || el.value || '').trim().toLowerCase();
        if (text === 'cancel tee time' || text === 'cancel reservation' ||
            text === 'remove me' || text === 'remove') {
          el.click();
          return { clicked: true, text: text, method: 'exact-match' };
        }
      }
      // List all button-like elements for debugging
      return {
        clicked: false,
        buttons: Array.from(allEls)
          .filter(e => (e.textContent || '').trim().length > 0 && (e.textContent || '').trim().length < 50)
          .slice(0, 20)
          .map(e => (e.textContent || e.value || '').trim()),
      };
    });

    console.error(`[cancel] Cancel result: ${JSON.stringify(cancelResult)}`);

    if (!cancelResult.clicked) {
      // Maybe there's a "remove originator" checkbox + submit
      const hasRemove = await page.evaluate(() => {
        const checkbox = document.querySelector('input[name="remove_originator"], #remove_originator');
        if (checkbox) {
          checkbox.checked = true;
          checkbox.value = '1';
          checkbox.dispatchEvent(new Event('change', { bubbles: true }));
          return true;
        }
        return false;
      });

      if (hasRemove) {
        console.error('[cancel] Set remove_originator checkbox, submitting...');
        await page.evaluate(() => {
          const buttons = document.querySelectorAll('button, input[type="button"], input[type="submit"], a');
          for (const btn of buttons) {
            const text = (btn.textContent || btn.value || '').trim().toLowerCase();
            if (text.includes('submit')) {
              btn.click();
              return;
            }
          }
        });
      } else {
        return { success: false, error: 'No cancel button found', debug: cancelResult };
      }
    }

    // Wait for response
    const postResponse = await responsePromise;
    if (postResponse) {
      const respText = await postResponse.text();
      console.error(`[cancel] POST response: ${postResponse.status()} ${respText.substring(0, 300)}`);
      try {
        const jsonResp = JSON.parse(respText);
        const success = jsonResp.successful === true;
        const messages = [
          ...(jsonResp.message_list || []),
          ...(jsonResp.notice_list || []),
          ...(jsonResp.warning_list || []),
        ];
        return { success, title: jsonResp.title || '', messages };
      } catch { /* non-JSON */ }
    }

    await page.waitForTimeout(3000);
    const pageText = await page.evaluate(() => document.body?.innerText?.substring(0, 500));
    console.error(`[cancel] Page after action: ${pageText?.substring(0, 200)}`);

    if (pageText?.includes('cancelled') || pageText?.includes('removed') || pageText?.includes('Cancelled')) {
      return { success: true, title: 'Tee time cancelled', messages: [pageText.substring(0, 300)] };
    }

    return { success: false, title: 'Unknown result', messages: [pageText?.substring(0, 300) || 'No page content'] };

  } catch (err) {
    return { success: false, error: `Browser error: ${err.message}` };
  } finally {
    await browser.close();
  }
}

const args = JSON.parse(process.argv[2] || '{}');
cancel(args)
  .then(result => {
    console.log(JSON.stringify(result));
    process.exit(result.success ? 0 : 1);
  })
  .catch(err => {
    console.log(JSON.stringify({ success: false, error: err.message }));
    process.exit(1);
  });

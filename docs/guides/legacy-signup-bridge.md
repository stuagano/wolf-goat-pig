# Bridging the Legacy Tee Sheet

This guide explains how to run the modern Wolf Goat Pig sign-up workflow while
keeping the legacy CGI sheet (`wgp_tee_sheet.cgi`) in sync. The bridge is
entirely configuration-driven so you can pilot the new UI without disrupting the
existing production surface.

## 1. Configure the backend sync client

The backend now includes a best-effort client that mirrors create/update/cancel
operations to the legacy system. All configuration is sourced from environment
variables—update your `.env` (or deployment secrets) with the following keys:

```env
LEGACY_SIGNUP_SYNC_ENABLED=true
LEGACY_SIGNUP_CREATE_URL=https://thousand-cranes.com/WolfGoatPig/wgp_tee_sheet.cgi
# Optional overrides; omit to reuse the create URL
LEGACY_SIGNUP_UPDATE_URL=
LEGACY_SIGNUP_CANCEL_URL=

# Request shaping
LEGACY_SIGNUP_PAYLOAD_FORMAT=form  # or "json" if the CGI accepts JSON
LEGACY_SIGNUP_FIELD_MAP={"player_name": "player", "date": "signup_date"}
LEGACY_SIGNUP_EXTRA_FIELDS={"sheet_id": "wing-point"}
LEGACY_SIGNUP_CREATE_ACTION_FIELD=action
LEGACY_SIGNUP_CREATE_ACTION_VALUE=add
LEGACY_SIGNUP_UPDATE_ACTION_VALUE=update
LEGACY_SIGNUP_CANCEL_ACTION_VALUE=cancel
LEGACY_SIGNUP_TIMEOUT_SECONDS=10
LEGACY_SIGNUP_API_KEY= # Optional bearer token/header if you front the CGI with a proxy
```

**Recommendations**

- Keep credentials out of source control—place the values in your deployment
  secret manager and only mirror safe defaults in `.env.example`.
- If the legacy CGI requires HTTP basic auth or CSRF tokens, terminate those
  in a small proxy (Cloudflare Worker, AWS Lambda, etc.) and point the
  `LEGACY_SIGNUP_*_URL` variables at the proxy instead of the CGI directly.
- Monitor the logs (`Legacy signup sync ...`) to confirm the bridge is
  operating; failed calls are logged with warning level but never block modern
  clients.

## 2. Offer an opt-in banner on the legacy page

Because we cannot edit the CGI directly from this repository, you can drop the
following snippet onto the legacy HTML (e.g., via a Dreamweaver include or by
asking the host admin to paste it near the top of the page):

```html
<div style="margin:1rem 0;padding:1rem;border:2px dashed #065f46;background:#ecfdf5">
  <strong>🐺 Try the modern Wolf Goat Pig sign-up sheet!</strong>
  <p style="margin:0.5rem 0">
    Enjoy calendar views, reminders, and matchmaking suggestions while we
    continue to sync with the classic tee sheet everyone knows.
  </p>
  <a
    href="https://wolf-goat-pig.vercel.app/signup"
    style="display:inline-flex;align-items:center;gap:0.5rem;padding:0.6rem 1.2rem;background:#047857;color:#fff;font-weight:600;border-radius:0.5rem;text-decoration:none"
  >
    🚀 Try the new sign-up experience
  </a>
</div>
```

Feel free to update the link to point at your staging environment. If the CGI
does not allow HTML edits, consider injecting the banner via the hosting
provider's template system or a reverse-proxy HTML rewriter.

## 3. Operational checklist

1. Set the environment variables above in staging.
2. Verify new sign-ups replicate to the legacy sheet.
3. Validate cancellations propagate (either by deleting through the new UI or
   by hitting the `/signups/{id}` DELETE endpoint).
4. Once validated, enable the same configuration in production.
5. Monitor logs during the initial rollout and capture the warnings so we can
   harden the integration (e.g., add retries/backoff) if necessary.

## 4. Manually probe the legacy CGI

If you want to double-check the remote CGI accepts posts before flipping the
feature flag in production, use the `scripts/legacy_sync_probe.py` helper. The
script reuses the same configuration described above, keeping things DRY:

```bash
LEGACY_SIGNUP_SYNC_ENABLED=true \
LEGACY_SIGNUP_CREATE_URL=https://thousand-cranes.com/WolfGoatPig/wgp_tee_sheet.cgi \
LEGACY_SIGNUP_FIELD_MAP='{"player_name": "player"}' \
python scripts/legacy_sync_probe.py \
  --date 2024-05-01 \
  --player-name "Preview Golfer" \
  --preferred-start-time "07:30" \
  --notes "Smoke test" \
  --preview
```

Drop the `--preview` flag once you are ready to send a real request. Successful
responses log `Legacy CGI responded successfully`; failures bubble up the HTTP
status or transport error so you can adjust proxy credentials, firewall rules,
or payload mappings.

## 5. Future improvements

- Harden transport with signed webhooks instead of form posts.
- Capture a real API contract for the CGI so we can write automated tests
  against a mock server.
- Consider a scheduled reconciliation job that compares both systems and alerts
  when they drift.

Following these steps keeps us DRY—the mapping and action values live in one
place—and lets us migrate users gradually without breaking their current
workflow.

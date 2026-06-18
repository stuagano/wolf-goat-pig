# Uptime monitoring setup (Phase 2b)

`GET /health/external` runs read-only probes of the 8 external services (cached
~5 min, guarded by `X-Monitor-Key` when `MONITOR_KEY` is set). An external uptime
service pings it + `/health` and emails on failure.

## 1. Set the monitor key (Render)
- In the Render backend service env (`wolf-goat-pig-api` → Environment), set `MONITOR_KEY` to a **URL-safe** random value — generate one with `openssl rand -hex 32` (hex has no `/ + =`, so it works in a URL).
- (Optional) set `EXTERNAL_HEALTH_TTL` (seconds, default 300).

## 2. Create the monitors (UptimeRobot or BetterStack — free tier)
- **Monitor A — app up:** `GET https://wolf-goat-pig.onrender.com/health`, every 5 min. Alert if non-200. (No key needed.)
- **Monitor B — externals:** every 5–15 min, alert if non-200. The guard key can be sent two ways — use whichever your tool supports:
  - **Query param (works everywhere, incl. UptimeRobot free):**
    `GET https://wolf-goat-pig.onrender.com/health/external?monitor_key=<MONITOR_KEY>`
  - **Custom header (if your tool allows it):** `GET …/health/external` with header `X-Monitor-Key: <MONITOR_KEY>`.
- To reduce flapping, set the monitor to alert only after 2 consecutive failures.

## 3. Alerts → email
- Add stuagano@gmail.com as the alert contact on both monitors.

## What this catches (that Sentry/2a can't)
- **Total downtime** — `/health` unreachable.
- **A genuinely-down external** even with no user traffic — `/health/external` returns 503 listing the down services. (`not_configured` services never trigger an alert.)

## Notes
- The endpoint is cached, so pinging more often than the TTL does not increase real external calls (Groq spend / GHIN-ForeTees logins are bounded to ≤ once per TTL per instance).
- Down services are also sent to Sentry (`capture_message`) when `SENTRY_DSN` is set — a secondary signal alongside the monitor email.
- If `MONITOR_KEY` is unset, the endpoint is open (intended for local/dev, where no creds are configured so the probes all report `not_configured`). Always set `MONITOR_KEY` in production.

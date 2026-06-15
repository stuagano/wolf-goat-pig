# Making render.yaml authoritative (Render Blueprint)

`render.yaml` is version-controlled IaC for the backend + booking services, but
it only drives the live services if they are connected to Render as a
**Blueprint**. Today the live service was created/managed manually, so
`render.yaml` env changes do **not** auto-apply (you've been setting env in the
dashboard). This is how to make `render.yaml` the source of truth — and the one
trap to avoid first.

## ⚠️ Read this before connecting the Blueprint

When a Blueprint syncs, every env var with a literal `value:` in `render.yaml`
is **written to the service**, overwriting whatever is in the dashboard. Vars
with `sync: false` are left alone (dashboard-managed); `generateValue: true`
are generated once.

`render.yaml` currently declares these as **empty** literals:

```
FORETEES_USERNAME       value: ""
FORETEES_PASSWORD       value: ""
FORETEES_ENCRYPTION_KEY value: ""   # ← if this is set in the dashboard, a sync BLANKS it
```

`FORETEES_ENCRYPTION_KEY` is the Fernet key that decrypts per-user ForeTees
credentials — blanking it breaks ForeTees. **Before connecting the Blueprint**,
either confirm these are genuinely unused (per-user creds only, no global
account) or change them to `sync: false` so the Blueprint leaves the dashboard
values intact. (Ask Isaac to flip them to `sync: false` if unsure.)

## Connect the Blueprint

1. In the Render dashboard: **New → Blueprint** (or **Blueprints → New Blueprint Instance**), pick the `stuagano/wolf-goat-pig` repo.
2. Render reads `render.yaml` and lists the services. Because the names match
   the existing services (`wolf-goat-pig-api`, `wolf-goat-pig-booking`), Render
   **adopts** them rather than creating duplicates. Confirm it shows "update
   existing," not "create new" — if it offers to create new ones, the names
   don't match; stop and reconcile (don't end up with duplicate services).
3. Apply. From now on, a push to `main` that changes `render.yaml` syncs the
   `value:` env vars automatically. Secrets stay `sync: false` (set once in the
   dashboard); `MONITOR_KEY` is generated once by Render.

## What's already in code (this PR)

- `SENTRY_DSN` — `value:` (Sentry ingestion key, public by design). Applies on Blueprint sync.
- `MONITOR_KEY` — `generateValue: true` (Render makes a strong value; copy it from the dashboard into the uptime monitor's `X-Monitor-Key` header).
- `EXTERNAL_HEALTH_TTL` — `value: "300"`.

## Interim (before the Blueprint is connected)

Until you connect the Blueprint, the live service still ignores `render.yaml`.
To turn Sentry on **now**, set one env var in the Render dashboard:
`SENTRY_DSN` = the value in `render.yaml`. Once the Blueprint is connected you
can delete that manual override and let `render.yaml` drive it.

## Why some things must stay out of render.yaml

- True secrets (`DATABASE_URL`, `RESEND_API_KEY`, `GHIN_API_PASS`,
  `BOOKING_SERVICE_SECRET`, the ForeTees creds) → `sync: false`. Never commit
  them to this public repo.
- The frontend `VITE_SENTRY_DSN` lives in **Vercel** (it's a frontend build
  var), not here. It's public-safe (ships in the browser), so it can go in
  `vercel.json` `build.env` for version control once a frontend Sentry project
  exists — or be set in the Vercel dashboard.

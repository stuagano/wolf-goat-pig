# Production cutover — GCP is primary

**As of 2026-07-26:** Firebase Hosting + Cloud Run + Cloud SQL are **production**.
Vercel + Render are being frozen / decommissioned.

| Role | Frontend | API | DB |
|---|---|---|---|
| **Production** | Firebase Hosting | Cloud Run | Cloud SQL (`db-f1-micro`) |
| Rollback only (warm) | Vercel (paused) | Render web (suspended) | Render Postgres (keep ~7 days) |

**Production URLs**

- SPA: https://seventh-country-232522.web.app
- API: https://wolf-goat-pig-api-i5v2shrpoa-uc.a.run.app
- Auth0 cutover: [phase3-hosting/AUTH0_CUTOVER.md](phase3-hosting/AUTH0_CUTOVER.md)

## Cutover status

- [x] Auth0 includes Firebase domains (keep localhost for local dev)
- [x] Cloud Run `/health` + `/ready` healthy against Cloud SQL
- [x] Cloud Scheduler jobs enabled
- [x] Avatars on GCS (`wgp-media-seventh-country-232522`)
- [ ] Remove Vercel URLs from Auth0 (Firebase + localhost only)
- [ ] Suspend Render web service (keep Postgres)
- [ ] Pause / archive Vercel project
- [ ] After ≥7 days with no rollback need: delete Render Postgres
- [ ] Delete secret `RENDER_DATABASE_URL` after Postgres is gone

## Auth0 (do in dashboard)

App: `qAZuRv5E9mPQ9uTGg7NWpkpfVj8bCeoB`

**Allowed Callback / Logout / Web Origins — production set:**

```
https://seventh-country-232522.web.app
https://seventh-country-232522.firebaseapp.com
http://localhost:3000
```

Optionally set **Application Login URI** to `https://seventh-country-232522.web.app`.

Remove all `*.vercel.app` entries.

## Suspend Render (dashboard or CLI)

1. https://dashboard.render.com → `wolf-goat-pig` web service → **Suspend**
2. Leave the Postgres instance running for ~7 days
3. Booking microservice (`wolf-goat-pig-booking`) — leave running if ForeTees booking is still needed; it is still referenced by Cloud Run `BOOKING_SERVICE_URL`

```bash
render login
render services list
# then suspend the API web service in the dashboard (CLI suspend varies by plan)
```

## Pause Vercel

```bash
vercel login
vercel project ls
# Dashboard: Project → Settings → Advanced → Pause / Delete
# Or: leave project but remove production domain traffic
```

Production bookmark: **https://seventh-country-232522.web.app** only.

## Rollback (only while Render Postgres still exists)

```bash
printf '%s' "$(gcloud secrets versions access latest --secret=RENDER_DATABASE_URL)" \
  | gcloud secrets versions add DATABASE_URL --data-file=-
gcloud run services update wolf-goat-pig-api --region=us-central1 \
  --update-secrets=DATABASE_URL=DATABASE_URL:latest
```

Also re-enable the Render web service and unpause Vercel if you need the old SPA.

## After 7 days — delete Render Postgres

Only when you are sure you will not roll back:

1. Dashboard → Postgres → Delete
2. `gcloud secrets delete RENDER_DATABASE_URL --project=seventh-country-232522`
3. Remove any remaining Render URLs from docs / Auth0 / env examples

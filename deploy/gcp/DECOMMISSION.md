# Production cutover — GCP is primary

**As of 2026-07-31:** Firebase Hosting + Cloud Run + Cloud SQL are production.
All Render services and Render Postgres have been deleted; Vercel is paused.

| Role | Frontend | API | DB |
|---|---|---|---|
| **Production** | Firebase Hosting | Cloud Run | Cloud SQL (`db-f1-micro`) |

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
- [x] Pause / archive Vercel project (paused 2026-07-27 via Pause Vercel workflow)
- [x] Remove legacy `.github/workflows/deploy.yml` (Render/Vercel deploy hook) — GCP only (2026-07-29)
- [x] Deploy Computer Use booking agent (`wgp-booking`) and flip `BOOKING_SERVICE_URL` (2026-07-28)
- [x] Delete Render `wolf-goat-pig-booking` (2026-07-31; prod uses `wgp-booking`)
- [x] Delete Render Postgres (2026-07-31)
- [x] Delete secret `RENDER_DATABASE_URL` (2026-07-31)
- [x] Delete Render web services `wolf-goat-pig` + `wolf-goat-pig-api` (2026-07-31)

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

## Remaining manual cleanup

1. Remove all `*.vercel.app` entries from Auth0.
2. Delete the paused Vercel project when no longer needed as a historical shell.

Production bookmark: **https://seventh-country-232522.web.app** only.

There is no live Render rollback path. Recovery now uses Cloud SQL backups and
Cloud Run revision rollback.

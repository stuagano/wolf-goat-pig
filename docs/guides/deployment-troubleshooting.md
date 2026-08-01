# Deployment Troubleshooting

Production runs on Firebase Hosting, Cloud Run, and Cloud SQL. Start with:

```bash
curl https://wolf-goat-pig-api-i5v2shrpoa-uc.a.run.app/health
./scripts/deployment/verify-deployment.sh
```

## Cloud Run API

### Revision will not become ready

- Inspect the failing revision's Cloud Run logs.
- Confirm Secret Manager mappings in the deploy workflow.
- Verify `deploy/gcp/phase1-cloud-run/env.production.yaml`.
- Reproduce the import locally: `cd backend && venv/bin/python -c "from app.main import app"`.
- Check migration failures before later startup errors.

### Database failures

- Confirm `DATABASE_URL` points to Cloud SQL and uses `postgresql://`.
- Check the Cloud SQL instance and connector logs.
- Review migration logs from the revision startup.
- Use Cloud SQL backups or point-in-time recovery for data recovery.

### Authentication failures

`AUTH0_API_AUDIENCE` and `VITE_AUTH0_AUDIENCE` must match exactly. Their current
hostname-shaped value is a stable Auth0 identifier, not a live Render URL.

A junk bearer token sent to `/players/me` should return 401. A 500 indicates
broken backend auth configuration.

### CORS failures

- `FRONTEND_URL` must be `https://seventh-country-232522.web.app`.
- The backend also permits Firebase's `firebaseapp.com` alternate domain.
- `VITE_API_URL` is baked into the frontend build; rebuild after changing it.

## Firebase frontend

### Build fails

Run the same gate locally:

```bash
cd frontend
npm ci --legacy-peer-deps --no-audit
npm run typecheck
npx vitest run
npm run build
```

Check case-sensitive imports and confirm `frontend/build` was produced.

### Routes return 404

`firebase.json` rewrites all SPA routes to `/index.html`. Confirm the deployed
release includes that file and that the Hosting target points at
`frontend/build`.

### App calls the wrong API

Set the GitHub Actions repository variable `VITE_API_URL` to:

```text
https://wolf-goat-pig-api-i5v2shrpoa-uc.a.run.app
```

Then redeploy Firebase Hosting.

## Scheduler failures

Inspect Cloud Scheduler execution logs and the corresponding
`/internal/jobs/*` Cloud Run logs. Scheduler requests require the
`X-Internal-Job-Token` header, backed by the `INTERNAL_JOB_TOKEN` secret.

## Rollback

- Cloud Run: send traffic to a previous healthy revision.
- Firebase Hosting: roll back from Hosting release history.
- Cloud SQL: restore from backup / point-in-time recovery.

Render and Vercel are not production rollback targets.

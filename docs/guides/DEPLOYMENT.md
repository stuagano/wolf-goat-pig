# Deployment Guide

Wolf Goat Pig runs entirely on Google Cloud:

- Frontend: Firebase Hosting — https://seventh-country-232522.web.app
- API: Cloud Run — https://wolf-goat-pig-api-i5v2shrpoa-uc.a.run.app
- Database: Cloud SQL for PostgreSQL
- Booking agent: Cloud Run (`wgp-booking`)
- Scheduled work: Cloud Scheduler and selected GitHub Actions crons

The canonical infrastructure guide is
[`deploy/gcp/README.md`](../../deploy/gcp/README.md).

## Pre-push gate

Pushing to `main` may deploy production when `GCP_AUTO_DEPLOY=true`.

```bash
# Frontend
cd frontend && npm run typecheck && npx vitest run && npm run build

# Backend
cd backend && ruff check app/ tests/ && ruff format --check app/ tests/ \
  && python scripts/export_openapi.py --check \
  && pytest tests/ --ignore=tests/manual --ignore=tests/_diagnostic
```

## Deployment

`.github/workflows/deploy-gcp.yml` owns production deploys. It supports manual
backend, frontend, and booking-agent deploys; pushes to `main` auto-deploy the
affected service when the repository variable `GCP_AUTO_DEPLOY` is `true`.

The frontend build receives `VITE_API_URL` from the GitHub Actions repository
variable. Backend non-secret configuration lives in
`deploy/gcp/phase1-cloud-run/env.production.yaml`; secrets live in Secret
Manager and are mapped in `deploy/gcp/secrets.md`.

The Auth0 audience remains `https://wolf-goat-pig.onrender.com` as a stable API
identifier. It is not an active Render endpoint and must match in frontend and
backend configuration unless the Auth0 API identifier is deliberately migrated.

## Post-deploy verification

```bash
curl https://wolf-goat-pig-api-i5v2shrpoa-uc.a.run.app/health

curl -o /dev/null -w '%{http_code}\n' \
  -H 'Authorization: Bearer junk.token.here' \
  https://wolf-goat-pig-api-i5v2shrpoa-uc.a.run.app/players/me

./scripts/deployment/verify-deployment.sh
```

`/health` must report `environment: production`; the junk token request must
return 401 rather than 500.

## Rollback

- Cloud Run: route traffic to a previous healthy revision.
- Firebase Hosting: use Hosting release history to roll back.
- Database: use Cloud SQL backups / point-in-time recovery.
- Code: revert the offending commit and push after running the full gate.

Render services and Render Postgres were deleted on 2026-07-31. They are not a
rollback path.

## Monitoring

- [Cloud Monitoring](https://console.cloud.google.com/monitoring?project=seventh-country-232522)
- [Cloud Run](https://console.cloud.google.com/run?project=seventh-country-232522)
- [Cloud Scheduler](https://console.cloud.google.com/cloudscheduler?project=seventh-country-232522)
- [Firebase Hosting](https://console.firebase.google.com/project/seventh-country-232522/hosting)

See [deployment troubleshooting](./deployment-troubleshooting.md) for common
failure modes.

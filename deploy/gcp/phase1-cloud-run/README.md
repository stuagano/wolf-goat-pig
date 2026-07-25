# Phase 1 — Compute (FastAPI on Cloud Run)

Deploys the existing `backend/Dockerfile` container to Cloud Run, **still pointing
at the Render Postgres** via the `DATABASE_URL` secret. This is the design doc's
deliberate, reversible stepping stone (§4 "Interim") — compute moves first, data
moves in Phase 2.

## How it deploys

The build/push/deploy is a **Cloud Build pipeline** (`deploy/gcp/cloudbuild.yaml`):
it builds `backend/Dockerfile`, pushes to Artifact Registry, and runs
`gcloud run deploy` with `env.production.yaml` + Secret Manager. Three ways to run it:

1. **GitHub Actions (recommended):** **Actions → Deploy to GCP → Run workflow**
   with `deploy_backend = true`. The job authenticates keylessly via WIF and
   calls `gcloud builds submit --config deploy/gcp/cloudbuild.yaml` — the heavy
   image build runs on Cloud Build, not the runner.
2. **Auto-deploy on merge (opt-in):** set the repo Actions Variable
   `GCP_AUTO_DEPLOY=true`. Then a push to `main` touching `backend/**` or
   `deploy/gcp/**` deploys the backend automatically. Leave it unset for
   manual-only (a push still triggers the workflow but the deploy job is skipped).
3. **Native Cloud Build trigger (alternative):**
   `create-cloud-build-trigger.sh` wires Cloud Build to watch GitHub directly
   (needs a one-time console repo connection). Use this OR the Actions path.

IAM for the Cloud Build service account is granted by
`deploy/gcp/phase0-foundation/25-cloud-build-iam.sh`.

### Manual submit (no CI)

```bash
gcloud builds submit --project="$GCP_PROJECT_ID" --region="$GCP_REGION" \
  --config=deploy/gcp/cloudbuild.yaml \
  --substitutions="SHORT_SHA=manual,_REGION=$GCP_REGION" .
```

## Why it works unchanged on Cloud Run

- **Port:** `render-startup.py` binds `0.0.0.0:$PORT`; Cloud Run injects `PORT`.
- **Health:** `/ready` (startup) and `/health` already exist in
  `backend/app/routers/health.py`.
- **DB:** `app/database.py` normalizes `postgres://`→`postgresql://` and only
  needs `DATABASE_URL`; no Cloud SQL connector until Phase 2.
- **Statelessness:** WebSockets/in-memory registry were removed in PR #312
  (Phase 0.5, D7), so instances are interchangeable — no `max-instances=1`.

## Manual deploy (fallback, no CI)

```bash
source deploy/gcp/config.env
IMAGE="${GCP_REGION}-docker.pkg.dev/${GCP_PROJECT_ID}/${AR_REPO}/${RUN_SERVICE}"

gcloud auth configure-docker "${GCP_REGION}-docker.pkg.dev"
docker build -f backend/Dockerfile -t "${IMAGE}:manual" backend
docker push "${IMAGE}:manual"

gcloud run deploy "${RUN_SERVICE}" \
  --project="${GCP_PROJECT_ID}" --region="${GCP_REGION}" \
  --image="${IMAGE}:manual" \
  --service-account="${RUNTIME_SA_NAME}@${GCP_PROJECT_ID}.iam.gserviceaccount.com" \
  --allow-unauthenticated \
  --env-vars-file=deploy/gcp/phase1-cloud-run/env.production.yaml \
  --set-secrets="DATABASE_URL=DATABASE_URL:latest,GHIN_API_USER=GHIN_API_USER:latest,GHIN_API_PASS=GHIN_API_PASS:latest,RESEND_API_KEY=RESEND_API_KEY:latest,BOOKING_SERVICE_SECRET=BOOKING_SERVICE_SECRET:latest,FORETEES_USERNAME=FORETEES_USERNAME:latest,FORETEES_PASSWORD=FORETEES_PASSWORD:latest,FORETEES_ENCRYPTION_KEY=FORETEES_ENCRYPTION_KEY:latest,MONITOR_KEY=MONITOR_KEY:latest"
```

## After the first deploy

1. Grab the service URL: `gcloud run services describe wolf-goat-pig-api --region us-central1 --format='value(status.url)'`.
2. Set `BACKEND_URL` in `env.production.yaml` to that URL and redeploy.
3. Smoke test (mirrors CLAUDE.md's definition of done):
   ```bash
   curl "$URL/health"                              # environment must be production
   curl -s -o /dev/null -w '%{http_code}' \
     -H 'Authorization: Bearer junk' "$URL/players/me"   # must be 401, not 500
   ```

## Rollback

Cloud Run keeps every revision. Roll back instantly:

```bash
gcloud run services update-traffic wolf-goat-pig-api \
  --region us-central1 --to-revisions=PREVIOUS_REVISION=100
```

Render stays live and authoritative throughout Phase 1 — the canary Cloud Run URL
is additive, so "rollback" can also just mean "keep using Render."

# Wolf Goat Pig on Google Cloud

Infrastructure-as-code for the migration designed in
[`docs/architecture/FIREBASE_MIGRATION_DESIGN.md`](../../docs/architecture/FIREBASE_MIGRATION_DESIGN.md).

**Live project:** `seventh-country-232522` (`us-central1`)

## Current status

| Phase | Status |
|---|---|
| 0 Foundation | Done — APIs, Artifact Registry, SAs, WIF, Secret Manager |
| 1 Cloud Run | Live — `wolf-goat-pig-api` |
| 2 Cloud SQL | Live — `wgp-postgres` (Enterprise `db-f1-micro`, Postgres 17) |
| 3 Firebase Hosting | Canary live — https://seventh-country-232522.web.app |
| 4 Cloud Scheduler | Live — 6 jobs → `/internal/jobs/*` |
| 5 Decommission | Checklist ready — keep Vercel/Render until soak ([DECOMMISSION.md](DECOMMISSION.md)) |

**Cloud Run URL:** https://wolf-goat-pig-api-i5v2shrpoa-uc.a.run.app  
**Firebase canary:** https://seventh-country-232522.web.app  

Cloud SQL is intentionally **cheap**: Enterprise edition + `db-f1-micro` (not Enterprise Plus).

Auth stays on **Auth0** throughout (design decision D4). Add Firebase URLs per [phase3-hosting/AUTH0_CUTOVER.md](phase3-hosting/AUTH0_CUTOVER.md).

## Target architecture

```
Auth0 (unchanged) → JWT
Firebase Hosting (SPA)  →  Cloud Run (FastAPI container, as-is)  →  Cloud SQL (Postgres)
                                     │                                Secret Manager
Cloud Scheduler → Cloud Run jobs     └→ Cloud Storage (future: scorecard images)
```

## Layout

| Path | Phase | What |
|---|---|---|
| `config.env.example` | — | Copy to `config.env` (gitignored); single source of config. |
| `lib/common.sh` | — | Shared shell helpers (config load, derived names, logging). |
| `phase0-foundation/` | 0 | Enable APIs, Artifact Registry, service accounts, WIF, Secret Manager. |
| `cloudbuild.yaml` | 1 | Cloud Build pipeline: build → push → deploy to Cloud Run. |
| `phase1-cloud-run/` | 1 | Cloud Run env file, deploy notes. |
| `phase2-cloud-sql/` | 2 | Provision Cloud SQL + Postgres migration runbook. |
| `phase3-hosting/` | 3 | Firebase Hosting config (`firebase.json`). |
| `phase4-scheduling/` | 4 | Cloud Scheduler → Cloud Run jobs. |
| `secrets.md` | — | Secret Manager ↔ render.yaml mapping. |
| `DECOMMISSION.md` | 5 | Render/Vercel cutover checklist. |
| `../../.github/workflows/deploy-gcp.yml` | 1, 3 | GitHub Actions → Cloud Build (keyless WIF). |

## Prerequisites

- `gcloud` CLI, authenticated as project owner on `seventh-country-232522`.
- Billing enabled.
- GitHub Actions variables set (see below).

```bash
cp deploy/gcp/config.env.example deploy/gcp/config.env
source deploy/gcp/config.env
```

## Order of operations

```bash
# Phase 0 — foundation (one-time)
./deploy/gcp/phase0-foundation/00-enable-apis.sh
./deploy/gcp/phase0-foundation/10-artifact-registry.sh
./deploy/gcp/phase0-foundation/20-service-accounts.sh
./deploy/gcp/phase0-foundation/25-cloud-build-iam.sh
./deploy/gcp/phase0-foundation/30-workload-identity-federation.sh
./deploy/gcp/phase0-foundation/40-secrets.sh

# Phase 1 — compute
# Actions → Deploy to GCP → deploy_backend=true
# Or: GCP_AUTO_DEPLOY=true for push-to-main

# Phase 3 — hosting
# Set VITE_API_URL, then Actions → deploy_frontend=true

# Phase 2 — database
./deploy/gcp/phase2-cloud-sql/10-provision.sh
# follow deploy/gcp/phase2-cloud-sql/migration-runbook.md

# Phase 4 — scheduling
export INTERNAL_JOB_TOKEN="$(gcloud secrets versions access latest --secret=INTERNAL_JOB_TOKEN)"
./deploy/gcp/phase4-scheduling/10-create-scheduler-jobs.sh
```

## GitHub Actions variables

| Variable | Value |
|---|---|
| `GCP_PROJECT_ID` | `seventh-country-232522` |
| `GCP_REGION` | `us-central1` |
| `GCP_WORKLOAD_IDENTITY_PROVIDER` | `projects/713531282314/locations/global/workloadIdentityPools/github-pool/providers/github-provider` |
| `GCP_DEPLOYER_SA` | `wgp-deployer@seventh-country-232522.iam.gserviceaccount.com` |
| `GCP_AUTO_DEPLOY` | `true` (optional) |
| `VITE_API_URL` | Cloud Run service URL |
| `FIREBASE_SITE` | `seventh-country-232522` (optional) |

## Safety notes

- Phase 1 keeps Render Postgres authoritative until Phase 2 cutover.
- Legacy tee sheet stays disconnected by default (`LEGACY_TEE_SHEET_ENABLED` unset).
- Every script is idempotent and re-runnable.

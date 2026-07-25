# Wolf Goat Pig on Google Cloud — deployment scaffolding

Infrastructure-as-code for the migration designed in
[`docs/architecture/FIREBASE_MIGRATION_DESIGN.md`](../../docs/architecture/FIREBASE_MIGRATION_DESIGN.md).
Target project: **`stuartgano-n8n`**, region **`us-central1`**.

> **Scope & status.** This is *scaffolding*: reviewable scripts, a CI deploy
> workflow, and runbooks. Nothing here has been applied to the live project.
> Each phase is independently shippable and reversible, matching the design doc's
> phased plan. Auth stays on **Auth0** throughout (design decision D4) — no auth
> migration here.

## Target architecture (recap)

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
| `phase0-foundation/` | 0 | Enable APIs, Artifact Registry, service accounts, Workload Identity Federation, Secret Manager. |
| `phase1-cloud-run/` | 1 | Cloud Run env file + deploy notes (deploy runs via GitHub Actions). |
| `phase2-cloud-sql/` | 2 | Provision Cloud SQL + Postgres migration runbook. |
| `phase3-hosting/` | 3 | Firebase Hosting config (`firebase.json`, `.firebaserc`). |
| `phase4-scheduling/` | 4 | Cloud Scheduler → Cloud Run jobs. |
| `secrets.md` | — | Secret Manager ↔ render.yaml mapping. |
| `../../.github/workflows/deploy-gcp.yml` | 1, 3 | Manual (`workflow_dispatch`) build+deploy, keyless via WIF. |

Phase **0.5** (remove WebSockets → stateless HTTP, design D7) already shipped in
**PR #312**, so the app is already Cloud-Run-ready (interchangeable instances).

## Prerequisites

- `gcloud` CLI, authenticated as a project owner/editor of `stuartgano-n8n`.
- `docker` (for the manual backend build path; CI has its own).
- `firebase-tools` (Phase 3 manual path; CI installs it).
- Billing enabled on the project (Cloud Run, Cloud SQL, Artifact Registry bill).

```bash
cp deploy/gcp/config.env.example deploy/gcp/config.env
# review values, then:
source deploy/gcp/config.env
```

## Order of operations

```bash
# ── Phase 0 — foundation (one-time) ──────────────────────────────────────────
./deploy/gcp/phase0-foundation/00-enable-apis.sh
./deploy/gcp/phase0-foundation/10-artifact-registry.sh
./deploy/gcp/phase0-foundation/20-service-accounts.sh
./deploy/gcp/phase0-foundation/30-workload-identity-federation.sh   # prints repo vars to set
./deploy/gcp/phase0-foundation/40-secrets.sh                        # then populate values (secrets.md)

# ── Phase 1 — compute ────────────────────────────────────────────────────────
# Set the printed GitHub Actions Variables, then run the workflow:
#   Actions → "Deploy to GCP" → deploy_backend = true
# (manual fallback: deploy/gcp/phase1-cloud-run/README.md)

# ── Phase 2 — database ───────────────────────────────────────────────────────
./deploy/gcp/phase2-cloud-sql/10-provision.sh
# then follow deploy/gcp/phase2-cloud-sql/migration-runbook.md

# ── Phase 3 — hosting ────────────────────────────────────────────────────────
#   Actions → "Deploy to GCP" → deploy_frontend = true
# (see deploy/gcp/phase3-hosting/README.md for API-connectivity options)

# ── Phase 4 — scheduling (needs an app code change first) ────────────────────
./deploy/gcp/phase4-scheduling/10-create-scheduler-jobs.sh
```

## What CI needs (set once, from `30-workload-identity-federation.sh` output)

GitHub → Settings → Secrets and variables → Actions → **Variables**:

| Variable | Example |
|---|---|
| `GCP_PROJECT_ID` | `stuartgano-n8n` |
| `GCP_REGION` | `us-central1` |
| `GCP_WORKLOAD_IDENTITY_PROVIDER` | `projects/NNN/locations/global/workloadIdentityPools/github-pool/providers/github-provider` |
| `GCP_DEPLOYER_SA` | `wgp-deployer@stuartgano-n8n.iam.gserviceaccount.com` |
| `VITE_API_URL` (Phase 3) | the Cloud Run service URL |
| `FIREBASE_SITE` (Phase 3, optional) | `stuartgano-n8n` |

No service-account JSON key is ever created or stored — auth is keyless OIDC.

## Safety notes

- The deploy workflow is **manual only** (`workflow_dispatch`); it never fires on
  push, so it can't surprise-deploy to the live GCP project.
- Phase 1 keeps **Render authoritative** — Cloud Run points at Render Postgres and
  the Cloud Run URL is additive. Rollback = keep using Render.
- The legacy tee sheet stays **disconnected** by default (`LEGACY_TEE_SHEET_ENABLED`
  unset, #313), so no live tee-sheet writes occur even under `ENVIRONMENT=production`.
- Every script is idempotent and re-runnable.

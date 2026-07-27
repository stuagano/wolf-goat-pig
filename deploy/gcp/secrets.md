# Secret Manager mapping

Every value Render kept as `sync: false` (dashboard-managed, never committed)
becomes a Secret Manager secret. `phase0-foundation/40-secrets.sh` creates the
containers and grants the runtime SA `secretAccessor`; the Cloud Run deploy wires
them in with `--set-secrets`.

| Secret name | From render.yaml | Notes |
|---|---|---|
| `DATABASE_URL` | `DATABASE_URL` | Phase 1: the Render Postgres URL. Phase 2: the Cloud SQL URL. Use the `postgresql://` scheme (not `+psycopg2`). |
| `GHIN_API_USER` | `GHIN_API_USER` | GHIN handicap lookups. |
| `GHIN_API_PASS` | `GHIN_API_PASS` | |
| `RESEND_API_KEY` | `RESEND_API_KEY` | Email delivery (Resend). |
| `BOOKING_SERVICE_SECRET` | `BOOKING_SERVICE_SECRET` | Shared secret with the ForeTees booking microservice. |
| `FORETEES_ENCRYPTION_KEY` | `FORETEES_ENCRYPTION_KEY` | Fernet key for per-user ForeTees creds — **losing/rotating it breaks stored creds**. |
| `INTERNAL_JOB_TOKEN` | — (new) | Phase 4: shared secret guarding `POST /internal/jobs/*`. Cloud Scheduler sends it as the `X-Internal-Job-Token` header. Endpoints are **disabled** (503) when unset. Generate with `openssl rand -hex 32`. |
| `CLOUD_SQL_PASSWORD` | — (new) | Phase 2 only: the Cloud SQL `wgp` user password. Not injected into the app; used by provisioning + to build `DATABASE_URL`. |

## Intentionally **not** wired on GCP

| Secret | Why dropped |
|---|---|
| `MONITOR_KEY` | Optional. Leave unset on GCP — uptime is Cloud Monitoring (phase6). Endpoint stays open/fail-open when unset (dev-safe). |
| `FORETEES_USERNAME` / `FORETEES_PASSWORD` | Direct ForeTees login/health probe only. Booking still works via `BOOKING_SERVICE_*`. Without these, ForeTees health reports `not_configured`. |

## What is **not** a secret (stays in `env.production.yaml`)

The Auth0 domain/client-id/audience, `GHIN_API_STATIC_TOKEN` (`"ghincom"`), and
the various `LEGACY_SIGNUP_*` / URL / tuning values. These mirror the plain
(non-`sync:false`) entries in render.yaml. **Sentry DSNs were removed** —
observability is Cloud Monitoring + Cloud Logging only.

## Populate a secret value

```bash
printf '%s' 'THE-VALUE' | \
  gcloud --project=seventh-country-232522 secrets versions add DATABASE_URL --data-file=-
```

Or seed everything at once from a local env (values already exported):

```bash
DATABASE_URL=... RESEND_API_KEY=... ./phase0-foundation/40-secrets.sh --from-env
```

Cloud Run reads `:latest`, so adding a new version + redeploy rotates a secret.
Never `echo` a secret into shell history or commit it — `config.env` is gitignored
and holds only non-secret names.

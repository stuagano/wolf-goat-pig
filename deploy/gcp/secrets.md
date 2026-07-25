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
| `FORETEES_USERNAME` | `FORETEES_USERNAME` | |
| `FORETEES_PASSWORD` | `FORETEES_PASSWORD` | |
| `FORETEES_ENCRYPTION_KEY` | `FORETEES_ENCRYPTION_KEY` | Fernet key for per-user ForeTees creds — **losing/rotating it breaks stored creds**. |
| `MONITOR_KEY` | `MONITOR_KEY` | Guards `GET /health/external`. |
| `CLOUD_SQL_PASSWORD` | — (new) | Phase 2 only: the Cloud SQL `wgp` user password. Not injected into the app; used by provisioning + to build `DATABASE_URL`. |

## What is **not** a secret (stays in `env.production.yaml`)

`SENTRY_DSN` (public by design — also ships in the browser bundle),
`GHIN_API_STATIC_TOKEN` (`"ghincom"`), the Auth0 domain/client-id/audience, and
the various `LEGACY_SIGNUP_*` / URL / tuning values. These mirror the plain
(non-`sync:false`) entries in render.yaml.

## Populate a secret value

```bash
printf '%s' 'THE-VALUE' | \
  gcloud --project=stuartgano-n8n secrets versions add DATABASE_URL --data-file=-
```

Or seed everything at once from a local env (values already exported):

```bash
DATABASE_URL=... RESEND_API_KEY=... ./phase0-foundation/40-secrets.sh --from-env
```

Cloud Run reads `:latest`, so adding a new version + redeploy rotates a secret.
Never `echo` a secret into shell history or commit it — `config.env` is gitignored
and holds only non-secret names.

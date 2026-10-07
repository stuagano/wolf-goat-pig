# Secret Manager mapping

`phase0-foundation/40-secrets.sh` creates the secret containers and grants the
runtime service account `secretAccessor`; the Cloud Run deploy wires them in
with `--set-secrets`.

| Secret name | Purpose |
|---|---|
| `DATABASE_URL` | Cloud SQL connection URL. Use the `postgresql://` scheme (not `+psycopg2`). |
| `GHIN_API_USER` | GHIN handicap lookups. |
| `GHIN_API_PASS` | GHIN authentication. |
| `RESEND_API_KEY` | Email delivery (Resend). |
| `BOOKING_SERVICE_SECRET` | Shared secret between the API and booking agent (also used for scorecard agent auth). |
| `FORETEES_ENCRYPTION_KEY` | Fernet key for per-user ForeTees creds — **losing/rotating it breaks stored creds**. |
| `INTERNAL_JOB_TOKEN` | Guards `POST /internal/jobs/*`; Cloud Scheduler sends it as `X-Internal-Job-Token`. Endpoints are disabled (503) when unset. |
| `WGP_FEEDBACK_GITHUB_TOKEN` | Server-only `stuagano` token for `POST /feedback`, creating issues in `stuagano/wolf-goat-pig`. Prefer a fine-grained token restricted to this repository with **Issues: read and write**. |
| `CLOUD_SQL_PASSWORD` | Provisioning-only Cloud SQL `wgp` user password; not injected into the app. |

## Intentionally **not** wired on GCP

| Secret | Why dropped |
|---|---|
| `MONITOR_KEY` | Optional. Leave unset on GCP — uptime is Cloud Monitoring (phase6). Endpoint stays open/fail-open when unset (dev-safe). |
| `FORETEES_USERNAME` / `FORETEES_PASSWORD` | Direct ForeTees login/health probe only. Booking still works via `BOOKING_SERVICE_*`. Without these, ForeTees health reports `not_configured`. |

## What is **not** a secret (stays in `env.production.yaml`)

The Auth0 domain/client-id/audience, `GHIN_API_STATIC_TOKEN` (`"ghincom"`), and
the various `LEGACY_SIGNUP_*` / URL / tuning values live in
`phase1-cloud-run/env.production.yaml`. **Sentry DSNs were removed** —
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

## Feedback issue submission

The app's **More → Feedback** form requires the existing Auth0 login. It posts
only the chosen type, title, description, and optional bug reproduction steps to
this public repository; it does not copy account details or browser context.
The GitHub token belongs only in the API environment, never a `VITE_*` variable.
See [GitHub's issue-creation permissions](https://docs.github.com/en/rest/issues/issues#create-an-issue).

Before deploying the feedback route, create/populate `WGP_FEEDBACK_GITHUB_TOKEN`
and grant `wgp-run` access using the setup script above. The backend Cloud Build
config injects it on deployment. Without a token, the route returns 503.
For local development, export the same variable in the backend process only.

To seed from the locally authenticated `stuagano` account without printing the
credential, first verify the account through `gh-as.sh stuagano api user --jq .login`,
then stream its token directly to Secret Manager:

```bash
set -o pipefail
env -u GH_TOKEN -u GITHUB_TOKEN gh auth token --hostname github.com --user stuagano | \
  gcloud --project=seventh-country-232522 secrets versions add WGP_FEEDBACK_GITHUB_TOKEN --data-file=-
```

The one-minute per-player cooldown uses the existing in-memory rate limiter and
applies per worker, so multiple instances or a restart can allow extra submissions.
Delivery is attempted once. On a timeout, check the issue list before retrying:
GitHub may have created the issue even when its response did not arrive.

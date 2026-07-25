# Phase 4 — Scheduling (Cloud Scheduler → Cloud Run)

Design doc §9 (Phase 4). Today the backend runs periodic work inside the process
via the `schedule` library (`app/services/email_scheduler.py`,
`pairing_scheduler_service.py`, plus callout/matchmaking/sheet-sync loops). That
assumes one long-lived process — which is exactly the assumption Cloud Run
autoscaling breaks (every instance would run its own copy of every loop).

**Target:** move each loop to an HTTP endpoint that **Cloud Scheduler** POSTs to
on a cron. Because the Cloud Run service is `--allow-unauthenticated`, the
endpoints are guarded at the app layer by the `INTERNAL_JOB_TOKEN` shared secret
(sent as the `X-Internal-Job-Token` header); an OIDC token for `wgp-scheduler` is
also attached for when the service is later locked down.

## Status — app code has landed

Both halves are now in place:

1. **App code (done).** `app/routers/internal_jobs.py` exposes
   `POST /internal/jobs/{job}` for each key in `EmailScheduler.JOB_METHODS`, each
   running one cycle of the matching in-process job. The endpoints are
   **fail-closed**: disabled (503) unless `INTERNAL_JOB_TOKEN` is set. Setting
   `RUN_INPROCESS_SCHEDULERS=false` (already in `env.production.yaml`) stops the
   in-process `schedule` thread so Cloud Scheduler owns the cadence.
2. **Infra (this script).** `10-create-scheduler-jobs.sh` creates one Cloud
   Scheduler job per endpoint (cadences mirror the in-process schedule), attaches
   the token header, and grants the scheduler SA `run.invoker`.

### Jobs / endpoints

| Scheduler job | Cron (UTC) | Endpoint |
|---|---|---|
| `wgp-daily-reminders` | `0 9 * * *` | `/internal/jobs/daily-reminders` |
| `wgp-weekly-summaries` | `0 9 * * 0` | `/internal/jobs/weekly-summaries` |
| `wgp-saturday-pairings` | `0 14 * * 6` | `/internal/jobs/saturday-pairings` |
| `wgp-legacy-rounds-sync` | `0 */2 * * *` | `/internal/jobs/legacy-rounds-sync` |
| `wgp-pending-sheet-syncs` | `0 0 * * *` | `/internal/jobs/pending-sheet-syncs` |
| `wgp-ghin-sync` | `0 6 * * *` | `/internal/jobs/ghin-sync` |

Export `INTERNAL_JOB_TOKEN` (same value as the secret) before running the script;
set `SCHEDULER_TIME_ZONE` if the schedules were meant for club-local time.

## Idempotency (doc §12)

The in-process `schedule` loop is effectively at-most-once. Cloud Scheduler is
**at-least-once** — a job can fire twice. Every `/internal/jobs/*` handler must be
safe to run twice in a row (e.g. the email jobs already gate on
`*_email_sent_at` columns; preserve that discipline for pairing/callouts/sync).

## Verify

```bash
gcloud scheduler jobs list --location us-central1
gcloud scheduler jobs run wgp-email-digest --location us-central1   # manual fire
```

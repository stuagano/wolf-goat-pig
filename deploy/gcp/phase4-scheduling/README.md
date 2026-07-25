# Phase 4 — Scheduling (Cloud Scheduler → Cloud Run)

Design doc §9 (Phase 4). Today the backend runs periodic work inside the process
via the `schedule` library (`app/services/email_scheduler.py`,
`pairing_scheduler_service.py`, plus callout/matchmaking/sheet-sync loops). That
assumes one long-lived process — which is exactly the assumption Cloud Run
autoscaling breaks (every instance would run its own copy of every loop).

**Target:** move each loop to a private HTTP endpoint that **Cloud Scheduler**
POSTs to on a cron, authenticated with an OIDC token for the `wgp-scheduler`
service account.

## Two-part change

1. **App code (out of scope for this infra PR).** Extract each in-process loop
   into an idempotent endpoint under `/internal/jobs/*` and stop starting the
   `schedule` thread when running on Cloud Run. This is the real work and needs
   its own PR.
2. **Infra (this script).** `10-create-scheduler-jobs.sh` creates the Cloud
   Scheduler jobs and grants the scheduler SA `run.invoker`. Run it **after** the
   endpoints exist; comment out any job whose endpoint isn't implemented yet.

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

#!/usr/bin/env bash
# Phase 4 — replace in-process `schedule` loops with Cloud Scheduler → Cloud Run.
# Design doc §9 (Phase 4) / §12 (audit idempotency).
#
# Cloud Scheduler POSTs to authenticated Cloud Run endpoints on a cron. Each job
# authenticates with an OIDC token minted for the scheduler SA, so the endpoints
# stay private (no public trigger surface).
#
# ⚠️  SCAFFOLDING: the trigger endpoints below (/internal/jobs/*) do NOT exist in
#     the app yet. Extracting each in-process scheduler
#     (app/services/email_scheduler.py, pairing_scheduler_service.py, and the
#     callout/matchmaking/sheet-sync loops) into an idempotent HTTP-invoked
#     endpoint is an app code change that must land BEFORE these jobs will do
#     anything. This script creates the jobs so the infra is ready; comment out
#     any job whose endpoint isn't implemented yet.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../lib/common.sh
source "${SCRIPT_DIR}/../lib/common.sh"

require_cmd gcloud
require_config RUN_SERVICE GCP_REGION

RUN_URL="$(gc run services describe "${RUN_SERVICE}" --region="${GCP_REGION}" \
  --format='value(status.url)' 2>/dev/null || true)"
[[ -n "${RUN_URL}" ]] || die "Cloud Run service '${RUN_SERVICE}' not found — deploy Phase 1 first."

# The endpoints are guarded by the INTERNAL_JOB_TOKEN shared secret (the service
# is --allow-unauthenticated). Scheduler sends it as a static header. Must match
# the INTERNAL_JOB_TOKEN secret value the Cloud Run service reads.
[[ -n "${INTERNAL_JOB_TOKEN:-}" ]] || die "export INTERNAL_JOB_TOKEN (same value as the Secret Manager secret) before running."

# In-process clock times are UTC on Render; keep parity. Change if the schedules
# were meant for club-local (Pacific) time.
TIME_ZONE="${SCHEDULER_TIME_ZONE:-Etc/UTC}"

# Let the scheduler SA invoke the Cloud Run service (belt-and-suspenders alongside
# the shared-secret header; harmless while the service is public).
log "Granting ${SCHEDULER_SA} roles/run.invoker on ${RUN_SERVICE}…"
gc run services add-iam-policy-binding "${RUN_SERVICE}" --region="${GCP_REGION}" \
  --member="serviceAccount:${SCHEDULER_SA}" --role=roles/run.invoker >/dev/null

# job name | cron | endpoint job-key (see EmailScheduler.JOB_METHODS)
# Cadences mirror the in-process schedule in app/services/email_scheduler.py.
JOBS=(
  "wgp-daily-reminders|0 9 * * *|daily-reminders"
  "wgp-weekly-summaries|0 9 * * 0|weekly-summaries"
  "wgp-saturday-pairings|0 14 * * 6|saturday-pairings"
  "wgp-legacy-rounds-sync|0 */2 * * *|legacy-rounds-sync"
  "wgp-pending-sheet-syncs|0 0 * * *|pending-sheet-syncs"
  "wgp-ghin-sync|0 6 * * *|ghin-sync"
)

for entry in "${JOBS[@]}"; do
  IFS='|' read -r name cron key <<<"${entry}"
  uri="${RUN_URL}/internal/jobs/${key}"
  if gc scheduler jobs describe "${name}" --location="${GCP_REGION}" >/dev/null 2>&1; then
    log "Updating scheduler job ${name} (${cron} ${TIME_ZONE})…"
    gc scheduler jobs update http "${name}" --location="${GCP_REGION}" \
      --schedule="${cron}" --time-zone="${TIME_ZONE}" --uri="${uri}" --http-method=POST \
      --update-headers="X-Internal-Job-Token=${INTERNAL_JOB_TOKEN}" \
      --oidc-service-account-email="${SCHEDULER_SA}" --oidc-token-audience="${RUN_URL}"
  else
    log "Creating scheduler job ${name} (${cron} ${TIME_ZONE})…"
    gc scheduler jobs create http "${name}" --location="${GCP_REGION}" \
      --schedule="${cron}" --time-zone="${TIME_ZONE}" --uri="${uri}" --http-method=POST \
      --headers="X-Internal-Job-Token=${INTERNAL_JOB_TOKEN}" \
      --oidc-service-account-email="${SCHEDULER_SA}" --oidc-token-audience="${RUN_URL}"
  fi
done

ok "Scheduler jobs configured against ${RUN_URL}."
warn "Set RUN_INPROCESS_SCHEDULERS=false on the Cloud Run service (env.production.yaml"
warn "already does) so the in-process thread doesn't double-run these jobs."
warn "Cloud Scheduler is at-least-once — each /internal/jobs/* target must stay"
warn "idempotent (doc §12)."

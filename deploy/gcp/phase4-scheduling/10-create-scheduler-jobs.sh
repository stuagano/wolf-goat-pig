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

# Let the scheduler SA invoke the Cloud Run service.
log "Granting ${SCHEDULER_SA} roles/run.invoker on ${RUN_SERVICE}…"
gc run services add-iam-policy-binding "${RUN_SERVICE}" --region="${GCP_REGION}" \
  --member="serviceAccount:${SCHEDULER_SA}" --role=roles/run.invoker >/dev/null

# job name | cron (UTC) | endpoint path
# Adjust cadence to match the current in-process schedules before enabling.
JOBS=(
  "wgp-email-digest|*/15 * * * *|/internal/jobs/email-digest"
  "wgp-pairing|0 * * * *|/internal/jobs/pairing"
  "wgp-callouts|*/10 * * * *|/internal/jobs/callouts"
  "wgp-sheet-sync|*/30 * * * *|/internal/jobs/sheet-sync"
)

for entry in "${JOBS[@]}"; do
  IFS='|' read -r name cron path <<<"${entry}"
  uri="${RUN_URL}${path}"
  if gc scheduler jobs describe "${name}" --location="${GCP_REGION}" >/dev/null 2>&1; then
    log "Updating scheduler job ${name} (${cron})…"
    gc scheduler jobs update http "${name}" --location="${GCP_REGION}" \
      --schedule="${cron}" --uri="${uri}" --http-method=POST \
      --oidc-service-account-email="${SCHEDULER_SA}" --oidc-token-audience="${RUN_URL}"
  else
    log "Creating scheduler job ${name} (${cron})…"
    gc scheduler jobs create http "${name}" --location="${GCP_REGION}" \
      --schedule="${cron}" --uri="${uri}" --http-method=POST \
      --oidc-service-account-email="${SCHEDULER_SA}" --oidc-token-audience="${RUN_URL}"
  fi
done

ok "Scheduler jobs configured against ${RUN_URL}."
warn "These fire immediately on schedule. Ensure each /internal/jobs/* endpoint"
warn "exists and is IDEMPOTENT before enabling — Cloud Scheduler is at-least-once,"
warn "unlike the previous single-process at-most-once loop (doc §12)."

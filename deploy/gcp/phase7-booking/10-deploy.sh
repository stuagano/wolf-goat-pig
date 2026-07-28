#!/usr/bin/env bash
# Phase 7 — build + deploy the Computer Use booking agent to Cloud Run.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../lib/common.sh
source "${SCRIPT_DIR}/../lib/common.sh"

require_config GCP_PROJECT_ID GCP_REGION RUNTIME_SA_NAME

REPO_ROOT="$(cd "${GCP_DIR}/../.." && pwd)"
SERVICE="${BOOKING_RUN_SERVICE:-wgp-booking}"
AR_REPO="${AR_REPO:-wolf-goat-pig}"
IMAGE="${GCP_REGION}-docker.pkg.dev/${GCP_PROJECT_ID}/${AR_REPO}/${SERVICE}:$(git -C "${REPO_ROOT}" rev-parse --short HEAD)"
RUNTIME_SA="${RUNTIME_SA_NAME}@${GCP_PROJECT_ID}.iam.gserviceaccount.com"

log "Ensuring Vertex AI API…"
gc services enable aiplatform.googleapis.com --project="${GCP_PROJECT_ID}" >/dev/null

log "Granting aiplatform.user to ${RUNTIME_SA}…"
gc projects add-iam-policy-binding "${GCP_PROJECT_ID}" \
  --member="serviceAccount:${RUNTIME_SA}" \
  --role="roles/aiplatform.user" \
  --condition=None >/dev/null || true

log "Building ${IMAGE}…"
gc builds submit \
  --project="${GCP_PROJECT_ID}" \
  --region="${GCP_REGION}" \
  --tag="${IMAGE}" \
  "${REPO_ROOT}/booking-agent"

log "Deploying Cloud Run service ${SERVICE}…"
gc run deploy "${SERVICE}" \
  --project="${GCP_PROJECT_ID}" \
  --region="${GCP_REGION}" \
  --image="${IMAGE}" \
  --service-account="${RUNTIME_SA}" \
  --allow-unauthenticated \
  --session-affinity \
  --min-instances=0 \
  --max-instances=2 \
  --cpu=2 \
  --memory=2Gi \
  --timeout=300 \
  --concurrency=1 \
  --port=8080 \
  --set-env-vars="GCP_PROJECT_ID=${GCP_PROJECT_ID},GCP_LOCATION=global,COMPUTER_USE_MODEL=gemini-3.5-flash,HEADLESS=true" \
  --set-secrets="BOOKING_SERVICE_SECRET=BOOKING_SERVICE_SECRET:latest"

URL="$(gc run services describe "${SERVICE}" --region="${GCP_REGION}" --format='value(status.url)')"
ok "Booking agent live at ${URL}"
warn "Set BOOKING_SERVICE_URL=${URL} on wolf-goat-pig-api and redeploy (or update env.production.yaml)."

#!/usr/bin/env bash
# Phase 8 — build + deploy the scorecard vision agent to Cloud Run.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../lib/common.sh
source "${SCRIPT_DIR}/../lib/common.sh"

require_config GCP_PROJECT_ID GCP_REGION RUNTIME_SA_NAME

REPO_ROOT="$(cd "${GCP_DIR}/../.." && pwd)"
SERVICE="${SCORECARD_RUN_SERVICE:-wgp-scorecard}"
RUNTIME_SA="${RUNTIME_SA_NAME}@${GCP_PROJECT_ID}.iam.gserviceaccount.com"

log "Ensuring Vertex AI API…"
gc services enable aiplatform.googleapis.com --project="${GCP_PROJECT_ID}" >/dev/null

log "Granting aiplatform.user to ${RUNTIME_SA}…"
gc projects add-iam-policy-binding "${GCP_PROJECT_ID}" \
  --member="serviceAccount:${RUNTIME_SA}" \
  --role="roles/aiplatform.user" \
  --condition=None >/dev/null || true

log "Building + deploying ${SERVICE} via Cloud Build…"
gc builds submit \
  --project="${GCP_PROJECT_ID}" \
  --region="${GCP_REGION}" \
  --config="${GCP_DIR}/cloudbuild-scorecard.yaml" \
  --substitutions="SHORT_SHA=$(git -C "${REPO_ROOT}" rev-parse --short HEAD),_REGION=${GCP_REGION}" \
  "${REPO_ROOT}"

URL="$(gc run services describe "${SERVICE}" --region="${GCP_REGION}" --format='value(status.url)')"
ok "Scorecard agent live at ${URL}"
warn "Set SCORECARD_SERVICE_URL=${URL} and SCORECARD_VISION_PROVIDER=agent on wolf-goat-pig-api."

#!/usr/bin/env bash
# Phase 0 — create the Artifact Registry Docker repo that holds backend images.
# Idempotent: skips creation if the repo already exists.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../lib/common.sh
source "${SCRIPT_DIR}/../lib/common.sh"

require_cmd gcloud
require_config AR_REPO GCP_REGION

if gc artifacts repositories describe "${AR_REPO}" --location="${GCP_REGION}" >/dev/null 2>&1; then
  ok "Artifact Registry repo '${AR_REPO}' already exists in ${GCP_REGION}."
else
  log "Creating Artifact Registry Docker repo '${AR_REPO}' in ${GCP_REGION}…"
  gc artifacts repositories create "${AR_REPO}" \
    --repository-format=docker \
    --location="${GCP_REGION}" \
    --description="Wolf Goat Pig backend container images"
  ok "Created ${AR_HOST}/${GCP_PROJECT_ID}/${AR_REPO}"
fi

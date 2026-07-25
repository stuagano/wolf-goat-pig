#!/usr/bin/env bash
# Phase 0 — enable the Google Cloud APIs the whole migration needs.
# Idempotent: enabling an already-enabled API is a no-op.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../lib/common.sh
source "${SCRIPT_DIR}/../lib/common.sh"

require_cmd gcloud

APIS=(
  run.googleapis.com                # Cloud Run (Phase 1)
  cloudbuild.googleapis.com         # Cloud Build pipeline (Phase 1)
  artifactregistry.googleapis.com   # container images (Phase 1)
  secretmanager.googleapis.com      # secrets (Phase 0)
  sqladmin.googleapis.com           # Cloud SQL (Phase 2)
  firebasehosting.googleapis.com    # Firebase Hosting (Phase 3)
  cloudscheduler.googleapis.com     # Cloud Scheduler (Phase 4)
  iamcredentials.googleapis.com     # Workload Identity Federation
  sts.googleapis.com                # Workload Identity Federation
  iam.googleapis.com                # service accounts / IAM
  logging.googleapis.com            # Cloud Logging
  monitoring.googleapis.com         # Cloud Monitoring
)

log "Enabling ${#APIS[@]} APIs on project ${GCP_PROJECT_ID} (this can take a minute)…"
gc services enable "${APIS[@]}"
ok "APIs enabled."

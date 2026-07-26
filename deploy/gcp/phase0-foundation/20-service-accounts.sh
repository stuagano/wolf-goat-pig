#!/usr/bin/env bash
# Phase 0 — create the three service accounts and grant least-privilege roles.
#
#   runtime   (wgp-run)       — the identity the Cloud Run service runs as.
#   deployer  (wgp-deployer)  — impersonated by GitHub Actions (via WIF) to deploy.
#   scheduler (wgp-scheduler) — Cloud Scheduler uses this to call Cloud Run (Phase 4).
#
# Idempotent: creating an existing SA / re-adding a binding is a no-op.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../lib/common.sh
source "${SCRIPT_DIR}/../lib/common.sh"

require_cmd gcloud

create_sa() {
  local name="$1" display="$2"
  local email="${name}@${GCP_PROJECT_ID}.iam.gserviceaccount.com"
  if gc iam service-accounts describe "${email}" >/dev/null 2>&1; then
    ok "service account ${email} exists"
  else
    log "Creating service account ${email}…"
    gc iam service-accounts create "${name}" --display-name="${display}"
  fi
}

grant() {
  # grant <member> <role>
  log "  binding $2 → $1"
  gc projects add-iam-policy-binding "${GCP_PROJECT_ID}" \
    --member="$1" --role="$2" --condition=None >/dev/null
}

create_sa "${RUNTIME_SA_NAME:-wgp-run}"       "WGP Cloud Run runtime"
create_sa "${DEPLOYER_SA_NAME:-wgp-deployer}" "WGP CI deployer (GitHub Actions)"
create_sa "${SCHEDULER_SA_NAME:-wgp-scheduler}" "WGP Cloud Scheduler caller"

log "Granting runtime SA roles…"
grant "serviceAccount:${RUNTIME_SA}" "roles/secretmanager.secretAccessor"  # read secrets
grant "serviceAccount:${RUNTIME_SA}" "roles/cloudsql.client"               # Phase 2 DB
grant "serviceAccount:${RUNTIME_SA}" "roles/logging.logWriter"             # structured logs

log "Granting deployer SA roles…"
grant "serviceAccount:${DEPLOYER_SA}" "roles/run.admin"                    # deploy Cloud Run
grant "serviceAccount:${DEPLOYER_SA}" "roles/artifactregistry.writer"      # push images
grant "serviceAccount:${DEPLOYER_SA}" "roles/cloudbuild.builds.editor"     # submit Cloud Build
grant "serviceAccount:${DEPLOYER_SA}" "roles/serviceusage.serviceUsageConsumer"  # gcloud builds submit
grant "serviceAccount:${DEPLOYER_SA}" "roles/storage.admin"               # upload to *_cloudbuild bucket
grant "serviceAccount:${DEPLOYER_SA}" "roles/secretmanager.viewer"         # validate --set-secrets refs
# deployer must be able to run the service *as* the runtime SA:
grant "serviceAccount:${DEPLOYER_SA}" "roles/iam.serviceAccountUser"

ok "Service accounts configured."
warn "Least privilege: roles/run.admin on the deployer is project-wide for"
warn "simplicity. Tighten to the single service with a conditional binding later."

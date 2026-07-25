#!/usr/bin/env bash
# Phase 0 — grant the Cloud Build service account the roles it needs to build the
# image, push it to Artifact Registry, and deploy to Cloud Run.
#
# Which SA runs a build differs by project age:
#   - legacy default : PROJECT_NUMBER@cloudbuild.gserviceaccount.com
#   - newer default  : PROJECT_NUMBER-compute@developer.gserviceaccount.com
# Rather than guess, this grants the roles to whichever of the two exists (both,
# if both do). Idempotent.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../lib/common.sh
source "${SCRIPT_DIR}/../lib/common.sh"

require_cmd gcloud

PROJECT_NUMBER="$(gc projects describe "${GCP_PROJECT_ID}" --format='value(projectNumber)')"

CANDIDATES=(
  "${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com"
  "${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"
)

ROLES=(
  roles/run.admin                    # deploy Cloud Run
  roles/artifactregistry.writer      # push images
  roles/iam.serviceAccountUser       # deploy the service AS the runtime SA
  roles/secretmanager.viewer         # validate --set-secrets references
  roles/logging.logWriter            # build logs (options.logging=CLOUD_LOGGING_ONLY)
)

granted_any=0
for sa in "${CANDIDATES[@]}"; do
  if gc iam service-accounts describe "${sa}" >/dev/null 2>&1; then
    granted_any=1
    log "Granting Cloud Build roles to ${sa}…"
    for role in "${ROLES[@]}"; do
      log "  ${role}"
      gc projects add-iam-policy-binding "${GCP_PROJECT_ID}" \
        --member="serviceAccount:${sa}" --role="${role}" --condition=None >/dev/null
    done
  else
    warn "build SA candidate not found (skipping): ${sa}"
  fi
done

[[ "${granted_any}" -eq 1 ]] || die "no Cloud Build service account found — run 00-enable-apis.sh first (cloudbuild.googleapis.com creates it)."

ok "Cloud Build service account(s) can now build, push, and deploy."
warn "roles/run.admin + project-level serviceAccountUser are broad for simplicity"
warn "(matches the deployer-SA note in 20-service-accounts.sh). Tighten later if desired."

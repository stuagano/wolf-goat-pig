#!/usr/bin/env bash
# Phase 1 (optional) — create a NATIVE Cloud Build trigger that watches GitHub
# directly, instead of driving Cloud Build from GitHub Actions.
#
# Use this only if you prefer Cloud Build to own CI/CD end-to-end. The GitHub
# Actions path (.github/workflows/deploy-gcp.yml) needs none of this — pick one.
#
# ⚠️  ONE-TIME MANUAL STEP FIRST: connect the repo to Cloud Build. The 2nd-gen
#     GitHub connection uses OAuth and cannot be fully scripted headlessly:
#       Console → Cloud Build → Repositories → 2nd gen → "Create host connection"
#       (installs the Cloud Build GitHub App), then "Link repository".
#     Then set CB_CONNECTION and CB_REMOTE_REPO below (or export them) and run.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../lib/common.sh
source "${SCRIPT_DIR}/../lib/common.sh"

require_cmd gcloud
require_config GITHUB_REPO GCP_REGION

# The 2nd-gen connection name and linked-repo resource created in the console step.
CB_CONNECTION="${CB_CONNECTION:-github}"
CB_REMOTE_REPO="${CB_REMOTE_REPO:-wolf-goat-pig}"
TRIGGER_NAME="${TRIGGER_NAME:-wgp-backend-main}"

REPO_RESOURCE="projects/${GCP_PROJECT_ID}/locations/${GCP_REGION}/connections/${CB_CONNECTION}/repositories/${CB_REMOTE_REPO}"

log "Creating Cloud Build trigger '${TRIGGER_NAME}' on push to main (${GITHUB_REPO})…"
warn "This deploys on every matching push to main. Comment out / delete the"
warn "trigger if you want manual-only deploys."

gc builds triggers create github \
  --name="${TRIGGER_NAME}" \
  --region="${GCP_REGION}" \
  --repository="${REPO_RESOURCE}" \
  --branch-pattern='^main$' \
  --included-files='backend/**;deploy/gcp/**' \
  --build-config='deploy/gcp/cloudbuild.yaml' \
  --substitutions="_REGION=${GCP_REGION}"

ok "Trigger created. It uses deploy/gcp/cloudbuild.yaml; \$SHORT_SHA is supplied"
ok "automatically by the trigger. Manage it under Cloud Build → Triggers."

#!/usr/bin/env bash
# Phase 0 — Workload Identity Federation so GitHub Actions can authenticate to
# GCP with NO long-lived service-account key (keyless OIDC). GitHub mints an OIDC
# token per run; GCP trusts it only for this exact repo and lets it impersonate
# the deployer SA.
#
# Idempotent: existing pool/provider/binding are left as-is.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../lib/common.sh
source "${SCRIPT_DIR}/../lib/common.sh"

require_cmd gcloud
require_config GITHUB_REPO WIF_POOL WIF_PROVIDER

PROJECT_NUMBER="$(gc projects describe "${GCP_PROJECT_ID}" --format='value(projectNumber)')"
POOL="${WIF_POOL}"
PROVIDER="${WIF_PROVIDER}"

# ── Pool ────────────────────────────────────────────────────────────────────
if gc iam workload-identity-pools describe "${POOL}" --location=global >/dev/null 2>&1; then
  ok "WIF pool '${POOL}' exists"
else
  log "Creating WIF pool '${POOL}'…"
  gc iam workload-identity-pools create "${POOL}" \
    --location=global --display-name="GitHub Actions"
fi

# ── OIDC provider (trusts GitHub's token issuer, scoped to this repo) ────────
if gc iam workload-identity-pools providers describe "${PROVIDER}" \
      --location=global --workload-identity-pool="${POOL}" >/dev/null 2>&1; then
  ok "WIF provider '${PROVIDER}' exists"
else
  log "Creating OIDC provider '${PROVIDER}' (scoped to ${GITHUB_REPO})…"
  gc iam workload-identity-pools providers create-oidc "${PROVIDER}" \
    --location=global \
    --workload-identity-pool="${POOL}" \
    --display-name="GitHub OIDC" \
    --issuer-uri="https://token.actions.githubusercontent.com" \
    --attribute-mapping="google.subject=assertion.sub,attribute.repository=assertion.repository,attribute.ref=assertion.ref" \
    --attribute-condition="assertion.repository=='${GITHUB_REPO}'"
fi

# ── Let tokens from this repo impersonate the deployer SA ────────────────────
MEMBER="principalSet://iam.googleapis.com/projects/${PROJECT_NUMBER}/locations/global/workloadIdentityPools/${POOL}/attribute.repository/${GITHUB_REPO}"
log "Binding ${GITHUB_REPO} → ${DEPLOYER_SA} (roles/iam.workloadIdentityUser)…"
gc iam service-accounts add-iam-policy-binding "${DEPLOYER_SA}" \
  --role=roles/iam.workloadIdentityUser \
  --member="${MEMBER}" >/dev/null

PROVIDER_RESOURCE="projects/${PROJECT_NUMBER}/locations/global/workloadIdentityPools/${POOL}/providers/${PROVIDER}"
ok "Workload Identity Federation configured."
echo
log "Set these in the GitHub repo (Settings → Secrets and variables → Actions → Variables):"
echo "    GCP_WORKLOAD_IDENTITY_PROVIDER = ${PROVIDER_RESOURCE}"
echo "    GCP_DEPLOYER_SA                = ${DEPLOYER_SA}"
echo "    GCP_PROJECT_ID                 = ${GCP_PROJECT_ID}"
echo "    GCP_REGION                     = ${GCP_REGION}"

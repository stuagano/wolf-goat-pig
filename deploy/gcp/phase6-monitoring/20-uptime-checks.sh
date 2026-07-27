#!/usr/bin/env bash
# Phase 6 — synthetic uptime checks for Firebase Hosting + Cloud Run /health.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../lib/common.sh
source "${SCRIPT_DIR}/../lib/common.sh"

require_cmd gcloud
require_config FIREBASE_SITE RUN_SERVICE GCP_REGION

RUN_URL="$(gc run services describe "${RUN_SERVICE}" --region="${GCP_REGION}" \
  --format='value(status.url)' 2>/dev/null || true)"
[[ -n "${RUN_URL}" ]] || die "Cloud Run service '${RUN_SERVICE}' not found."

API_HOST="${RUN_URL#https://}"
API_HOST="${API_HOST%%/*}"
HOSTING_HOST="${FIREBASE_SITE}.web.app"

# gcloud --period is minutes: 1 | 5 | 10 | 15 (not seconds).
PERIOD_MINUTES="${UPTIME_PERIOD_MINUTES:-5}"

# display_name | host | path
CHECKS=(
  "WGP API /health|${API_HOST}|/health"
  "WGP Firebase Hosting|${HOSTING_HOST}|/"
)

upsert_check() {
  local display="$1" host="$2" path="$3"
  local existing
  existing="$(gc monitoring uptime list-configs \
    --filter="displayName=\"${display}\"" \
    --format='value(name)' 2>/dev/null | head -1 || true)"

  if [[ -n "${existing}" ]]; then
    log "Uptime check already exists: ${display} (${existing})"
    echo "${existing}"
    return
  fi

  log "Creating uptime check ${display} → https://${host}${path} (every ${PERIOD_MINUTES}m)…"
  local name
  name="$(gc monitoring uptime create "${display}" \
    --resource-type=uptime-url \
    --resource-labels="host=${host},project_id=${GCP_PROJECT_ID}" \
    --path="${path}" \
    --period="${PERIOD_MINUTES}" \
    --timeout=10 \
    --status-classes=2xx \
    --format='value(name)')"
  [[ -n "${name}" ]] || die "failed to create uptime check ${display}"
  ok "Created ${display}: ${name}"
  echo "${name}"
}

: > "${SCRIPT_DIR}/.uptime-checks"
for entry in "${CHECKS[@]}"; do
  IFS='|' read -r display host path <<<"${entry}"
  upsert_check "${display}" "${host}" "${path}" \
    >> "${SCRIPT_DIR}/.uptime-checks"
done

ok "Uptime checks written to ${SCRIPT_DIR}/.uptime-checks"

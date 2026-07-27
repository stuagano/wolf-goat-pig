#!/usr/bin/env bash
# Phase 6 — create (or reuse) an email notification channel for alerts.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../lib/common.sh
source "${SCRIPT_DIR}/../lib/common.sh"

require_cmd gcloud

ALERT_EMAIL="${MONITOR_ALERT_EMAIL:-stuagano@gmail.com}"
CHANNEL_DISPLAY="WGP email alerts (${ALERT_EMAIL})"

log "Looking for existing email channel → ${ALERT_EMAIL}…"
EXISTING="$(gc beta monitoring channels list \
  --filter="type=email AND labels.email_address=${ALERT_EMAIL}" \
  --format='value(name)' 2>/dev/null | head -1 || true)"

if [[ -n "${EXISTING}" ]]; then
  ok "Reusing channel: ${EXISTING}"
  echo "${EXISTING}" > "${SCRIPT_DIR}/.notification-channel"
  exit 0
fi

log "Creating email notification channel for ${ALERT_EMAIL}…"
CREATED="$(gc beta monitoring channels create \
  --display-name="${CHANNEL_DISPLAY}" \
  --type=email \
  --channel-labels="email_address=${ALERT_EMAIL}" \
  --format='value(name)')"

[[ -n "${CREATED}" ]] || die "failed to create notification channel"
echo "${CREATED}" > "${SCRIPT_DIR}/.notification-channel"
ok "Created ${CREATED}"
warn "Check ${ALERT_EMAIL} and verify the channel if Google sent a confirmation email."

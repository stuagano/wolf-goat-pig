#!/usr/bin/env bash
# Phase 6 — alert policies: uptime failures, Cloud Run 5xx, Scheduler failures.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../lib/common.sh
source "${SCRIPT_DIR}/../lib/common.sh"

require_cmd gcloud python3

CHANNEL_FILE="${SCRIPT_DIR}/.notification-channel"
[[ -f "${CHANNEL_FILE}" ]] || die "Run 10-notification-channel.sh first (missing ${CHANNEL_FILE})."
CHANNEL="$(tr -d '[:space:]' < "${CHANNEL_FILE}")"
[[ -n "${CHANNEL}" ]] || die "notification channel file is empty"

POLICY_DIR="${SCRIPT_DIR}/policies"
mkdir -p "${POLICY_DIR}"

upsert_policy() {
  local display="$1" json_file="$2"
  local existing
  existing="$(gc alpha monitoring policies list \
    --filter="displayName=\"${display}\"" \
    --format='value(name)' 2>/dev/null | head -1 || true)"

  if [[ -n "${existing}" ]]; then
    log "Updating policy ${display}…"
    gc alpha monitoring policies update "${existing}" --policy-from-file="${json_file}" >/dev/null
    ok "Updated ${display} (${existing})"
  else
    log "Creating policy ${display}…"
    local name
    name="$(gc alpha monitoring policies create \
      --policy-from-file="${json_file}" \
      --format='value(name)')"
    ok "Created ${display} (${name})"
  fi
}

# ── 1) Uptime failures ──────────────────────────────────────────────────────
# Filter is project-scoped; keep only WGP uptime checks in this project.
python3 - "${CHANNEL}" "${POLICY_DIR}/uptime-failed.json" <<'PY'
import json, sys
channel, out = sys.argv[1], sys.argv[2]
policy = {
  "displayName": "WGP uptime check failed",
  "documentation": {
    "content": (
      "Firebase Hosting or Cloud Run /health failed an uptime probe "
      "(2 consecutive minutes).\n\n"
      "Dashboards:\n"
      "- Uptime: https://console.cloud.google.com/monitoring/uptime\n"
      "- Cloud Run: https://console.cloud.google.com/run\n"
    ),
    "mimeType": "text/markdown",
  },
  "combiner": "OR",
  "conditions": [{
    "displayName": "Any WGP uptime URL failing",
    "conditionThreshold": {
      "filter": (
        'resource.type = "uptime_url" AND '
        'metric.type = "monitoring.googleapis.com/uptime_check/check_passed"'
      ),
      "comparison": "COMPARISON_LT",
      "thresholdValue": 1,
      "duration": "120s",
      "aggregations": [{
        "alignmentPeriod": "60s",
        "perSeriesAligner": "ALIGN_FRACTION_TRUE",
        "crossSeriesReducer": "REDUCE_MIN",
        "groupByFields": ["resource.label.host"],
      }],
      "trigger": {"count": 1},
    },
  }],
  "notificationChannels": [channel],
  "alertStrategy": {"autoClose": "1800s"},
  "enabled": True,
}
with open(out, "w") as f:
    json.dump(policy, f, indent=2)
print(out)
PY

upsert_policy "WGP uptime check failed" "${POLICY_DIR}/uptime-failed.json"

# ── 2) Cloud Run 5xx spike (covers signup/auth crashes that return 500) ─────
python3 - "${CHANNEL}" "${GCP_PROJECT_ID}" "${RUN_SERVICE}" "${POLICY_DIR}/cloudrun-5xx.json" <<'PY'
import json, sys
channel, project, service, out = sys.argv[1:5]
policy = {
  "displayName": "WGP Cloud Run 5xx spike",
  "documentation": {
    "content": (
      "Cloud Run is returning elevated 5xx responses. Day-to-day actions "
      "(signup, login profile load) may be failing.\n\n"
      "Check Logs Explorer (severity>=ERROR) for the exception stack.\n"
      f"Service: {service}"
    ),
    "mimeType": "text/markdown",
  },
  "combiner": "OR",
  "conditions": [{
    "displayName": "5xx request rate > 0 for 5m",
    "conditionThreshold": {
      "filter": (
        'resource.type = "cloud_run_revision" AND '
        f'resource.labels.service_name = "{service}" AND '
        'metric.type = "run.googleapis.com/request_count" AND '
        'metric.labels.response_code_class = "5xx"'
      ),
      "comparison": "COMPARISON_GT",
      "thresholdValue": 0,
      "duration": "300s",
      "aggregations": [{
        "alignmentPeriod": "60s",
        "perSeriesAligner": "ALIGN_RATE",
        "crossSeriesReducer": "REDUCE_SUM",
        "groupByFields": ["resource.label.service_name"],
      }],
      "trigger": {"count": 1},
    },
  }],
  "notificationChannels": [channel],
  "alertStrategy": {"autoClose": "1800s"},
  "enabled": True,
}
with open(out, "w") as f:
    json.dump(policy, f, indent=2)
print(out)
PY

upsert_policy "WGP Cloud Run 5xx spike" "${POLICY_DIR}/cloudrun-5xx.json"

# ── 3) Cloud Scheduler job failed ───────────────────────────────────────────
python3 - "${CHANNEL}" "${GCP_PROJECT_ID}" "${POLICY_DIR}/scheduler-failed.json" <<'PY'
import json, sys
channel, project, out = sys.argv[1:4]
policy = {
  "displayName": "WGP Cloud Scheduler job failed",
  "documentation": {
    "content": (
      "A Cloud Scheduler job (emails, GHIN sync, pairings, sheet sync) failed.\n\n"
      "Jobs: https://console.cloud.google.com/cloudscheduler\n"
      "Logs: filter resource.type=\"cloud_scheduler_job\""
    ),
    "mimeType": "text/markdown",
  },
  "combiner": "OR",
  "conditions": [{
    "displayName": "Scheduler attempt failed",
    "conditionThreshold": {
      "filter": (
        'resource.type = "cloud_scheduler_job" AND '
        'metric.type = "logging.googleapis.com/log_entry_count" AND '
        'metric.labels.severity = "ERROR"'
      ),
      "comparison": "COMPARISON_GT",
      "thresholdValue": 0,
      "duration": "60s",
      "aggregations": [{
        "alignmentPeriod": "60s",
        "perSeriesAligner": "ALIGN_DELTA",
        "crossSeriesReducer": "REDUCE_SUM",
        "groupByFields": ["resource.label.job_id"],
      }],
      "trigger": {"count": 1},
    },
  }],
  "notificationChannels": [channel],
  "alertStrategy": {"autoClose": "3600s"},
  "enabled": True,
}
with open(out, "w") as f:
    json.dump(policy, f, indent=2)
print(out)
PY

upsert_policy "WGP Cloud Scheduler job failed" "${POLICY_DIR}/scheduler-failed.json"

# ── 4) Reported app failures (replaces Sentry issue emails) ─────────────────
# Python report_exception / report_message → Cloud Logging ERROR.
python3 - "${CHANNEL}" "${RUN_SERVICE}" "${POLICY_DIR}/reported-errors.json" <<'PY'
import json, sys
channel, service, out = sys.argv[1:4]
log_filter = (
    f'resource.type="cloud_run_revision"\n'
    f'resource.labels.service_name="{service}"\n'
    f'severity>=ERROR\n'
    f'("Reported exception" OR "External services down" OR '
    f'"Signup confirmation" OR "Welcome email" OR '
    f'"provider not configured" OR "rejected by provider")'
)
policy = {
  "displayName": "WGP reported app error",
  "documentation": {
    "content": (
      "Cloud Logging saw a reported operational error "
      "(signup email, welcome email, GHIN/Sheets/ForeTees swallow, etc.).\n\n"
      "Open Logs Explorer filtered to Cloud Run service "
      f"`{service}` severity>=ERROR."
    ),
    "mimeType": "text/markdown",
  },
  "combiner": "OR",
  "conditions": [{
    "displayName": "Reported operational ERROR log",
    "conditionMatchedLog": {
      "filter": log_filter,
    },
  }],
  "notificationChannels": [channel],
  "alertStrategy": {
    "notificationRateLimit": {"period": "300s"},
    "autoClose": "1800s",
  },
  "enabled": True,
}
with open(out, "w") as f:
    json.dump(policy, f, indent=2)
print(out)
PY

upsert_policy "WGP reported app error" "${POLICY_DIR}/reported-errors.json"

ok "Alert policies provisioned. Channel: ${CHANNEL}"
warn "Uptime policy may cover all uptime_url checks in this project — keep only WGP checks or narrow the filter later."

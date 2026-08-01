#!/usr/bin/env bash
# Phase 0 — create Secret Manager secrets and grant the runtime SA read access.
#
# These runtime values must NEVER be committed. This script creates the *containers*
# and IAM; it does not put real values in git. Add each value as a version with:
#
#   printf '%s' "the-value" | gcloud --project=PROJECT secrets versions add NAME --data-file=-
#
# Or set matching env vars before running and pass --from-env to seed them.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../lib/common.sh
source "${SCRIPT_DIR}/../lib/common.sh"

require_cmd gcloud

FROM_ENV=0
[[ "${1:-}" == "--from-env" ]] && FROM_ENV=1

# Secret names must match what the Cloud Run deploy wires via --set-secrets
# (see .github/workflows/deploy-gcp.yml and secrets.md).
SECRETS=(
  DATABASE_URL             # Phase 1: the Render Postgres URL; Phase 2: Cloud SQL
  GHIN_API_USER
  GHIN_API_PASS
  RESEND_API_KEY
  BOOKING_SERVICE_SECRET
  FORETEES_ENCRYPTION_KEY  # Fernet key for per-user ForeTees creds — do not lose
  INTERNAL_JOB_TOKEN       # Phase 4: guards POST /internal/jobs/* (Cloud Scheduler)
)

for name in "${SECRETS[@]}"; do
  if gc secrets describe "${name}" >/dev/null 2>&1; then
    ok "secret ${name} exists"
  else
    log "Creating secret ${name}…"
    gc secrets create "${name}" --replication-policy="automatic"
  fi

  # Optionally seed a first version from a same-named env var.
  if [[ "${FROM_ENV}" -eq 1 && -n "${!name:-}" ]]; then
    log "  adding version to ${name} from env…"
    printf '%s' "${!name}" | gc secrets versions add "${name}" --data-file=- >/dev/null
  fi

  # Runtime SA may read the latest version.
  gc secrets add-iam-policy-binding "${name}" \
    --member="serviceAccount:${RUNTIME_SA}" \
    --role="roles/secretmanager.secretAccessor" >/dev/null
done

ok "Secrets created and readable by ${RUNTIME_SA}."
echo
warn "Populate any empty secrets before the first Cloud Run deploy, e.g.:"
echo "    printf '%s' \"\$DATABASE_URL\" | gcloud --project=${GCP_PROJECT_ID} \\"
echo "      secrets versions add DATABASE_URL --data-file=-"

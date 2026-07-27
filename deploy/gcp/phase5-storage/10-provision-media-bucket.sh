#!/usr/bin/env bash
# Phase 5 — private GCS bucket for avatars (and future media).
# Idempotent: skips create if the bucket already exists.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../lib/common.sh
source "${SCRIPT_DIR}/../lib/common.sh"

require_cmd gcloud
require_config GCP_PROJECT_ID GCP_REGION RUNTIME_SA_NAME

MEDIA_BUCKET="${MEDIA_BUCKET:-wgp-media-${GCP_PROJECT_ID}}"
BUCKET_URI="gs://${MEDIA_BUCKET}"

log "Ensuring Cloud Storage API is enabled…"
gc services enable storage.googleapis.com >/dev/null

if gc storage buckets describe "${BUCKET_URI}" >/dev/null 2>&1; then
  ok "Bucket ${BUCKET_URI} already exists."
else
  log "Creating private media bucket ${BUCKET_URI} in ${GCP_REGION}…"
  gc storage buckets create "${BUCKET_URI}" \
    --location="${GCP_REGION}" \
    --uniform-bucket-level-access \
    --public-access-prevention
  ok "Created ${BUCKET_URI}"
fi

log "Granting objectAdmin on ${MEDIA_BUCKET} to ${RUNTIME_SA}…"
gc storage buckets add-iam-policy-binding "${BUCKET_URI}" \
  --member="serviceAccount:${RUNTIME_SA}" \
  --role="roles/storage.objectAdmin" \
  >/dev/null
ok "IAM updated."

cat <<EOF

Next: set MEDIA_BUCKET=${MEDIA_BUCKET} on Cloud Run
  (already in deploy/gcp/phase1-cloud-run/env.production.yaml — redeploy).

Avatar uploads go to gs://${MEDIA_BUCKET}/avatars/{player_id}.jpg
and are still served via GET /players/{id}/avatar (no public bucket).
EOF

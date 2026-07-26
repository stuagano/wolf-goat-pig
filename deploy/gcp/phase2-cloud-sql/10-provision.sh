#!/usr/bin/env bash
# Phase 2 — provision the Cloud SQL for PostgreSQL instance, database, and user.
# Design doc D1/§4: Cloud SQL lift-and-shift, schema unchanged.
#
# Idempotent-ish: skips the instance/db/user if they already exist. The DB
# password is read from the Secret Manager secret CLOUD_SQL_PASSWORD (create it
# first, see below).
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../lib/common.sh
source "${SCRIPT_DIR}/../lib/common.sh"

require_cmd gcloud
require_config SQL_INSTANCE SQL_VERSION SQL_TIER SQL_DB SQL_USER GCP_REGION

warn "Match SQL_VERSION (${SQL_VERSION}) to the CURRENT Render Postgres major"
warn "version before running. Check with: SELECT version();"
confirm "Provision Cloud SQL instance '${SQL_INSTANCE}' (${SQL_TIER}, always-on)?" \
  || die "aborted"

# ── Instance ────────────────────────────────────────────────────────────────
if gc sql instances describe "${SQL_INSTANCE}" >/dev/null 2>&1; then
  ok "Cloud SQL instance '${SQL_INSTANCE}' exists"
else
  log "Creating Cloud SQL instance '${SQL_INSTANCE}' (this takes several minutes)…"
  # Explicit --edition=enterprise keeps us on the cheap shared-core tiers
  # (db-f1-micro). Without it, gcloud defaults to enterprise-plus and rejects
  # db-f1-micro.
  gc sql instances create "${SQL_INSTANCE}" \
    --database-version="${SQL_VERSION}" \
    --edition="${SQL_EDITION:-enterprise}" \
    --tier="${SQL_TIER}" \
    --region="${GCP_REGION}" \
    --storage-auto-increase \
    --availability-type=zonal \
    --storage-size=10GB
fi

# ── Password (from Secret Manager) ──────────────────────────────────────────
if ! gc secrets describe CLOUD_SQL_PASSWORD >/dev/null 2>&1; then
  die "Secret 'CLOUD_SQL_PASSWORD' not found. Create it first:
    openssl rand -base64 32 | tr -d '/+=' | \\
      gcloud --project=${GCP_PROJECT_ID} secrets create CLOUD_SQL_PASSWORD --data-file=-"
fi
DB_PASSWORD="$(gc secrets versions access latest --secret=CLOUD_SQL_PASSWORD)"

# ── Database ────────────────────────────────────────────────────────────────
if gc sql databases describe "${SQL_DB}" --instance="${SQL_INSTANCE}" >/dev/null 2>&1; then
  ok "database '${SQL_DB}' exists"
else
  log "Creating database '${SQL_DB}'…"
  gc sql databases create "${SQL_DB}" --instance="${SQL_INSTANCE}"
fi

# ── User ────────────────────────────────────────────────────────────────────
if gc sql users list --instance="${SQL_INSTANCE}" --format='value(name)' | grep -qx "${SQL_USER}"; then
  ok "user '${SQL_USER}' exists"
else
  log "Creating user '${SQL_USER}'…"
  gc sql users create "${SQL_USER}" --instance="${SQL_INSTANCE}" --password="${DB_PASSWORD}"
fi

CONN_NAME="$(gc sql instances describe "${SQL_INSTANCE}" --format='value(connectionName)')"
ok "Cloud SQL ready. Connection name: ${CONN_NAME}"
echo
log "Next:"
echo "  1. Attach to Cloud Run:   gcloud run services update ${RUN_SERVICE:-wolf-goat-pig-api} \\"
echo "        --region ${GCP_REGION} --add-cloudsql-instances=${CONN_NAME}"
echo "  2. Point DATABASE_URL at it (Unix socket via the Cloud SQL connector)."
echo "     Use the plain 'postgresql://' scheme — app/database.py detects Postgres"
echo "     via startswith('postgresql://'), so a '+psycopg2' scheme would misroute"
echo "     to the SQLite branch:"
echo "        postgresql://${SQL_USER}:PASSWORD@/${SQL_DB}?host=/cloudsql/${CONN_NAME}"
echo "     Store that as a new version of the DATABASE_URL secret (see migration-runbook.md)."

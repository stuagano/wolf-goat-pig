#!/usr/bin/env bash
# Shared helpers for the deploy/gcp/* scripts.
#
# Usage (from a phase script):
#   SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
#   source "${SCRIPT_DIR}/../lib/common.sh"
#
# This file loads config.env, verifies required CLIs, and exposes the derived
# names (IMAGE, RUNTIME_SA, …) plus small log/confirm helpers. It performs no
# mutations itself.

set -euo pipefail

# ── Locate and load config ──────────────────────────────────────────────────
GCP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if [[ -f "${GCP_DIR}/config.env" ]]; then
  # shellcheck disable=SC1091
  source "${GCP_DIR}/config.env"
elif [[ -f "${GCP_DIR}/config.env.example" ]]; then
  echo "WARNING: config.env not found — falling back to config.env.example." >&2
  echo "         Copy it first:  cp deploy/gcp/config.env.example deploy/gcp/config.env" >&2
  # shellcheck disable=SC1091
  source "${GCP_DIR}/config.env.example"
else
  echo "ERROR: no config.env or config.env.example under ${GCP_DIR}" >&2
  exit 1
fi

# ── Log helpers ─────────────────────────────────────────────────────────────
log()  { printf '\033[1;34m▸\033[0m %s\n' "$*"; }
ok()   { printf '\033[1;32m✓\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33m!\033[0m %s\n' "$*" >&2; }
die()  { printf '\033[1;31m✗ %s\033[0m\n' "$*" >&2; exit 1; }

# ── Preconditions ───────────────────────────────────────────────────────────
require_cmd() {
  command -v "$1" >/dev/null 2>&1 || die "required command not found: $1"
}

require_config() {
  local missing=0 var
  for var in "$@"; do
    if [[ -z "${!var:-}" ]]; then
      warn "config value missing: ${var}"
      missing=1
    fi
  done
  [[ "${missing}" -eq 0 ]] || die "fill the missing values in deploy/gcp/config.env"
}

confirm() {
  # Skip prompts in CI / non-interactive shells.
  if [[ ! -t 0 || "${ASSUME_YES:-}" == "1" ]]; then
    return 0
  fi
  local reply
  read -r -p "$1 [y/N] " reply
  [[ "${reply}" == "y" || "${reply}" == "Y" ]]
}

# ── Derived names (single source of truth) ──────────────────────────────────
require_config GCP_PROJECT_ID GCP_REGION

AR_HOST="${GCP_REGION}-docker.pkg.dev"
IMAGE="${AR_HOST}/${GCP_PROJECT_ID}/${AR_REPO:-wolf-goat-pig}/${RUN_SERVICE:-wolf-goat-pig-api}"
RUNTIME_SA="${RUNTIME_SA_NAME:-wgp-run}@${GCP_PROJECT_ID}.iam.gserviceaccount.com"
DEPLOYER_SA="${DEPLOYER_SA_NAME:-wgp-deployer}@${GCP_PROJECT_ID}.iam.gserviceaccount.com"
SCHEDULER_SA="${SCHEDULER_SA_NAME:-wgp-scheduler}@${GCP_PROJECT_ID}.iam.gserviceaccount.com"

export AR_HOST IMAGE RUNTIME_SA DEPLOYER_SA SCHEDULER_SA

# gcloud, invoked with the configured project every time (never relies on the
# caller's active gcloud config).
gc() { gcloud --project="${GCP_PROJECT_ID}" "$@"; }

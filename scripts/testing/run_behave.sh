#!/bin/bash
set -euo pipefail

ROOT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
cd "$ROOT_DIR"

echo "🧪 Executing Behave feature tests"

if ! command -v behave >/dev/null 2>&1; then
  echo "📦 Installing Behave and dependencies via pip"
  PIP_BREAK_SYSTEM_PACKAGES=1 python3 -m pip install behave
fi

if [ -f "backend/requirements.txt" ]; then
  echo "📦 Ensuring backend test dependencies are available"
  PIP_BREAK_SYSTEM_PACKAGES=1 python3 -m pip install -r backend/requirements.txt >/dev/null
fi

echo "🚀 Running Behave against tests/bdd"
behave tests/bdd "$@"

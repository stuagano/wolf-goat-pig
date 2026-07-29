#!/usr/bin/env bash
# Regenerate the committed API contract + frontend types.
# Run whenever backend routes/schemas change, or after bumping fastapi /
# pydantic / starlette. Mirrors what OpenAPI Contract CI expects.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"

cd "$ROOT/backend"
python scripts/export_openapi.py
python scripts/export_openapi.py --check

cd "$ROOT/frontend"
npm run gen:api

echo "✅ OpenAPI contract + frontend types are in sync."
echo "   Commit: backend/openapi.json frontend/src/api/schema.d.ts"

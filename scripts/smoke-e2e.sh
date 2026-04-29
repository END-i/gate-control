#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_LOADER="$ROOT_DIR/scripts/lib/load-env.sh"
ENV_FILE="$ROOT_DIR/.env"

if [[ -f "$ENV_LOADER" ]]; then
  # shellcheck source=./lib/load-env.sh
  source "$ENV_LOADER"
  load_env_file_if_present "$ENV_FILE"
fi

API_BASE="${VITE_API_BASE_URL:-http://localhost:${BACKEND_PORT:-8010}/api}"
ADMIN_USER="${ADMIN_USERNAME:-admin}"
ADMIN_PASS="${ADMIN_PASSWORD:-change-me}"

login_payload=$(printf '{"username":"%s","password":"%s"}' "$ADMIN_USER" "$ADMIN_PASS")
login_response=$(curl -sS -f -X POST "$API_BASE/auth/login" \
  -H 'Content-Type: application/json' \
  -d "$login_payload")

token=$(python3 -c 'import json,sys; print(json.loads(sys.argv[1])["access_token"])' "$login_response")

auth_header="Authorization: Bearer $token"

curl -sS -f "$API_BASE/auth/me" -H "$auth_header" >/dev/null
curl -sS -f "$API_BASE/system/status" -H "$auth_header" >/dev/null
curl -sS -f "$API_BASE/stats" -H "$auth_header" >/dev/null
curl -sS -f "$API_BASE/logs?limit=1" -H "$auth_header" >/dev/null

echo "Smoke E2E passed: login, me, system/status, stats, logs"

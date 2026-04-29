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

BACKEND_PORT="${BACKEND_PORT:-8010}"
FRONTEND_PORT="${FRONTEND_PORT:-3000}"
FRONTEND_URL="${FRONTEND_URL:-http://localhost:$FRONTEND_PORT}"
API_BASE="${VITE_API_BASE_URL:-http://localhost:$BACKEND_PORT/api}"
BACKEND_HEALTH="http://localhost:$BACKEND_PORT/health"

if ! curl -sS -f "$BACKEND_HEALTH" >/dev/null; then
  echo "ERROR: backend health check failed at $BACKEND_HEALTH"
  exit 1
fi

echo "OK: backend health reachable at $BACKEND_HEALTH"

preflight_headers=$(curl -sS -D - -o /dev/null -X OPTIONS "$API_BASE/auth/login" \
  -H "Origin: $FRONTEND_URL" \
  -H 'Access-Control-Request-Method: POST' \
  -H 'Access-Control-Request-Headers: content-type,authorization')

if ! printf '%s' "$preflight_headers" | grep -qi "access-control-allow-origin: $FRONTEND_URL"; then
  echo "ERROR: CORS preflight does not allow origin $FRONTEND_URL"
  exit 1
fi

echo "OK: CORS preflight allows $FRONTEND_URL"

if curl -sS -f "http://localhost:$FRONTEND_PORT" >/dev/null; then
  echo "OK: frontend reachable at http://localhost:$FRONTEND_PORT"
else
  echo "WARN: frontend not reachable at http://localhost:$FRONTEND_PORT"
fi

echo "Doctor checks passed"

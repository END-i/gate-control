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
WEBHOOK_MODE="${WEBHOOK_AUTH_MODE:-token}"
WEBHOOK_TOKEN="${WEBHOOK_SHARED_SECRET:-change-me}"

if [[ "$WEBHOOK_MODE" != "token" ]]; then
  echo "smoke-critical-flow requires WEBHOOK_AUTH_MODE=token"
  exit 1
fi

login_payload=$(printf '{"username":"%s","password":"%s"}' "$ADMIN_USER" "$ADMIN_PASS")
login_response=$(curl -sS -f -X POST "$API_BASE/auth/login" \
  -H 'Content-Type: application/json' \
  -d "$login_payload")

token=$(python3 -c 'import json,sys; print(json.loads(sys.argv[1])["access_token"])' "$login_response")
auth_header="Authorization: Bearer $token"

suffix=$(date +%s)
allowed_plate="SMK${suffix}A"
blocked_plate="SMK${suffix}B"

create_vehicle() {
  local plate="$1"
  local status="$2"
  local payload
  payload=$(printf '{"license_plate":"%s","status":"%s"}' "$plate" "$status")

  curl -sS -f -X POST "$API_BASE/vehicles" \
    -H 'Content-Type: application/json' \
    -H "$auth_header" \
    -d "$payload" >/dev/null
}

send_webhook() {
  local plate="$1"
  local event_id="$2"

  local image_file
  image_file="$(mktemp)"
  trap 'rm -f "$image_file"' RETURN
  printf '\xFF\xD8\xFF\xE0\x00\x10JFIF' >"$image_file"

  curl -sS -f -X POST "$API_BASE/webhook/anpr" \
    -H "X-Webhook-Token: $WEBHOOK_TOKEN" \
    -H "X-Event-Id: $event_id" \
    -F "plate_number=$plate" \
    -F "image=@$image_file;type=image/jpeg"
}

create_vehicle "$allowed_plate" "allowed"
create_vehicle "$blocked_plate" "blocked"

allowed_response=$(send_webhook "$allowed_plate" "smoke-allowed-$suffix")
blocked_response=$(send_webhook "$blocked_plate" "smoke-blocked-$suffix")

allowed_status=$(python3 -c 'import json,sys; print(json.loads(sys.argv[1])["status"])' "$allowed_response")
blocked_status=$(python3 -c 'import json,sys; print(json.loads(sys.argv[1])["status"])' "$blocked_response")

if [[ "$allowed_status" != "opened" ]]; then
  echo "Expected allowed plate status=opened, got: $allowed_status"
  exit 1
fi

if [[ "$blocked_status" != "denied" ]]; then
  echo "Expected blocked plate status=denied, got: $blocked_status"
  exit 1
fi

echo "Critical flow smoke passed: allowed plate opened, blocked plate denied"

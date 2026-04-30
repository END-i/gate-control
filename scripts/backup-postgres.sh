#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="$ROOT_DIR/.env"
ENV_LOADER="$ROOT_DIR/scripts/lib/load-env.sh"

if [[ -f "$ENV_LOADER" ]]; then
  # shellcheck source=./lib/load-env.sh
  source "$ENV_LOADER"
  load_env_file_if_present "$ENV_FILE"
fi

COMPOSE_ENV_FILE_VALUE="${COMPOSE_ENV_FILE:-./.env}"
POSTGRES_USER_VALUE="${POSTGRES_USER:-postgres}"
POSTGRES_DB_VALUE="${POSTGRES_DB:-anpr}"
BACKUP_DIR_VALUE="${BACKUP_DIR:-$ROOT_DIR/backups}"
TIMESTAMP="$(date -u +%Y%m%dT%H%M%SZ)"
BACKUP_FILE_NAME="postgres-${POSTGRES_DB_VALUE}-${TIMESTAMP}.dump"
CONTAINER_TMP_PATH="/tmp/${BACKUP_FILE_NAME}"
TARGET_PATH="${BACKUP_DIR_VALUE}/${BACKUP_FILE_NAME}"

mkdir -p "$BACKUP_DIR_VALUE"

POSTGRES_CONTAINER_ID="$(COMPOSE_ENV_FILE="$COMPOSE_ENV_FILE_VALUE" docker compose --env-file "$COMPOSE_ENV_FILE_VALUE" ps -q postgres)"
if [[ -z "$POSTGRES_CONTAINER_ID" ]]; then
  echo "Postgres container is not running. Start compose stack first."
  exit 1
fi

docker exec "$POSTGRES_CONTAINER_ID" sh -lc "pg_dump -U '$POSTGRES_USER_VALUE' -d '$POSTGRES_DB_VALUE' -F c -f '$CONTAINER_TMP_PATH'"
docker cp "$POSTGRES_CONTAINER_ID:$CONTAINER_TMP_PATH" "$TARGET_PATH"
docker exec "$POSTGRES_CONTAINER_ID" rm -f "$CONTAINER_TMP_PATH"

echo "Backup created: $TARGET_PATH"

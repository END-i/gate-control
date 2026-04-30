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

if [[ $# -ne 1 ]]; then
  echo "Usage: ./scripts/restore-postgres.sh <path-to-backup.dump>"
  exit 1
fi

BACKUP_PATH="$1"
if [[ ! -f "$BACKUP_PATH" ]]; then
  echo "Backup file not found: $BACKUP_PATH"
  exit 1
fi

COMPOSE_ENV_FILE_VALUE="${COMPOSE_ENV_FILE:-./.env}"
POSTGRES_USER_VALUE="${POSTGRES_USER:-postgres}"
POSTGRES_DB_VALUE="${POSTGRES_DB:-anpr}"
RESTORE_NAME="restore-$(date -u +%s).dump"
CONTAINER_TMP_PATH="/tmp/${RESTORE_NAME}"

POSTGRES_CONTAINER_ID="$(COMPOSE_ENV_FILE="$COMPOSE_ENV_FILE_VALUE" docker compose --env-file "$COMPOSE_ENV_FILE_VALUE" ps -q postgres)"
if [[ -z "$POSTGRES_CONTAINER_ID" ]]; then
  echo "Postgres container is not running. Start compose stack first."
  exit 1
fi

docker cp "$BACKUP_PATH" "$POSTGRES_CONTAINER_ID:$CONTAINER_TMP_PATH"
docker exec "$POSTGRES_CONTAINER_ID" sh -lc "pg_restore -U '$POSTGRES_USER_VALUE' -d '$POSTGRES_DB_VALUE' --clean --if-exists --no-owner '$CONTAINER_TMP_PATH'"
docker exec "$POSTGRES_CONTAINER_ID" rm -f "$CONTAINER_TMP_PATH"

echo "Restore completed from: $BACKUP_PATH"

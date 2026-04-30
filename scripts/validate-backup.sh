#!/usr/bin/env bash
# validate-backup.sh — dump the live DB, restore into a temp DB, verify, and clean up.
# Exits 0 on success, non-zero on failure.
#
# Environment variables honoured:
#   POSTGRES_USER    default: postgres
#   POSTGRES_DB      default: anpr
#   POSTGRES_HOST    default: localhost
#   POSTGRES_PORT    default: 5432
#   PGPASSWORD       (pass through to pg_* tools)
set -euo pipefail

POSTGRES_USER_VALUE="${POSTGRES_USER:-postgres}"
POSTGRES_DB_VALUE="${POSTGRES_DB:-anpr}"
POSTGRES_HOST_VALUE="${POSTGRES_HOST:-localhost}"
POSTGRES_PORT_VALUE="${POSTGRES_PORT:-5432}"

VERIFY_DB="anpr_validate_$$"
DUMP_FILE=$(mktemp /tmp/anpr-validate-XXXXXX.dump)

_PG_OPTS=(
  -U "$POSTGRES_USER_VALUE"
  -h "$POSTGRES_HOST_VALUE"
  -p "$POSTGRES_PORT_VALUE"
)

cleanup() {
  dropdb --if-exists "${_PG_OPTS[@]}" "$VERIFY_DB" 2>/dev/null || true
  rm -f "$DUMP_FILE"
}
trap cleanup EXIT

echo "[validate-backup] Dumping '${POSTGRES_DB_VALUE}' → ${DUMP_FILE} ..."
pg_dump "${_PG_OPTS[@]}" -d "$POSTGRES_DB_VALUE" -F c -f "$DUMP_FILE"

echo "[validate-backup] Creating verification database '${VERIFY_DB}' ..."
createdb "${_PG_OPTS[@]}" "$VERIFY_DB"

echo "[validate-backup] Restoring dump to '${VERIFY_DB}' ..."
pg_restore "${_PG_OPTS[@]}" -d "$VERIFY_DB" "$DUMP_FILE"

echo "[validate-backup] Running sanity query ..."
ROW_COUNT=$(psql "${_PG_OPTS[@]}" -d "$VERIFY_DB" \
  -c "SELECT COUNT(*) FROM admins;" \
  --no-align --tuples-only)
echo "[validate-backup] admins table row count: ${ROW_COUNT}"

echo "[validate-backup] Backup validation PASSED."

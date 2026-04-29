#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FRONTEND_DIR="$ROOT_DIR/frontend"
ENV_FILE="$ROOT_DIR/.env"
ENV_LOADER="$ROOT_DIR/scripts/lib/load-env.sh"

if [[ -f "$ENV_LOADER" ]]; then
  # shellcheck source=./lib/load-env.sh
  source "$ENV_LOADER"
  load_env_file_if_present "$ENV_FILE"
fi

if ! command -v pnpm >/dev/null 2>&1; then
  echo "pnpm is not installed. Install Node.js + pnpm first."
  exit 1
fi

cd "$FRONTEND_DIR"
pnpm install --frozen-lockfile
exec pnpm dev --host --port "${FRONTEND_PORT:-3000}"

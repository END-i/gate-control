#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_ROOT_VENV="$ROOT_DIR/.venv/bin/python"
PYTHON_BACKEND_VENV="$ROOT_DIR/backend/.venv/bin/python"
ENV_FILE="$ROOT_DIR/.env"
ENV_LOADER="$ROOT_DIR/scripts/lib/load-env.sh"

if [[ -f "$ENV_LOADER" ]]; then
  # shellcheck source=./lib/load-env.sh
  source "$ENV_LOADER"
  load_env_file_if_present "$ENV_FILE"
fi

if [[ -x "$PYTHON_ROOT_VENV" ]]; then
  PYTHON_BIN="$PYTHON_ROOT_VENV"
elif [[ -x "$PYTHON_BACKEND_VENV" ]]; then
  PYTHON_BIN="$PYTHON_BACKEND_VENV"
else
  echo "Python venv not found. Create one of these:"
  echo "  - $ROOT_DIR/.venv"
  echo "  - $ROOT_DIR/backend/.venv"
  echo "Example: python3 -m venv backend/.venv && backend/.venv/bin/python -m pip install -r backend/requirements.txt"
  exit 1
fi

exec "$PYTHON_BIN" -m uvicorn main:app \
  --app-dir "$ROOT_DIR/backend" \
  --host "${BACKEND_HOST:-0.0.0.0}" \
  --port "${BACKEND_PORT:-8000}" \
  --reload

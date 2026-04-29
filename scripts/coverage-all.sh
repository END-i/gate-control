#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
FRONTEND_DIR="$ROOT_DIR/frontend"
PYTHON_BIN_DEFAULT="$ROOT_DIR/.venv/bin/python"
PYTHON_BIN_BACKEND_VENV="$BACKEND_DIR/.venv/bin/python"
BACKEND_COVERAGE_MIN="${BACKEND_COVERAGE_MIN:-70}"

if [[ -n "${PYTHON_BIN:-}" ]]; then
  PYTHON_BIN="$PYTHON_BIN"
elif [[ -x "$PYTHON_BIN_DEFAULT" ]]; then
  PYTHON_BIN="$PYTHON_BIN_DEFAULT"
elif [[ -x "$PYTHON_BIN_BACKEND_VENV" ]]; then
  PYTHON_BIN="$PYTHON_BIN_BACKEND_VENV"
else
  PYTHON_BIN="python3"
fi

echo "==> Backend coverage"
"$PYTHON_BIN" -m pytest "$BACKEND_DIR/tests" \
  --cov="$BACKEND_DIR" \
  --cov-report=term-missing \
  --cov-fail-under="$BACKEND_COVERAGE_MIN" \
  -q

echo "==> Frontend coverage"
pnpm --dir "$FRONTEND_DIR" install --frozen-lockfile
pnpm --dir "$FRONTEND_DIR" exec vitest run --coverage

echo "==> Coverage checks completed"

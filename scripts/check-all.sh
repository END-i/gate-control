#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
FRONTEND_DIR="$ROOT_DIR/frontend"
PYTHON_BIN_DEFAULT="$ROOT_DIR/.venv/bin/python"
PYTHON_BIN_BACKEND_VENV="$BACKEND_DIR/.venv/bin/python"

if [[ -n "${PYTHON_BIN:-}" ]]; then
  PYTHON_BIN="$PYTHON_BIN"
elif [[ -x "$PYTHON_BIN_DEFAULT" ]]; then
  PYTHON_BIN="$PYTHON_BIN_DEFAULT"
elif [[ -x "$PYTHON_BIN_BACKEND_VENV" ]]; then
  PYTHON_BIN="$PYTHON_BIN_BACKEND_VENV"
else
  PYTHON_BIN="python3"
fi

print_step() {
  echo "==> $1"
}

if [[ ! -d "$BACKEND_DIR" ]]; then
  echo "ERROR: missing backend directory at $BACKEND_DIR"
  exit 1
fi

if [[ ! -d "$FRONTEND_DIR" ]]; then
  echo "ERROR: missing frontend directory at $FRONTEND_DIR"
  exit 1
fi

if [[ ! -f "$FRONTEND_DIR/package.json" ]]; then
  echo "WARN: frontend package.json not found, skipping frontend checks"
  SKIP_FRONTEND=1
else
  SKIP_FRONTEND=0
fi

RUN_COVERAGE="${RUN_COVERAGE:-0}"

print_step "Backend lint"
"$PYTHON_BIN" -m ruff check "$BACKEND_DIR"

print_step "Backend typecheck"
"$PYTHON_BIN" -m mypy "$BACKEND_DIR" \
  --ignore-missing-imports \
  --disable-error-code call-arg \
  --disable-error-code arg-type \
  --disable-error-code attr-defined \
  --disable-error-code import-untyped \
  --disable-error-code misc \
  --disable-error-code type-var

print_step "Backend tests"
"$PYTHON_BIN" -m pytest "$BACKEND_DIR/tests" -q

if [[ "$SKIP_FRONTEND" -eq 0 ]]; then
  print_step "Frontend install"
  pnpm --dir "$FRONTEND_DIR" install --frozen-lockfile

  print_step "Frontend lint"
  if grep -q '"lint"' "$FRONTEND_DIR/package.json"; then
    pnpm --dir "$FRONTEND_DIR" lint
  else
    echo "WARN: frontend lint script not found, using check as fallback"
    pnpm --dir "$FRONTEND_DIR" check
  fi

  print_step "Frontend typecheck"
  pnpm --dir "$FRONTEND_DIR" check

  print_step "Frontend tests"
  if grep -q '"test:run"' "$FRONTEND_DIR/package.json"; then
    pnpm --dir "$FRONTEND_DIR" test:run
  else
    pnpm --dir "$FRONTEND_DIR" test -- --run
  fi
fi

print_step "Backend Docker build"
if command -v docker >/dev/null 2>&1; then
  docker build -t anpr-backend "$BACKEND_DIR"
else
  echo "WARN: docker not found, skipping backend image build"
fi

print_step "Frontend Docker build"
if command -v docker >/dev/null 2>&1; then
  docker build -t anpr-frontend "$FRONTEND_DIR"
else
  echo "WARN: docker not found, skipping frontend image build"
fi

if [[ "$RUN_COVERAGE" == "1" ]]; then
  print_step "Coverage (backend + frontend)"
  "$ROOT_DIR/scripts/coverage-all.sh"
fi

print_step "All checks passed"

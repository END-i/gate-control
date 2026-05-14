#!/usr/bin/env bash
set -euo pipefail

ensure_pnpm() {
  if command -v pnpm >/dev/null 2>&1; then
    return 0
  fi

  if ! command -v corepack >/dev/null 2>&1; then
    echo "pnpm is not installed and corepack is unavailable. Install Node.js + pnpm first."
    return 1
  fi

  echo "pnpm not found, preparing pnpm@9.15.9 via corepack..."
  corepack enable
  corepack prepare pnpm@9.15.9 --activate

  if ! command -v pnpm >/dev/null 2>&1; then
    echo "Failed to activate pnpm via corepack."
    return 1
  fi
}

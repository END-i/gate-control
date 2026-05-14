#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

case "$(uname -s)" in
  MINGW*|MSYS*|CYGWIN*)
    cmd.exe /c "$(cygpath -w "$ROOT_DIR/scripts/build-windows.bat")"
    ;;
  *)
    echo "EXE build is supported only on Windows. Run scripts\\build-windows.bat on a Windows host."
    exit 1
    ;;
esac

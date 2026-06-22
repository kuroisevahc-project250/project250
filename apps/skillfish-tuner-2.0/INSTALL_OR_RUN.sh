#!/usr/bin/env bash
set -euo pipefail
APPDIR="$(cd "$(dirname "$0")" && pwd)"
ARCH="$(uname -m 2>/dev/null || echo unknown)"
if [ "$ARCH" != "x86_64" ]; then
  echo "ERROR: Skillfish Tuner requires x86_64 / 64-bit Bazzite. Detected: $ARCH" >&2
  exit 64
fi

case "${1:-run}" in
  run)
    exec "$APPDIR/Cyan-Skillfish-All-In-One.AppRun"
    ;;
  install)
    exec "$APPDIR/install-desktop-entry.sh"
    ;;
  preflight|check)
    exec "$APPDIR/preflight-check.sh"
    ;;
  *)
    echo "Usage: ./INSTALL_OR_RUN.sh [run|install|preflight]"
    exit 2
    ;;
esac

#!/usr/bin/env bash
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="${XDG_STATE_HOME:-$HOME/.local/state}/skillfish-tuner"
mkdir -p "$LOG_DIR"
exec "$HERE/Cyan-Skillfish-All-In-One.AppRun" >>"$LOG_DIR/app.log" 2>&1

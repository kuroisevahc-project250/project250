#!/usr/bin/env bash
# Optional single-icon tray helper using yad when available.
# It is intentionally optional: the main app works without it.
set -euo pipefail
APP_DIR="$(cd "$(dirname "$0")" && pwd)"
ICON="$APP_DIR/assets/bagz_fishbone_logo.png"
[ -f "$ICON" ] || ICON="$APP_DIR/assets/bagz_fishbone_logo_transparent.png"
OPEN_CMD="$APP_DIR/Cyan-Skillfish-All-In-One.AppRun"
LOG_DIR="$HOME/.config/skillfish-tuner/logs"
REPORT_DIR="$HOME/.config/skillfish-tuner/reports"
mkdir -p "$LOG_DIR" "$REPORT_DIR"
if command -v yad >/dev/null 2>&1; then
  yad --notification \
    --image="$ICON" \
    --text="Skillfish Tuner" \
    --command="$OPEN_CMD" \
    --menu="Open Skillfish Tuner!$OPEN_CMD|Open Logs!xdg-open $LOG_DIR|Open Reports!xdg-open $REPORT_DIR|Quit!quit" \
    >/dev/null 2>&1 || true
elif command -v kdialog >/dev/null 2>&1; then
  # No persistent tray without yad/appindicator, but give a soft notification.
  kdialog --passivepopup "Skillfish Tuner tray helper needs 'yad' for a persistent tray icon." 5 >/dev/null 2>&1 || true
fi

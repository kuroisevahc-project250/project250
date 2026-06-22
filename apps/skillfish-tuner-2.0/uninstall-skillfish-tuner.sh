#!/usr/bin/env bash
set -euo pipefail
rm -rf "$HOME/.local/opt/skillfish-tuner"
rm -f "$HOME/.local/bin/skillfish-tuner"
rm -f "$HOME/.local/share/applications/skillfish-tuner.desktop"
rm -f "$HOME/.local/share/icons/hicolor/256x256/apps/skillfish-tuner.png"
rm -f "$HOME/.config/autostart/skillfish-tuner-tray.desktop"
printf '✓ Skillfish Tuner removed from user app menu. User configs/logs were kept.\n'

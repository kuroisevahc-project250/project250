#!/usr/bin/env bash
set -euo pipefail
APPDIR="$(cd "$(dirname "$0")" && pwd)"
ARCH="$(uname -m 2>/dev/null || echo unknown)"
if [ "$ARCH" != "x86_64" ]; then
  echo "ERROR: Skillfish Tuner requires x86_64 / 64-bit Bazzite. Detected: $ARCH" >&2
  exit 64
fi
mkdir -p "$HOME/.local/bin" "$HOME/.local/share/applications" "$HOME/.local/share/icons/hicolor/256x256/apps"
ln -sf "$APPDIR/Cyan-Skillfish-All-In-One.AppRun" "$HOME/.local/bin/Skillfish-Tuner"
cp "$APPDIR/share/icons/hicolor/256x256/apps/org.skillfish.tuner.png" "$HOME/.local/share/icons/hicolor/256x256/apps/"
cat > "$HOME/.local/share/applications/org.skillfish.tuner.desktop" <<EOF2
[Desktop Entry]
Type=Application
Name=Skillfish Tuner
Comment=BC-250 GPU / CU / Governor Tuner
Exec=$HOME/.local/bin/Skillfish-Tuner
Icon=org.skillfish.tuner
Terminal=false
Categories=System;Settings;Utility;
StartupNotify=true
EOF2
update-desktop-database "$HOME/.local/share/applications" >/dev/null 2>&1 || true
gtk-update-icon-cache "$HOME/.local/share/icons/hicolor" >/dev/null 2>&1 || true
echo "Installed Skillfish Tuner launcher. Start it from your app menu or run: Skillfish-Tuner"

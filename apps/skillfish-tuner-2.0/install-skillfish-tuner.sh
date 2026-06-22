#!/usr/bin/env bash
set -euo pipefail
SRC_DIR="$(cd "$(dirname "$0")" && pwd)"
APP_DIR="$HOME/.local/opt/skillfish-tuner"
BIN_DIR="$HOME/.local/bin"
APP_DESKTOP_DIR="$HOME/.local/share/applications"
ICON_DIR="$HOME/.local/share/icons/hicolor/256x256/apps"
AUTOSTART_DIR="$HOME/.config/autostart"
mkdir -p "$APP_DIR" "$BIN_DIR" "$APP_DESKTOP_DIR" "$ICON_DIR" "$AUTOSTART_DIR"
rsync -a --delete --exclude='.git' --exclude='__pycache__' "$SRC_DIR/" "$APP_DIR/"
chmod +x "$APP_DIR/Cyan-Skillfish-All-In-One.AppRun" || true
chmod +x "$APP_DIR/skillfish-tuner-tray.sh" || true
chmod +x "$APP_DIR/uninstall-skillfish-tuner.sh" || true
ln -sf "$APP_DIR/Cyan-Skillfish-All-In-One.AppRun" "$BIN_DIR/skillfish-tuner"
if [ -f "$APP_DIR/assets/bagz_fishbone_logo.png" ]; then
  cp -f "$APP_DIR/assets/bagz_fishbone_logo.png" "$ICON_DIR/skillfish-tuner.png"
elif [ -f "$APP_DIR/assets/bagz_fishbone_logo_transparent.png" ]; then
  cp -f "$APP_DIR/assets/bagz_fishbone_logo_transparent.png" "$ICON_DIR/skillfish-tuner.png"
fi
cat > "$APP_DESKTOP_DIR/skillfish-tuner.desktop" <<DESKTOP
[Desktop Entry]
Type=Application
Name=Skillfish Tuner
Comment=BC-250 GPU / CU / Governor Tuner
Exec=$BIN_DIR/skillfish-tuner
Icon=skillfish-tuner
Terminal=false
Categories=System;Settings;HardwareSettings;
StartupNotify=true
DESKTOP
chmod +x "$APP_DESKTOP_DIR/skillfish-tuner.desktop"
cat > "$AUTOSTART_DIR/skillfish-tuner-tray.desktop" <<TRAY
[Desktop Entry]
Type=Application
Name=Skillfish Tuner Tray
Comment=Skillfish Tuner tray helper
Exec=$APP_DIR/skillfish-tuner-tray.sh
Icon=skillfish-tuner
Terminal=false
X-GNOME-Autostart-enabled=false
TRAY
chmod +x "$AUTOSTART_DIR/skillfish-tuner-tray.desktop"
if command -v update-desktop-database >/dev/null 2>&1; then update-desktop-database "$APP_DESKTOP_DIR" >/dev/null 2>&1 || true; fi
if command -v gtk-update-icon-cache >/dev/null 2>&1; then gtk-update-icon-cache "$HOME/.local/share/icons/hicolor" >/dev/null 2>&1 || true; fi
printf '\n✓ Skillfish Tuner installed\n\n'
printf 'Desktop entry: %s\n' "$APP_DESKTOP_DIR/skillfish-tuner.desktop"
printf 'Command:       skillfish-tuner\n'
printf 'Tray helper:   %s\n' "$AUTOSTART_DIR/skillfish-tuner-tray.desktop"
printf '\nTip: enable the tray autostart from your desktop Startup Apps settings if desired.\n'

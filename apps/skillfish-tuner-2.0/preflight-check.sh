#!/usr/bin/env bash
set -euo pipefail
APPDIR="$(cd "$(dirname "$0")" && pwd)"

echo "Skillfish Tuner x86_64 preflight check"
echo "APPDIR=$APPDIR"

echo
echo "[1/6] Architecture"
ARCH="$(uname -m 2>/dev/null || echo unknown)"
echo "Detected: $ARCH"
test "$ARCH" = "x86_64"

echo
echo "[2/6] Python syntax"
python3 -m py_compile "$APPDIR/gui/app.py" "$APPDIR/gui/sudo_launcher.py" "$APPDIR/src/daemon.py"

echo
echo "[3/6] Runtime files"
test -x "$APPDIR/Cyan-Skillfish-All-In-One.AppRun"
test -x "$APPDIR/INSTALL_OR_RUN.sh"
test -f "$APPDIR/gui/app.py"
test -f "$APPDIR/gui/sudo_launcher.py"
test -f "$APPDIR/src/daemon.py"

echo
echo "[4/6] Python imports"
python3 - <<'PY'
import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw
print("GTK/Adwaita imports OK")
PY

echo
echo "[5/6] Optional host tools"
command -v sudo >/dev/null && echo "sudo OK" || echo "sudo missing"
command -v python3 >/dev/null && echo "python3 OK" || echo "python3 missing"
command -v rpm-ostree >/dev/null && echo "rpm-ostree OK" || echo "rpm-ostree not found"
command -v systemctl >/dev/null && echo "systemctl OK" || echo "systemctl missing"
command -v umr >/dev/null && echo "umr OK" || echo "umr not found; app can still install/use fallback if supported"

echo
echo "[6/6] Logs directory"
mkdir -p "$HOME/.config/skillfish-tuner/logs"
echo "Log path: $HOME/.config/skillfish-tuner/logs/latest.log"

echo
echo "Preflight complete."

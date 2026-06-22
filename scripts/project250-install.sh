#!/usr/bin/env bash
set -euo pipefail

USER_NAME="${SUDO_USER:-$USER}"
HOME_DIR="/home/$USER_NAME"
KERNEL_DIR="$HOME_DIR/40cu kernel/bazzite-bc250cu-rpms-ba29"
TELINHA="$HOME_DIR/telinha.py"
SKILLFISH_DIR="$HOME_DIR/skillfish-tuner-2.0"

need_root() {
  if [[ $EUID -ne 0 ]]; then
    echo "Rode com sudo: sudo $0"
    exit 1
  fi
}

step() { echo; echo "=== $1 ==="; }

need_root

step "1/9 - Kernel BC250CU"
if uname -r | grep -q "bc250cu"; then
  echo "OK: kernel já é BC250CU"
else
  rpm-ostree override replace "$KERNEL_DIR"/*.rpm
  echo "Kernel instalado. REBOOT necessário depois."
fi

step "2/9 - Pacotes necessários"
rpm-ostree install --idempotent cyan-skillfish-governor-smu stress umr || true

step "3/9 - Kernel args"
rpm-ostree kargs \
  --append-if-missing=bluetooth.disable_ertm=1 \
  --append-if-missing=zswap.enabled=1 \
  --append-if-missing=zswap.max_pool_percent=25 \
  --append-if-missing=zswap.compressor=lz4 \
  --append-if-missing=loglevel=0 \
  --append-if-missing=rd.systemd.show_status=false \
  --append-if-missing=amdgpu.bc250_cc_write_mode=3 || true

step "4/9 - ESP32 ttyUSB liberado sem dialout"
cat >/etc/udev/rules.d/99-cp210x.rules <<'EOF'
SUBSYSTEM=="tty", ATTRS{idVendor}=="10c4", ATTRS{idProduct}=="ea60", MODE="0666"
EOF
udevadm control --reload-rules || true
udevadm trigger || true

step "5/9 - Telinha ESP32"
sudo -u "$USER_NAME" python3 -m pip install --user pyserial psutil || true

if [[ -f "$TELINHA" ]]; then
  chmod +x "$TELINHA"
  cat >/etc/systemd/system/telinha.service <<EOF
[Unit]
Description=Project250 Telinha ESP32
After=multi-user.target

[Service]
Type=simple
User=$USER_NAME
WorkingDirectory=$HOME_DIR
ExecStart=/usr/bin/python3 $TELINHA
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF
  systemctl daemon-reload
  systemctl enable telinha.service
else
  echo "AVISO: $TELINHA não encontrado"
fi

step "6/9 - Skillfish shortcut"
if [[ -d "$SKILLFISH_DIR" ]]; then
  chmod +x "$SKILLFISH_DIR/INSTALL_OR_RUN.sh" 2>/dev/null || true
  mkdir -p "$HOME_DIR/Desktop"
  cat >"$HOME_DIR/Desktop/SkillFish-Tuner.desktop" <<EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=SkillFish Tuner 2.0
Comment=Executar SkillFish Tuner
Exec=konsole -e $SKILLFISH_DIR/INSTALL_OR_RUN.sh
Icon=utilities-terminal
Terminal=false
Categories=System;
EOF
  chmod +x "$HOME_DIR/Desktop/SkillFish-Tuner.desktop"
  chown "$USER_NAME:$USER_NAME" "$HOME_DIR/Desktop/SkillFish-Tuner.desktop"
else
  echo "AVISO: $SKILLFISH_DIR não encontrado"
fi

step "7/9 - NCT6683 monitoramento RPM"
echo nct6683 >/etc/modules-load.d/nct6683.conf
modprobe nct6683 || true

step "8/9 - Serviços"
systemctl daemon-reload
systemctl enable cyan-skillfish-governor-smu.service 2>/dev/null || true
systemctl enable bc250-smu-oc.service 2>/dev/null || true
systemctl enable plugin_loader.service 2>/dev/null || true
systemctl enable telinha.service 2>/dev/null || true

step "9/9 - Validação rápida"
echo "Kernel: $(uname -r)"
rpm-ostree kargs | grep -o "amdgpu.bc250_cc_write_mode=3" || true
ls -l /dev/ttyUSB* 2>/dev/null || true
systemctl is-enabled telinha.service 2>/dev/null || true
systemctl is-enabled cyan-skillfish-governor-smu.service 2>/dev/null || true

echo
echo "=== Project250 install v0.2 finalizado ==="
echo "Reinicie agora:"
echo "systemctl reboot"

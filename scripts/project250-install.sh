#!/usr/bin/env bash
set -euo pipefail

USER_NAME="${SUDO_USER:-$USER}"
HOME_DIR="/home/$USER_NAME"
REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PROJECT_DIR="/opt/project250"

KERNEL_DIR="$REPO_DIR/kernel-rpms"
TELINHA_SRC="$REPO_DIR/opt/project250/telinha.py"
TELINHA="$PROJECT_DIR/telinha.py"
SKILLFISH_SRC="$REPO_DIR/apps/skillfish-tuner-2.0"
SKILLFISH_DIR="$PROJECT_DIR/skillfish-tuner-2.0"

if [[ $EUID -ne 0 ]]; then
  echo "Rode com sudo:"
  echo "sudo ./scripts/project250-install.sh"
  exit 1
fi

step() {
  echo
  echo "=== $1 ==="
}

step "1/9 - Kernel BC250CU"
if uname -r | grep -q "bc250cu"; then
  echo "OK: kernel já é BC250CU"
else
  rpm-ostree override replace "$KERNEL_DIR"/*.rpm
  echo "Kernel instalado. Reinicie depois."
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

step "4/9 - ESP32 ttyUSB liberado"
install -D -m 0644 "$REPO_DIR/udev/99-cp210x.rules" /etc/udev/rules.d/99-cp210x.rules
udevadm control --reload-rules || true
udevadm trigger || true

step "5/9 - Project250 em /opt"
mkdir -p "$PROJECT_DIR"

if [[ -f "$TELINHA_SRC" ]]; then
  install -m 0755 "$TELINHA_SRC" "$TELINHA"
else
  echo "ERRO: telinha.py não encontrado em $TELINHA_SRC"
fi

if [[ -d "$SKILLFISH_SRC" ]]; then
  rm -rf "$SKILLFISH_DIR"
  cp -a "$SKILLFISH_SRC" "$SKILLFISH_DIR"
  chmod +x "$SKILLFISH_DIR/INSTALL_OR_RUN.sh" 2>/dev/null || true
else
  echo "AVISO: Skillfish não encontrado em $SKILLFISH_SRC"
fi

chown -R "$USER_NAME:$USER_NAME" "$PROJECT_DIR"

step "6/9 - Dependências Python da telinha"
sudo -u "$USER_NAME" python3 -m pip install --user pyserial psutil || true

step "7/9 - Serviço da telinha"
cat >/etc/systemd/system/telinha.service <<EOF_SERVICE
[Unit]
Description=Project250 Telinha ESP32
After=multi-user.target

[Service]
Type=simple
User=$USER_NAME
WorkingDirectory=$PROJECT_DIR
ExecStart=/usr/bin/python3 $TELINHA
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF_SERVICE

systemctl daemon-reload
systemctl enable telinha.service

step "8/9 - Atalho Skillfish"
mkdir -p "$HOME_DIR/Desktop"

cat >"$HOME_DIR/Desktop/SkillFish-Tuner.desktop" <<EOF_DESKTOP
[Desktop Entry]
Version=1.0
Type=Application
Name=SkillFish Tuner 2.0
Comment=Executar SkillFish Tuner
Exec=konsole -e $SKILLFISH_DIR/INSTALL_OR_RUN.sh
Icon=utilities-terminal
Terminal=false
Categories=System;
EOF_DESKTOP

chmod +x "$HOME_DIR/Desktop/SkillFish-Tuner.desktop"
chown "$USER_NAME:$USER_NAME" "$HOME_DIR/Desktop/SkillFish-Tuner.desktop"

step "9/9 - NCT6683 e serviços"
echo nct6683 >/etc/modules-load.d/nct6683.conf
modprobe nct6683 || true

systemctl daemon-reload
systemctl enable cyan-skillfish-governor-smu.service 2>/dev/null || true
systemctl enable bc250-smu-oc.service 2>/dev/null || true
systemctl enable plugin_loader.service 2>/dev/null || true
systemctl enable telinha.service 2>/dev/null || true

echo
echo "=== Validação rápida ==="
echo "Kernel: $(uname -r)"
rpm-ostree kargs | grep -o "amdgpu.bc250_cc_write_mode=3" || true
ls -l /dev/ttyUSB* 2>/dev/null || true
systemctl is-enabled telinha.service 2>/dev/null || true
systemctl is-enabled cyan-skillfish-governor-smu.service 2>/dev/null || true

echo
echo "=== Project250 install finalizado ==="
echo "Reinicie com:"
echo "systemctl reboot"

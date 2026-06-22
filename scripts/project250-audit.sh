#!/usr/bin/env bash

echo "=== PROJECT250 AUDIT ==="
echo

echo "[1] Sistema"
echo "User: $USER"
echo "Host: $(hostname)"
echo "Kernel: $(uname -r)"
echo

echo "[2] rpm-ostree"
rpm-ostree status | sed -n '1,80p'
echo

echo "[3] Pacotes BC250 / Skillfish / Cyan"
rpm -qa | grep -Ei "bc250|skillfish|cyan|umr|kernel" | sort
echo

echo "[4] Serviços Project250"
systemctl list-unit-files | grep -Ei "telinha|skillfish|cyan|bc250|decky|plugin" || true
echo

echo "[5] Status serviços principais"
for svc in \
  telinha.service \
  cyan-skillfish-governor-smu.service \
  bc250-smu-oc.service \
  skillfish-fan.service \
  plugin_loader.service
do
  echo "--- $svc ---"
  systemctl is-enabled "$svc" 2>/dev/null || true
  systemctl is-active "$svc" 2>/dev/null || true
done
echo

echo "[6] Kernel args"
rpm-ostree kargs
echo

echo "[7] CUs Vulkan"
RADV_DEBUG=info vulkaninfo --summary 2>&1 | grep -i "num_cu" || true
echo

echo "[8] Clocks GPU"
cat /sys/class/drm/card*/device/pp_dpm_sclk 2>/dev/null || true
echo

echo "[9] ESP32 / ttyUSB"
ls -l /dev/ttyUSB* 2>/dev/null || echo "Nenhuma ttyUSB encontrada"
echo
echo "Regras udev ESP32:"
ls -l /etc/udev/rules.d/*esp* /etc/udev/rules.d/*cp210* 2>/dev/null || true
echo

echo "[10] Telinha"
ls -l /home/Abraao/telinha.py 2>/dev/null || echo "telinha.py não encontrado"
systemctl status telinha.service --no-pager -n 5 2>/dev/null || true
echo

echo "[11] NCT6683 / sensores"
lsmod | grep nct || true
cat /etc/modules-load.d/nct6683.conf 2>/dev/null || true
sensors 2>/dev/null | head -80 || true
echo

echo "[12] Skillfish"
ls -ld /home/Abraao/skillfish-tuner-2.0 2>/dev/null || true
ls -l /home/Abraao/Desktop/*Skill* 2>/dev/null || true
echo

echo "[13] EmuDeck / Emulation"
ls -ld /home/Abraao/Emulation 2>/dev/null || true
ls -ld /home/Abraao/Applications 2>/dev/null || true
ls -l /home/Abraao/Desktop/*Emu* 2>/dev/null || true
echo

echo "=== FIM DA AUDITORIA ==="

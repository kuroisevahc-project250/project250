import os
import json
import re
import shutil
import subprocess
from pathlib import Path

APP = Path(__file__).resolve().parent.parent
TOOLS = APP / "tools"
SCRIPT = TOOLS / "bc250-cu-live-manager.sh"
URL = "https://raw.githubusercontent.com/WinnieLV/bc250-cu-live-manager/refs/heads/main/bc250-cu-live-manager.sh"


def _user_log_path():
    """Return a user-visible Skillfish log path even when daemon runs as root."""
    import pwd
    user = os.environ.get("SUDO_USER") or os.environ.get("USER") or ""
    home = None
    try:
        if user and user != "root":
            home = pwd.getpwnam(user).pw_dir
    except Exception:
        home = None
    if not home:
        home = os.path.expanduser("~")
    return Path(home) / ".config" / "skillfish-tuner" / "logs" / "latest.log"

def _append_log(title, text=""):
    """Append to user, /tmp, and system logs; never fail the main operation.

    The daemon sometimes runs as root without SUDO_USER, so a root home log is
    not useful.  /tmp is always user-visible, and /var/log is written via sudo
    when needed.  This prevents the GUI from ever saying "see log" with no log.
    """
    stamp = __import__("datetime").datetime.now().isoformat(timespec="seconds")
    body = f"\n=== {stamp} {title} ===\n{text}\n"

    paths = []
    # Prefer the real desktop user if available; Bazzite home is often /var/home/$USER.
    user = os.environ.get("SUDO_USER") or os.environ.get("PKEXEC_UID_USER") or ""
    try:
        if user and user != "root":
            import pwd
            home = pwd.getpwnam(user).pw_dir
            paths.append(Path(home) / ".config" / "skillfish-tuner" / "logs" / "latest.log")
    except Exception:
        pass
    # Also write for the current process and a universal fallback.
    paths.append(_user_log_path())
    paths.append(Path("/tmp/skillfish-tuner-latest.log"))

    written = set()
    for path in paths:
        try:
            if str(path) in written:
                continue
            written.add(str(path))
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, "a", encoding="utf-8") as f:
                f.write(body)
            if user and user != "root" and (str(path).startswith("/home/") or str(path).startswith("/var/home/")):
                import pwd, os as _os
                pw = pwd.getpwnam(user)
                _os.chown(path, pw.pw_uid, pw.pw_gid)
                _os.chown(path.parent, pw.pw_uid, pw.pw_gid)
        except Exception:
            pass

    # System log; sudo tee avoids permission problems when GUI is not root.
    try:
        syslog = "/var/log/skillfish-tuner/latest.log"
        if os.geteuid() == 0:
            Path(syslog).parent.mkdir(parents=True, exist_ok=True)
            with open(syslog, "a", encoding="utf-8") as f:
                f.write(body)
        else:
            subprocess.run(["sudo", "install", "-d", "-m", "0755", "/var/log/skillfish-tuner"], capture_output=True, text=True, timeout=10)
            subprocess.run(["sudo", "tee", "-a", syslog], input=body, capture_output=True, text=True, timeout=10)
    except Exception:
        pass

def log_location_text():
    return f"Log: {_user_log_path()}\nFallback log: /tmp/skillfish-tuner-latest.log\nSystem log: /var/log/skillfish-tuner/latest.log"

def run(cmd, timeout=180):
    try:
        env = os.environ.copy()
        env["PATH"] = "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:" + env.get("PATH", "")
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, env=env)
        return r.returncode, (r.stdout or r.stderr or "").strip()
    except Exception as e:
        return 999, str(e)

def have(cmd):
    return shutil.which(cmd) is not None

def umr_path():
    for p in ["/usr/bin/umr", "/usr/local/bin/umr", "/bin/umr", shutil.which("umr") or ""]:
        if p and Path(p).exists():
            return p
    return ""

def install_script():
    TOOLS.mkdir(parents=True, exist_ok=True)
    if have("curl"):
        rc, msg = run(["curl", "-L", "-o", str(SCRIPT), URL], 120)
    elif have("wget"):
        rc, msg = run(["wget", "-O", str(SCRIPT), URL], 120)
    else:
        return "ERR curl/wget missing"

    if rc != 0:
        return f"ERR download failed: {msg}"

    SCRIPT.chmod(0o755)
    return f"OK installed CU manager script: {SCRIPT}"

def ensure():
    if SCRIPT.exists():
        SCRIPT.chmod(0o755)
        return True, ""
    msg = install_script()
    return SCRIPT.exists(), msg

def install_umr():
    before = umr_path()
    if before:
        return f"OK umr already installed: {before}"

    out = []

    if have("rpm-ostree"):
        # Bazzite/SteamOS-style immutable systems layer packages with rpm-ostree.
        # This can take several minutes and may only make /usr/bin/umr available
        # after reboot.  --idempotent avoids failing when the package is already
        # requested/layered from a previous attempt.
        rc, msg = run(["sudo", "rpm-ostree", "install", "--idempotent", "umr"], 900)
        text = msg or str(rc)
        out.append(f"rpm-ostree install --idempotent umr: {text}")
        after = umr_path()
        low = text.lower()
        if after:
            out.append(f"OK umr found: {after}")
            return "\n".join(out)
        if rc == 0 or "already requested" in low or "already installed" in low or "no change" in low or "unchanged" in low:
            out.append("OK umr is layered/requested. Reboot Bazzite, then run: command -v umr")
            return "\n".join(out)
        out.append("ERR rpm-ostree could not layer umr. Try manually: sudo rpm-ostree install --idempotent umr")
        return "\n".join(out)

    if have("dnf"):
        rc, msg = run(["sudo", "dnf", "install", "-y", "umr"], 900)
        out.append(f"dnf install umr: {msg or rc}")
        after = umr_path()
        if rc == 0 and after:
            out.append(f"OK umr found: {after}")
        else:
            out.append(f"umr path: {after or 'not found'}")
        return "\n".join(out)

    if have("pacman"):
        rc, msg = run(["sudo", "pacman", "-S", "--noconfirm", "umr"], 900)
        out.append(f"pacman install umr: {msg or rc}")
        after = umr_path()
        if rc == 0 and after:
            out.append(f"OK umr found: {after}")
        else:
            out.append(f"umr path: {after or 'not found'}")
        return "\n".join(out)

    return "ERR no supported installer found for umr. Install manually, then reboot if using rpm-ostree."

def preflight():
    ok, msg = ensure()
    script_state = f"CU manager script: {'OK ' + str(SCRIPT) if ok else 'MISSING ' + msg}"
    u = umr_path()
    umr_state = f"umr: {'OK ' + u if u else 'MISSING - press Install UMR, then reboot on rpm-ostree/Bazzite if needed'}"
    return script_state + "\n" + umr_state

def call(*args, timeout=240):
    ok, msg = ensure()
    if not ok:
        return msg

    u = umr_path()
    if not u and args not in [("install-umr",)]:
        return (
            "ERR umr not found. CU live manager cannot access registers.\n"
            "Press Install UMR. On Bazzite/rpm-ostree, reboot after layering if needed.\n"
            "Check with: command -v umr"
        )

    rc, out = run(["sudo", str(SCRIPT), *args], timeout)
    return out if out else ("OK" if rc == 0 else f"ERR rc={rc}")

def install_umr_via_script():
    ok, msg = ensure()
    if not ok:
        return msg
    return call("install-umr", timeout=300)

def status():
    return preflight() + "\n\n" + call("status", timeout=120)

def dry_run():
    return call("--dry-run", "--yes", "enable", "all")

def enable_all():
    return call("--yes", "enable", "all")

def stock():
    return call("--yes", "stock-dispatch")

def write_table():
    return call("--yes", "write-service-table")

def install_boot():
    return call("--yes", "install-service")

def apply_boot():
    return call("--yes", "apply-service")

def uninstall_boot():
    return call("--yes", "uninstall-service")

def enable_wgp(triplet):
    return call("--yes", "enable-wgp", str(triplet), timeout=240)

def disable_wgp(triplet):
    return call("--yes", "disable-wgp", str(triplet), timeout=240)

def persist_live_table():
    """Save current live WGP routing table and enable boot restore service.

    This follows WinnieLV/bc250-cu-live-manager persistence exactly:
    1) write-service-table -> /etc/bc250-cu-live-manager.conf
    2) install-service -> systemd boot restore
    """
    out=[]
    out.append(write_table())
    out.append(install_boot())
    return "\n".join(out)

def enable_all_persistent():
    out=[]
    out.append(enable_all())
    out.append(persist_live_table())
    out.append("RESTART_REQUIRED=1")
    return "\n".join(out)

def activate_spi_persistent():
    """Activate SPI-routed CUs live and save them for boot restore.

    Important: the kernel/driver boot topology may still report 24/40.
    That is normal for the WinnieLV UMR method: extra WGPs are routed through
    SPI dispatch, so the effective dispatch count is SPI total, not driver lock.
    """
    return enable_all_persistent() + "\nOK SPI-routed CUs activated. Driver lock can remain 24/40; use Effective/SPI total as the active count."

def stock_persistent():
    out=[]
    out.append(stock())
    out.append(persist_live_table())
    out.append("RESTART_REQUIRED=1")
    return "\n".join(out)


def _sudo_write(path, content):
    """Write root-owned config files from the GUI helper via sudo tee."""
    rc, out = run(["sudo", "install", "-d", "-m", "0755", str(Path(path).parent)], 30)
    if rc != 0:
        return False, out
    try:
        proc = subprocess.run(
            ["sudo", "tee", path], input=content, text=True,
            capture_output=True, timeout=30,
            env={**os.environ, "PATH": "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:" + os.environ.get("PATH", "")},
        )
        if proc.returncode != 0:
            return False, (proc.stderr or proc.stdout or f"tee rc={proc.returncode}").strip()
        return True, ""
    except Exception as e:
        return False, str(e)

def _sudo_run_shell(script, timeout=120):
    return run(["sudo", "bash", "-lc", script], timeout)

def parse_wgp_key(key):
    """Convert app key 'SE0.SH1:WGP4' into amdgpu.disable_cu triplet '0.1.4'."""
    m = re.match(r"SE(\d+)\.SH(\d+):WGP(\d+)$", key.strip())
    if not m:
        return None
    return f"{int(m.group(1))}.{int(m.group(2))}.{int(m.group(3))}"

def _normalize_disable_mask(disable_mask):
    mask = []
    for item in disable_mask or []:
        item = str(item).strip()
        if re.match(r"^[01]\.[01]\.[0-4]$", item) and item not in mask:
            mask.append(item)
    return sorted(mask, key=lambda x: tuple(int(v) for v in x.split('.')))


def _kernel_arg_value_for_mask(mask):
    args = ["amdgpu.bc250_cc_write_mode=3"]
    if mask:
        args.append("amdgpu.disable_cu=" + ",".join(mask))
    return args


def _install_hybrid_boot_args(mask):
    """Persist amdgpu params in the real boot path and verify they are staged."""
    wanted = _kernel_arg_value_for_mask(mask)
    wanted_lines = "\n".join(wanted)
    script = f"""
set -euo pipefail
log(){{ printf '%s\n' "$*"; }}
log "Wanted kernel args:"
printf '%s\n' {wanted_lines!r}
if command -v rpm-ostree >/dev/null 2>&1; then
  BEFORE="$(rpm-ostree kargs 2>/dev/null || true)"
  log "Current rpm-ostree kargs before: $BEFORE"
  for tok in $BEFORE $(cat /proc/cmdline 2>/dev/null || true); do
    case "$tok" in
      amdgpu.bc250_cc_write_mode=*|amdgpu.disable_cu=*|bc250_cc_write_mode=*|disable_cu=*)
        rpm-ostree kargs --delete-if-present="$tok" || true
        ;;
    esac
  done
"""
    for arg in wanted:
        script += f"  rpm-ostree kargs --append-if-missing='{arg}'\n"
    script += """
  AFTER="$(rpm-ostree kargs 2>/dev/null || true)"
  log "Current rpm-ostree kargs after: $AFTER"
"""
    for arg in wanted:
        script += f"  echo \"$AFTER\" | grep -F -- '{arg}' >/dev/null || {{ log 'ERR missing staged karg: {arg}'; exit 20; }}\n"
    script += """
  log "OK rpm-ostree kargs staged; reboot required"
  exit 0
fi

if command -v dracut >/dev/null 2>&1; then
  dracut -f
  log "OK dracut initramfs rebuilt"
elif command -v update-initramfs >/dev/null 2>&1; then
  update-initramfs -u
  log "OK initramfs updated"
else
  log "WARN no rpm-ostree/dracut/update-initramfs found; modprobe config and runtime restore only"
fi
"""
    rc, msg = _sudo_run_shell(script, 900)
    _append_log("install hybrid boot args", msg or f"rc={rc}")
    return rc, msg


def _install_hybrid_runtime_service(mask, active):
    """Install a small, stable runtime restore service.

    Important fixes for Bazzite testing:
    - Do not depend on the app still living in Downloads after reboot.
    - Do not install three confusing services that can fail independently.
    - Copy the bundled bc250-cu-live-manager script into /usr/local/sbin.
    - Keep compatibility aliases so old status checks still find service names.
    - Always write /var/log/skillfish-tuner/latest.log and /tmp fallback.
    """
    selected_json = json.dumps({
        "expected_active": active,
        "disable_mask": mask,
        "kernel_args": _kernel_arg_value_for_mask(mask),
        "note": "Driver Lock can remain 24/40. Effective/SPI dispatch is the value to verify.",
    }, indent=2)
    app_script = str(SCRIPT)
    script = r'''set -euo pipefail
install -d -m 0755 /etc/skillfish-tuner /usr/local/sbin /etc/systemd/system /var/log/skillfish-tuner
printf '
=== Skillfish hybrid service install %s ===
' "$(date -Is)" >> /var/log/skillfish-tuner/latest.log
cat > /etc/skillfish-tuner/cu-selected.json <<'JSON_EOF'
__SELECTED_JSON__
JSON_EOF

# Put the CU manager in a stable system path. The app may be launched from Downloads,
# and that path must not be required after reboot.
if [ -x '__APP_SCRIPT__' ]; then
  # Overwrite safely. Some systems reported `install: ... File exists`; remove first
  # and install via a temporary file so an existing old copy cannot abort Apply Unlock.
  TMP=/usr/local/sbin/.skillfish-bc250-cu-live-manager.sh.tmp
  rm -f "$TMP"
  install -m 0755 '__APP_SCRIPT__' "$TMP"
  mv -f "$TMP" /usr/local/sbin/skillfish-bc250-cu-live-manager.sh
  chmod 0755 /usr/local/sbin/skillfish-bc250-cu-live-manager.sh
elif [ -x /usr/local/sbin/skillfish-bc250-cu-live-manager.sh ]; then
  chmod 0755 /usr/local/sbin/skillfish-bc250-cu-live-manager.sh
else
  echo 'ERR bundled bc250-cu-live-manager.sh missing; cannot install restore service' | tee -a /var/log/skillfish-tuner/latest.log
  exit 41
fi

cat > /usr/local/sbin/skillfish-cu-restore <<'HELPER_EOF'
#!/usr/bin/env bash
set -u
install -d -m 0755 /var/log/skillfish-tuner
LOG=/var/log/skillfish-tuner/cu-restore.log
exec >>"$LOG" 2>&1
echo "=== Skillfish CU restore $(date -Is) ==="
echo "Driver Lock may stay 24/40; checking/restoring effective SPI dispatch."
SCRIPT=/usr/local/sbin/skillfish-bc250-cu-live-manager.sh
if [ ! -x "$SCRIPT" ]; then
  echo "ERR $SCRIPT missing"
  exit 0
fi
# First try the saved service table generated by the manager.
timeout 45s "$SCRIPT" --yes apply-service || true
# Then print status for verification; never make boot fail because of display text.
timeout 45s "$SCRIPT" status || true
echo "Skillfish CU restore finished $(date -Is)"
exit 0
HELPER_EOF
chmod 0755 /usr/local/sbin/skillfish-cu-restore

cat > /etc/systemd/system/skillfish-cu.service <<'UNIT_EOF'
[Unit]
Description=Skillfish BC-250 selected CU runtime restore
Documentation=https://github.com/WinnieLV/bc250-cu-live-manager
After=local-fs.target systemd-modules-load.service bc250-cu-live-manager.service
Wants=bc250-cu-live-manager.service
Before=cyan-skillfish-governor-smu.service cyan-skillfish-governor.service cyan-skillfish-governor-tt.service
ConditionPathExists=/etc/skillfish-tuner/cu-selected.json

[Service]
Type=oneshot
ExecStart=/usr/local/sbin/skillfish-cu-restore
RemainAfterExit=yes
TimeoutStartSec=60

[Install]
WantedBy=multi-user.target
UNIT_EOF

# Compatibility service names used by earlier test builds and checks.
# Use real copies instead of aliases so systemctl enable works everywhere.
for svc in skillfish-cu-hybrid.service skillfish-cu-restore.service skillfish-cu-verify.service; do
  cp /etc/systemd/system/skillfish-cu.service "/etc/systemd/system/$svc"
done

# Ensure governor starts after CU restore.
for svc in cyan-skillfish-governor-smu.service cyan-skillfish-governor.service cyan-skillfish-governor-tt.service; do
  install -d -m 0755 "/etc/systemd/system/$svc.d"
  cat > "/etc/systemd/system/$svc.d/10-skillfish-cu-order.conf" <<'DROPIN_EOF'
[Unit]
After=skillfish-cu.service bc250-cu-live-manager.service
Wants=skillfish-cu.service
DROPIN_EOF
done

systemctl daemon-reload
timeout 30s systemctl enable skillfish-cu.service skillfish-cu-hybrid.service skillfish-cu-restore.service skillfish-cu-verify.service
printf 'OK installed skillfish-cu.service and compatibility aliases
' | tee -a /var/log/skillfish-tuner/latest.log
systemctl is-enabled skillfish-cu.service skillfish-cu-hybrid.service skillfish-cu-restore.service skillfish-cu-verify.service || true
'''.replace('__SELECTED_JSON__', selected_json).replace('__APP_SCRIPT__', app_script)
    rc, msg = _sudo_run_shell(script, 90)
    _append_log("install hybrid runtime service", msg or f"rc={rc}")
    if rc != 0:
        return False, "could not install/enable skillfish-cu.service: " + (msg or f"rc={rc}")
    verify = """set -e
for f in /etc/systemd/system/skillfish-cu.service /etc/systemd/system/skillfish-cu-hybrid.service /etc/systemd/system/skillfish-cu-restore.service /etc/systemd/system/skillfish-cu-verify.service /usr/local/sbin/skillfish-cu-restore /usr/local/sbin/skillfish-bc250-cu-live-manager.sh /etc/skillfish-tuner/cu-selected.json; do
  test -e \"$f\" || { echo \"ERR missing $f\"; exit 44; }
done
systemctl is-enabled skillfish-cu.service >/dev/null
echo OK verified skillfish-cu.service
"""
    vrc, vmsg = _sudo_run_shell(verify, 30)
    _append_log("verify hybrid runtime service", vmsg or f"rc={vrc}")
    if vrc != 0:
        return False, "service verification failed: " + (vmsg or f"rc={vrc}")
    return True, "OK skillfish-cu.service enabled; compatibility service aliases installed; governor ordered after CU restore"

def persist_disable_mask(disable_mask, expected_active=None):
    """Hybrid reboot persistence for selected-only BC-250 CU topology."""
    _append_log("apply hybrid unlock requested", f"disable_mask={disable_mask} expected_active={expected_active}")
    mask = _normalize_disable_mask(disable_mask)
    active = 40 - (2 * len(mask))
    if expected_active is not None:
        try:
            active = int(expected_active)
        except Exception:
            pass

    opts = "options amdgpu bc250_cc_write_mode=3"
    if mask:
        opts += " disable_cu=" + ",".join(mask)
    content = (
        "# Generated by Skillfish Tuner - BC-250 hybrid CU persistent topology\n"
        "# Early path: amdgpu driver init unlock. Runtime path: WinnieLV service restore.\n"
        "# Format: amdgpu.disable_cu=SE.SH.WGP ; each WGP contains two CUs.\n"
        f"# Expected selected active CUs: {active}/40\n"
        f"{opts}\n"
    )
    ok, msg = _sudo_write("/etc/modprobe.d/bc250-40cu.conf", content)
    if not ok:
        return "ERR could not write /etc/modprobe.d/bc250-40cu.conf: " + msg

    out = []
    out.append("OK wrote /etc/modprobe.d/bc250-40cu.conf")
    out.append("Kernel args: " + " ".join(_kernel_arg_value_for_mask(mask)))

    rc, msg = _install_hybrid_boot_args(mask)
    if rc != 0:
        out.append("WARN boot args/initramfs step returned rc=%s: %s" % (rc, msg))
    else:
        out.append(msg or "OK boot args/initramfs updated")

    live_msgs = []
    try:
        live_msgs.append(write_table())
        live_msgs.append(install_boot())
    except Exception as e:
        live_msgs.append(f"WARN live-manager table/service failed: {e}")
    out.extend(live_msgs)

    ok, msg = _install_hybrid_runtime_service(mask, active)
    if not ok:
        out.append("ERR " + msg)
        return "\n".join(out)
    out.append(msg)

    out.append(f"OK hybrid CU persistence installed for selected {active}/40 CUs")
    out.append(f"disable_cu mask: {(','.join(mask) if mask else '(none)')}")
    out.append("RESTART_REQUIRED=1")
    out.append("Restart required. After reboot, use Refresh Topology to compare Driver / Selected / Effective counts.")
    out.append(log_location_text())
    result = "\n".join(out)
    _append_log("apply hybrid unlock finished", result)
    return result



def apply_selected_live(staged=None, expected_active=None):
    """Apply only the user's selected WGP changes live and save the live table.

    This is the safe/quick path behind "Apply Selected Live + Save".  It does
    not force Full 40 and does not require the optional driver helper.  It runs
    the requested enable/disable WGP commands, writes the resulting live table,
    installs/enables the existing bc250-cu-live-manager boot service, and returns
    a clear result instead of hanging on optional boot/kargs work.
    """
    staged = staged or {}
    _append_log("apply selected live requested", json.dumps(staged, indent=2, sort_keys=True))
    out = []
    applied = 0
    for key, val in sorted(staged.items()):
        trip = parse_wgp_key(key)
        if not trip:
            out.append(f"WARN skipped invalid CU key: {key}")
            continue
        if val == "activate":
            msg = enable_wgp(trip)
            out.append(f"activate {trip}: {msg}")
        elif val == "deactivate":
            msg = disable_wgp(trip)
            out.append(f"deactivate {trip}: {msg}")
        else:
            out.append(f"WARN skipped unknown action for {key}: {val}")
            continue
        applied += 1
        if msg.startswith("ERR") or "\nERR" in msg:
            result = "\n".join(out + [log_location_text()])
            _append_log("apply selected live failed", result)
            return result

    if applied <= 0:
        result = "ERR no valid selected CU changes were found\n" + log_location_text()
        _append_log("apply selected live failed", result)
        return result

    out.append(write_table())
    out.append(install_boot())
    if expected_active:
        out.append(f"OK selected live table saved for {expected_active}/40 effective CUs")
    else:
        out.append("OK selected live table saved")
    out.append("NO_REBOOT_REQUIRED_FOR_LIVE_APPLY=1")
    out.append(log_location_text())
    result = "\n".join(out)
    _append_log("apply selected live finished", result)
    return result

def selected_disable_mask_from_rows(rows, staged=None):
    """Return disable_cu triplets for every WGP that should remain OFF."""
    staged = staged or {}
    mask = []
    active = 0
    for row in rows or []:
        rn = row.get("row", "")
        for wgp in row.get("wgps", []):
            name = wgp.get("name", "")
            key = f"{rn}:{name}"
            state = wgp.get("color_state") or ("active" if wgp.get("driver") else ("spi" if wgp.get("spi_only") else "off"))
            desired_on = state in ("active", "spi")
            if staged.get(key) == "activate":
                desired_on = True
            elif staged.get(key) == "deactivate":
                desired_on = False
            trip = parse_wgp_key(key)
            if desired_on:
                active += 2
            elif trip:
                mask.append(trip)
    mask = sorted(set(mask), key=lambda x: tuple(int(v) for v in x.split('.')))
    return mask, active


def _download_unlock_repo():
    target = "/var/lib/skillfish-tuner/bc250-40cu-unlock"
    script = """
set -euo pipefail
install -d -m 0755 /var/lib/skillfish-tuner
cd /var/lib/skillfish-tuner
if command -v git >/dev/null 2>&1; then
  if [ -d bc250-40cu-unlock/.git ]; then
    git -C bc250-40cu-unlock pull --ff-only
  else
    rm -rf bc250-40cu-unlock
    git clone --depth=1 https://github.com/duggasco/bc250-40cu-unlock.git bc250-40cu-unlock
  fi
else
  rm -rf bc250-40cu-unlock bc250-40cu-unlock-main main.tar.gz
  if command -v curl >/dev/null 2>&1; then
    curl -L -o main.tar.gz https://github.com/duggasco/bc250-40cu-unlock/archive/refs/heads/main.tar.gz
  elif command -v wget >/dev/null 2>&1; then
    wget -O main.tar.gz https://github.com/duggasco/bc250-40cu-unlock/archive/refs/heads/main.tar.gz
  else
    echo "ERR git/curl/wget missing"
    exit 2
  fi
  tar -xzf main.tar.gz
  mv bc250-40cu-unlock-main bc250-40cu-unlock
fi
chmod +x bc250-40cu-unlock/scripts/*.sh || true
"""
    rc, msg = _sudo_run_shell(script, 300)
    return rc, msg, target


def install_driver_unlock_patch(disable_mask=None, expected_active=None):
    """Apply hybrid unlock.

    Reliability fix: persist selected boot/runtime configuration first. The optional
    duggasco driver-module build can fail on rpm-ostree/kernel-header mismatch, but
    that must not prevent kargs, modprobe config, and runtime restore services from
    being installed.
    """
    out = []
    out.append("Apply BC-250 hybrid CU unlock")
    out.append("1/3 Persist selected boot/runtime configuration")
    persist_msg = persist_disable_mask(disable_mask or [], expected_active)
    out.append(persist_msg)
    if persist_msg.startswith("ERR") or "\nERR" in persist_msg:
        result = "\n".join(out + [log_location_text()])
        _append_log("apply hybrid unlock failed during persistence", result)
        return result

    out.append("2/3 Optional duggasco driver-init helper")
    out.append("SKIPPED by default in this test build: no network clone/build during Apply Hybrid Unlock, so the app cannot hang here. Use the external project manually only if you specifically want the experimental driver helper.")

    out.append("3/3 Verify staged configuration")
    verify = """
set +e
echo '--- rpm-ostree kargs ---'
rpm-ostree kargs 2>/dev/null || true
echo '--- modprobe bc250 ---'
cat /etc/modprobe.d/bc250-40cu.conf 2>/dev/null || true
echo '--- services ---'
systemctl is-enabled skillfish-cu-hybrid.service 2>/dev/null || true
systemctl is-enabled skillfish-cu-restore.service 2>/dev/null || true
systemctl is-enabled bc250-cu-live-manager.service 2>/dev/null || true
"""
    vrc, vmsg = _sudo_run_shell(verify, 60)
    out.append(vmsg or "OK verification complete")
    out.append("RESTART_REQUIRED=1")
    out.append("Restart required: rpm-ostree kargs only take effect after reboot.")
    out.append(log_location_text())
    result = "\n".join(out)
    _append_log("apply hybrid unlock finished", result)
    return result


def parse_dashboard(text):
    """
    Parse the text dashboard from bc250-cu-live-manager into a GUI-friendly shape.
    Handles rows like:
    | SE0.SH0 |  D+  |  S+  |  D+  | ...
    """
    rows = []
    active_total = None
    spi_total = None
    driver_active = None
    umr = umr_path()
    manager_ok = SCRIPT.exists()

    for line in text.splitlines():
        stripped = line.strip()

        if stripped.startswith("| SE") and "|" in stripped:
            parts = [p.strip() for p in stripped.strip("|").split("|")]
            if len(parts) >= 8:
                row_name = parts[0]
                wgps = []
                for i in range(1, 6):
                    state = parts[i].strip()
                    driver = "D" in state and "+" in state
                    spi_only = ("S" in state and "+" in state and not driver)
                    off = not driver and not spi_only
                    enabled = driver or spi_only
                    # UI rule: anything actually routed/effective is active green.
                    # Yellow is reserved for staged/pending user selection, not active SPI routing.
                    color_state = "active" if (driver or spi_only) else "off"
                    wgps.append({
                        "name": f"WGP{i-1}",
                        "state": state,
                        "enabled": enabled,
                        "driver": driver,
                        "spi_only": spi_only,
                        "spi": spi_only or driver,
                        "off": off,
                        "color_state": color_state,
                    })
                cu_text = parts[-1]
                rows.append({"row": row_name, "wgps": wgps, "cus": cu_text})

        if "SPI total" in stripped:
            m = re.search(r"(\d+)\s*/\s*(\d+)", stripped)
            if m:
                spi_total = f"{m.group(1)}/{m.group(2)}"

        if "Driver lock" in stripped:
            m = re.search(r"(\d+)\s*/\s*(\d+)", stripped)
            if m:
                driver_active = f"{m.group(1)}/{m.group(2)}"
                active_total = int(m.group(1))

    return {
        "umr_ok": bool(umr),
        "umr_path": umr,
        "manager_ok": bool(manager_ok),
        "manager_path": str(SCRIPT) if manager_ok else "",
        "spi_total": spi_total or "",
        "driver_active": driver_active or "",
        "active_total": active_total,
        "effective_active": spi_total or driver_active or "",
        "rows": rows,
        "raw": text,
    }

def status_json():
    raw = status()
    return json.dumps(parse_dashboard(raw), indent=2)

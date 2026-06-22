#!/usr/bin/env python3
import json, os, socket, threading, time, shlex, subprocess
from metrics import read_metrics, sensors_json
from config_editor import read_config, parse_points, apply_points, apply_frequency, restore_optimized, service_status
import profiles, governor, cu_manager
from fan_control import set_pwm, set_auto, status as fan_status

SOCKET=os.environ.get("CYAN_SOCKET","/tmp/bagz-blue-gpu-zen-v7-current-card-appfix.sock")
MINF=350; MAXF=2150

PENDING_DIR = "/var/lib/skillfish-tuner"
GOV_PENDING_MARKER = os.path.join(PENDING_DIR, "governor-restart-pending")

def _marker_exists(path):
    try:
        return os.path.exists(path)
    except Exception:
        return False

def _write_marker(path, text):
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(text.rstrip()+"\n")
    except Exception:
        pass

def _remove_marker(path):
    try:
        if os.path.exists(path):
            os.remove(path)
    except Exception:
        pass


def systemd_state(unit):
    """Return a small, UI-friendly status for a systemd unit.

    The GUI uses this to avoid misleading red/yellow icons. Missing optional
    services are reported as not-installed, disabled services as disabled, and
    active services as running.
    """
    try:
        active = subprocess.run(["systemctl", "is-active", unit], text=True,
                                capture_output=True, timeout=5)
        enabled = subprocess.run(["systemctl", "is-enabled", unit], text=True,
                                 capture_output=True, timeout=5)
        a = (active.stdout or active.stderr or "").strip()
        e = (enabled.stdout or enabled.stderr or "").strip()
        if a == "active":
            return "running"
        if e in ("enabled", "static", "generated", "linked", "linked-runtime"):
            return "enabled"
        if "not-found" in e or "could not be found" in e.lower() or active.returncode == 4:
            return "not-installed"
        if e == "disabled":
            return "disabled"
        if a in ("inactive", "failed", "activating", "deactivating"):
            return a
        return e or a or "unknown"
    except Exception:
        return "unknown"


def skillfish_service_statuses(governor_state):
    # Governor may be exposed by either service name depending on the build.
    gov = "running" if governor_state == "active" else systemd_state("cyan-skillfish-governor-smu.service")
    if gov in ("not-installed", "disabled", "unknown"):
        alt = systemd_state("cyan-skillfish-governor.service")
        if alt not in ("not-installed", "disabled", "unknown"):
            gov = alt

    # On Bazzite/rpm-ostree the package can be successfully layered into the
    # next deployment but the service unit is not visible until reboot.  Do not
    # show this as "Not installed"; it is installed/staged and restart-pending.
    if governor_state == "active" or gov == "running":
        _remove_marker(GOV_PENDING_MARKER)
    elif _marker_exists(GOV_PENDING_MARKER):
        gov = "installed-restart-pending"

    cu_primary = systemd_state("skillfish-cu.service")
    return {
        "governor": gov,
        "cu": cu_primary if cu_primary != "not-installed" else systemd_state("bc250-cu-live-manager.service"),
        "fan": systemd_state("skillfish-fan.service"),
    }


def fan_persist_enable(profile_path):
    """Install/enable a small systemd service that reapplies the saved fan profile at boot.

    The profile path is passed from the GUI so the root daemon does not accidentally
    use /root/.config. The service is oneshot and silent; no desktop notifications.
    """
    try:
        profile_path = os.path.abspath(os.path.expanduser(profile_path.strip()))
        app_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        helper_src = os.path.join(app_root, "tools", "skillfish-fan-profile-apply.py")
        helper_dst = "/usr/local/sbin/skillfish-fan-profile-apply.py"
        service_path = "/etc/systemd/system/skillfish-fan.service"
        if not os.path.exists(helper_src):
            return f"ERR fan helper missing: {helper_src}"
        os.makedirs(os.path.dirname(helper_dst), exist_ok=True)
        with open(helper_src, "rb") as src, open(helper_dst, "wb") as dst:
            dst.write(src.read())
        os.chmod(helper_dst, 0o755)
        unit = f"""[Unit]
Description=Skillfish Tuner fan profile restore
After=multi-user.target

[Service]
Type=oneshot
ExecStart=/usr/bin/python3 {helper_dst} {shlex.quote(profile_path)}
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
"""
        with open(service_path, "w", encoding="utf-8") as f:
            f.write(unit)
        subprocess.run(["systemctl", "daemon-reload"], check=False, timeout=20)
        subprocess.run(["systemctl", "enable", "skillfish-fan.service"], check=False, timeout=40)
        return f"OK fan restore enabled at boot using {profile_path}"
    except Exception as e:
        return f"ERR fan restore enable failed: {e}"


def fan_persist_disable():
    try:
        subprocess.run(["systemctl", "disable", "skillfish-fan.service"], check=False, timeout=40)
        subprocess.run(["systemctl", "daemon-reload"], check=False, timeout=20)
        return "OK fan restore disabled"
    except Exception as e:
        return f"ERR fan restore disable failed: {e}"

class D:
    def __init__(self): self.target=2000
    def status(self):
        m=read_metrics(self.target)
        gov_state = service_status()
        m.update({"target": self.target, "service_status": gov_state, "fan_control": fan_status(), "service_health": skillfish_service_statuses(gov_state)})
        return m
    def handle(self,text):
        p=text.strip().split(); cmd=p[0] if p else ""
        if cmd=="status": return json.dumps(self.status())
        if cmd=="reboot":
            subprocess.Popen(["systemctl", "reboot"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return "OK rebooting"
        if cmd=="set": self.target=max(MINF,min(MAXF,int(p[1]))); return apply_frequency(self.target)
        if cmd=="points": return json.dumps(parse_points(read_config()))
        if cmd=="apply_points": return apply_points(json.loads(text.split(" ",1)[1]))
        if cmd=="profiles": return json.dumps(profiles.list_profiles())
        if cmd=="load_profile": return json.dumps(profiles.load(text.split(" ",1)[1] if " " in text else "My Profile"))
        if cmd=="save_profile":
            d=json.loads(text.split(" ",1)[1]); return profiles.save(d["name"],d["max_freq"],d["points"])
        if cmd=="delete_profile": return profiles.delete(text.split(" ",1)[1] if " " in text else "")
        if cmd=="fan_pwm": return set_pwm(int(p[1]))
        if cmd=="fan_auto": return set_auto()
        if cmd=="fan_persist_enable":
            return fan_persist_enable(text.split(" ",1)[1] if " " in text else "")
        if cmd=="fan_persist_disable": return fan_persist_disable()
        if cmd=="fan_test_max":
            out = []
            samples = []
            # First record the current running RPM as the low reference point.
            try:
                rpm = int(read_metrics(self.target).get("fan_rpm", 0) or 0)
            except Exception:
                rpm = 0
            if rpm > 0:
                samples.append(rpm)
                out.append(f"sample rpm={rpm}")
            out.append(set_pwm(255))
            # Give the fan time to ramp up and sample multiple times.
            for _ in range(8):
                time.sleep(1)
                try:
                    rpm = int(read_metrics(self.target).get("fan_rpm", 0) or 0)
                except Exception:
                    rpm = 0
                if rpm > 0:
                    samples.append(rpm)
                out.append(f"sample rpm={rpm}")
            min_rpm = min(samples) if samples else 0
            max_rpm = max(samples) if samples else 0
            out.append(f"MIN_RPM={min_rpm}")
            out.append(f"MAX_RPM={max_rpm}")
            # Keep fan safely high after test, but not necessarily full blast.
            out.append(set_pwm(190))
            return "\n".join(out)
        if cmd=="fan_status": return json.dumps(fan_status(),indent=2)
        if cmd=="debug_sensors": return json.dumps(sensors_json(),indent=2)
        if cmd=="restore_default": return restore_optimized()
        if cmd=="gov_status": return json.dumps(governor.status())
        if cmd=="gov_deploy":
            res = governor.deploy_one_click()
            if "RESTART_REQUIRED=1" in res and not (res.startswith("ERR") or "\nERR" in res):
                _write_marker(GOV_PENDING_MARKER, "Governor installed - restart pending")
            return res
        if cmd=="gov_install":
            res = governor.install()
            if "RESTART_REQUIRED=1" in res and not (res.startswith("ERR") or "\nERR" in res):
                _write_marker(GOV_PENDING_MARKER, "Governor installed - restart pending")
            return res
        if cmd=="gov_start": return governor.enable_start()
        if cmd=="gov_restart": return governor.restart()
        if cmd=="gov_logs": return governor.logs()
        if cmd=="gov_optimize": return governor.optimize()
        if cmd=="cu_install": return cu_manager.install_script()
        if cmd=="cu_umr": return cu_manager.install_umr()
        if cmd=="cu_setup":
            return "\n\n".join([
                "== Install / check UMR ==\n" + cu_manager.install_umr(),
                "== Install / check CU manager ==\n" + cu_manager.install_script(),
                "== CU requirements ==\n" + cu_manager.preflight(),
            ])
        if cmd=="cu_status": return cu_manager.status()
        if cmd=="cu_status_json": return cu_manager.status_json()
        if cmd=="cu_preflight": return cu_manager.preflight()
        if cmd=="cu_dry": return cu_manager.dry_run()
        if cmd=="cu_enable": return governor.stop()+"\n"+cu_manager.enable_all()+"\n"+governor.restart()
        if cmd=="cu_enable_persist": return "ERR Full 40 auto-enable disabled. Select CUs in the grid, then use Apply Selected CU Changes + Save."
        if cmd=="cu_activate_spi": return "ERR Full 40 auto-activation disabled. Select CUs in the grid, then use Apply Selected CU Changes + Save."
        if cmd=="cu_stock": return governor.stop()+"\n"+cu_manager.stock()+"\n"+governor.restart()
        if cmd=="cu_stock_persist": return governor.stop()+"\n"+cu_manager.stock_persistent()+"\n"+governor.restart()
        if cmd=="cu_save": return governor.stop()+"\n"+cu_manager.persist_live_table()+"\n"+governor.restart()+"\nRESTART_REQUIRED=1"
        if cmd=="cu_boot": return cu_manager.install_boot()
        if cmd=="cu_apply": return governor.stop()+"\n"+cu_manager.apply_boot()+"\n"+governor.restart()
        if cmd=="cu_enable_wgp":
            parts=text.split()
            return cu_manager.enable_wgp(parts[1]) if len(parts)>1 else "ERR missing WGP triplet"
        if cmd=="cu_disable_wgp":
            parts=text.split()
            return cu_manager.disable_wgp(parts[1]) if len(parts)>1 else "ERR missing WGP triplet"
        if cmd=="cu_persist":
            try:
                payload=json.loads(text.split(" ",1)[1]) if " " in text else {}
                return governor.stop()+"\n"+cu_manager.persist_disable_mask(payload.get("disable_mask", []), payload.get("expected_active"))+"\n"+governor.restart()
            except Exception as e:
                return "ERR cu_persist failed: "+str(e)
        if cmd=="cu_apply_selected_live":
            try:
                payload=json.loads(text.split(" ",1)[1]) if " " in text else {}
                return governor.stop()+"\n"+cu_manager.apply_selected_live(payload.get("staged", {}), payload.get("expected_active"))+"\n"+governor.restart()
            except Exception as e:
                return "ERR cu_apply_selected_live failed: "+str(e)
        if cmd=="cu_apply_unlock":
            try:
                payload=json.loads(text.split(" ",1)[1]) if " " in text else {}
                return governor.stop()+"\n"+cu_manager.install_driver_unlock_patch(payload.get("disable_mask", []), payload.get("expected_active"))+"\n"+governor.restart()
            except Exception as e:
                return "ERR cu_apply_unlock failed: "+str(e)
        if cmd=="cu_uninstall": return cu_manager.uninstall_boot()
        return "ERR unknown command"
    def client(self,c):
        # A GTK refresh/action can close the Unix socket before the helper has
        # finished building the response.  That is normal client-side behaviour
        # and must not crash the daemon thread.
        with c:
            try:
                data=c.recv(262144).decode(errors="replace").strip()
                if not data:
                    return
                response=(self.handle(data)+"\n").encode()
                try:
                    c.sendall(response)
                except (BrokenPipeError, ConnectionResetError):
                    return
            except (BrokenPipeError, ConnectionResetError):
                return
            except Exception as e:
                try:
                    c.sendall(("ERR daemon client failed: "+str(e)+"\n").encode())
                except Exception:
                    return
    def run(self):
        if os.path.exists(SOCKET):
            try:
                os.remove(SOCKET)
            except FileNotFoundError:
                pass
            except PermissionError:
                # If another root-owned helper is still alive, fail clearly instead of
                # creating a second broken instance. The launcher will normally reuse it.
                raise RuntimeError(f"Socket already exists and cannot be removed: {SOCKET}")
        s=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM)
        s.bind(SOCKET)
        os.chmod(SOCKET,0o666)
        s.listen(16)
        print(f"helper {SOCKET}",flush=True)
        while True:
            c,_=s.accept(); threading.Thread(target=self.client,args=(c,),daemon=True).start()
if __name__=="__main__": D().run()

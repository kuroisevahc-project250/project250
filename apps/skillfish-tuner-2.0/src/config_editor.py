from pathlib import Path
import re
import shutil
import time
from common import run

SERVICES = ["cyan-skillfish-governor-smu", "cyan-skillfish-governor"]
SERVICE = SERVICES[0]
CONFIG_PATH = Path("/etc/cyan-skillfish-governor-smu/config.toml")
APP_DIR = Path(__file__).resolve().parent.parent
OPT_CONFIG = APP_DIR / "configs" / "bc250-optimized-governor.toml"


def _sudo_write(path, text):
    proc = __import__('subprocess').run(
        ["sudo", "tee", str(path)], input=text, text=True,
        capture_output=True, timeout=30
    )
    if proc.returncode != 0:
        raise PermissionError((proc.stderr or proc.stdout or f"tee rc={proc.returncode}").strip())


def _active_service():
    for svc in SERVICES:
        rc, msg = run(["systemctl", "is-active", svc], 5)
        if rc == 0 or (msg or "").strip() in ("active", "activating"):
            return svc
    for svc in SERVICES:
        rc, msg = run(["systemctl", "is-enabled", svc], 5)
        if rc == 0 or (msg or "").strip() == "enabled":
            return svc
    return SERVICES[0]


def ensure_config():
    run(["sudo", "install", "-d", "-m", "0755", str(CONFIG_PATH.parent)], 30)
    if not CONFIG_PATH.exists() and OPT_CONFIG.exists():
        _sudo_write(CONFIG_PATH, OPT_CONFIG.read_text())

def backup_config():
    ensure_config()
    if CONFIG_PATH.exists():
        backup = CONFIG_PATH.with_suffix(f".toml.bak-{int(time.time())}")
        run(["sudo", "cp", str(CONFIG_PATH), str(backup)], 30)
        return str(backup)
    return ""

def read_config():
    ensure_config()
    try:
        return CONFIG_PATH.read_text()
    except Exception:
        return ""

def write_config(text):
    backup = backup_config()
    _sudo_write(CONFIG_PATH, text)
    return backup

def stop_service():
    svc=_active_service()
    rc, msg = run(["sudo", "systemctl", "stop", svc], 30)
    if rc == 0:
        return f"OK sudo systemctl stop {svc}"
    return msg or f"ERR stop rc={rc}"

def restart_service():
    svc=_active_service()
    rc, msg = run(["sudo", "systemctl", "restart", svc], 30)
    if rc == 0:
        return f"OK sudo systemctl restart {svc}"
    return msg or f"ERR restart rc={rc}"

def service_status():
    svc=_active_service()
    rc, msg = run(["systemctl", "is-active", svc], 5)
    return f"{svc}: {msg or 'unknown'}"

def set_range(text, min_freq=350, max_freq=2000):
    if "[frequency-range]" not in text:
        return text.rstrip() + f"\n\n[frequency-range]\nmin = {int(min_freq)}\nmax = {int(max_freq)}\n"

    def repl(match):
        block = match.group(0)
        if re.search(r"(?m)^\s*min\s*=", block):
            block = re.sub(r"(?m)^\s*min\s*=.*$", f"min = {int(min_freq)}", block)
        else:
            block += f"\nmin = {int(min_freq)}"

        if re.search(r"(?m)^\s*max\s*=", block):
            block = re.sub(r"(?m)^\s*max\s*=.*$", f"max = {int(max_freq)}", block)
        else:
            block += f"\nmax = {int(max_freq)}"

        return block

    return re.sub(r"(?ms)^\[frequency-range\].*?(?=^\[|^\[\[|\Z)", repl, text, count=1)

def parse_points(text):
    points = []
    blocks = re.findall(r"(?ms)^\[\[safe-points\]\]\s*(.*?)(?=^\[\[safe-points\]\]|^\[|\Z)", text)
    for block in blocks:
        fm = re.search(r"(?m)^\s*frequency\s*=\s*(\d+)", block)
        vm = re.search(r"(?m)^\s*voltage\s*=\s*(\d+)", block)
        if fm and vm:
            points.append({"frequency": int(fm.group(1)), "voltage": int(vm.group(1))})
    return points

def validate_points(points):
    if not points:
        return False, "safe-points cannot be empty"

    last_f = -1
    last_v = -1
    for p in points:
        f = int(p["frequency"])
        v = int(p["voltage"])

        if f <= last_f:
            return False, "frequencies must increase"
        if v < last_v:
            return False, f"voltage decreases at {f} MHz"
        if v < 700 or v > 1250:
            return False, f"voltage out of range: {v} mV (allowed 700-1250 mV)"

        last_f = f
        last_v = v

    return True, "OK"

def replace_points(text, points):
    ok, msg = validate_points(points)
    if not ok:
        raise ValueError(msg)

    rendered = []
    for p in points:
        rendered.append("[[safe-points]]")
        rendered.append(f"frequency = {int(p['frequency'])}")
        rendered.append(f"voltage = {int(p['voltage'])}")
        rendered.append("")

    text2 = re.sub(r"(?ms)^\[\[safe-points\]\]\s*.*?(?=^\[\[safe-points\]\]|^\[|\Z)", "", text)
    return text2.rstrip() + "\n\n" + "\n".join(rendered).rstrip() + "\n"

def apply_points(points):
    text = read_config()
    ok, msg = validate_points(points)
    if not ok:
        return f"ERR {msg}"

    stop = stop_service()
    backup = write_config(replace_points(text, points))
    restart = restart_service()

    return f"{stop}\nOK safe-points written backup={backup}\n{restart}"

def apply_frequency(max_freq):
    text = read_config()

    stop = stop_service()
    backup = write_config(set_range(text, 350, int(max_freq)))
    restart = restart_service()

    return f"{stop}\nOK max={int(max_freq)} backup={backup}\n{restart}"

def restore_optimized():
    stop = stop_service()
    backup = backup_config()
    _sudo_write(CONFIG_PATH, OPT_CONFIG.read_text())
    restart = restart_service()

    return f"{stop}\nOK restored optimized backup={backup}\n{restart}"

import subprocess
from pathlib import Path

def run(cmd, timeout=60, cwd=None):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, cwd=cwd)
        return r.returncode, (r.stdout or r.stderr or "").strip()
    except Exception as e:
        return 999, str(e)

def read_text(path):
    try:
        return Path(path).read_text().strip()
    except Exception:
        return ""

def write_text(path, value):
    try:
        Path(path).write_text(str(value))
        return True, "OK"
    except Exception as e:
        return False, str(e)

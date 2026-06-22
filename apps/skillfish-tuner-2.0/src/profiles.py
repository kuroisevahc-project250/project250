import json, re
from pathlib import Path
APP=Path(__file__).resolve().parent.parent
DEFAULT=APP/"profiles"/"default-profile.json"
CUSTOM=APP/"profiles"/"custom"
def clean(n): return re.sub(r"[^A-Za-z0-9_. -]+","_", (n or "").strip())[:64]
def list_profiles():
    CUSTOM.mkdir(parents=True, exist_ok=True)
    out=[json.loads(DEFAULT.read_text())]
    for p in sorted(CUSTOM.glob("*.json")):
        try: out.append(json.loads(p.read_text()))
        except Exception: pass
    return out
def load(name):
    n=clean(name)
    if not n or n.lower() in ("my profile","default"): return json.loads(DEFAULT.read_text())
    p=CUSTOM/f"{n}.json"
    if p.exists(): return json.loads(p.read_text())
    raise FileNotFoundError(n)
def save(name,max_freq,points):
    n=clean(name)
    if not n: return "ERR name empty"
    CUSTOM.mkdir(parents=True, exist_ok=True)
    (CUSTOM/f"{n}.json").write_text(json.dumps({"name":n,"min_freq":350,"max_freq":int(max_freq),"points":points},indent=2))
    return f"OK saved {n}"
def delete(name):
    n=clean(name)
    if n.lower() in ("my profile","default"): return "ERR cannot delete default"
    p=CUSTOM/f"{n}.json"
    if p.exists(): p.unlink(); return f"OK deleted {n}"
    return "ERR profile not found"

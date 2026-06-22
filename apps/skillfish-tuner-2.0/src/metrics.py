import json, re, subprocess
from pathlib import Path
from common import read_text

CARD = Path("/sys/class/drm/card1/device")

def sensors_json():
    try:
        r=subprocess.run(["sensors","-j"],capture_output=True,text=True,timeout=1.5)
        return json.loads(r.stdout) if r.returncode==0 else {}
    except Exception: return {}

NCT6686_SENSOR_CHIP = "nct6686-isa-0a20"
NCT6686_FAN_LABEL = "Pump Fan"
NCT6686_FAN_FALLBACKS = ("Pump Fan", "fan2", "fan1", "fan3")

def chip(data, name):
    name=name.lower()
    for k,v in data.items():
        if name in k.lower(): return v
    return {}

def chip_exact_or(data, exact_name, fallback_name):
    # Prefer the user's BC-250 sensor chip, but fall back so the app still works on other boards.
    wanted=exact_name.lower()
    for k,v in data.items():
        if k.lower()==wanted: return v
    return chip(data, fallback_name)

def val(block, feature):
    if not isinstance(block, dict): return 0.0
    f=block.get(feature)
    if isinstance(f, dict):
        for k,v in f.items():
            if k.endswith("input"):
                try: return float(v)
                except Exception: pass
    return 0.0

def match(block, text):
    text=text.lower()
    for n,f in (block or {}).items():
        if text in n.lower() and isinstance(f,dict):
            for k,v in f.items():
                if k.endswith("input"):
                    try: return float(v)
                    except Exception: pass
    return 0.0

def fan_rpm_from_nct(block):
    # lm-sensors reports the BC-250 pump tachometer as:
    # nct6686-isa-0a20 / "Pump Fan" / fan*_input.
    for feature in NCT6686_FAN_FALLBACKS:
        rpm = val(block, feature) or match(block, feature)
        if rpm:
            return int(rpm)
    return 0

def dpm_clock(path):
    t=read_text(path)
    for line in t.splitlines():
        if "*" in line:
            m=re.findall(r"(\d+)\s*Mhz", line, re.I)
            if m: return int(m[-1])
    return 0

def amdgpu_hwmon():
    for hw in sorted((CARD/"hwmon").glob("hwmon*")):
        if read_text(hw/"name").lower()=="amdgpu": return hw
    for hw in sorted((CARD/"hwmon").glob("hwmon*")): return hw
    return None

def hw_label(hw, prefix, label):
    if not hw: return 0.0
    for l in hw.glob(f"{prefix}*_label"):
        if read_text(l).lower()==label.lower():
            n=l.name.replace(prefix,"").replace("_label","")
            try: return float(read_text(hw/f"{prefix}{n}_input"))
            except Exception: return 0.0
    return 0.0

def gpu_hw():
    hw=amdgpu_hwmon()
    temp=hw_label(hw,"temp","edge")/1000 if hw else 0
    volt=hw_label(hw,"in","vddgfx") if hw else 0
    if 0<volt<10: volt*=1000
    power=hw_label(hw,"power","PPT") if hw else 0
    if power>10000: power/=1_000_000
    return temp,volt,power

def read_metrics(last_target=0):
    data=sensors_json()
    nct=chip_exact_or(data,NCT6686_SENSOR_CHIP,"nct6686"); cpu=chip(data,"k10temp"); nvme=chip(data,"nvme"); gpu=chip(data,"amdgpu")
    gt,gv,gp=gpu_hw()
    if not gt: gt=val(gpu,"edge")
    if not gv:
        gv=val(gpu,"vddgfx")
        if 0<gv<10: gv*=1000
    if not gp: gp=val(gpu,"PPT") or match(gpu,"ppt")
    return {
        "freq": dpm_clock(CARD/"pp_dpm_sclk") or int(last_target or 0),
        "mclk": dpm_clock(CARD/"pp_dpm_mclk"),
        "temp": gt, "voltage": gv, "power": gp,
        "fan_rpm": fan_rpm_from_nct(nct),
        "fan_sensor": NCT6686_SENSOR_CHIP,
        "fan_label": NCT6686_FAN_LABEL,
        "cpu_temp": val(cpu,"Tctl") or match(cpu,"tctl"),
        "ssd_temp": val(nvme,"Composite") or match(nvme,"composite"),
    }

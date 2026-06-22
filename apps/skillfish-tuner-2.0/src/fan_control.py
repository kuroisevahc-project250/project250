from pathlib import Path
from common import read_text, write_text
BASE=Path("/sys/class/hwmon")
NCT6686_SENSOR_CHIP="nct6686-isa-0a20"
PUMP_FAN_LABEL="Pump Fan"
def nct():
    # /sys exposes the chip name as nct6686; lm-sensors shows it as nct6686-isa-0a20.
    for h in sorted(BASE.glob("hwmon*")):
        if "nct6686" in read_text(h/"name").lower(): return h
    return None
def status():
    h=nct()
    return {"nct_hwmon":str(h) if h else "", "sensor_chip":NCT6686_SENSOR_CHIP, "fan_label":PUMP_FAN_LABEL, "pwm2_exists": bool(h and (h/"pwm2").exists())}
def set_pwm(v):
    h=nct()
    if not h: return "ERR nct6686 hwmon not found"
    pwm=h/"pwm2"; en=h/"pwm2_enable"
    if not pwm.exists(): return "ERR pwm2 not exposed/writable"
    if en.exists():
        ok,msg=write_text(en,"1")
        if not ok: return f"ERR pwm2_enable: {msg}"
    ok,msg=write_text(pwm, str(max(0,min(255,int(v)))))
    return f"OK pwm2={v}" if ok else f"ERR pwm2: {msg}"


def set_auto():
    h=nct()
    if not h: return "ERR nct6686 hwmon not found"
    en=h/"pwm2_enable"
    if not en.exists(): return "ERR pwm2_enable not exposed/writable"
    # hwmon convention is commonly 2=automatic on many controllers; if unsupported, the write fails safely.
    ok,msg=write_text(en,"2")
    return "OK pwm2_enable=auto" if ok else f"ERR pwm2_enable auto: {msg}"

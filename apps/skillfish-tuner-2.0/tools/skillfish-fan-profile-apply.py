#!/usr/bin/env python3
"""Apply the saved Skillfish fan profile once.

This is intentionally small and separate so it can be used later by a systemd user
service without keeping the full GUI open.
"""
import json, os, time, sys
from pathlib import Path

PROFILE = Path(sys.argv[1]).expanduser() if len(sys.argv) > 1 else Path(os.environ.get("SKILLFISH_FAN_PROFILE", str(Path.home()/".config"/"skillfish-tuner"/"fan-profile.json"))).expanduser()
HWMON = Path('/sys/class/hwmon')

def read(path):
    try: return Path(path).read_text().strip()
    except Exception: return ''

def nct():
    for h in sorted(HWMON.glob('hwmon*')):
        if 'nct6686' in read(h/'name').lower():
            return h
    return None

def write(path, text):
    Path(path).write_text(str(text))

def main():
    if not PROFILE.exists():
        print('ERR no saved fan profile')
        return 1
    data=json.loads(PROFILE.read_text())
    h=nct()
    if not h:
        print('ERR nct6686 hwmon not found')
        return 2
    if data.get('mode') == 'auto':
        write(h/'pwm2_enable','2')
        print('OK fan auto')
        return 0
    raw=int(data.get('applied_pwm_raw', 128))
    raw=max(0,min(255,raw))
    if (h/'pwm2_enable').exists(): write(h/'pwm2_enable','1')
    write(h/'pwm2', str(raw))
    print(f'OK applied saved fan pwm raw={raw}')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())

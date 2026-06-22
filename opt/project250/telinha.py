import os
import time
import serial

PORT = "/dev/ttyUSB0"
BAUD = 115200

# Liga overlay quando passar disso
CPU_ON = 50
GPU_ON = 45

# Volta para idle quando cair abaixo disso
CPU_OFF = 46
GPU_OFF = 41

def find_hwmon(name):
    base = "/sys/class/hwmon"
    for hw in os.listdir(base):
        path = os.path.join(base, hw)
        try:
            with open(os.path.join(path, "name")) as f:
                if f.read().strip() == name:
                    return path
        except Exception:
            pass
    return None

def read_temp(sensor_path):
    try:
        with open(os.path.join(sensor_path, "temp1_input")) as f:
            return round(int(f.read().strip()) / 1000)
    except Exception:
        return 0

def should_show_overlay(cpu, gpu, last_mode):
    if last_mode == "OVERLAY":
        # Só volta para idle depois de esfriar bem
        return cpu > CPU_OFF or gpu > GPU_OFF

    # Só entra no overlay quando realmente esquentar
    return cpu >= CPU_ON or gpu >= GPU_ON

gpu_sensor = find_hwmon("amdgpu")
cpu_sensor = find_hwmon("k10temp")

if not gpu_sensor or not cpu_sensor:
    print("Sensores não encontrados")
    print("GPU:", gpu_sensor)
    print("CPU:", cpu_sensor)
    raise SystemExit(1)

print("GPU sensor:", gpu_sensor)
print("CPU sensor:", cpu_sensor)

ser = serial.Serial(PORT, BAUD, timeout=1)
time.sleep(2)

last_mode = None
last_cpu = None
last_gpu = None

try:
    while True:
        gpu = read_temp(gpu_sensor)
        cpu = read_temp(cpu_sensor)

        overlay = should_show_overlay(cpu, gpu, last_mode)

        if not overlay:
            if last_mode != "IDLE":
                print("IDLE")
                ser.write(b"IDLE\n")
                ser.flush()
                last_mode = "IDLE"
                last_cpu = None
                last_gpu = None

            time.sleep(2)
            continue

        if last_mode != "OVERLAY" or cpu != last_cpu or gpu != last_gpu:
            msg = f"OVERLAY|CPU:{cpu}|GPU:{gpu}\n"
            print(msg.strip())
            ser.write(msg.encode("utf-8"))
            ser.flush()

            last_mode = "OVERLAY"
            last_cpu = cpu
            last_gpu = gpu

        time.sleep(2)

except KeyboardInterrupt:
    print("Saindo... voltando para IDLE")
    ser.write(b"IDLE\n")
    ser.flush()
    time.sleep(0.5)
    ser.close()

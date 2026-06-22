#!/usr/bin/env python3
import json
import math
import os
import socket
import sys
import time
import threading
import subprocess
import shutil
import tarfile
import tempfile
import shlex

import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw, GLib, Gio, Gdk, Pango

SOCKET = os.environ.get("CYAN_SOCKET") or os.environ.get("bagz_SOCKET", "/tmp/bagz-blue-gpu-zen-v7-current-card-appfix.sock")
APPDIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BAGZ_LOGO = os.path.join(APPDIR, "assets", "bagz_fishbone_logo_transparent.png")
BAGZ_FAN_IMAGE1 = os.path.join(APPDIR, "assets", "bagz_fan_image1.png")
BAGZ_FAN_REFERENCE = os.path.join(APPDIR, "assets", "bagz_fan_reference.png")

CSS = """
window { background: #020712; }
.root {
  background: radial-gradient(circle at 15% 5%, alpha(#00aaff,0.16), transparent 28%),
              linear-gradient(135deg, #020712, #061322 52%, #02050a);
}
.sidebar {
  background: linear-gradient(180deg, alpha(#06111f,0.985), alpha(#02050b,0.985));
  border-right: 1px solid alpha(#16a7ff,0.30);
  padding: 14px;
  box-shadow: 0 0 28px alpha(#009dff,0.10);
}
.skillfish-logo {
  font-size: 46px;
  font-weight: 900;
  letter-spacing: 2px;
  color: #19d7ff;
  text-shadow: 0 0 26px alpha(#00b7ff,0.85);
}
.skillfish-logo-sub {
  font-size: 12px;
  font-weight: 900;
  letter-spacing: 6px;
  color: alpha(#dff8ff,0.86);
  text-shadow: 0 0 16px alpha(#00b7ff,0.45);
}
.logo-main {
  font-size: 31px;
  font-weight: 900;
  letter-spacing: 5px;
  color: #16b7ff;
  text-shadow: 0 0 18px alpha(#00b7ff,0.70);
}
.bagz-title {
  font-size: 31px;
  font-weight: 900;
  letter-spacing: 6px;
  color: #19d7ff;
  text-shadow: 0 0 24px alpha(#00b7ff,0.85);
}
.bagz-subtitle {
  font-size: 10px;
  font-weight: 900;
  letter-spacing: 3px;
  color: alpha(#dff8ff,0.86);
  text-shadow: 0 0 16px alpha(#00b7ff,0.45);
}
.logo-sub {
  font-size: 10px;
  font-weight: 900;
  letter-spacing: 4px;
  color: alpha(white,0.72);
}
.nav-btn {
  border-radius: 13px;
  padding: 9px;
  font-weight: 900;
  background: transparent;
}
.nav-btn-active {
  background: linear-gradient(90deg, alpha(#006dff,0.78), alpha(#071c34,0.72));
  border: 1px solid alpha(#19b7ff,0.95);
  box-shadow: 0 0 20px alpha(#00aaff,0.46), inset 0 0 16px alpha(#00aaff,0.16);
}
.card {
  border-radius: 15px;
  padding: 9px;
  background: linear-gradient(145deg, alpha(#0b1d31,0.95), alpha(#06101c,0.91));
  border: 1px solid alpha(#18aaff,0.34);
  box-shadow: 0 12px 30px alpha(black,0.30), 0 0 18px alpha(#009dff,0.10);
}
.card-green {
  border-radius: 15px;
  padding: 9px;
  background: linear-gradient(145deg, alpha(#07351c,0.68), alpha(#04140b,0.82));
  border: 1px solid alpha(#27ff55,0.72);
  box-shadow: 0 0 30px alpha(#27ff55,0.25);
}

.task-result-card {
  min-height: 54px;
  padding: 8px 10px;
  border-radius: 14px;
}
.task-result-success {
  background: alpha(#23ff4f,0.16);
  border: 1px solid alpha(#23ff4f,0.72);
  box-shadow: 0 0 20px alpha(#23ff4f,0.20);
}
.task-result-error {
  background: alpha(#ff4b4b,0.16);
  border: 1px solid alpha(#ff4b4b,0.72);
  box-shadow: 0 0 20px alpha(#ff4b4b,0.20);
}
.task-result-warning {
  background: alpha(#ffd84a,0.16);
  border: 1px solid alpha(#ffd84a,0.72);
  box-shadow: 0 0 20px alpha(#ffd84a,0.20);
}
.task-result-working {
  background: alpha(#00aaff,0.16);
  border: 1px solid alpha(#00aaff,0.72);
  box-shadow: 0 0 20px alpha(#00aaff,0.20);
}
.task-result-label {
  font-size: 14px;
  font-weight: 900;
  letter-spacing: .5px;
}
.title {
  font-size: 14px;
  font-weight: 900;
  letter-spacing: 1px;
  color: alpha(white,0.86);
}
.small {
  font-size: 10px;
  font-weight: 900;
  letter-spacing: .7px;
  color: alpha(white,0.70);
}
.big {
  font-size: 32px;
  font-weight: 900;
  color: white;
}
.hero {
  font-size: 36px;
  font-weight: 900;
  color: white;
}
.blue { color: #00b7ff; }
.green { color: #3cff58; }
.yellow { color: #ffd84a; }
.red { color: #ff4b4b; }
.badge-ok {
  border-radius: 10px;
  padding: 8px 15px;
  background: alpha(#23ff4f,0.14);
  border: 1px solid alpha(#23ff4f,0.56);
  color: #e7ffec;
  font-weight: 900;
}
.badge-warn {
  border-radius: 10px;
  padding: 8px 15px;
  background: alpha(#ffd84a,0.14);
  border: 1px solid alpha(#ffd84a,0.56);
  color: #fff4c2;
  font-weight: 900;
}
.badge-error {
  border-radius: 10px;
  padding: 8px 15px;
  background: alpha(#ff4b4b,0.14);
  border: 1px solid alpha(#ff4b4b,0.56);
  color: #ffd0d0;
  font-weight: 900;
}
.clock-mini-card {
  border-radius: 12px;
  padding: 9px;
  background: alpha(#081524,0.62);
  border: 1px solid alpha(#22b5ff,0.22);
}
.metric {
  border-radius: 13px;
  padding: 9px;
  background: linear-gradient(145deg, alpha(#0f2034,0.94), alpha(#07111d,0.92));
  border: 1px solid alpha(#18aaff,0.34);
  box-shadow: 0 0 16px alpha(#009dff,0.12), inset 0 0 18px alpha(#009dff,0.05);
}
.metric-number {
  font-size: 25px;
  font-weight: 900;
  color: white;
}
.metric-unit {
  color: #00b7ff;
  font-size: 13px;
  font-weight: 800;
}
.blue-button {
  background: linear-gradient(90deg, #005eff, #06b8ff);
  color: white;
  font-weight: 900;
  box-shadow: 0 0 18px alpha(#009dff,0.38), inset 0 0 14px alpha(#bdefff,0.14);
}
.outline-button {
  border: 1px solid alpha(#22b5ff,0.38);
  background: alpha(#081524,0.82);
  font-weight: 800;
  box-shadow: inset 0 0 12px alpha(#00aaff,0.08);
}
.profile-chip {
  border-radius: 12px;
  padding: 10px 14px;
  background: alpha(#081524,0.82);
  border: 1px solid alpha(#22b5ff,0.30);
  font-weight: 900;
}
.service-ok { color: #3cff58; font-weight: 900; }
.service-warn { color: #b8c0cc; font-weight: 900; }
.service-bad { color: #ff4b4b; font-weight: 900; }
.pending-badge {
  border-radius: 10px;
  padding: 8px 15px;
  background: alpha(#ffd84a,0.16);
  border: 1px solid alpha(#ffd84a,0.58);
  color: #fff0a8;
  font-weight: 900;
}
.pending-badge-clear {
  border-radius: 10px;
  padding: 8px 15px;
  background: alpha(#23ff4f,0.10);
  border: 1px solid alpha(#23ff4f,0.32);
  color: alpha(#e7ffec,0.86);
  font-weight: 900;
}
.mono { font-family: monospace; }
.mode-toggle { margin-top: 4px; margin-bottom: 4px; }
.red-button {
  color: #ff4b4b;
  border: 1px solid alpha(#ff4b4b,0.55);
}
.pulse-button {
  box-shadow: 0 0 28px alpha(#00a6ff,0.48), inset 0 0 24px alpha(#bdefff,0.18);
}
.install-busy-button {
  background: linear-gradient(90deg, alpha(#006dff,0.95), alpha(#00d7ff,0.88));
  color: white;
  font-weight: 900;
  box-shadow: 0 0 30px alpha(#00d7ff,0.58), inset 0 0 22px alpha(#ffffff,0.16);
}
.install-done-button {
  background: alpha(#23ff4f,0.20);
  border: 1px solid alpha(#23ff4f,0.70);
  box-shadow: 0 0 22px alpha(#23ff4f,0.34);
}
.cu-cell {
  min-width: 64px;
  min-height: 32px;
  border-radius: 8px;
  padding: 3px 6px;
}
.cu-active {
  background: alpha(#27ff55,0.18);
  border: 1px solid alpha(#27ff55,0.72);
  box-shadow: 0 0 14px alpha(#27ff55,0.24);
}
.cu-spi {
  /* SPI-routed/effective CUs are ACTIVE and must be green, not yellow. */
  background: alpha(#27ff55,0.18);
  border: 1px solid alpha(#27ff55,0.72);
  box-shadow: 0 0 14px alpha(#27ff55,0.24);
}
.cu-off {
  background: alpha(#ff4b4b,0.16);
  border: 1px solid alpha(#ff4b4b,0.70);
}
.cu-staged {
  border: 2px solid #00a6ff;
  box-shadow: 0 0 22px alpha(#00a6ff,0.42);
}

.cu-summary-gauge {
  border-radius: 14px;
  padding: 3px;
  background: alpha(#081524,0.92);
  border: 1px solid alpha(#22b5ff,0.28);
}
.cu-gauge-active {
  min-height: 26px;
  border-radius: 10px 0 0 10px;
  background: alpha(#27ff55,0.62);
  border: 1px solid alpha(#27ff55,0.75);
  color: #eaffee;
  font-weight: 900;
}
.cu-gauge-disabled {
  min-height: 26px;
  border-radius: 0 10px 10px 0;
  background: alpha(#ff4b4b,0.56);
  border: 1px solid alpha(#ff4b4b,0.78);
  color: #ffe0e0;
  font-weight: 900;
}
.cu-gauge-caption {
  font-size: 12px;
  font-weight: 900;
  letter-spacing: .7px;
  color: alpha(white,0.78);
}

.core-steps-panel {
  border-radius: 14px;
  padding: 10px;
  background: alpha(#06111d,0.94);
  border: 1px solid alpha(#00a6ff,0.42);
  box-shadow: 0 0 22px alpha(#00a6ff,0.16), inset 0 0 18px alpha(#00a6ff,0.08);
}
.core-step-small {
  font-size: 10px;
  font-weight: 900;
  color: alpha(white,0.76);
}
.fan-curve-panel {
  border-radius: 14px;
  padding: 9px;
  background: alpha(#06111d,0.94);
  border: 1px solid alpha(#00a6ff,0.38);
}
.chart-card {
  border-radius: 12px;
  padding: 8px;
  background: alpha(#020914,0.86);
  border: 1px solid alpha(#00a6ff,0.42);
  box-shadow: 0 0 24px alpha(#00a6ff,0.16), inset 0 0 22px alpha(#00a6ff,0.06);
}
.mono { font-family: monospace; font-size: 12px; }
.footer {
  border-radius: 10px;
  padding: 8px 10px;
  background: alpha(#07111d,0.90);
  border: 1px solid alpha(#49b7ff,0.18);
}
"""

def call(cmd):
    sock = None
    try:
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        # Package installs, rpm-ostree layering, governor deployment and CU writes
        # can legitimately take longer than the old 14s GUI timeout.  The helper
        # already has its own command timeouts, so the GUI must wait long enough
        # to receive the real result instead of showing a false timeout error.
        long_cmds = (
            "cu_umr", "cu_enable", "cu_enable_persist", "cu_activate_spi", "cu_stock", "cu_stock_persist", "cu_save", "cu_boot", "cu_apply",
            "cu_enable_wgp", "cu_disable_wgp", "cu_status", "cu_status_json", "cu_persist", "cu_apply_unlock", "cu_apply_selected_live",
            "gov_deploy", "gov_install", "gov_start", "gov_restart", "gov_optimize",
            "fan_test_max", "fan_persist_enable", "fan_persist_disable",
        )
        parts = cmd.strip().split()
        sock.settimeout(900 if parts and parts[0] in long_cmds else 30)
        sock.connect(SOCKET)
        sock.sendall(cmd.encode())
        try:
            sock.shutdown(socket.SHUT_WR)
        except OSError:
            pass
        chunks = []
        while True:
            part = sock.recv(524288)
            if not part:
                break
            chunks.append(part)
        return b"".join(chunks).decode(errors="replace").strip()
    except Exception as e:
        return f"ERR {e}"
    finally:
        if sock is not None:
            try:
                sock.close()
            except Exception:
                pass

class Sparkline(Gtk.DrawingArea):
    """
    Smooth telemetry sparkline.

    Sensor polling is intentionally slow and off-thread; this widget renders at
    ~60 FPS and animates toward each new sample.  The line is drawn as a
    Catmull-Rom style cubic curve with a subtle filled area so temp/power/fan
    cards feel smooth instead of jumping every sensor refresh.
    """
    def __init__(self):
        super().__init__()
        self.values = []
        self.display_values = []
        self.target_last = None
        self.set_content_width(110)
        self.set_content_height(34)
        self.set_draw_func(self.draw)
        self._last_frame = time.monotonic()
        GLib.timeout_add(1000 // 60, self.tick)

    def push(self, v):
        try:
            v = float(v)
            self.target_last = v
            self.values.append(v)
            # 60 samples at 1 Hz = 60 second history.
            self.values = self.values[-60:]
            if not self.display_values:
                self.display_values = list(self.values)
            elif len(self.display_values) < len(self.values):
                self.display_values.append(self.display_values[-1])
            self.display_values = self.display_values[-len(self.values):]
        except Exception:
            pass

    def tick(self):
        now = time.monotonic()
        dt = max(0.001, min(0.050, now - getattr(self, '_last_frame', now)))
        self._last_frame = now
        if self.values:
            # Time-compensated easing: smooth enough for meters, responsive enough for tuning.
            alpha = min(0.18, 1.0 - pow(0.002, dt))
            if len(self.display_values) != len(self.values):
                self.display_values = list(self.values)
            else:
                for i, target in enumerate(self.values):
                    self.display_values[i] += (target - self.display_values[i]) * alpha
            self.queue_draw()
        return True

    def _point(self, i, v, mn, rng, w, h):
        x = i * w / max(1, len(self.display_values) - 1)
        y = h - ((v - mn) / rng) * (h - 8) - 4
        return x, y

    def draw(self, area, cr, w, h):
        vals = self.display_values if len(self.display_values) >= 2 else self.values
        if len(vals) < 2:
            return
        mn, mx = min(vals), max(vals)
        pad = max(1.0, (mx - mn) * 0.08)
        mn -= pad; mx += pad
        rng = max(1.0, mx - mn)
        pts = [self._point(i, v, mn, rng, w, h) for i, v in enumerate(vals)]

        try:
            cr.set_antialias(1)
        except Exception:
            pass

        # Filled area.
        cr.new_path()
        cr.move_to(pts[0][0], h)
        cr.line_to(pts[0][0], pts[0][1])
        self._smooth_path(cr, pts)
        cr.line_to(pts[-1][0], h)
        cr.close_path()
        cr.set_source_rgba(0.0, 0.72, 1.0, 0.11)
        cr.fill()

        # Smoothed line.
        cr.new_path()
        cr.move_to(*pts[0])
        self._smooth_path(cr, pts)
        cr.set_source_rgba(0.12, 0.86, 1.0, 0.98)
        cr.set_line_width(2.05)
        cr.set_line_cap(1)
        cr.set_line_join(1)
        cr.stroke()

    def _smooth_path(self, cr, pts):
        # Catmull-Rom to Bezier conversion, clamped by available points.
        if len(pts) < 2:
            return
        for i in range(len(pts) - 1):
            p0 = pts[max(0, i - 1)]
            p1 = pts[i]
            p2 = pts[i + 1]
            p3 = pts[min(len(pts) - 1, i + 2)]
            c1 = (p1[0] + (p2[0] - p0[0]) / 6.0, p1[1] + (p2[1] - p0[1]) / 6.0)
            c2 = (p2[0] - (p3[0] - p1[0]) / 6.0, p2[1] - (p3[1] - p1[1]) / 6.0)
            cr.curve_to(c1[0], c1[1], c2[0], c2[1], p2[0], p2[1])

class FanWidget(Gtk.DrawingArea):
    """
    Realistic clean RGB PC fan:
    static case frame + ring, animated blades, no logo on center hub.
    """
    def __init__(self):
        super().__init__()
        self.rpm = 0
        self.display_rpm = 0.0
        self.angle = 0.0
        self._last_frame = time.monotonic()
        self.set_hexpand(True)
        self.set_vexpand(False)
        self.set_content_width(230)
        self.set_content_height(230)
        self.set_draw_func(self.draw)
        # Dedicated ~60 FPS animation clock.  This is intentionally separate
        # from sensor polling and fan-test commands so the spinner never hitches.
        GLib.timeout_add(1000 // 60, self.tick)

    def set_rpm(self, rpm):
        self.rpm = max(0, int(rpm or 0))

    def tick(self):
        now = time.monotonic()
        dt = max(0.001, min(0.050, now - getattr(self, "_last_frame", now)))
        self._last_frame = now

        # Exponential smoothing with time compensation keeps animation fluid
        # even if GTK occasionally delivers a frame late.
        smooth = 1.0 - pow(0.001, dt)
        self.display_rpm += (self.rpm - self.display_rpm) * min(0.20, smooth)
        visual = max(50, self.display_rpm)
        degrees_per_second = 90.0 + min(2600.0, visual * 1.05)
        self.angle = (self.angle + degrees_per_second * dt) % 360
        self.queue_draw()
        return True

    def rr(self, cr, x, y, w, h, r):
        cr.new_sub_path()
        cr.arc(x+w-r, y+r, r, -math.pi/2, 0)
        cr.arc(x+w-r, y+h-r, r, 0, math.pi/2)
        cr.arc(x+r, y+h-r, r, math.pi/2, math.pi)
        cr.arc(x+r, y+r, r, math.pi, 3*math.pi/2)
        cr.close_path()

    def blade_path(self, cr, r):
        # Realistic wide swept blade, not symbolic.
        cr.move_to(r*0.18, -r*0.045)
        cr.curve_to(r*0.35, -r*0.34, r*0.73, -r*0.56, r*1.10, -r*0.42)
        cr.curve_to(r*1.25, -r*0.36, r*1.23, -r*0.12, r*1.02, r*0.06)
        cr.curve_to(r*0.82, r*0.22, r*0.60, r*0.18, r*0.43, r*0.08)
        cr.line_to(r*0.31, r*0.19)
        cr.curve_to(r*0.24, r*0.12, r*0.17, r*0.055, r*0.10, r*0.012)
        cr.close_path()

    def draw(self, area, cr, w, h):
        cx, cy = w/2, h/2
        size = min(w, h)
        r = size * 0.285
        rpm = self.display_rpm

        # Matte square fan frame
        self.rr(cr, 5, 5, w-10, h-10, 22)
        cr.set_source_rgb(0.010, 0.015, 0.024)
        cr.fill_preserve()
        cr.set_source_rgba(0.20, 0.34, 0.52, 0.55)
        cr.set_line_width(2.0)
        cr.stroke()

        # Corner screw housings
        for sx, sy in [(28,28), (w-28,28), (28,h-28), (w-28,h-28)]:
            cr.set_source_rgba(0.018, 0.025, 0.035, 0.98)
            cr.arc(sx, sy, 14, 0, 2*math.pi)
            cr.fill_preserve()
            cr.set_source_rgba(0.25, 0.36, 0.48, 0.35)
            cr.stroke()
            cr.set_source_rgba(0, 0, 0, 0.92)
            cr.arc(sx, sy, 7, 0, 2*math.pi)
            cr.fill()
            cr.set_source_rgba(0.0, 0.50, 1.0, 0.23)
            cr.arc(sx, sy, 4, 0, 2*math.pi)
            cr.fill()

        # Angular neon insets on frame
        cr.set_source_rgba(0.0, 0.52, 1.0, 0.82)
        cr.set_line_width(3)
        for (x1,y1,x2,y2) in [
            (45,22,92,22), (w-92,22,w-45,22),
            (45,h-22,92,h-22), (w-92,h-22,w-45,h-22),
            (22,45,22,92), (w-22,45,w-22,92),
            (22,h-92,22,h-45), (w-22,h-92,w-22,h-45)
        ]:
            cr.move_to(x1,y1); cr.line_to(x2,y2); cr.stroke()

        # Cavity and LED rings
        cr.set_source_rgba(0.0, 0.003, 0.010, 0.98)
        cr.arc(cx, cy, r+39, 0, 2*math.pi)
        cr.fill()

        # outer glow
        cr.set_source_rgba(0.0, 0.43, 1.0, 0.15)
        cr.arc(cx, cy, r+43, 0, 2*math.pi)
        cr.set_line_width(17)
        cr.stroke()

        # crisp RGB ring
        cr.set_source_rgba(0.0, 0.66, 1.0, 0.95)
        cr.arc(cx, cy, r+36, 0, 2*math.pi)
        cr.set_line_width(4.5)
        cr.stroke()

        # inner ring
        cr.set_source_rgba(0.0, 0.20, 0.50, 0.70)
        cr.arc(cx, cy, r+25, 0, 2*math.pi)
        cr.set_line_width(2)
        cr.stroke()

        # Static rear grill rings/spokes
        for rr in (r+20, r+8):
            cr.set_source_rgba(0.14, 0.24, 0.34, 0.16)
            cr.arc(cx, cy, rr, 0, 2*math.pi)
            cr.set_line_width(1.1)
            cr.stroke()
        cr.save()
        cr.translate(cx, cy)
        cr.set_source_rgba(0.20, 0.32, 0.44, 0.10)
        cr.set_line_width(1)
        for i in range(12):
            cr.save()
            cr.rotate(i*2*math.pi/12)
            cr.move_to(r*0.45, 0)
            cr.line_to(r+22, 0)
            cr.stroke()
            cr.restore()
        cr.restore()

        # RPM-dependent motion blur disk
        if rpm > 700:
            cr.set_source_rgba(0.0, 0.42, 1.0, min(0.23, rpm/10500))
            cr.arc(cx, cy, r+20, 0, 2*math.pi)
            cr.fill()

        # Animated blades
        cr.save()
        cr.translate(cx, cy)
        cr.rotate(math.radians(self.angle))
        for i in range(7):
            # blade shadow
            cr.save()
            cr.rotate(i*2*math.pi/7 + 0.03)
            self.blade_path(cr, r*1.02)
            cr.set_source_rgba(0,0,0,0.56)
            cr.fill()
            cr.restore()

            # main blade
            cr.save()
            cr.rotate(i*2*math.pi/7)
            self.blade_path(cr, r)
            cr.set_source_rgba(0.006, 0.011, 0.021, 0.99)
            cr.fill_preserve()
            cr.set_source_rgba(0.16, 0.35, 0.62, 0.24)
            cr.set_line_width(4.5)
            cr.stroke()
            cr.restore()

            # blue leading highlight
            cr.save()
            cr.rotate(i*2*math.pi/7 - 0.018)
            self.blade_path(cr, r*0.93)
            cr.set_source_rgba(0.0, 0.55, 1.0, min(0.34, 0.08 + rpm/8500))
            cr.fill()
            cr.restore()
        cr.restore()

        # Clean static hub, no logo
        cr.set_source_rgb(0.008, 0.012, 0.022)
        cr.arc(cx, cy, r*0.43, 0, 2*math.pi)
        cr.fill_preserve()
        cr.set_source_rgba(0.0, 0.62, 1.0, 0.68)
        cr.set_line_width(2.6)
        cr.stroke()

        cr.set_source_rgba(0.0, 0.60, 1.0, 0.12)
        cr.arc(cx, cy, r*0.30, 0, 2*math.pi)
        cr.fill()

        # subtle glossy highlight only
        cr.set_source_rgba(1, 1, 1, 0.13)
        cr.arc(cx-r*0.10, cy-r*0.12, r*0.08, 0, 2*math.pi)
        cr.fill()
class MetricCard(Gtk.Box):
    def __init__(self, icon, title, unit):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        self.add_css_class("metric")
        self.set_hexpand(True)
        h = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=7)
        i = Gtk.Label(label=icon); i.add_css_class("title")
        t = Gtk.Label(label=title); t.add_css_class("title")
        h.append(i); h.append(t)
        self.append(h)
        r = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        self.value = Gtk.Label(label="--"); self.value.add_css_class("metric-number")
        self.unit = Gtk.Label(label=unit); self.unit.add_css_class("metric-unit"); self.unit.set_valign(Gtk.Align.END)
        r.append(self.value); r.append(self.unit)
        self.append(r)
        self.spark = Sparkline()
        self.append(self.spark)

    def set_value(self, txt, spark=None):
        self.value.set_label(str(txt))
        if spark is not None: self.spark.push(spark)

class FanCurveChart(Gtk.DrawingArea):
    def __init__(self, get_points_cb, set_point_cb, get_max_rpm_cb):
        super().__init__()
        self.get_points_cb = get_points_cb
        self.set_point_cb = set_point_cb
        self.get_max_rpm_cb = get_max_rpm_cb
        self.current_temp = 0
        self.drag_index = None
        self.set_content_width(880)
        self.set_content_height(320)
        self.add_css_class("chart-card")
        self.set_draw_func(self.draw)

        click = Gtk.GestureClick()
        click.set_button(1)
        click.connect("pressed", self.on_press)
        click.connect("released", self.on_release)
        self.add_controller(click)

        drag = Gtk.GestureDrag()
        drag.connect("drag-update", self.on_drag_update)
        drag.connect("drag-end", self.on_drag_end)
        self.add_controller(drag)
        self._press_xy = (0,0)

    def set_current_temp(self, temp):
        self.current_temp = float(temp or 0)
        self.queue_draw()

    def bounds(self,w,h): return 105, w-54, 48, h-82
    def map_x(self,t,w,h):
        x0,x1,y1,y0 = self.bounds(w,h)
        return x0 + (max(20,min(100,t))-20)/80*(x1-x0)
    def map_y(self,p,w,h):
        x0,x1,y1,y0 = self.bounds(w,h)
        return y0 - max(0,min(100,p))/100*(y0-y1)
    def unmap(self,x,y,w,h):
        x0,x1,y1,y0 = self.bounds(w,h)
        t = 20 + (max(x0,min(x1,x))-x0)/max(1,x1-x0)*80
        p = (y0-max(y1,min(y0,y)))/max(1,y0-y1)*100
        return round(t), round(p)

    def nearest(self,x,y):
        w,h = max(1,self.get_width()), max(1,self.get_height())
        best, dist = None, 999
        for i,(t,p) in enumerate(self.get_points_cb()):
            px,py = self.map_x(t,w,h), self.map_y(p,w,h)
            d = ((px-x)**2+(py-y)**2)**.5
            if d < dist: best,dist = i,d
        return best if dist <= 18 else None

    def on_press(self, gesture, n, x, y):
        self._press_xy=(x,y); self.drag_index=self.nearest(x,y)
    def on_release(self,*_): self.drag_index=None
    def on_drag_update(self, gesture, dx, dy):
        if self.drag_index is None: self.drag_index=self.nearest(*self._press_xy)
        if self.drag_index is None: return
        t,p = self.unmap(self._press_xy[0]+dx, self._press_xy[1]+dy, max(1,self.get_width()), max(1,self.get_height()))
        self.set_point_cb(self.drag_index,t,p); self.queue_draw()
    def on_drag_end(self,*_): self.drag_index=None

    def text(self,cr,txt,x,y,size=10,rgba=(1,1,1,.7),align="left"):
        cr.set_source_rgba(*rgba); cr.select_font_face("Sans",0,0); cr.set_font_size(size)
        xb,yb,tw,th,xa,ya=cr.text_extents(str(txt))
        if align=="center": x-=tw/2
        if align=="right": x-=tw
        cr.move_to(x,y); cr.show_text(str(txt))

    def draw(self, area, cr, w, h):
        x0,x1,y1,y0 = self.bounds(w,h)
        maxrpm = max(500,int(self.get_max_rpm_cb() or 2600))
        self.text(cr,"Fan Curve",x0,24,13,(1,1,1,.86))
        self.text(cr,"PWM / RPM",x0-82,y1-22,10,(1,1,1,.78))
        self.text(cr,"Temperature °C",x1-2,h-24,10,(1,1,1,.78),"right")

        cr.set_line_width(1)
        for i in range(6):
            pwm=i*20; y=self.map_y(pwm,w,h)
            cr.set_source_rgba(0,.65,1,.09); cr.move_to(x0,y); cr.line_to(x1,y); cr.stroke()
            self.text(cr,f"{pwm}%",x0-26,y-4,10,(1,1,1,.72),"right")
            self.text(cr,f"{round(maxrpm*pwm/100)} rpm",x0-68,y+16,8,(0,.75,1,.68),"right")
        for temp in range(20,101,20):
            x=self.map_x(temp,w,h)
            cr.set_source_rgba(0,.65,1,.08); cr.move_to(x,y0); cr.line_to(x,y1); cr.stroke()
            self.text(cr,f"{temp}°",x,y0+36,10,(1,1,1,.70),"center")

        cr.set_source_rgba(0,.72,1,.65); cr.set_line_width(1.7)
        cr.move_to(x0,y1); cr.line_to(x0,y0); cr.line_to(x1,y0); cr.stroke()

        pts = sorted([(int(t),int(p)) for t,p in self.get_points_cb()])
        if len(pts)>=2:
            cr.set_source_rgba(0,.55,1,.13); cr.move_to(self.map_x(pts[0][0],w,h),y0)
            for t,p in pts: cr.line_to(self.map_x(t,w,h), self.map_y(p,w,h))
            cr.line_to(self.map_x(pts[-1][0],w,h),y0); cr.close_path(); cr.fill()
            cr.set_source_rgba(0,.82,1,1); cr.set_line_width(4)
            for i,(t,p) in enumerate(pts):
                x,y = self.map_x(t,w,h), self.map_y(p,w,h)
                if i==0: cr.move_to(x,y)
                else: cr.line_to(x,y)
            cr.stroke()
        for i,(t,p) in enumerate(pts):
            x,y = self.map_x(t,w,h), self.map_y(p,w,h)
            cr.set_source_rgba(0,.85,1,1); cr.arc(x,y,8 if i==self.drag_index else 6,0,2*math.pi); cr.fill()
            cr.set_source_rgba(1,1,1,.92); cr.arc(x,y,2.3,0,2*math.pi); cr.fill()
            if i==self.drag_index or i in (0,len(pts)-1):
                align="left"; lx=x+8
                if x>(x0+x1)/2: align="right"; lx=x-8
                self.text(cr,f"{t}°C  {p}%",lx,y-9,9,(1,1,1,.78),align)
        if self.current_temp:
            cx=self.map_x(self.current_temp,w,h)
            cr.set_source_rgba(.2,1,.35,.88); cr.set_line_width(2)
            cr.move_to(cx,y1); cr.line_to(cx,y0); cr.stroke()
            cr.arc(cx,y1+7,5,0,2*math.pi); cr.fill()
            self.text(cr,f"GPU {self.current_temp:.0f}°C",max(x0+40,min(x1-45,cx)),y1-8,10,(.2,1,.35,.95),"center")

class CUSemicircleGauge(Gtk.DrawingArea):
    """Compact 180-degree CU gauge split into 20 square WGP/pair segments.

    Each segment represents two CUs, so 40 CUs = 20 visible blocks = 100%.
    Green means that CU pair is active/effective; red means inactive/disabled;
    amber is reserved for a partial/pending pair.
    """
    def __init__(self):
        super().__init__()
        self.active = 0
        self.total = 40
        # 10% larger than the previous compact gauge while keeping the card tidy.
        self.set_content_width(281)
        self.set_content_height(135)
        self.set_hexpand(False)
        self.set_halign(Gtk.Align.CENTER)
        self.set_draw_func(self._draw)

    def set_counts(self, active, total=40):
        try:
            active = int(active)
            total = int(total)
        except Exception:
            active, total = 0, 40
        total = max(1, total)
        self.active = max(0, min(active, total))
        self.total = total
        self.queue_draw()

    def _draw(self, area, cr, width, height):
        active = max(0, min(int(self.active), int(self.total or 40)))
        total = max(1, int(self.total or 40))
        pct = active / total

        # Pair gauge: exactly 20 visible square blocks around the arc.
        # BC250 = 40 physical CUs, so each visual block represents one CU pair.
        pair_size = 2
        segments = 20
        active_full_pairs = active // pair_size
        partial_pair = active % pair_size

        cx = width / 2.0
        cy = height * 0.90
        radius = min(width * 0.425, height * 0.82)
        # Twenty square-like blocks with deliberate gaps so every CU pair is readable.
        block_w = max(9.0, radius * 0.118)
        block_h = max(9.0, radius * 0.118)

        # Subtle half-ring shadow/background.
        cr.save()
        cr.set_line_width(block_h + 4)
        cr.set_line_cap(1)
        cr.set_source_rgba(0.015, 0.055, 0.095, 0.78)
        cr.arc(cx, cy, radius, math.pi, 2 * math.pi)
        cr.stroke()
        cr.restore()

        # Square blocks along the semicircle. They are spaced clearly and rotated tangent to the arc.
        # Left-to-right maps from 0 CU to 40 CU.
        for idx in range(segments):
            # Center each segment inside its angular cell, leaving natural visible gaps.
            frac = (idx + 0.5) / segments
            angle = math.pi + math.pi * frac
            x = cx + math.cos(angle) * radius
            y = cy + math.sin(angle) * radius

            if idx < active_full_pairs:
                fill = (0.12, 0.92, 0.26, 0.90)
                edge = (0.38, 1.0, 0.45, 0.95)
            elif idx == active_full_pairs and partial_pair:
                fill = (1.0, 0.78, 0.12, 0.88)  # partial pair / pending visual fallback
                edge = (1.0, 0.92, 0.35, 0.95)
            else:
                fill = (1.0, 0.16, 0.16, 0.80)
                edge = (1.0, 0.34, 0.30, 0.94)

            cr.save()
            cr.translate(x, y)
            cr.rotate(angle + math.pi / 2.0)
            self._rounded_rect(cr, -block_w / 2.0, -block_h / 2.0, block_w, block_h, 1.8)
            cr.set_source_rgba(*fill)
            cr.fill_preserve()
            cr.set_line_width(1.15)
            cr.set_source_rgba(*edge)
            cr.stroke()
            cr.restore()

        # End labels.
        self._text(cr, '0 CU', cx - radius - block_w * 0.90, cy + 12, 8.5, (0.88,0.96,1,0.72), 'center')
        self._text(cr, '40 CU', cx + radius + block_w * 0.90, cy + 12, 8.5, (0.88,0.96,1,0.72), 'center')

        # Center text, compact like the reference image.
        self._text(cr, f"{active} / {total}", cx, cy - radius * 0.50, 21, (0.94,1,0.95,1), 'center', bold=True)
        self._text(cr, "CUs Active", cx, cy - radius * 0.28, 10.5, (0.92,0.98,1,0.86), 'center', bold=True)
        self._text(cr, f"{round(pct * 100):.0f}%", cx, cy - radius * 0.05, 18, (0.35,1.0,0.43,0.95), 'center', bold=True)

    def _rounded_rect(self, cr, x, y, w, h, r):
        r = min(r, w / 2.0, h / 2.0)
        cr.new_sub_path()
        cr.arc(x + w - r, y + r, r, -math.pi / 2, 0)
        cr.arc(x + w - r, y + h - r, r, 0, math.pi / 2)
        cr.arc(x + r, y + h - r, r, math.pi / 2, math.pi)
        cr.arc(x + r, y + r, r, math.pi, 3 * math.pi / 2)
        cr.close_path()

    def _text(self, cr, text, x, y, size, rgba, align='left', bold=False):
        cr.save()
        cr.select_font_face('Sans', 0, 1 if bold else 0)
        cr.set_font_size(size)
        xb, yb, tw, th, xa, ya = cr.text_extents(str(text))
        if align == 'center':
            x -= tw / 2 + xb
        elif align == 'right':
            x -= tw + xb
        cr.set_source_rgba(*rgba)
        cr.move_to(x, y)
        cr.show_text(str(text))
        cr.restore()


class MainWindow(Adw.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app)
        self.set_title("bagz")
        self.set_default_size(1180, 760)
        self.set_size_request(820, 560)
        self.set_decorated(True)
        self.cu_staged = {}
        self.cu_stage_file = os.path.join(os.path.expanduser("~"), ".config", "skillfish-tuner", "cu-staged.json")
        self.cu_backup_dir = os.path.join(os.path.expanduser("~"), ".config", "skillfish-tuner", "backups")
        self.cu_last_good_file = os.path.join(self.cu_backup_dir, "last-good.json")
        self.cu_factory_file = os.path.join(self.cu_backup_dir, "factory-topology.json")
        self.last_good_config_file = os.path.join(self.cu_backup_dir, "last-good-config.json")
        self.pending_changes = set()
        self.load_cu_staged()
        self.nav_buttons = {}
        self.max_fan_rpm = 2600
        self.min_fan_rpm = 0
        self.fan_calibration_file = os.path.join(os.path.expanduser("~"), ".config", "skillfish-tuner", "fan-calibration.json")
        self.load_fan_calibration()
        self.advanced_widgets = []
        self.simple_mode = False  # Option 1: all controls visible; no Simple/Advanced split.
        self.manual_voltage_overrides = {}
        self._auto_updating_voltage = False

        toolbar = Adw.ToolbarView()
        self.set_content(toolbar)
        header = Adw.HeaderBar()
        header.set_title_widget(Adw.WindowTitle(title="Skillfish Tuner", subtitle="BC-250 GPU / CU / Governor Tuner"))
        toolbar.add_top_bar(header)

        root = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        root.add_css_class("root")
        toolbar.set_content(root)

        self.sidebar = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self.sidebar.add_css_class("sidebar")
        self.sidebar.set_size_request(190,-1)
        root.append(self.sidebar)

        self.main = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.main.set_margin_top(10); self.main.set_margin_bottom(10); self.main.set_margin_start(10); self.main.set_margin_end(10)
        self.main.set_hexpand(True); self.main.set_vexpand(True)
        root.append(self.main)

        self.build_sidebar()
        self.build_badges()
        self.stack = Gtk.Stack()
        self.stack.set_hexpand(True); self.stack.set_vexpand(True)
        self.stack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT_RIGHT)
        self.main.append(self.stack)

        self.build_dashboard_page()
        self.build_governor_page()
        self.build_gpu_page()
        self.build_contributors_page()
        self.build_report_page()
        self.select_page("dashboard")
        GLib.timeout_add(250, lambda: (self.apply_mode_visibility(), False)[1])

        # Sensor polling must never run on the GTK/UI thread.
        # A blocking sensors/status call every ~2 seconds was freezing animations.
        self._sensor_cache = None
        self._sensor_inflight = False
        self._sensor_last_poll = 0.0
        self._sensor_poll_interval = 1.0
        self._sensor_last_ui = 0.0
        GLib.timeout_add(1000 // 60, self.refresh)
        self.refresh()
        self.load_points()
        self.load_profiles()
        self.load_profile("My Profile", show=False)
        GLib.timeout_add(900, self.auto_refresh_cu_topology_on_startup)

    def label(self,text,classes=""):
        l=Gtk.Label(label=text)
        for c in classes.split(): l.add_css_class(c)
        return l
    def card(self,title=None,green=False):
        b=Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=8)
        b.add_css_class("card-green" if green else "card")
        if title:
            t=self.label(title,"title"); t.set_halign(Gtk.Align.START); b.append(t)
        return b
    def pulse_button(self,btn):
        btn.add_css_class("pulse-button"); btn.add_css_class("nav-btn-active")
        GLib.timeout_add(240,lambda:self.end_pulse(btn))
    def end_pulse(self,btn):
        btn.remove_css_class("pulse-button"); btn.remove_css_class("nav-btn-active"); return False
    def build_sidebar(self):
        logo=Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=4)
        logo.set_margin_bottom(14)

        logo_path = os.path.join(
            os.path.abspath(os.path.join(os.path.dirname(__file__), "..")),
            "assets",
            "bagz_fishbone_logo_transparent.png"
        )

        if os.path.isfile(logo_path):
            pic = Gtk.Picture.new_for_filename(logo_path)
            pic.set_size_request(150, 72)
            pic.set_halign(Gtk.Align.CENTER)
            logo.append(pic)
        else:
            mark=self.label("><(((º>","bagz-title")
            mark.set_halign(Gtk.Align.CENTER)
            logo.append(mark)

        title=self.label("skillfish","bagz-title")
        title.set_halign(Gtk.Align.CENTER)

        sub=self.label("blue all-in-one gpu zen","bagz-subtitle")
        sub.set_justify(Gtk.Justification.CENTER)
        sub.set_halign(Gtk.Align.CENTER)

        logo.append(title)
        logo.append(sub)
        self.sidebar.append(logo)

        for key,text in [("dashboard","⌂   DASHBOARD"),("governor","⬟   CU MANAGER"),("gpu","◌   GPU / FAN"),("report","▣   SYSTEM REPORT"),("contributors","♡   CONTRIBUTORS")]:
            b=Gtk.Button(label=text)
            b.add_css_class("nav-btn")
            b.connect("clicked",lambda _,k=key:self.select_page(k))
            self.nav_buttons[key]=b
            self.sidebar.append(b)

        # Option 1 design: no Simple/Advanced mode toggle. BC250 users get all controls, organized by tab.

        spacer=Gtk.Box()
        spacer.set_vexpand(True)
        self.sidebar.append(spacer)
        self.sidebar.append(self.label("v2.0.0","small"))

    def build_badges(self):
        row=Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL,spacing=12); row.set_halign(Gtk.Align.START); self.main.append(row)
        self.umr_badge=Gtk.Label(label="● UMR READY")
        self.cu_badge=Gtk.Label(label="● CU MANAGER READY")
        self.pending_badge=Gtk.Label(label="✓ No Pending Changes")
        self.pending_badge.add_css_class("pending-badge-clear")
        for b in [self.umr_badge,self.cu_badge]:
            b.add_css_class("badge-ok")
            row.append(b)
        row.append(self.pending_badge)
    def select_page(self,key):
        self.stack.set_visible_child_name(key)
        for k,b in self.nav_buttons.items():
            b.remove_css_class("nav-btn-active")
            if k==key: b.add_css_class("nav-btn-active")

    def mark_pending(self, area):
        try:
            self.pending_changes.add(str(area))
            self.update_pending_badge()
        except Exception:
            pass

    def clear_pending(self, area=None):
        try:
            if area is None:
                self.pending_changes.clear()
            else:
                self.pending_changes.discard(str(area))
            self.update_pending_badge()
        except Exception:
            pass

    def update_pending_badge(self):
        if not hasattr(self, "pending_badge"):
            return
        for c in ("pending-badge", "pending-badge-clear"):
            self.pending_badge.remove_css_class(c)
        if getattr(self, "pending_changes", set()):
            names = ", ".join(sorted(self.pending_changes))
            self.pending_badge.set_label(f"● Pending: {names}")
            self.pending_badge.add_css_class("pending-badge")
        else:
            self.pending_badge.set_label("✓ No Pending Changes")
            self.pending_badge.add_css_class("pending-badge-clear")

    def save_last_good_full_config(self, reason="before-change"):
        """Best-effort safety snapshot before applying risky settings.

        This intentionally stores app-level state, not secrets: CU status/staged
        map, fan curve/calibration, and current OC curve/target.
        """
        try:
            os.makedirs(self.cu_backup_dir, exist_ok=True)
            payload = {
                "version": 1,
                "reason": reason,
                "created": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
                "pending": sorted(list(getattr(self, "pending_changes", set()))),
                "cu_staged": getattr(self, "cu_staged", {}),
                "cu_status": getattr(self, "last_cu_data", {}),
                "fan_curve": self.get_fan_curve_points() if hasattr(self, "fan_curve_rows") else [],
                "fan_keep_after_reboot": bool(getattr(self, "fan_keep_after_reboot", None) and self.fan_keep_after_reboot.get_active()),
                "fan_calibration": {"min_rpm": int(getattr(self, "min_fan_rpm", 0) or 0), "max_rpm": int(getattr(self, "max_fan_rpm", 0) or 0)},
                "oc": {
                    "max_freq": int(self.clock_scale.get_value()) if hasattr(self, "clock_scale") else None,
                    "points": self.merged_points() if hasattr(self, "full_points") else [],
                },
            }
            with open(self.last_good_config_file, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2, sort_keys=True)
            return True
        except Exception as e:
            self.add_status(f"Could not save last-good configuration: {e}")
            return False

    def restore_last_good_full_config(self):
        try:
            with open(self.last_good_config_file, "r", encoding="utf-8") as f:
                data=json.load(f)
        except Exception as e:
            self.add_status(f"No last-good configuration found: {e}")
            if hasattr(self, "report_status"):
                self.report_status.set_label("No last-good configuration found yet. Apply something once first.")
            return
        try:
            oc=data.get("oc") or {}
            if oc.get("points") and hasattr(self, "set_points"):
                self.set_points(oc.get("points") or [])
            if oc.get("max_freq") and hasattr(self, "clock_scale"):
                self.clock_scale.set_value(int(oc.get("max_freq")))
            fan=data.get("fan_curve") or []
            if fan and hasattr(self, "apply_fan_curve_points_to_rows"):
                self.apply_fan_curve_points_to_rows(fan)
            self.mark_pending("OC")
            self.mark_pending("Fan")
            self.add_status("Last-good configuration loaded into the UI; press Apply on the relevant page to use it.")
            if hasattr(self, "report_status"):
                self.report_status.set_label("✓ Last-good configuration loaded. Review values, then apply on CU/Fan/OC pages.")
        except Exception as e:
            self.add_status(f"Restore last-good configuration failed: {e}")

    def open_logs_folder(self):
        path=os.path.expanduser("~/.config/skillfish-tuner/logs")
        os.makedirs(path, exist_ok=True)
        self._open_local_file_or_uri(path)

    def on_mode_toggled(self, *_):
        # Kept for compatibility with older builds; Option 1 has no Simple/Advanced mode.
        self.simple_mode = False
        self.apply_mode_visibility()

    def apply_mode_visibility(self):
        # Option 1: advanced BC250 workspace. Do not hide raw/service controls.
        for widget in getattr(self, "advanced_widgets", []):
            try:
                widget.set_visible(True)
            except Exception:
                pass
        if hasattr(self, "dashboard_mode_label"):
            self.dashboard_mode_label.set_label("Advanced BC250 Workspace")
        return False

    def _read_first_line(self, path, default="--"):
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                return f.readline().strip() or default
        except Exception:
            return default

    def _cmd_text(self, cmd, default="--", timeout=2):
        try:
            return subprocess.check_output(cmd, text=True, stderr=subprocess.DEVNULL, timeout=timeout).strip() or default
        except Exception:
            return default

    def populate_dashboard_system_info(self):
        if not hasattr(self, "dash_os"):
            return False
        os_name = "Bazzite / Fedora Atomic"
        try:
            data = {}
            with open("/etc/os-release", "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    if "=" in line:
                        k, v = line.rstrip().split("=", 1)
                        data[k] = v.strip('"')
            os_name = data.get("PRETTY_NAME") or data.get("NAME") or os_name
        except Exception:
            pass
        kernel = self._cmd_text(["uname", "-r"])
        mem = self._cmd_text(["bash", "-lc", "awk '/MemTotal/ {printf \"%.1f GB\", $2/1024/1024}' /proc/meminfo"])
        gpu = self._cmd_text(["bash", "-lc", "lspci -nn | grep -Ei 'VGA|Display|3D|13FE|Skillfish' | head -1"], default="BC250/Cyan Skillfish GPU")
        self.dash_platform.set_label("Platform: BC250 / Cyan Skillfish")
        self.dash_os.set_label(f"OS: {os_name}")
        self.dash_kernel.set_label(f"Kernel: {kernel}")
        self.dash_memory.set_label(f"Memory: {mem}")
        self.dash_bc250.set_label("BC250: Detected" if "13FE" in gpu or "Skillfish" in gpu or "BC250" in gpu else "BC250: Check report")
        self.dash_nct.set_label("Fan Controller: NCT6686 / Pump Fan")
        if hasattr(self, "dash_uptime"):
            self.dash_uptime.set_label("Uptime: " + self._cmd_text(["bash", "-lc", "uptime -p 2>/dev/null | sed 's/^up //'"], default="--"))
        if hasattr(self, "dash_driver"):
            self.dash_driver.set_label("Driver: amdgpu")
        return False

    def build_dashboard_page(self):
        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        page.set_margin_top(8); page.set_margin_bottom(12); page.set_margin_start(4); page.set_margin_end(4)
        scroll.set_child(page)

        hero = self.card("SYSTEM OVERVIEW")
        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=14)
        row.set_hexpand(True)
        hero.append(row)

        left = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        left.set_hexpand(True)
        title = self.label("Skillfish Tuner", "hero blue")
        left.append(title)
        self.dashboard_mode_label = self.label("Advanced BC250 Workspace", "badge-ok")
        self.dashboard_mode_label.set_halign(Gtk.Align.START)
        left.append(self.dashboard_mode_label)
        hint = Gtk.Label(label="Advanced BC250 workspace: all core controls are visible, with details expandable where useful.", xalign=0)
        hint.set_wrap(True); hint.add_css_class("title"); left.append(hint)
        row.append(left)

        gauge_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        gauge_box.set_halign(Gtk.Align.CENTER)
        self.dashboard_cu_gauge = CUSemicircleGauge()
        gauge_box.append(self.dashboard_cu_gauge)
        self.dashboard_cu_label = self.label("-- / 40 CUs", "title")
        self.dashboard_cu_label.set_halign(Gtk.Align.CENTER)
        gauge_box.append(self.dashboard_cu_label)
        row.append(gauge_box)
        page.append(hero)

        quick = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        quick.set_hexpand(True)
        page.append(quick)

        health = self.card("SERVICE HEALTH")
        health.set_hexpand(True)
        self.health_rows = {}
        for key, label in [("governor", "Governor"), ("cu", "CU Restore"), ("fan", "Fan Restore")]:
            r = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
            r.append(self.label(label, "small"))
            status = self.label("checking…", "service-warn")
            status.set_hexpand(True); status.set_halign(Gtk.Align.END)
            r.append(status)
            health.append(r)
            self.health_rows[key] = status
        quick.append(health)

        live = self.card("LIVE STATUS")
        live.set_hexpand(True)
        self.dash_temp = self.label("GPU Temp: -- °C", "title")
        self.dash_clock = self.label("GPU Clock: -- MHz", "title")
        self.dash_fan = self.label("Pump Fan: -- RPM", "title")
        for w in [self.dash_temp, self.dash_clock, self.dash_fan]: live.append(w)
        quick.append(live)

        info_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        info_row.set_hexpand(True)
        page.append(info_row)

        sysinfo = self.card("SYSTEM INFORMATION")
        sysinfo.set_hexpand(True)
        self.dash_platform = self.label("Platform: Detecting…", "title")
        self.dash_os = self.label("OS: Detecting…", "small")
        self.dash_kernel = self.label("Kernel: Detecting…", "small")
        self.dash_memory = self.label("Memory: Detecting…", "small")
        self.dash_uptime = self.label("Uptime: Detecting…", "small")
        self.dash_driver = self.label("Driver: amdgpu", "small")
        for w in [self.dash_platform, self.dash_os, self.dash_kernel, self.dash_memory, self.dash_uptime, self.dash_driver]:
            sysinfo.append(w)
        info_row.append(sysinfo)

        config = self.card("CURRENT CONFIGURATION")
        config.set_hexpand(True)
        self.dash_cfg_clock = self.label("Clock: -- MHz", "title")
        self.dash_cfg_voltage = self.label("Voltage: -- mV", "small")
        self.dash_cfg_power = self.label("Power: -- W", "small")
        self.dash_cfg_fan = self.label("Fan: -- RPM", "small")
        for w in [self.dash_cfg_clock, self.dash_cfg_voltage, self.dash_cfg_power, self.dash_cfg_fan]:
            config.append(w)
        info_row.append(config)

        platform = self.card("PLATFORM STATUS")
        platform.set_hexpand(True)
        self.dash_bc250 = self.label("BC250: Detecting…", "small")
        self.dash_nct = self.label("Fan Controller: Detecting…", "small")
        self.dash_workspace = self.label("Workspace: Advanced BC250", "small")
        for w in [self.dash_bc250, self.dash_nct, self.dash_workspace]:
            platform.append(w)
        info_row.append(platform)

        flow = self.card("WORKFLOW")
        txt = Gtk.Label(label="Advanced BC250 workflow: tune directly in each tab, apply live first, then enable Keep after reboot only when stable. Use expandable details and reports for diagnostics.", xalign=0)
        txt.set_wrap(True); flow.append(txt); page.append(flow)
        self.populate_dashboard_system_info()

        self.stack.add_titled(scroll, "dashboard", "Dashboard")

    def update_dashboard_cu(self, active_value):
        active, total = self.parse_cu_count_pair(active_value)
        if active is None:
            active, total = 0, 40
        active = max(0, min(int(active), 40)); total = 40
        if hasattr(self, "dashboard_cu_gauge"):
            self.dashboard_cu_gauge.set_counts(active, total)
        if hasattr(self, "dashboard_cu_label"):
            self.dashboard_cu_label.set_label(f"{active} / {total} CUs active")
        if hasattr(self, "health_rows"):
            self._set_health("cu", "active" if active > 0 else "check")

    def _set_health(self, key, state):
        if not hasattr(self, "health_rows") or key not in self.health_rows:
            return
        lab = self.health_rows[key]
        for c in ("service-ok", "service-warn", "service-bad"):
            lab.remove_css_class(c)
        state = str(state).strip().lower()
        # End-user wording: no permanent yellow "checking" state. Optional
        # services that are not enabled are neutral/gray, not scary red.
        if state in ("active", "running", "ok", "enabled", "true"):
            lab.set_label("Running" if state == "running" else "Enabled")
            lab.add_css_class("service-ok")
        elif state in ("installed-restart-pending", "installed restart pending", "restart-pending", "restart pending", "pending-restart"):
            lab.set_label("Installed — restart pending")
            lab.add_css_class("service-warn")
        elif state in ("missing", "not-installed", "not installed"):
            lab.set_label("Not installed")
            lab.add_css_class("service-warn")
        elif state in ("disabled", "inactive", "off"):
            lab.set_label("Disabled")
            lab.add_css_class("service-warn")
        elif state in ("failed", "error", "false"):
            lab.set_label("Error")
            lab.add_css_class("service-bad")
        else:
            lab.set_label("Unknown")
            lab.add_css_class("service-warn")

    # Quick consumer profiles intentionally removed for Option 1.

    def build_governor_page(self):
        scroll=Gtk.ScrolledWindow(); page=Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=10); scroll.set_child(page)
        intro=self.card("UNLOCK FIRST, THEN OVERCLOCK")
        text=Gtk.Label(label="Simple flow: click CUs to enable/disable them, choose whether to keep the configuration after reboot, then press Apply Changes.",xalign=0)
        text.set_wrap(True); intro.append(text); page.append(intro)

        self.gov_result_card=self.card("TASK RESULT")
        self.gov_result_card.add_css_class("task-result-card")
        self.gov_result_card.add_css_class("task-result-success")
        self.gov_result_card.set_size_request(-1, 64)
        self.gov_result=Gtk.Label(label="✓ Ready",xalign=0)
        self.gov_result.add_css_class("task-result-label")
        self.gov_result.set_wrap(False)
        self.gov_result.set_single_line_mode(True)
        self.gov_result.set_ellipsize(Pango.EllipsizeMode.END)
        self.gov_result.set_selectable(False)
        self.gov_result_card.append(self.gov_result); page.append(self.gov_result_card)
        self.gov_task_progress = Gtk.ProgressBar()
        self.gov_task_progress.set_show_text(True)
        self.gov_task_progress.set_text("Ready")
        self.gov_task_progress.set_visible(False)
        page.append(self.gov_task_progress)

        top=Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL,spacing=10); page.append(top)
        self.action_buttons = getattr(self, "action_buttons", {})

        umr=self.card("UMR MANAGER"); umr.set_hexpand(True); self.advanced_widgets.append(umr)
        hint=Gtk.Label(label="Tools and checks are combined here. Setup installs/checks UMR, installs the CU manager, then runs preflight.", xalign=0)
        hint.add_css_class("small"); hint.set_wrap(True); umr.append(hint)
        for label,cmd,blue in [
            ("🧰 SETUP / CHECK UMR + CU TOOLS","cu_setup",True),
            ("⟳ REFRESH CU TOPOLOGY","cu_status_json",False),
            ("UMR / CU REQUIREMENTS LOG","cu_preflight",False),
        ]:
            b=Gtk.Button(label=label); b.add_css_class("blue-button" if blue else "outline-button")
            self.action_buttons[cmd] = b
            b.connect("clicked",lambda btn,c=cmd,l=label:(self.pulse_button(btn),self.run_action(l,c,btn)))
            umr.append(b)
        top.append(umr)

        cu=self.card("CU MANAGER"); cu.set_hexpand(True)
        hint=Gtk.Label(label="Click CU/WGP tiles to toggle them. First run automatically backs up the original topology. Green = active, gray/red = disabled, yellow = pending change only.", xalign=0)
        hint.add_css_class("small"); hint.set_wrap(True); cu.append(hint)
        self.cu_persist_check = Gtk.CheckButton(label="Keep after reboot")
        self.cu_persist_check.set_active(True)
        cu.append(self.cu_persist_check)

        # Animated feedback for slow CU/topology writes. The apply behavior stays the same,
        # but the user can clearly see that work is still running.
        self.cu_apply_progress = Gtk.ProgressBar()
        self.cu_apply_progress.set_show_text(True)
        self.cu_apply_progress.set_text("Ready")
        self.cu_apply_progress.set_visible(False)
        cu.append(self.cu_apply_progress)

        self.cu_action_buttons = []
        for label,cb,blue in [("✓ APPLY CHANGES",self.apply_cu_changes,True),("↺ REVERT LAST GOOD",self.revert_last_good_cu,False),("⟲ RESTORE FACTORY TOPOLOGY",self.restore_factory_cu,False),("⟳ CLEAR PENDING",self.reset_cu_staged,False)]:
            b=Gtk.Button(label=label); b.add_css_class("blue-button" if blue else "outline-button")
            b._skillfish_original_label = label
            if "APPLY CHANGES" in label:
                self.cu_apply_button = b
            self.cu_action_buttons.append(b)
            b.connect("clicked",lambda btn,f=cb:(self.pulse_button(btn),f()))
            cu.append(b)
        top.append(cu)

        gov=self.card("GOVERNOR"); gov.set_hexpand(True); self.advanced_widgets.append(gov)
        self.gov_service_label = self.label("Governor Service: check with STATUS", "small")
        gov.append(self.gov_service_label)
        for label,cmd,blue in [("🐟 ONE-CLICK DEPLOY GOVERNOR","gov_deploy",True),("GOVERNOR STATUS / SERVICE","gov_status",False),("RESTART GOVERNOR","gov_restart",False)]:
            b=Gtk.Button(label=label); b.add_css_class("blue-button" if blue else "outline-button")
            self.action_buttons[cmd] = b
            b.connect("clicked",lambda btn,c=cmd,l=label:(self.pulse_button(btn),self.run_action(l,c,btn)))
            gov.append(b)
        top.append(gov)

        topo=self.card("LIVE CU TOPOLOGY")
        self.gov_cu_grid=Gtk.Grid(column_spacing=7,row_spacing=7); self.gov_cu_grid.set_column_homogeneous(True); topo.append(self.gov_cu_grid)
        topo.append(self.label("🟢 ACTIVE     🟡 PENDING CHANGE     ⚪/🔴 DISABLED","small"))
        page.append(topo)
        bottom=Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL,spacing=10); page.append(bottom)
        summary=self.card("CU SUMMARY"); summary.set_hexpand(True)
        self.gov_cu_gauge = CUSemicircleGauge()
        summary.append(self.gov_cu_gauge)
        self.gov_active_cu_big=self.label("-- / 40", "hero")
        self.gov_active_cu_big.set_halign(Gtk.Align.CENTER)
        summary.append(self.gov_active_cu_big)
        self.gov_cu_gauge_caption=Gtk.Label(label="20 CU-pair segments", xalign=0.5)
        self.gov_cu_gauge_caption.add_css_class("cu-gauge-caption")
        summary.append(self.gov_cu_gauge_caption)
        bottom.append(summary)
        info=self.card("ADVANCED STATUS / PERSISTENCE"); info.set_hexpand(True); self.advanced_widgets.append(info); self.gov_umr_info=Gtk.Grid(column_spacing=10,row_spacing=7); self.gov_umr_info.set_column_homogeneous(True); info.append(self.gov_umr_info); bottom.append(info)
        self.stack.add_titled(scroll,"governor","Governor / CU")

    def _open_local_file_or_uri(self, target):
        """Open a local legal/source file or external source URL from the GUI."""
        try:
            if target.startswith("http://") or target.startswith("https://"):
                Gio.AppInfo.launch_default_for_uri(target, None)
                return
            path = target if os.path.isabs(target) else os.path.join(APPDIR, target)
            Gio.AppInfo.launch_default_for_uri(GLib.filename_to_uri(path), None)
        except Exception as e:
            dialog = Gtk.MessageDialog(
                transient_for=self,
                modal=True,
                message_type=Gtk.MessageType.WARNING,
                buttons=Gtk.ButtonsType.OK,
                text="Could not open link or file",
            )
            dialog.format_secondary_text(str(e))
            dialog.connect("response", lambda d, r: d.destroy())
            dialog.show()


    def build_report_page(self):
        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        page.set_margin_top(14); page.set_margin_bottom(14); page.set_margin_start(14); page.set_margin_end(14)
        scroll.set_child(page)

        hero = self.card("SYSTEM / DEVELOPER REPORT")
        title = self.label("Generate a safe support bundle", "hero blue")
        title.set_halign(Gtk.Align.CENTER)
        hero.append(title)
        desc = Gtk.Label(
            label=(
                "Creates one tar.gz report with OS, GPU, CU topology, sensors, governor status, "
                "Skillfish logs and configuration snapshots. Use it for troubleshooting and future add-ons like RGB control."
            ),
            xalign=0,
        )
        desc.set_wrap(True); desc.add_css_class("title"); hero.append(desc)
        page.append(hero)

        privacy = self.card("PRIVACY NOTE")
        privacy_text = Gtk.Label(
            label=(
                "The report may include hostname, kernel command line, package state, PCI/USB devices, systemd service status, "
                "hardware IDs, log excerpts and Skillfish configuration. It does not intentionally collect passwords, browser data, "
                "SSH keys, personal documents or full home-directory contents. Review before sharing publicly."
            ),
            xalign=0,
        )
        privacy_text.set_wrap(True); privacy.append(privacy_text); page.append(privacy)

        actions = self.card("ACTIONS")
        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        gen = Gtk.Button(label="GENERATE REPORT")
        gen.add_css_class("blue-button")
        gen.connect("clicked", lambda btn: (self.pulse_button(btn), self.generate_system_report()))
        open_btn = Gtk.Button(label="OPEN REPORT FOLDER")
        open_btn.add_css_class("outline-button")
        open_btn.connect("clicked", lambda btn: self._open_local_file_or_uri(os.path.expanduser("~/.config/skillfish-tuner/reports")))
        logs_btn = Gtk.Button(label="OPEN LOGS")
        logs_btn.add_css_class("outline-button")
        logs_btn.connect("clicked", lambda btn: self.open_logs_folder())
        restore_btn = Gtk.Button(label="RESTORE LAST GOOD CONFIG")
        restore_btn.add_css_class("outline-button")
        restore_btn.connect("clicked", lambda btn: (self.pulse_button(btn), self.restore_last_good_full_config()))
        row.append(gen); row.append(open_btn); row.append(logs_btn); row.append(restore_btn); actions.append(row)
        self.report_status = Gtk.Label(label="Ready to generate report.", xalign=0)
        self.report_status.set_wrap(True); self.report_status.set_selectable(True)
        actions.append(self.report_status)
        page.append(actions)

        includes = self.card("INCLUDED SECTIONS")
        inc = Gtk.Label(
            label=(
                "system: uname, os-release, rpm-ostree, kernel args, modules\n"
                "gpu/cu: lspci, amdgpu messages, CU status JSON, saved CU backups\n"
                "sensors: lm-sensors output, hwmon tree, fan calibration\n"
                "services: Skillfish, BC250 CU manager and governor service status\n"
                "logs: Skillfish app logs and system service logs\n"
                "rgb discovery: lsusb, i2c device list, OpenRGB availability if installed"
            ),
            xalign=0,
        )
        inc.set_wrap(True); inc.set_selectable(True); inc.add_css_class("mono"); includes.append(inc); page.append(includes)
        self.stack.add_titled(scroll, "report", "System Report")

    def _write_text_file(self, path, text):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8", errors="replace") as f:
            f.write(text if isinstance(text, str) else str(text))

    def _run_report_command(self, cmd, timeout=20):
        try:
            proc = subprocess.run(cmd, shell=True, text=True, capture_output=True, timeout=timeout)
            return f"$ {cmd}\nrc={proc.returncode}\n\n--- stdout ---\n{proc.stdout}\n\n--- stderr ---\n{proc.stderr}\n"
        except Exception as e:
            return f"$ {cmd}\nERR {e}\n"

    def generate_system_report(self):
        if hasattr(self, "report_status"):
            self.report_status.set_label("⟳ Generating report…")
        self.add_status("Generating developer system report")

        def worker():
            import os, json, time, shutil, tarfile, tempfile
            stamp = time.strftime("%Y%m%d-%H%M%S")
            base_dir = os.path.expanduser("~/.config/skillfish-tuner/reports")
            os.makedirs(base_dir, exist_ok=True)
            work = tempfile.mkdtemp(prefix=f"skillfish-report-{stamp}-")
            root = os.path.join(work, f"skillfish-report-{stamp}")
            os.makedirs(root, exist_ok=True)
            def w(rel, text):
                self._write_text_file(os.path.join(root, rel), text)
            def c(rel, cmd, timeout=20):
                w(rel, self._run_report_command(cmd, timeout))

            w("README.txt", "Skillfish Tuner developer report. Review before sharing publicly. Generated: %s\n" % time.strftime("%F %T"))
            c("system/uname.txt", "uname -a")
            c("system/os-release.txt", "cat /etc/os-release 2>/dev/null || true")
            c("system/rpm-ostree-status.txt", "rpm-ostree status 2>&1 || true", 45)
            c("system/rpm-ostree-kargs.txt", "rpm-ostree kargs 2>&1 || true", 45)
            c("system/lsmod.txt", "lsmod 2>&1 || true")
            c("system/kernel-cmdline.txt", "cat /proc/cmdline 2>/dev/null || true")
            c("hardware/lspci.txt", "lspci -nnk 2>&1 || true")
            c("hardware/lsusb.txt", "lsusb 2>&1 || true")
            c("hardware/i2c-devices.txt", "ls -la /dev/i2c* 2>&1 || true; command -v i2cdetect >/dev/null && i2cdetect -l 2>&1 || true")
            c("gpu/amdgpu-dmesg.txt", "dmesg 2>/dev/null | grep -Ei 'amdgpu|cyan|skillfish|bc250|disable_cu|drm' | tail -n 300 || true")
            c("gpu/drm-debugfs.txt", "ls -R /sys/kernel/debug/dri 2>&1 | head -400 || true")
            c("gpu/umr.txt", "which umr 2>&1; umr --version 2>&1 || true")
            c("sensors/sensors.txt", "sensors 2>&1 || true")
            c("sensors/hwmon.txt", "find /sys/class/hwmon -maxdepth 3 -type f -print 2>/dev/null | while read f; do echo '---' $f; cat $f 2>/dev/null; done | head -2000")
            c("services/skillfish-services.txt", "systemctl status 'skillfish*' 'bc250*' 'cyan-skillfish-governor-smu.service' --no-pager 2>&1 || true", 30)
            c("services/journal-skillfish.txt", "journalctl -b --no-pager 2>/dev/null | grep -Ei 'skillfish|bc250|cu-live|umr|cyan-skillfish' | tail -n 500 || true", 30)
            c("rgb/discovery.txt", "which openrgb 2>&1 || true; openrgb --version 2>&1 || true; lsusb 2>&1 || true; ls -la /dev/hidraw* /dev/i2c* 2>&1 || true")

            try:
                w("gpu/cu-status.json", call("cu_status_json"))
            except Exception as e:
                w("gpu/cu-status.json", f"ERR {e}\n")
            try:
                w("gpu/daemon-status.json", call("status"))
            except Exception as e:
                w("gpu/daemon-status.json", f"ERR {e}\n")

            copy_items = [
                (os.path.expanduser("~/.config/skillfish-tuner/fan-calibration.json"), "config/fan-calibration.json"),
                (os.path.expanduser("~/.config/skillfish-tuner/cu-staged.json"), "config/cu-staged.json"),
                (os.path.expanduser("~/.config/skillfish-tuner/backups/factory-topology.json"), "config/factory-topology.json"),
                (os.path.expanduser("~/.config/skillfish-tuner/backups/last-good.json"), "config/last-good.json"),
                ("/etc/modprobe.d/bc250-40cu.conf", "config/bc250-40cu.conf"),
                ("/etc/cyan-skillfish-governor-smu/config.toml", "config/governor-config.toml"),
                (os.path.expanduser("~/.config/skillfish-tuner/logs/latest.log"), "logs/skillfish-latest.log"),
                ("/tmp/skillfish-tuner-latest.log", "logs/skillfish-tmp-latest.log"),
            ]
            for src, rel in copy_items:
                try:
                    if os.path.isfile(src):
                        dst = os.path.join(root, rel)
                        os.makedirs(os.path.dirname(dst), exist_ok=True)
                        shutil.copy2(src, dst)
                except Exception as e:
                    w(rel + ".copy-error.txt", str(e))

            manifest = []
            for dirpath, _, files in os.walk(root):
                for fn in files:
                    manifest.append(os.path.relpath(os.path.join(dirpath, fn), root))
            w("MANIFEST.txt", "\n".join(sorted(manifest)) + "\n")
            archive = os.path.join(base_dir, f"skillfish-report-{stamp}.tar.gz")
            with tarfile.open(archive, "w:gz") as tf:
                tf.add(root, arcname=os.path.basename(root))
            shutil.rmtree(work, ignore_errors=True)
            GLib.idle_add(self._finish_system_report, archive)

        threading.Thread(target=worker, daemon=True).start()

    def _finish_system_report(self, archive):
        if hasattr(self, "report_status"):
            self.report_status.set_label(f"✓ Report created:\n{archive}")
        self.add_status("Developer report created")
        return False

    def build_contributors_page(self):
        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)

        page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        page.set_margin_top(14)
        page.set_margin_bottom(14)
        page.set_margin_start(14)
        page.set_margin_end(14)
        scroll.set_child(page)

        hero = self.card("CONTRIBUTORS & LEGAL")
        title = self.label("Contributors, credits, and project notices", "hero blue")
        title.set_halign(Gtk.Align.CENTER)
        hero.append(title)
        intro = Gtk.Label(
            label=(
                "Skillfish Tuner focuses on BC-250 CU management, overclocking, fan control, governor integration, "
                "system reports, and future expansion/RGB discovery. Unrelated third-party test tools are not part of the tuner, keeping the package smaller, clearer, and easier to maintain."
            ),
            xalign=0,
        )
        intro.set_wrap(True)
        intro.add_css_class("title")
        hero.append(intro)
        page.append(hero)

        def text_card(name, body):
            c = self.card(name)
            txt = Gtk.Label(label=body, xalign=0)
            txt.set_wrap(True)
            txt.set_selectable(True)
            c.append(txt)
            page.append(c)
            return c

        def link_card(name, body, buttons):
            c = self.card(name)
            txt = Gtk.Label(label=body, xalign=0)
            txt.set_wrap(True)
            txt.set_selectable(True)
            c.append(txt)
            row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
            for label, target in buttons:
                b = Gtk.Button(label=label)
                b.add_css_class("outline-button")
                b.connect("clicked", lambda btn, t=target: self._open_local_file_or_uri(t))
                row.append(b)
            c.append(row)
            page.append(c)
            return c

        text_card(
            "Community contributors",
            "Special thanks to the BC-250 community and the people whose public research and tooling made this tuner possible: "
            "Filippo R. / Cyan Skillfish Governor contributors, Duggasco / BC250 40CU unlock contributors, "
            "WinnieLV / BC250 CU Live Manager contributors, AMD GPUOpen / UMR contributors, Mesa, AMDGPU, Linux kernel, Fedora, Bazzite, GTK, and GNOME contributors."
        )

        link_card(
            "Referenced community projects",
            "Skillfish Tuner may install, configure, or interoperate with external community tools. This app keeps attribution visible and links to the upstream projects.",
            [
                ("Cyan Skillfish Governor", "https://github.com/filippor/cyan-skillfish-governor"),
                ("BC250 40CU Unlock", "https://github.com/duggasco/bc250-40cu-unlock"),
                ("BC250 CU Live Manager", "https://github.com/WinnieLV/bc250-cu-live-manager"),
                ("UMR", "https://gitlab.freedesktop.org/tomstdenis/umr"),
            ],
        )


        text_card(
            "Safety disclaimer",
            "BC-250 CU unlocking, overclocking, voltage changes, and fan tuning can increase power draw, heat, driver resets, and system instability. Save your work, use adequate cooling and power, and keep a known-good topology/profile backup before saving changes for boot."
        )

        footer = self.card("OPEN SOURCE NOTICE")
        footer_text = Gtk.Label(
            label=(
                "Third-party projects remain the property of their respective authors and are referenced under their original licenses. "
                "This package keeps attribution visible for the community tools used by Skillfish Tuner.\n\n"
                "Yours truly,\nBagz"
            ),
            xalign=0,
        )
        footer_text.set_wrap(True)
        footer_text.set_selectable(True)
        footer.append(footer_text)
        page.append(footer)

        self.stack.add_titled(scroll, "contributors", "Contributors & Legal")

    def build_gpu_page(self):
        scroll=Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        page=Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=10)
        scroll.set_child(page)
        # Top: fan animation + all sensor cards directly next to it.
        top=Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL,spacing=10)
        top.set_hexpand(True)
        page.append(top)

        fan_card=self.card()
        fan_card.set_hexpand(False)
        fan_card.set_size_request(360,-1)

        fan_row=Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL,spacing=10)
        fan_row.set_hexpand(True)
        self.fan=FanWidget()
        fan_row.append(self.fan)

        fs=Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=6)
        fs.set_valign(Gtk.Align.CENTER)
        rpmrow=Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL,spacing=5)
        self.rpm_big=self.label("--","hero")
        unit=self.label("RPM","blue")
        unit.set_valign(Gtk.Align.CENTER)
        rpmrow.append(self.rpm_big)
        rpmrow.append(unit)
        fs.append(rpmrow)
        self.fan_percent=self.label("-- %","hero blue")
        fs.append(self.fan_percent)
        self.fan_live_curve=Sparkline()
        fs.append(self.fan_live_curve)

        self.fan_curve_button=Gtk.Button(label="✤ FAN CURVE")
        self.fan_curve_button.add_css_class("outline-button")
        self.fan_curve_button.connect("clicked",lambda btn:(self.pulse_button(btn),self.toggle_fan_curve()))
        fs.append(self.fan_curve_button)
        fan_row.append(fs)
        fan_card.append(fan_row)
        top.append(fan_card)

        sensors_box=Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=10)
        sensors_box.set_hexpand(True)
        top.append(sensors_box)

        row1=Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL,spacing=10)
        row1.set_hexpand(True)
        row2=Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL,spacing=10)
        row2.set_hexpand(True)
        sensors_box.append(row1)
        sensors_box.append(row2)

        self.metrics={
            "temp":MetricCard("♨","GPU TEMP","°C"),
            "freq":MetricCard("▣","GPU CORE","MHz"),
            "power":MetricCard("↯","GPU POWER","W"),
            "volt":MetricCard("↯","GPU VOLTAGE","mV"),
            "mclk":MetricCard("▤","VRAM CLOCK","MHz"),
            "cpu":MetricCard("▣","CPU TEMP","°C"),
            "ssd":MetricCard("▤","SSD TEMP","°C")
        }
        for k in ["temp","freq","power"]:
            row1.append(self.metrics[k])
        for k in ["volt","mclk","cpu","ssd"]:
            row2.append(self.metrics[k])

        # Fan curve drawer is full width below fan + sensors.
        self.fan_curve_holder=Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.fan_curve_holder.set_hexpand(True)
        self.fan_curve_holder.append(self.build_fan_curve_panel())
        page.append(self.fan_curve_holder)

        mid=Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL,spacing=10)
        mid.set_hexpand(True)
        page.append(mid)

        tune=self.card("CORE CLOCK")
        tune.set_hexpand(True)
        current_card=Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=4)
        current_card.add_css_class("clock-mini-card")
        current_card.set_hexpand(True)
        current_card.append(self.label("CURRENT CLOCK","small"))
        self.current_clock_big=self.label("-- MHz","hero blue")
        self.current_clock_big.set_halign(Gtk.Align.CENTER)
        current_card.append(self.current_clock_big)
        tune.append(current_card)

        tune.append(self.label("CORE OVERCLOCK","small"))
        self.clock_big=self.label("2000 MHz","hero blue"); self.clock_big.set_halign(Gtk.Align.CENTER); tune.append(self.clock_big)
        self.clock_scale=Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL,350,2150,25); self.clock_scale.set_value(2000); self.clock_scale.set_draw_value(False); self.clock_scale.connect("value-changed",self.on_clock_changed); tune.append(self.clock_scale)

        self.core_steps_button=Gtk.Button(label="▾ SHOW ALL CLOCK / VOLTAGE STEPS")
        self.core_steps_button.add_css_class("outline-button")
        self.core_steps_button.connect("clicked",lambda btn:(self.pulse_button(btn),self.toggle_core_steps()))
        tune.append(self.core_steps_button)

        self.voltage_curve_button=Gtk.Button(label="▾ SHOW VOLTAGE CURVE 1500+ MHz")
        self.voltage_curve_button.add_css_class("outline-button")
        self.voltage_curve_button.set_tooltip_text("Open the editable voltage curve. Lower boot/idle points stay hidden and unchanged.")
        self.voltage_curve_button.connect("clicked",lambda btn:(self.pulse_button(btn),self.toggle_voltage_curve()))
        tune.append(self.voltage_curve_button)

        self.voltage_curve_revealer=Gtk.Revealer()
        self.voltage_curve_revealer.set_transition_type(Gtk.RevealerTransitionType.SLIDE_DOWN)
        self.voltage_curve_revealer.set_transition_duration(260)
        voltage_panel=Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=6)
        voltage_panel.add_css_class("core-steps-panel")
        voltage_panel.append(self.label("VOLTAGE CURVE 1500+ MHz (mV)","title"))
        vhint=Gtk.Label(label="Only performance points from 1500 MHz upward are shown. Idle/low-clock voltage points are kept unchanged for safety.",xalign=0)
        vhint.add_css_class("small")
        vhint.set_wrap(True)
        voltage_panel.append(vhint)
        self.voltage_grid=Gtk.Grid(column_spacing=7,row_spacing=2)
        self.voltage_grid.set_column_homogeneous(True)
        voltage_panel.append(self.voltage_grid)
        self.voltage_curve_revealer.set_child(voltage_panel)
        tune.append(self.voltage_curve_revealer)

        self.core_steps_revealer=self.build_core_steps_panel()
        tune.append(self.core_steps_revealer)

        br=Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL,spacing=8)
        apply=Gtk.Button(label="APPLY OVERCLOCK")
        self.oc_apply_button = apply
        apply.add_css_class("blue-button")
        apply.set_tooltip_text("Apply the staged clock/voltage values now. Sliders only stage values until this is clicked.")
        apply.connect("clicked",lambda btn:(self.pulse_button(btn),self.apply_all()))
        save_boot=Gtk.Button(label="SAVE FOR BOOT")
        save_boot.add_css_class("outline-button")
        save_boot.set_tooltip_text("Save this overclock profile for startup/boot use without stress testing.")
        save_boot.connect("clicked",lambda btn:(self.pulse_button(btn),self.save_profile()))
        reset=Gtk.Button(label="REVERT")
        reset.add_css_class("outline-button")
        reset.set_tooltip_text("Revert the staged sliders to the selected profile.")
        reset.connect("clicked",lambda btn:(self.pulse_button(btn),self.load_profile("My Profile")))
        self.live_preview_check=Gtk.CheckButton(label="LIVE PREVIEW")
        self.live_preview_check.set_tooltip_text("Optional. Only works when the governor exposes a safe live backend; otherwise values remain staged.")
        br.append(apply)
        br.append(save_boot)
        br.append(reset)
        br.append(self.live_preview_check)
        tune.append(br)

        hint=Gtk.Label(label="Workflow: move sliders → Apply Overclock → Save for Boot only after validating with your own workload.",xalign=0)
        hint.set_wrap(True)
        hint.add_css_class("small")
        tune.append(hint)
        mid.append(tune)

        profile=self.card("SNAPSHOT / BOOT SAVE")
        profile.set_hexpand(True)
        self.profile_combo=Gtk.DropDown.new_from_strings(["My Profile"])
        profile.append(self.profile_combo)
        self.profile_name_entry=Gtk.Entry()
        self.profile_name_entry.set_placeholder_text("Snapshot name")
        profile.append(self.profile_name_entry)

        pr=Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL,spacing=8)
        save=Gtk.Button(label="SAVE SNAPSHOT")
        save.add_css_class("blue-button")
        save.connect("clicked",lambda btn:(self.pulse_button(btn),self.save_profile()))
        delete=Gtk.Button(label="DELETE")
        delete.add_css_class("red-button")
        delete.connect("clicked",lambda btn:(self.pulse_button(btn),self.delete_profile()))
        pr.append(save)
        pr.append(delete)
        profile.append(pr)
        mid.append(profile)

        status=self.card("STATUS")
        status.set_hexpand(True)
        self.status_list=Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=5)
        status.append(self.status_list)
        self.result=self.card(green=True)
        rr=Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL,spacing=10)
        rr.append(self.label("✓","hero green"))
        self.result_text=Gtk.Label(label="COMPLETED\nAll changes applied successfully.",xalign=0)
        rr.append(self.result_text)
        self.result.append(rr)
        status.append(self.result)
        mid.append(status)

        footer=Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL,spacing=18)
        footer.add_css_class("footer")
        page.append(footer)
        footer.append(self.label("▣ GPU: BC-250","small"))
        footer.append(self.label("⚙ DRIVER: amdgpu","small"))
        footer.append(self.label("▣ LAYOUT: responsive","small"))
        spacer=Gtk.Box()
        spacer.set_hexpand(True)
        footer.append(spacer)
        footer.append(self.label("● System Healthy","green"))

        self.stack.add_titled(scroll,"gpu","GPU Overclock")

    def toggle_voltage_curve(self):
        state=not self.voltage_curve_revealer.get_reveal_child()
        self.voltage_curve_revealer.set_reveal_child(state)
        if hasattr(self,"voltage_curve_button"):
            self.voltage_curve_button.remove_css_class("outline-button")
            self.voltage_curve_button.remove_css_class("nav-btn-active")
            self.voltage_curve_button.add_css_class("nav-btn-active" if state else "outline-button")
            self.voltage_curve_button.set_label("▴ HIDE VOLTAGE CURVE 1500+ MHz" if state else "▾ SHOW VOLTAGE CURVE 1500+ MHz")

    def close_voltage_curve(self):
        if hasattr(self,"voltage_curve_revealer"):
            self.voltage_curve_revealer.set_reveal_child(False)
        if hasattr(self,"voltage_curve_button"):
            self.voltage_curve_button.remove_css_class("nav-btn-active")
            self.voltage_curve_button.add_css_class("outline-button")
            self.voltage_curve_button.set_label("▾ SHOW VOLTAGE CURVE 1500+ MHz")

    def build_fan_curve_panel(self):
        self.fan_curve_revealer=Gtk.Revealer(); self.fan_curve_revealer.set_transition_type(Gtk.RevealerTransitionType.SLIDE_DOWN); self.fan_curve_revealer.set_transition_duration(260)
        panel=Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=8); panel.add_css_class("fan-curve-panel"); panel.set_hexpand(True)
        panel.append(self.label("FAN CURVE  •  Drag points or edit the table","title"))
        prof=Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL,spacing=8); prof.append(self.label("PROFILE","small"))
        self.fan_curve_profile_combo=Gtk.DropDown.new_from_strings(["Default"]); self.fan_curve_profile_combo.set_size_request(180,-1); prof.append(self.fan_curve_profile_combo)
        for label,cb,cls in [("LOAD",self.load_fan_curve_profile,"outline-button"),("SAVE PROFILE",self.save_fan_curve_profile,"blue-button"),("DELETE",self.delete_fan_curve_profile,"red-button")]:
            b=Gtk.Button(label=label); b.add_css_class(cls); b.connect("clicked",lambda btn,f=cb:(self.pulse_button(btn),f())); prof.append(b)
        self.fan_curve_profile_entry=Gtk.Entry(); self.fan_curve_profile_entry.set_placeholder_text("New fan curve profile name"); self.fan_curve_profile_entry.set_hexpand(True); prof.append(self.fan_curve_profile_entry)
        panel.append(prof)

        body=Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL,spacing=12); body.set_hexpand(True); panel.append(body)
        left=Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=8); left.set_size_request(300,-1); body.append(left)
        grid=Gtk.Grid(column_spacing=10,row_spacing=8); grid.set_column_homogeneous(True)
        for c,h in enumerate(["TEMP °C","PWM %","PWM RAW"]):
            lab=self.label(h,"small"); lab.set_halign(Gtk.Align.CENTER); grid.attach(lab,c,0,1,1)
        self.fan_curve_rows=[]
        for r,(temp,pwm) in enumerate([(35,30),(45,45),(55,60),(65,75),(75,90),(85,100)],start=1):
            ts=Gtk.SpinButton.new_with_range(20,100,1); ts.set_value(temp); ts.set_digits(0)
            ps=Gtk.SpinButton.new_with_range(0,100,1); ps.set_value(pwm); ps.set_digits(0)
            raw=Gtk.Label(label=str(round(pwm*255/100))); raw.set_halign(Gtk.Align.CENTER)
            def update(_spin, raw_label=raw, pwm_widget=ps):
                raw_label.set_label(str(round(int(pwm_widget.get_value())*255/100)))
                self.mark_pending("Fan")
                if hasattr(self,"fan_curve_chart"): self.fan_curve_chart.queue_draw()
            ts.connect("value-changed",update); ps.connect("value-changed",update)
            grid.attach(ts,0,r,1,1); grid.attach(ps,1,r,1,1); grid.attach(raw,2,r,1,1); self.fan_curve_rows.append((ts,ps,raw))
        left.append(grid)
        persist_row=Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL,spacing=8)
        self.fan_keep_after_reboot=Gtk.CheckButton(label="Keep after reboot")
        self.fan_keep_after_reboot.add_css_class("small")
        persist_row.append(self.fan_keep_after_reboot)
        left.append(persist_row)

        ar=Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL,spacing=8)
        for label,cb,cls in [("TEST MAX RPM",self.test_fan_max_rpm,"outline-button"),("APPLY & SAVE FAN SETTINGS",self.apply_and_save_fan_settings,"blue-button"),("RETURN TO AUTO",self.return_fan_to_auto,"outline-button"),("CLOSE",self.close_fan_curve,"outline-button")]:
            b=Gtk.Button(label=label); b.add_css_class(cls); b.connect("clicked",lambda btn,f=cb:(self.pulse_button(btn),f())); ar.append(b)
        left.append(ar)
        hint=Gtk.Label(label="Apply & Save writes the current fan curve, applies it immediately, and enables reboot restore when checked.",xalign=0); hint.add_css_class("small"); hint.set_wrap(True); left.append(hint)
        right=Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=6); right.set_hexpand(True); right.append(self.label("CURVE PREVIEW  •  TEMP / PWM / RPM","title"))
        self.fan_curve_chart=FanCurveChart(self.get_fan_curve_points,self.set_fan_curve_point,self.get_max_fan_rpm); self.fan_curve_chart.set_hexpand(True); right.append(self.fan_curve_chart); body.append(right)
        self.fan_curve_revealer.set_child(panel); GLib.timeout_add(100,self.load_fan_curve_profiles); return self.fan_curve_revealer

    def toggle_fan_curve(self):
        state=not self.fan_curve_revealer.get_reveal_child(); self.fan_curve_revealer.set_reveal_child(state)
        self.fan_curve_button.remove_css_class("outline-button"); self.fan_curve_button.remove_css_class("nav-btn-active")
        self.fan_curve_button.add_css_class("nav-btn-active" if state else "outline-button")
    def close_fan_curve(self):
        self.fan_curve_revealer.set_reveal_child(False); self.fan_curve_button.remove_css_class("nav-btn-active"); self.fan_curve_button.add_css_class("outline-button")

    def fan_curve_profiles_path(self):
        path=os.path.expanduser("~/.config/cyan-skillfish/fan_curves.json"); os.makedirs(os.path.dirname(path),exist_ok=True); return path
    def read_fan_curve_profiles(self):
        default={"Default":[(35,30),(45,45),(55,60),(65,75),(75,90),(85,100)]}
        try:
            if not os.path.exists(self.fan_curve_profiles_path()): return default
            data=json.load(open(self.fan_curve_profiles_path(),"r",encoding="utf-8"))
            if "Default" not in data: data["Default"]=default["Default"]
            return data
        except Exception: return default
    def write_fan_curve_profiles(self,profiles):
        json.dump(profiles,open(self.fan_curve_profiles_path(),"w",encoding="utf-8"),indent=2)
    def load_fan_curve_profiles(self):
        if not hasattr(self,"fan_curve_profile_combo"): return False
        profiles=self.read_fan_curve_profiles(); names=sorted(profiles.keys())
        if "Default" in names: names.remove("Default"); names.insert(0,"Default")
        self.fan_curve_profile_combo.set_model(Gtk.StringList.new(names)); self.fan_curve_profile_combo.set_selected(0); return False
    def selected_fan_curve_profile_name(self):
        model=self.fan_curve_profile_combo.get_model(); item=model.get_item(self.fan_curve_profile_combo.get_selected()) if model else None
        return item.get_string() if item else "Default"
    def apply_fan_curve_points_to_rows(self,points):
        for idx,(temp,pwm) in enumerate(points[:len(self.fan_curve_rows)]):
            ts,ps,raw=self.fan_curve_rows[idx]; ts.set_value(int(temp)); ps.set_value(int(pwm)); raw.set_label(str(round(int(pwm)*255/100)))
        self.fan_curve_chart.queue_draw()
    def load_fan_curve_profile(self):
        name=self.selected_fan_curve_profile_name(); pts=self.read_fan_curve_profiles().get(name)
        if pts: self.apply_fan_curve_points_to_rows(pts); self.add_status(f"Loaded fan curve profile: {name}")
    def save_fan_curve_profile(self):
        name=self.fan_curve_profile_entry.get_text().strip() or self.selected_fan_curve_profile_name() or "Default"
        profiles=self.read_fan_curve_profiles(); profiles[name]=self.get_fan_curve_points(); self.write_fan_curve_profiles(profiles); self.load_fan_curve_profiles(); self.add_status(f"Saved fan curve profile: {name}")
    def delete_fan_curve_profile(self):
        name=self.selected_fan_curve_profile_name()
        if name=="Default": self.add_status("Default fan curve profile cannot be deleted"); return
        profiles=self.read_fan_curve_profiles(); profiles.pop(name,None); self.write_fan_curve_profiles(profiles); self.load_fan_curve_profiles(); self.add_status(f"Deleted fan curve profile: {name}")
    def fan_calibration_path(self):
        path = getattr(self, "fan_calibration_file", os.path.join(os.path.expanduser("~"), ".config", "skillfish-tuner", "fan-calibration.json"))
        os.makedirs(os.path.dirname(path), exist_ok=True)
        return path

    def load_fan_calibration(self):
        try:
            path = self.fan_calibration_path()
            if not os.path.exists(path):
                return
            data = json.load(open(path, "r", encoding="utf-8"))
            cal = data.get("fan_calibration", data) if isinstance(data, dict) else {}
            min_rpm = int(cal.get("min_rpm", 0) or 0)
            max_rpm = int(cal.get("max_rpm", 0) or 0)
            if min_rpm > 0:
                self.min_fan_rpm = min_rpm
            if max_rpm > 0:
                self.max_fan_rpm = max_rpm
            self.add_status(f"Loaded fan calibration: min {self.min_fan_rpm or '--'} RPM / max {self.max_fan_rpm or '--'} RPM")
        except Exception as e:
            self.add_status(f"Could not load fan calibration: {e}")

    def save_fan_calibration(self, min_rpm, max_rpm):
        min_rpm = int(min_rpm or 0)
        max_rpm = int(max_rpm or 0)
        if max_rpm <= 0:
            return False
        if min_rpm <= 0 or min_rpm > max_rpm:
            min_rpm = int(getattr(self, "min_fan_rpm", 0) or 0) or max_rpm
        self.min_fan_rpm = min_rpm
        self.max_fan_rpm = max_rpm
        data = {
            "fan_calibration": {
                "min_rpm": min_rpm,
                "max_rpm": max_rpm,
                "sensor": "nct6686-isa-0a20",
                "label": "Pump Fan",
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            }
        }
        try:
            with open(self.fan_calibration_path(), "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            return True
        except Exception as e:
            self.add_status(f"Could not save fan calibration: {e}")
            return False

    def get_max_fan_rpm(self): return int(self.max_fan_rpm or 2600)
    def get_fan_curve_points(self): return sorted([(int(r[0].get_value()),int(r[1].get_value())) for r in self.fan_curve_rows])
    def set_fan_curve_point(self,index,temp,pwm):
        rows=self.fan_curve_rows
        if index<0 or index>=len(rows): return
        temp=max(20,min(100,int(temp))); pwm=max(0,min(100,int(pwm)))
        if index>0: temp=max(temp,int(rows[index-1][0].get_value())+1)
        if index<len(rows)-1: temp=min(temp,int(rows[index+1][0].get_value())-1)
        ts,ps,raw=rows[index]; ts.set_value(temp); ps.set_value(pwm); raw.set_label(str(round(pwm*255/100))); self.mark_pending("Fan"); self.fan_curve_chart.queue_draw()
    def test_fan_max_rpm(self):
        # The max-RPM test can block while the controller ramps the fan and
        # waits for sensors to settle.  Never run it on the GTK thread.
        if getattr(self, "fan_test_running", False):
            self.add_status("Max RPM test already running")
            return
        self.fan_test_running = True
        self.add_status("Testing maximum fan RPM...")
        if hasattr(self, "set_task_result"):
            self.set_task_result("Fan Max RPM", "WORKING", "Testing fan maximum RPM…")

        def worker():
            res = call("fan_test_max")
            GLib.idle_add(self.finish_fan_max_rpm_test, res)

        threading.Thread(target=worker, daemon=True).start()

    def finish_fan_max_rpm_test(self, res):
        self.fan_test_running = False
        maxrpm = 0
        minrpm = 0
        samples = []
        for line in str(res).splitlines():
            if line.startswith("MAX_RPM="):
                try:
                    maxrpm = int(line.split("=", 1)[1].strip())
                except Exception:
                    pass
            elif line.startswith("MIN_RPM="):
                try:
                    minrpm = int(line.split("=", 1)[1].strip())
                except Exception:
                    pass
            elif "rpm=" in line:
                try:
                    samples.append(int(line.rsplit("rpm=", 1)[1].strip()))
                except Exception:
                    pass
        valid_samples = [v for v in samples if v > 0]
        if not maxrpm and valid_samples:
            maxrpm = max(valid_samples)
        if not minrpm and valid_samples:
            minrpm = min(valid_samples)
        if maxrpm > 0:
            self.save_fan_calibration(minrpm, maxrpm)
            rows = self.fan_curve_rows
            if rows:
                rows[-1][1].set_value(100)
                rows[-1][2].set_label("255")
            self.fan_curve_chart.queue_draw()
            self.add_status(f"Fan calibration saved: min {self.min_fan_rpm} RPM / max {self.max_fan_rpm} RPM")
            if hasattr(self, "set_task_result"):
                self.set_task_result("Fan Calibration", "COMPLETED", f"✓ Fan calibration saved: {self.min_fan_rpm}-{self.max_fan_rpm} RPM")
        else:
            self.add_status("Fan max RPM test failed")
            if hasattr(self, "set_task_result"):
                self.set_task_result("Fan Calibration", "ERROR", "✗ Fan calibration failed")
        print(res)
        return False
    def fan_profile_path(self):
        path = os.path.join(os.path.expanduser("~"), ".config", "skillfish-tuner", "fan-profile.json")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        return path

    def calculate_curve_pwm_for_temp(self, temp=None):
        try:
            temp = float(temp if temp is not None else getattr(self, "last_gpu_temp", 0) or 0)
        except Exception:
            temp = 0
        pwm = 30
        for t, p in self.get_fan_curve_points():
            if temp >= int(t):
                pwm = int(p)
        return max(0, min(100, int(pwm)))

    def save_current_fan_settings(self, applied_pwm=None, mode="curve"):
        points = self.get_fan_curve_points()
        pwm = self.calculate_curve_pwm_for_temp()
        if applied_pwm is not None:
            pwm = max(0, min(100, int(applied_pwm)))
        data = {
            "version": 1,
            "mode": mode,
            "sensor": "nct6686-isa-0a20",
            "label": "Pump Fan",
            "curve": [{"temp_c": int(t), "pwm_percent": int(p)} for t, p in points],
            "applied_pwm_percent": int(pwm),
            "applied_pwm_raw": int(round(pwm * 255 / 100)),
            "min_rpm": int(getattr(self, "min_fan_rpm", 0) or 0),
            "max_rpm": int(getattr(self, "max_fan_rpm", 0) or 0),
            "updated": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            "note": "Generated by Skillfish Tuner. Apply Fan Settings saves automatically.",
        }
        with open(self.fan_profile_path(), "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        return data

    def apply_and_save_fan_settings(self):
        if getattr(self, "fan_apply_running", False):
            self.add_status("Fan settings are already being applied")
            return
        self.fan_apply_running = True
        self.save_last_good_full_config("before-fan-apply")
        pwm = self.calculate_curve_pwm_for_temp()
        raw = int(round(pwm * 255 / 100))
        try:
            self.save_current_fan_settings(applied_pwm=pwm, mode="curve")
        except Exception as e:
            self.fan_apply_running = False
            self.add_status(f"Could not save fan profile: {e}")
            if hasattr(self, "set_task_result"):
                self.set_task_result("Fan Settings", "ERROR", "✗ Could not save fan profile")
            return
        keep = bool(getattr(self, "fan_keep_after_reboot", None) and self.fan_keep_after_reboot.get_active())
        self.add_status(f"Applying and saving fan settings: {pwm}% / raw {raw}" + ("; reboot restore enabled" if keep else ""))
        if hasattr(self, "set_task_result"):
            self.set_task_result("Fan Settings", "WORKING", "Applying fan settings…")
        self.start_percent_progress("fan_apply", message="Applying fan settings", bar=getattr(self, "gpu_apply_progress", None), button=getattr(self, "fan_apply_button", None), button_text="Applying fan settings", delay_ms=5000)
        def worker():
            parts = [call(f"fan_pwm {raw}")]
            if keep:
                parts.append(call("fan_persist_enable " + shlex.quote(self.fan_profile_path())))
            else:
                parts.append(call("fan_persist_disable"))
            res = "\n".join(parts)
            GLib.idle_add(self.finish_apply_fan_settings, res, pwm, raw)
        threading.Thread(target=worker, daemon=True).start()

    def finish_apply_fan_settings(self, res, pwm, raw):
        self.fan_apply_running = False
        text = str(res).strip()
        if text.startswith("OK") and "\nERR" not in text and not text.startswith("ERR"):
            keep = bool(getattr(self, "fan_keep_after_reboot", None) and self.fan_keep_after_reboot.get_active())
            suffix = " + boot restore" if keep else ""
            self.add_status(f"Fan settings applied and saved: {pwm}% / raw {raw}{suffix}")
            if hasattr(self, "set_task_result"):
                self.set_task_result("Fan Settings", "COMPLETED", f"✓ Fan settings saved and applied{suffix}: {pwm}%")
            self.clear_pending("Fan")
        else:
            self.add_status(f"Fan apply failed: {res}")
            if hasattr(self, "set_task_result"):
                self.set_task_result("Fan Settings", "ERROR", "✗ Fan apply failed")
        return False

    def return_fan_to_auto(self):
        # Hand control back to the hardware/controller where pwm2_enable supports auto mode.
        try:
            self.save_current_fan_settings(applied_pwm=None, mode="auto")
        except Exception:
            pass
        self.add_status("Returning fan control to auto/unmanaged mode")
        if hasattr(self, "set_task_result"):
            self.set_task_result("Fan Auto", "WORKING", "Returning fan to auto…")
        def worker():
            res = call("fan_auto")
            GLib.idle_add(self.finish_return_fan_to_auto, res)
        threading.Thread(target=worker, daemon=True).start()

    def finish_return_fan_to_auto(self, res):
        if str(res).strip().startswith("OK"):
            self.add_status("Fan returned to auto/unmanaged mode")
            if hasattr(self, "set_task_result"):
                self.set_task_result("Fan Auto", "COMPLETED", "✓ Fan returned to auto")
        else:
            self.add_status(f"Fan auto failed: {res}")
            if hasattr(self, "set_task_result"):
                self.set_task_result("Fan Auto", "ERROR", "✗ Fan auto failed")
        return False

    def apply_current_curve_pwm(self):
        temp=getattr(self,"last_gpu_temp",0); pwm=30
        for t,p in self.get_fan_curve_points():
            if temp>=t: pwm=p
        raw=round(pwm*255/100); print(call(f"fan_pwm {raw}")); self.add_status(f"Fan curve applied: {pwm}% / raw {raw}")

    # Governor / CU helpers
    def run_action(self,label,cmd,button=None):
        if getattr(self, "action_running", False):
            self.add_status("Another task is already running")
            return
        self.action_running = True
        self.busy_title = label
        self.busy_dots = 0
        self.set_action_buttons_sensitive(False)
        self.set_button_busy(button, label)
        self.set_task_result(label,"WORKING","Running command…")
        self.start_percent_progress("task_action", message="Loading", bar=getattr(self, "gov_task_progress", None), button=button, button_text="Loading", delay_ms=5000)
        self.busy_timer = GLib.timeout_add(280, self.animate_running_task)

        def worker():
            res = call(cmd)
            GLib.idle_add(self.finish_action, label, cmd, res, button)
        threading.Thread(target=worker, daemon=True).start()

    def finish_action(self,label,cmd,res,button=None):
        if getattr(self, "busy_timer", None):
            GLib.source_remove(self.busy_timer)
            self.busy_timer = None
        low=res.lower()
        if cmd == "gov_deploy":
            status="ERROR" if res.startswith("ERR") or "\nERR" in res or "traceback" in low else "COMPLETED"
        else:
            status="ERROR" if res.startswith("ERR") or "failed" in low or "traceback" in low or "not active" in low else "COMPLETED"
        display_res = res
        if cmd == "cu_status_json" and status == "COMPLETED":
            self.update_cu_dashboard_from_json(res)
            display_res = self.short_cu_topology_result(res)
        if cmd == "cu_setup" and status == "COMPLETED":
            # Refresh after the combined setup/check workflow, but keep setup log visible.
            GLib.timeout_add_seconds(1, self.refresh_cu_dashboard)
        self.stop_percent_progress("task_action", ok=(status=="COMPLETED"), hide=False, restore_button=False)
        self.set_task_result(label,status,display_res)
        self.add_status(f"{label}: {status}")
        self.set_button_done(button, label, status)
        self.set_action_buttons_sensitive(True)
        self.action_running = False
        GLib.timeout_add(250,self.refresh)
        GLib.timeout_add_seconds(3,self.refresh)
        if cmd in ("cu_umr", "cu_setup") and status == "COMPLETED" and ("reboot" in low or "restart" in low or "rpm-ostree" in low):
            GLib.timeout_add(250, self.show_umr_restart_dialog)
        if cmd in ("cu_enable_persist", "cu_activate_spi", "cu_stock_persist", "cu_save") and status == "COMPLETED":
            GLib.timeout_add(250, self.show_cu_restart_dialog)
        if cmd == "gov_deploy" and status == "COMPLETED" and "RESTART_REQUIRED=1" in res:
            self._set_health("governor", "installed-restart-pending")
            self.gov_service_label.set_label("Governor Service: Installed — restart pending")
            GLib.timeout_add(250, self.show_governor_restart_dialog)
        return False

    def animate_running_task(self):
        if not getattr(self, "action_running", False):
            return False
        self.busy_dots = (getattr(self, "busy_dots", 0) + 1) % 4
        dots = "." * self.busy_dots
        self.set_task_result(self.busy_title, "WORKING", f"Running{dots}")
        return True

    def _progress_label(self, message, pct):
        base = str(message or "Applying…")
        if not base.endswith("…") and not base.endswith("..."):
            base = base.rstrip(".") + "…"
        return f"{base} {pct}%"

    def start_percent_progress(self, name, message="Applying…", bar=None, button=None, button_text=None, delay_ms=5000):
        """Show a percentage progress bar only when work lasts longer than delay_ms.

        The real command has no reliable percent output, so this is a user-facing
        estimated progress indicator capped at 95% until the task finishes.
        """
        self.stop_percent_progress(name, hide=True, restore_button=False)
        state = {
            "name": name,
            "message": message or "Applying…",
            "bar": bar,
            "button": button,
            "button_text": button_text,
            "fraction": 0.0,
            "visible": False,
            "delay_id": None,
            "timer_id": None,
            "original_button_label": button.get_label() if button else None,
        }
        if bar:
            bar.set_visible(False)
            bar.set_fraction(0.0)
            bar.set_text("Preparing…")
        if button:
            button.add_css_class("install-busy-button")
            button.add_css_class("pulse-button")
            if button_text:
                button.set_label(button_text)
        if not hasattr(self, "percent_progress_states"):
            self.percent_progress_states = {}
        self.percent_progress_states[name] = state
        state["delay_id"] = GLib.timeout_add(delay_ms, self._show_percent_progress, name)

    def _show_percent_progress(self, name):
        state = getattr(self, "percent_progress_states", {}).get(name)
        if not state:
            return False
        state["delay_id"] = None
        state["visible"] = True
        state["fraction"] = max(state.get("fraction", 0.0), 0.05)
        bar = state.get("bar")
        pct = int(state["fraction"] * 100)
        if bar:
            bar.set_visible(True)
            bar.set_fraction(state["fraction"])
            bar.set_text(self._progress_label(state.get("message"), pct))
        btn = state.get("button")
        if btn:
            btn.set_label(self._progress_label(state.get("button_text") or state.get("message"), pct))
        state["timer_id"] = GLib.timeout_add(250, self._tick_percent_progress, name)
        return False

    def _tick_percent_progress(self, name):
        state = getattr(self, "percent_progress_states", {}).get(name)
        if not state:
            return False
        frac = float(state.get("fraction", 0.0))
        # Move fast at first, then slow down and cap at 95% until the task finishes.
        step = 0.018 if frac < 0.70 else 0.006
        frac = min(0.95, frac + step)
        state["fraction"] = frac
        pct = int(frac * 100)
        bar = state.get("bar")
        if bar:
            bar.set_fraction(frac)
            bar.set_text(self._progress_label(state.get("message"), pct))
        btn = state.get("button")
        if btn:
            btn.set_label(self._progress_label(state.get("button_text") or state.get("message"), pct))
        return True

    def stop_percent_progress(self, name, ok=True, hide=False, restore_button=True):
        states = getattr(self, "percent_progress_states", {})
        state = states.pop(name, None)
        if not state:
            return
        for key in ("delay_id", "timer_id"):
            sid = state.get(key)
            if sid:
                try:
                    GLib.source_remove(sid)
                except Exception:
                    pass
        bar = state.get("bar")
        if bar:
            if state.get("visible") and not hide:
                bar.set_visible(True)
                bar.set_fraction(1.0 if ok else 0.0)
                bar.set_text(("Done… 100%" if ok else "Failed… 0%"))
                GLib.timeout_add_seconds(3, lambda b=bar: (b.set_visible(False), b.set_fraction(0.0), b.set_text("Ready"), False)[-1])
            else:
                bar.set_visible(False)
                bar.set_fraction(0.0)
                bar.set_text("Ready")
        btn = state.get("button")
        if btn:
            btn.remove_css_class("install-busy-button")
            btn.remove_css_class("pulse-button")
            if restore_button and state.get("original_button_label"):
                btn.set_label(state["original_button_label"])

    def start_cu_apply_feedback(self, message="Applying CU/topology changes…"):
        """Show delayed percentage feedback while CU/topology work runs."""
        for b in getattr(self, "cu_action_buttons", []):
            b.set_sensitive(False)
        btn = getattr(self, "cu_apply_button", None)
        if btn:
            btn.set_sensitive(True)
        self.start_percent_progress(
            "cu_apply",
            message=message,
            bar=getattr(self, "cu_apply_progress", None),
            button=btn,
            button_text="Applying changes…",
            delay_ms=5000,
        )

    def stop_cu_apply_feedback(self, ok=True):
        self.stop_percent_progress("cu_apply", ok=ok, hide=False, restore_button=False)
        bar = getattr(self, "cu_apply_progress", None)
        if bar:
            bar.set_fraction(1.0 if ok else 0.0)
            bar.set_text("Done… 100%" if ok else "Apply failed… 0%")
        for b in getattr(self, "cu_action_buttons", []):
            b.set_sensitive(True)
        btn = getattr(self, "cu_apply_button", None)
        if btn:
            btn.remove_css_class("install-busy-button")
            btn.remove_css_class("pulse-button")
            btn.set_label("✓ APPLY CHANGES" if ok else "✕ APPLY FAILED")
            GLib.timeout_add_seconds(3, self.restore_cu_apply_button)

    def restore_cu_apply_button(self):
        btn = getattr(self, "cu_apply_button", None)
        if btn:
            btn.set_label(getattr(btn, "_skillfish_original_label", "✓ APPLY CHANGES"))
        bar = getattr(self, "cu_apply_progress", None)
        if bar and not getattr(self, "action_running", False):
            bar.set_visible(False)
            bar.set_text("Ready")
            bar.set_fraction(0.0)
        return False

    def set_action_buttons_sensitive(self, sensitive):
        for b in getattr(self, "action_buttons", {}).values():
            b.set_sensitive(sensitive)

    def set_button_busy(self, button, label):
        if not button: return
        button.set_sensitive(True)
        button.add_css_class("install-busy-button")
        button.add_css_class("pulse-button")
        button.set_label("⟳  " + label + "  RUNNING")

    def set_button_done(self, button, label, status):
        if not button: return
        button.remove_css_class("install-busy-button")
        button.remove_css_class("pulse-button")
        if status == "COMPLETED":
            button.add_css_class("install-done-button")
            button.set_label("✓  " + label + "  DONE")
            GLib.timeout_add_seconds(3, lambda: self.restore_action_button(button, label))
        else:
            button.set_label("✕  " + label + "  ERROR")
            GLib.timeout_add_seconds(3, lambda: self.restore_action_button(button, label))

    def restore_action_button(self, button, label):
        button.remove_css_class("install-done-button")
        button.set_label(label)
        return False


    def show_restart_dialog(self, heading, body, response_handler, default_response="no"):
        """Use modern Adw.AlertDialog when available, fallback for older systems."""
        try:
            if hasattr(Adw, "AlertDialog"):
                dialog = Adw.AlertDialog(heading=heading, body=body)
                dialog.add_response("no", "Later")
                dialog.add_response("yes", "Restart Now")
                dialog.set_response_appearance("yes", Adw.ResponseAppearance.SUGGESTED)
                dialog.set_default_response(default_response)
                dialog.set_close_response("no")
                dialog.choose(self, None, response_handler)
                return False
        except Exception as e:
            self.add_status(f"Modern dialog failed, using fallback: {e}")
        dialog = Adw.MessageDialog.new(self, heading, body)
        dialog.add_response("no", "Later")
        dialog.add_response("yes", "Restart Now")
        dialog.set_response_appearance("yes", Adw.ResponseAppearance.SUGGESTED)
        dialog.set_default_response(default_response)
        dialog.set_close_response("no")
        dialog.connect("response", lambda d, response: response_handler(d, response))
        dialog.present()
        return False

    def request_reboot_via_daemon(self, reason="restart"):
        self.add_status(f"Restart requested by user: {reason}")
        res = call("reboot")
        if res.startswith("ERR"):
            self.add_status(f"Could not start reboot: {res}")
        else:
            self.add_status(res)

    def show_umr_restart_dialog(self):
        return self.show_restart_dialog(
            "UMR install successful",
            "Restart is needed before Bazzite/rpm-ostree exposes the newly layered UMR package. Restart now?",
            self.on_umr_restart_response,
            default_response="yes",
        )

    def on_umr_restart_response(self, dialog, response):
        if response == "yes":
            self.request_reboot_via_daemon("UMR install")
        else:
            self.add_status("Restart skipped. Reboot later to activate UMR.")


    def show_governor_restart_dialog(self):
        return self.show_restart_dialog(
            "Governor installed successfully",
            "The latest cyan-skillfish-governor-smu was deployed. Restart is required on Bazzite/rpm-ostree to activate the new deployment. Restart now?",
            self.on_governor_restart_response,
            default_response="yes",
        )

    def on_governor_restart_response(self, dialog, response):
        if response == "yes":
            self.request_reboot_via_daemon("governor deployment")
        else:
            self.add_status("Restart skipped. Reboot later to activate the governor.")

    def show_cu_restart_dialog(self):
        return self.show_restart_dialog(
            "Hybrid unlock successfully installed",
            "CU configuration was applied successfully and saved for reboot. A system reboot is required for the new boot settings to take effect. Restart now?",
            self.on_cu_restart_response,
            default_response="no",
        )

    def on_cu_restart_response(self, dialog, response):
        if response == "yes":
            self.request_reboot_via_daemon("CU persistence save")
        else:
            self.add_status("Restart skipped. Reboot later to keep the CU configuration after restart.")

    def short_cu_topology_result(self, raw):
        """Return a compact user-facing summary for CU refresh.

        The full JSON/topology dump is still used internally to update the grid,
        but the Task Result panel should stay readable.
        """
        try:
            data = json.loads(raw)
            active = data.get("effective_active") or data.get("spi_total") or data.get("driver_active") or "--"
            disabled = self.cu_disabled_from_effective(active)
            umr = "ready" if data.get("umr_ok") else "missing"
            manager = "ready" if data.get("manager_ok") else "missing"
            staged = len(getattr(self, "cu_staged", {}) or {})
            extra = f"\nStaged changes: {staged}" if staged else ""
            return f"CU topology refreshed.\nActive CUs: {active}\nDisabled CUs: {disabled}\nUMR: {umr} · CU manager: {manager}{extra}"
        except Exception:
            return "CU topology refreshed."

    def set_task_result(self,title,status,text):
        # Compact fixed-height task banner: never show raw command output here.
        # Verbose details are kept in the regular status/log output.
        title_clean = str(title or "Task").replace("🧰", "").replace("⟳", "").replace("✓", "").replace("◆", "").replace("↺", "").replace("🐟", "").strip()
        raw = str(text or "")
        low = raw.lower()
        for cls in ("task-result-success", "task-result-error", "task-result-warning", "task-result-working"):
            self.gov_result_card.remove_css_class(cls)
        if status == "WORKING":
            self.gov_result_card.add_css_class("task-result-working")
            self.gov_result.set_label(f"⟳ {title_clean} running…")
        elif status == "ERROR":
            self.gov_result_card.add_css_class("task-result-error")
            self.gov_result.set_label(f"✕ {title_clean} failed — log: /tmp/skillfish-tuner-latest.log")
        elif "reboot" in low or "restart" in low or "restart_required=1" in raw:
            self.gov_result_card.add_css_class("task-result-warning")
            self.gov_result.set_label(f"⚠ {title_clean} complete — restart required")
        else:
            self.gov_result_card.add_css_class("task-result-success")
            if "refresh cu topology" in title_clean.lower() or "cu_status_json" in title_clean.lower() or "auto refresh topology" in title_clean.lower():
                self.gov_result.set_label("✓ CU topology refreshed")
            elif "apply" in title_clean.lower() or "cu changes" in title_clean.lower():
                self.gov_result.set_label("✓ CU configuration applied")
            elif "setup" in title_clean.lower():
                self.gov_result.set_label("✓ Setup/check completed")
            elif "governor" in title_clean.lower() and "deploy" in title_clean.lower():
                self.gov_result.set_label("✓ Governor deployed")
            else:
                self.gov_result.set_label(f"✓ {title_clean} successful")
    def add_status(self,msg):
        if not hasattr(self,"status_list"): return
        row=Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL,spacing=8); row.append(self.label("●","green"))
        label=Gtk.Label(label=msg,xalign=0); row.append(label); row.append(self.label(time.strftime("%H:%M:%S"),"small")); self.status_list.append(row)

    def load_cu_staged(self):
        try:
            with open(self.cu_stage_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.cu_staged = data if isinstance(data, dict) else {}
        except Exception:
            self.cu_staged = {}

    def save_cu_staged(self):
        try:
            os.makedirs(os.path.dirname(self.cu_stage_file), exist_ok=True)
            with open(self.cu_stage_file, "w", encoding="utf-8") as f:
                json.dump(self.cu_staged, f, indent=2, sort_keys=True)
        except Exception as e:
            self.add_status(f"Could not save staged CU changes: {e}")

    def clear_cu_staged_file(self):
        self.cu_staged.clear()
        try:
            if os.path.exists(self.cu_stage_file):
                os.remove(self.cu_stage_file)
        except Exception:
            pass
        self.clear_pending("CU")

    def draw_cu_grid_into(self,grid,data):
        while child:=grid.get_first_child(): grid.remove(child)
        headers=["","WGP0\n0-1","WGP1\n2-3","WGP2\n4-5","WGP3\n6-7","WGP4\n8-9"]
        for c,h in enumerate(headers):
            lab=self.label(h,"small"); lab.set_justify(Gtk.Justification.CENTER); grid.attach(lab,c,0,1,1)
        for r,row in enumerate(data.get("rows",[]),start=1):
            rn=row.get("row","--"); lab=self.label(rn.replace("."," "),"small"); lab.set_halign(Gtk.Align.CENTER); grid.attach(lab,0,r,1,1)
            for c,wgp in enumerate(row.get("wgps",[]),start=1):
                key=f"{rn}:{wgp.get('name',f'WGP{c-1}')}"
                state=wgp.get("color_state") or ("active" if wgp.get("driver") else ("spi" if wgp.get("spi_only") else "off"))
                staged=self.cu_staged.get(key)
                # If a pending stage is already reflected by the effective/SPI state,
                # it is no longer pending. Do not keep showing the yellow diamond.
                if (staged == "activate" and state in ("active", "spi")) or (staged == "deactivate" and state == "off"):
                    self.cu_staged.pop(key, None)
                    staged = None
                    try:
                        self.save_cu_staged()
                    except Exception:
                        pass
                btn=Gtk.Button(); btn.add_css_class("cu-cell")
                cls,dot = {"active":("cu-active","green"),"spi":("cu-active","green"),"off":("cu-off","red")}.get(state,("cu-off","red"))
                btn.add_css_class(cls)
                # Green circle = active/effective. Yellow diamond = only staged/pending.
                symbol = "◆" if staged=="activate" else ("◇" if staged=="deactivate" else "●")
                if staged:
                    dot="yellow"
                    btn.add_css_class("cu-staged")
                box=Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL,spacing=5); box.append(self.label(symbol,dot)); box.append(self.label(wgp.get("name",f"WGP{c-1}"),"small")); btn.set_child(box)
                btn.connect("clicked",lambda _,k=key,st=state:self.tile_clicked(k,st)); grid.attach(btn,c,r,1,1)
    def tile_clicked(self,key,state):
        if self.cu_staged.get(key):
            del self.cu_staged[key]
        else:
            self.cu_staged[key]="deactivate" if state=="active" else "activate"
        self.save_cu_staged()
        self.draw_cu_from_last()
        self.mark_pending("CU") if self.cu_staged else self.clear_pending("CU")
        self.add_status(f"CU staged: {len(self.cu_staged)} pending change(s)")
    def draw_cu_from_last(self):
        if hasattr(self,"gov_cu_grid"): self.draw_cu_grid_into(self.gov_cu_grid,getattr(self,"last_cu_data",{}))
    def auto_refresh_cu_topology_on_startup(self):
        """Refresh CU topology once after the window opens without blocking GTK."""
        self.set_task_result("AUTO REFRESH TOPOLOGY", "WORKING", "Checking GPU topology…")
        self.add_status("Auto refreshing CU topology on startup")
        def worker():
            raw = call("cu_status_json")
            GLib.idle_add(self.finish_auto_refresh_cu_topology, raw)
        threading.Thread(target=worker, daemon=True).start()
        return False

    def finish_auto_refresh_cu_topology(self, raw):
        ok = self.update_cu_dashboard_from_json(raw, quiet=True)
        if ok:
            self.set_task_result("AUTO REFRESH TOPOLOGY", "COMPLETED", "Topology refreshed")
        else:
            self.set_task_result("AUTO REFRESH TOPOLOGY", "ERROR", raw or "No CU topology data returned")
        return False

    def refresh_cu_dashboard(self,*_):
        raw=call("cu_status_json")
        return self.update_cu_dashboard_from_json(raw)

    def cu_disabled_from_effective(self, effective):
        try:
            if isinstance(effective, str) and "/" in effective:
                a, total = effective.split("/", 1)
                return f"{max(0, int(total.strip()) - int(a.strip()))}/{int(total.strip())}"
            if isinstance(effective, int):
                return f"{max(0, 40 - effective)}/40"
        except Exception:
            pass
        return "--"


    def parse_cu_count_pair(self, value):
        try:
            if isinstance(value, str) and "/" in value:
                a, total = value.split("/", 1)
                return max(0, int(a.strip())), max(1, int(total.strip()))
            if isinstance(value, int):
                return max(0, value), 40
        except Exception:
            pass
        return None, 40

    def update_cu_summary_gauge(self, active_value):
        active, total = self.parse_cu_count_pair(active_value)
        if active is None:
            active, total = 0, 40
            self.gov_active_cu_big.set_label("-- / 40")
            self.gov_cu_gauge_caption.set_label("Waiting for topology refresh…")
            self.gov_cu_gauge.set_counts(active, total)
            return
        # BC250 has 40 CUs physically. Treat 40 as 100% even when driver
        # reports a lower factory topology. The gauge follows effective/SPI count.
        total = 40
        active = min(max(0, int(active)), total)
        disabled = max(0, total - active)
        pct = round((active / total) * 100)
        self.gov_cu_gauge.set_counts(active, total)
        self.gov_active_cu_big.set_label(f"{active} / {total} CUs")
        self.gov_cu_gauge_caption.set_label(f"{pct}% active · {disabled} inactive · 20 CU-pair segments")

    def update_cu_dashboard_from_json(self, raw, quiet=False):
        try:
            data=json.loads(raw)
        except Exception:
            if not quiet:
                self.set_task_result("REFRESH CU TOPOLOGY","ERROR",raw or "No CU topology data returned")
            self.add_status("Refresh CU topology failed - check UMR/CU requirements")
            return False
        self.last_cu_data=data
        self.umr_badge.set_label("● UMR READY" if data.get("umr_ok") else "● UMR MISSING")
        self.cu_badge.set_label("● CU MANAGER READY" if data.get("manager_ok") else "● CU MANAGER MISSING")
        effective = data.get("effective_active") or data.get("spi_total") or data.get("driver_active") or "-- / --"
        self.update_cu_summary_gauge(effective)
        self.update_dashboard_cu(effective)
        self.draw_cu_from_last(); self.draw_umr_info(data)
        self.maybe_create_factory_cu_backup()
        self.add_status("CU topology refreshed")
        return True if quiet else False
    def draw_umr_info(self,data):
        while child:=self.gov_umr_info.get_first_child(): self.gov_umr_info.remove(child)
        rows=[("UMR PATH",data.get("umr_path") or "--"),("ASIC","cyan_skillfish.gfx1013"),("ACTIVE COUNT","Effective / SPI dispatch"),("BOOT METHOD","kargs + saved live table"),("RUNTIME FIX","systemd restore before governor")]
        for r,(k,v) in enumerate(rows):
            self.gov_umr_info.attach(self.label(k,"small"),0,r,1,1); self.gov_umr_info.attach(Gtk.Label(label=str(v),xalign=0),1,r,1,1); self.gov_umr_info.attach(self.label("✓","green"),2,r,1,1)
    def cu_key_to_disable_triplet(self,key):
        import re
        m=re.match(r"SE(\d+)\.SH(\d+):WGP(\d+)$", key or "")
        if not m: return None
        return f"{int(m.group(1))}.{int(m.group(2))}.{int(m.group(3))}"



    def build_cu_backup_payload(self, label="backup", persist=False, staged_snapshot=None):
        """Create a portable CU topology backup from the last refreshed topology."""
        mask, active = self.compute_selected_cu_mask(staged_snapshot if staged_snapshot is not None else {})
        data = getattr(self, "last_cu_data", {}) or {}
        rows = data.get("rows", [])
        return {
            "label": label,
            "created_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            "disable_mask": mask,
            "expected_active": active,
            "disabled_cus": max(0, 40 - int(active or 0)),
            "persist": bool(persist),
            "source": "Skillfish Tuner first-run/current-topology backup",
            "driver_active": data.get("driver_active"),
            "effective_active": data.get("effective_active") or data.get("spi_total"),
            "rows": rows,
        }

    def maybe_create_factory_cu_backup(self):
        """On first successful topology refresh, preserve the original card state forever."""
        try:
            if os.path.exists(self.cu_factory_file):
                return False
            data = getattr(self, "last_cu_data", {}) or {}
            if not data.get("rows"):
                return False
            os.makedirs(self.cu_backup_dir, exist_ok=True)
            payload = self.build_cu_backup_payload(label="factory-original", persist=True, staged_snapshot={})
            with open(self.cu_factory_file, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2, sort_keys=True)
            self.add_status("Factory CU topology backup saved")
            self.set_task_result("FACTORY BACKUP", "COMPLETED", "✓ Original CU topology backed up")
            return True
        except Exception as e:
            self.add_status(f"Factory CU backup failed: {e}")
            return False

    def save_current_topology_backup(self, path, label="last-good", persist=False):
        try:
            data = getattr(self, "last_cu_data", {}) or {}
            if not data.get("rows"):
                return False
            os.makedirs(os.path.dirname(path), exist_ok=True)
            payload = self.build_cu_backup_payload(label=label, persist=persist, staged_snapshot={})
            with open(path, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2, sort_keys=True)
            return True
        except Exception as e:
            self.add_status(f"Could not save {label} CU backup: {e}")
            return False

    def restore_factory_cu(self):
        self.restore_cu_backup(self.cu_factory_file, "RESTORE FACTORY TOPOLOGY")

    def restore_cu_backup(self, path, title):
        if getattr(self, "action_running", False):
            self.add_status("Another task is already running")
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            disable_mask = data.get("disable_mask", [])
            expected_active = int(data.get("expected_active", 0) or 0)
            if expected_active <= 0 and not disable_mask:
                raise ValueError("backup does not contain a valid CU mask")
        except Exception as e:
            self.set_task_result(title, "ERROR", f"No usable backup found. Refresh topology first. Details: {e}")
            return
        self.action_running=True
        self.busy_title=title
        self.busy_dots=0
        self.set_action_buttons_sensitive(False)
        self.set_task_result(title,"WORKING",f"Restoring {expected_active}/40 CU topology…")
        self.busy_timer=GLib.timeout_add(280,self.animate_running_task)
        def worker():
            try:
                payload=json.dumps({"disable_mask":disable_mask,"expected_active":expected_active})
                res=call("cu_apply_unlock "+payload)+"\nRESTART_REQUIRED=1"
            except Exception as e:
                res="ERR restore CU backup failed: "+str(e)
            GLib.idle_add(self.finish_restore_cu_backup,title,res)
        threading.Thread(target=worker,daemon=True).start()

    def finish_restore_cu_backup(self,title,res):
        if getattr(self,"busy_timer",None):
            GLib.source_remove(self.busy_timer); self.busy_timer=None
        low=res.lower()
        required_ok = "RESTART_REQUIRED=1" in res and "amdgpu.bc250_cc_write_mode=3" in res
        hard_error = res.startswith("ERR") or "\nERR " in res or "traceback" in low or "service verification failed" in low
        status = "COMPLETED" if required_ok and not hard_error else ("ERROR" if hard_error else "COMPLETED")
        self.set_task_result(title,status,"✓ CU topology restored\nRestart required to keep restored topology after reboot." if status=="COMPLETED" else res)
        if status=="COMPLETED":
            self.clear_cu_staged_file()
            self.add_status(f"{title.title()} restored; reboot required")
            GLib.timeout_add(250, self.show_cu_restart_dialog)
        else:
            self.add_status(f"{title.title()} failed")
        self.set_action_buttons_sensitive(True)
        self.action_running=False
        return False

    def save_last_good_cu_config(self, persist=False):
        """Save the currently working topology before risky changes are applied."""
        self.save_current_topology_backup(self.cu_last_good_file, label="last-good-before-change", persist=persist)

    def apply_cu_changes(self):
        """Single end-user apply button.

        If Keep after reboot is checked, run the hybrid persistence flow.
        If unchecked, apply only the pending live changes and save the live boot table.
        """
        persist = bool(getattr(self, "cu_persist_check", None) and self.cu_persist_check.get_active())
        self.save_last_good_full_config("before-cu-apply")
        if persist:
            self.apply_cu_unlock_selected()
        else:
            self.apply_cu_staged()

    def revert_last_good_cu(self):
        self.restore_cu_backup(self.cu_last_good_file, "REVERT LAST GOOD")

    def compute_selected_cu_mask(self, staged_snapshot=None):
        """Build disable_cu mask for all WGPs that should stay disabled after driver unlock."""
        data = getattr(self, "last_cu_data", {}) or {}
        staged_snapshot = staged_snapshot if staged_snapshot is not None else getattr(self, "cu_staged", {})
        mask=[]; active=0
        for row in data.get("rows", []):
            rn=row.get("row", "")
            for wgp in row.get("wgps", []):
                name=wgp.get("name", "")
                key=f"{rn}:{name}"
                state=wgp.get("color_state") or ("active" if wgp.get("driver") else ("spi" if wgp.get("spi_only") else "off"))
                desired_on = state in ("active", "spi")
                if staged_snapshot.get(key)=="activate": desired_on=True
                elif staged_snapshot.get(key)=="deactivate": desired_on=False
                trip=self.cu_key_to_disable_triplet(key)
                if desired_on:
                    active += 2
                elif trip:
                    mask.append(trip)
        return sorted(set(mask), key=lambda x: tuple(int(v) for v in x.split('.'))), active

    def apply_cu_unlock_selected(self):
        if getattr(self, "action_running", False):
            self.add_status("Another task is already running")
            return
        staged_snapshot=dict(getattr(self, "cu_staged", {}) or {})
        disable_mask, expected_active = self.compute_selected_cu_mask(staged_snapshot)
        if expected_active <= 0:
            self.set_task_result("APPLY CHANGES", "ERROR", "No selected CUs detected. Refresh topology first, then select CUs.")
            return
        self.save_last_good_cu_config(persist=True)
        self.action_running=True
        self.busy_title="APPLY CHANGES"
        self.busy_dots=0
        self.set_action_buttons_sensitive(False)
        self.set_task_result(self.busy_title,"WORKING",f"Applying hybrid unlock for {expected_active}/40 selected CUs…")
        self.start_cu_apply_feedback(f"Applying selected CU topology ({expected_active}/40 active)…")
        self.busy_timer=GLib.timeout_add(280,self.animate_running_task)
        def worker():
            outputs=[]
            try:
                # Apply selected changes live first, then install selected-only boot unlock.
                for key,val in staged_snapshot.items():
                    trip=self.cu_key_to_disable_triplet(key)
                    if not trip: continue
                    if val=="activate": outputs.append(call(f"cu_enable_wgp {trip}"))
                    elif val=="deactivate": outputs.append(call(f"cu_disable_wgp {trip}"))
                payload=json.dumps({"disable_mask":disable_mask,"expected_active":expected_active})
                outputs.append(call("cu_apply_unlock "+payload))
                outputs.append("RESTART_REQUIRED=1")
                res="\n".join(outputs)
            except Exception as e:
                res="ERR apply unlock failed: "+str(e)
            GLib.idle_add(self.finish_apply_cu_unlock_selected,res)
        threading.Thread(target=worker,daemon=True).start()

    def finish_apply_cu_unlock_selected(self,res):
        if getattr(self,"busy_timer",None):
            GLib.source_remove(self.busy_timer); self.busy_timer=None
        low=res.lower()
        # Hybrid unlock can legitimately contain WARN/optional helper wording.
        # Treat it as success when the required persistence pieces completed and a reboot is requested.
        required_ok = (
            "RESTART_REQUIRED=1" in res
            and ("OK hybrid CU persistence installed" in res or "OK skillfish-cu.service enabled" in res or "OK installed skillfish-cu.service" in res)
            and ("amdgpu.bc250_cc_write_mode=3" in res)
        )
        hard_error = res.startswith("ERR") or "\nERR " in res or "traceback" in low or "service verification failed" in low or "could not install/enable" in low
        status = "COMPLETED" if required_ok and not hard_error else ("ERROR" if hard_error else "COMPLETED")
        display_res = res
        if status == "COMPLETED":
            display_res = "✓ CU configuration saved\nRestart required to keep changes after reboot.\nLog: /tmp/skillfish-tuner-latest.log"
        self.set_task_result("APPLY CHANGES",status,display_res)
        self.stop_cu_apply_feedback(status=="COMPLETED")
        if status=="COMPLETED":
            self.clear_cu_staged_file()
            self.add_status("CU configuration applied and saved for reboot")
            GLib.timeout_add(250, self.show_cu_restart_dialog)
        else:
            self.save_cu_staged()
            self.add_status("Apply unlock failed; selected changes were kept")
        self.set_action_buttons_sensitive(True)
        self.action_running=False
        return False

    def apply_cu_staged(self):
        if not self.cu_staged:
            self.add_status("No CU changes selected")
            self.set_task_result("APPLY CHANGES","ERROR","No pending CU changes selected.")
            return
        if getattr(self, "action_running", False):
            self.add_status("Another task is already running")
            return
        staged_snapshot=dict(self.cu_staged)
        self.save_last_good_cu_config(persist=False)
        self.action_running=True
        self.busy_title="APPLY CHANGES"
        self.busy_dots=0
        self.set_action_buttons_sensitive(False)
        self.set_task_result(self.busy_title,"WORKING",f"Applying {len(staged_snapshot)} selected CU change(s)…")
        self.start_cu_apply_feedback(f"Applying {len(staged_snapshot)} selected CU change(s)…")
        self.busy_timer=GLib.timeout_add(280,self.animate_running_task)

        def worker():
            try:
                disable_mask, expected_active = self.compute_selected_cu_mask(staged_snapshot)
                payload=json.dumps({"staged":staged_snapshot,"disable_mask":disable_mask,"expected_active":expected_active})
                res=call("cu_apply_selected_live "+payload)
            except Exception as e:
                res="ERR selected CU live apply failed: "+str(e)
            GLib.idle_add(self.finish_apply_cu_staged,res)
        threading.Thread(target=worker,daemon=True).start()

    def finish_apply_cu_staged(self,res):
        if getattr(self,"busy_timer",None):
            GLib.source_remove(self.busy_timer); self.busy_timer=None
        low=res.lower()
        status="ERROR" if res.startswith("ERR") or "\nERR" in res or "traceback" in low else "COMPLETED"
        self.set_task_result("APPLY CHANGES",status,res)
        self.stop_cu_apply_feedback(status=="COMPLETED")
        if status=="COMPLETED":
            self.clear_cu_staged_file()
            self.add_status("CU configuration applied live")
            GLib.timeout_add(300, self.refresh_cu_dashboard)
        else:
            self.save_cu_staged()
            self.add_status("CU live apply failed; selected changes were kept")
        self.set_action_buttons_sensitive(True)
        self.action_running=False
        return False

    def reset_cu_staged(self):
        self.clear_cu_staged_file(); self.draw_cu_from_last(); self.add_status("CU selected changes cleared")

    # OC/profile helpers
    def build_core_steps_panel(self):
        self.core_steps_revealer=Gtk.Revealer()
        self.core_steps_revealer.set_transition_type(Gtk.RevealerTransitionType.SLIDE_DOWN)
        self.core_steps_revealer.set_transition_duration(260)

        outer=Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=8)
        outer.add_css_class("core-steps-panel")

        title=self.label("CLOCK / VOLTAGE STEPPINGS 1500+ MHz","title")
        title.set_halign(Gtk.Align.START)
        outer.append(title)

        hint=Gtk.Label(label="Performance clock steps from 1500 MHz upward are shown here. Low idle points stay hidden and unchanged. Edit voltages, then press Apply Full Curve.", xalign=0)
        hint.add_css_class("small")
        hint.set_wrap(True)
        outer.append(hint)

        self.core_steps_grid=Gtk.Grid(column_spacing=10,row_spacing=6)
        self.core_steps_grid.set_column_homogeneous(True)
        outer.append(self.core_steps_grid)

        actions=Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL,spacing=8)
        apply_btn=Gtk.Button(label="APPLY FULL CURVE")
        apply_btn.add_css_class("blue-button")
        apply_btn.connect("clicked",lambda btn:(self.pulse_button(btn),self.apply_all()))
        close_btn=Gtk.Button(label="CLOSE")
        close_btn.add_css_class("outline-button")
        close_btn.connect("clicked",lambda btn:(self.pulse_button(btn),self.close_core_steps()))
        actions.append(apply_btn)
        actions.append(close_btn)
        outer.append(actions)

        self.core_steps_revealer.set_child(outer)
        return self.core_steps_revealer

    def toggle_core_steps(self):
        state=not self.core_steps_revealer.get_reveal_child()
        self.core_steps_revealer.set_reveal_child(state)
        if hasattr(self,"core_steps_button"):
            self.core_steps_button.remove_css_class("outline-button")
            self.core_steps_button.remove_css_class("nav-btn-active")
            self.core_steps_button.add_css_class("nav-btn-active" if state else "outline-button")
            self.core_steps_button.set_label("▴ HIDE ALL CLOCK / VOLTAGE STEPS" if state else "▾ SHOW ALL CLOCK / VOLTAGE STEPS")
        self.refresh_core_steps_grid()

    def close_core_steps(self):
        self.core_steps_revealer.set_reveal_child(False)
        if hasattr(self,"core_steps_button"):
            self.core_steps_button.remove_css_class("nav-btn-active")
            self.core_steps_button.add_css_class("outline-button")
            self.core_steps_button.set_label("▾ SHOW ALL CLOCK / VOLTAGE STEPS")

    def refresh_core_steps_grid(self):
        if not hasattr(self,"core_steps_grid"):
            return
        while child:=self.core_steps_grid.get_first_child():
            self.core_steps_grid.remove(child)

        for c,h in enumerate(["STEP","FREQUENCY MHz","VOLTAGE mV"]):
            lab=self.label(h,"small")
            lab.set_halign(Gtk.Align.CENTER)
            self.core_steps_grid.attach(lab,c,0,1,1)

        self.all_step_rows=[]
        visible_points=[p for p in getattr(self,"full_points",[]) if int(p.get("frequency",0))>=1500]
        for idx,p in enumerate(visible_points,start=1):
            freq=int(p.get("frequency",0))
            volt=int(p.get("voltage",0))
            step=Gtk.Label(label=str(idx))
            step.set_halign(Gtk.Align.CENTER)
            f_lab=Gtk.Label(label=str(freq))
            f_lab.set_halign(Gtk.Align.CENTER)
            spin=Gtk.SpinButton.new_with_range(700,1250,1)
            spin.set_digits(0)
            spin.set_value(volt)
            spin.connect("value-changed",self.on_all_step_voltage_changed,freq)
            self.core_steps_grid.attach(step,0,idx,1,1)
            self.core_steps_grid.attach(f_lab,1,idx,1,1)
            self.core_steps_grid.attach(spin,2,idx,1,1)
            self.all_step_rows.append((freq,spin))

    def on_all_step_voltage_changed(self,spin,freq):
        if self._auto_updating_voltage:
            return
        freq=int(freq)
        value=max(700,int(spin.get_value()))
        if int(spin.get_value()) < 700:
            spin.set_value(700)
        self.manual_voltage_overrides[freq]=value
        for p in getattr(self,"full_points",[]):
            if int(p.get("frequency",0))==freq:
                p["voltage"]=value
                break

    def recommended_voltage(self,freq):
        anchors=[(350,700),(1000,700),(1400,805),(1800,925),(1900,950),(1950,958),(2000,965),(2050,985),(2100,1000),(2150,1020)]
        freq=int(freq)
        for (f1,v1),(f2,v2) in zip(anchors,anchors[1:]):
            if f1<=freq<=f2: return int(round(v1+(v2-v1)*(freq-f1)/max(1,f2-f1)))
        return anchors[-1][1] if freq>anchors[-1][0] else anchors[0][1]
    def on_clock_changed(self,scale):
        self.clock_big.set_label(f"{int(scale.get_value())} MHz")
        self.mark_pending("OC")
        self.adapt_voltage_curve(int(scale.get_value()))
        # End-user safe default: moving the slider only stages values.
        # Live preview is optional and only attempted if a future live backend is available.
        if hasattr(self, "live_preview_check") and self.live_preview_check.get_active():
            self._try_live_preview_notice()

    def _try_live_preview_notice(self):
        now=time.time()
        last=getattr(self,"_last_live_preview_notice",0)
        if now-last<6:
            return
        self._last_live_preview_notice=now
        self.add_status("Live Preview backend unavailable; value staged. Click Apply Overclock to apply safely.")

    def on_voltage_manual_changed(self,spin,freq):
        if not self._auto_updating_voltage:
            value=max(700,int(spin.get_value()))
            if int(spin.get_value()) < 700:
                spin.set_value(700)
            self.manual_voltage_overrides[int(freq)]=value
            self.mark_pending("OC")
    def adapt_voltage_curve(self,target):
        if not hasattr(self,"full_points"): return
        self._auto_updating_voltage=True
        try:
            pts=[]; last=0
            for p in self.full_points:
                f=int(p["frequency"]); v=max(700,self.manual_voltage_overrides.get(f,max(int(p["voltage"]),self.recommended_voltage(f))))
                if v<last: v=last
                last=v; pts.append({"frequency":f,"voltage":v})
            self.set_points(pts,preserve_manual=True)
        finally: self._auto_updating_voltage=False
    def set_points(self,points,preserve_manual=False):
        self.full_points=points[:]
        if not preserve_manual and not self._auto_updating_voltage: self.manual_voltage_overrides={}
        while child:=self.voltage_grid.get_first_child(): self.voltage_grid.remove(child)
        for c,h in enumerate(["FREQUENCY","VOLTAGE"]): self.voltage_grid.attach(self.label(h,"small"),c,0,1,1)
        self.rows=[]
        visible_points=[p for p in points if int(p.get("frequency",0))>=1500]
        for i,p in enumerate(visible_points,start=1):
            f,v=int(p["frequency"]),int(p["voltage"]); fl=Gtk.Label(label=str(f)); fl.set_halign(Gtk.Align.CENTER)
            sp=Gtk.SpinButton.new_with_range(700,1250,1); sp.set_value(v); sp.set_digits(0); sp.connect("value-changed",self.on_voltage_manual_changed,f)
            self.voltage_grid.attach(fl,0,i,1,1); self.voltage_grid.attach(sp,1,i,1,1); self.rows.append((f,sp))
        if hasattr(self,"core_steps_revealer") and self.core_steps_revealer.get_reveal_child():
            self.refresh_core_steps_grid()
    def merged_points(self):
        upd={f:int(s.get_value()) for f,s in getattr(self,"rows",[])}
        for f,s in getattr(self,"all_step_rows",[]):
            upd[int(f)]=int(s.get_value())
        for f,v in getattr(self,"manual_voltage_overrides",{}).items():
            upd[int(f)]=int(v)
        out=[]; last=0
        for p in self.full_points:
            f=int(p["frequency"])
            v=max(700,upd.get(f,int(p["voltage"])))
            if v<last:
                self.add_status(f"Voltage curve error: {f} MHz is below previous step")
                return None
            last=v
            out.append({"frequency":f,"voltage":v})
        return out

    def load_points(self):
        try: self.set_points(json.loads(call("points")))
        except Exception as e: print(e)
    def load_profiles(self):
        try: names=[p.get("name","Unnamed") for p in json.loads(call("profiles"))]
        except Exception: names=["My Profile"]
        if "My Profile" not in names: names.insert(0,"My Profile")
        self.profile_combo.set_model(Gtk.StringList.new(names)); self.profile_combo.set_selected(0)
    def selected_profile(self):
        item=self.profile_combo.get_model().get_item(self.profile_combo.get_selected()); return item.get_string() if item else "My Profile"
    def load_profile(self,name,show=True):
        try: p=json.loads(call(f"load_profile {name}"))
        except Exception as e: print(e); return
        self.set_points(p.get("points",[])); self.clock_scale.set_value(int(p.get("max_freq",2000))); self.adapt_voltage_curve(int(p.get("max_freq",2000)))
        if show: self.add_status(f"Loaded {p.get('name',name)}")
    def save_profile(self):
        pts=self.merged_points()
        if pts is None: return
        name=self.profile_name_entry.get_text().strip() or self.selected_profile()
        print(call("save_profile "+json.dumps({"name":name,"max_freq":int(self.clock_scale.get_value()),"points":pts}))); self.load_profiles(); self.add_status("Snapshot saved")
    def delete_profile(self): print(call(f"delete_profile {self.selected_profile()}")); self.load_profiles(); self.add_status("Snapshot deleted")
    def apply_all(self):
        pts=self.merged_points()
        if pts is None: return
        target=int(self.clock_scale.get_value())
        self.save_last_good_full_config("before-overclock-apply")
        self.add_status(f"Applying overclock: {target} MHz")
        self.start_percent_progress("oc_apply", message="Applying overclock", bar=getattr(self, "gpu_apply_progress", None), button=getattr(self, "oc_apply_button", None), button_text="Applying overclock", delay_ms=5000)
        def worker():
            try:
                out1=call("apply_points "+json.dumps(pts))
                out2=call(f"set {target}")
                ok=("ERR" not in (out1+out2).upper())
                GLib.idle_add(self._finish_apply_overclock, ok, out1+"\n"+out2, target)
            except Exception as e:
                GLib.idle_add(self._finish_apply_overclock, False, str(e), target)
        threading.Thread(target=worker,daemon=True).start()

    def _finish_apply_overclock(self, ok, output, target):
        self.stop_percent_progress("oc_apply", ok=ok, hide=False, restore_button=True)
        if ok:
            self.add_status(f"Overclock applied: {target} MHz")
            if hasattr(self,"result_text"):
                self.result_text.set_label(f"✓ Overclock applied\n{target} MHz staged live. Validate with your preferred external workload before saving for boot.")
            self.clear_pending("OC")
        else:
            self.add_status("Overclock apply failed — see terminal/log output")
            if hasattr(self,"result_text"):
                self.result_text.set_label("✗ Overclock apply failed\nCheck governor/SMU backend and logs.")
        print(output)
        return False

    def _poll_sensors_worker(self):
        try:
            raw = call("status")
            data = json.loads(raw)
        except Exception:
            data = None
        GLib.idle_add(self._finish_sensor_poll, data)

    def _finish_sensor_poll(self, data):
        self._sensor_inflight = False
        if data is not None:
            self._sensor_cache = data
        return False

    def _apply_sensor_cache(self):
        s = self._sensor_cache
        if not s:
            return
        temp=float(s.get("temp",0) or 0); self.last_gpu_temp=temp
        if hasattr(self,"fan_curve_chart"): self.fan_curve_chart.set_current_temp(temp)
        freq=int(s.get("freq",0) or 0); mclk=int(s.get("mclk",0) or 0); volt=float(s.get("voltage",0) or 0); power=float(s.get("power",0) or 0); cpu=float(s.get("cpu_temp",0) or 0); ssd=float(s.get("ssd_temp",0) or 0); fan=int(s.get("fan_rpm",0) or 0)
        self.metrics["temp"].set_value(f"{temp:.0f}",temp); self.metrics["freq"].set_value(f"{freq}",freq); self.metrics["power"].set_value(f"{power:.0f}",power); self.metrics["volt"].set_value(f"{volt:.0f}",volt); self.metrics["mclk"].set_value(f"{mclk}",mclk); self.metrics["cpu"].set_value(f"{cpu:.0f}",cpu); self.metrics["ssd"].set_value(f"{ssd:.0f}",ssd)
        self.rpm_big.set_label(str(fan)); self.fan_percent.set_label(f"{min(100,round(fan/26))} %"); self.fan.set_rpm(fan); self.fan_live_curve.push(fan)
        if hasattr(self,"dash_temp"):
            self.dash_temp.set_label(f"GPU Temp: {temp:.0f} °C")
            self.dash_clock.set_label(f"GPU Clock: {freq} MHz")
            self.dash_fan.set_label(f"Pump Fan: {fan} RPM")
        if hasattr(self,"dash_cfg_clock"):
            self.dash_cfg_clock.set_label(f"Clock: {freq} MHz")
            self.dash_cfg_voltage.set_label(f"Voltage: {volt:.0f} mV")
            self.dash_cfg_power.set_label(f"Power: {power:.0f} W")
            self.dash_cfg_fan.set_label(f"Fan: {fan} RPM")
        if hasattr(self, "gov_service_label"):
            state = str(s.get("service_status", "--")).strip()
            pretty = "Active" if state == "active" else ("Starting…" if state == "activating" else state.capitalize())
            self.gov_service_label.set_label(f"Governor Service: {pretty}")
            if hasattr(self,"health_rows"):
                health = s.get("service_health") or {}
                if isinstance(health, dict):
                    self._set_health("governor", health.get("governor", "running" if state == "active" else "not-installed"))
                    if str(health.get("governor", "")).lower() in ("installed-restart-pending", "restart-pending", "pending-restart"):
                        pretty = "Installed — restart pending"
                        self.gov_service_label.set_label(f"Governor Service: {pretty}")
                    self._set_health("cu", health.get("cu", "unknown"))
                    self._set_health("fan", health.get("fan", "disabled"))
                else:
                    self._set_health("governor", "running" if state == "active" else "not-installed")
        live_clock=int(s.get("target",0) or s.get("freq",0) or 0)
        if live_clock and hasattr(self,"current_clock_big"):
            self.current_clock_big.set_label(f"{live_clock} MHz")

    def refresh(self):
        # Called at ~60 FPS by GTK, but it only starts a real sensor read every 1s.
        # The expensive socket/status/sensors path runs in a daemon thread.
        now = time.monotonic()
        if (not self._sensor_inflight) and (now - self._sensor_last_poll >= self._sensor_poll_interval):
            self._sensor_inflight = True
            self._sensor_last_poll = now
            threading.Thread(target=self._poll_sensors_worker, daemon=True).start()

        # UI value updates are cheap; graph widgets animate themselves at 60 FPS.
        if now - self._sensor_last_ui >= 0.20:
            self._sensor_last_ui = now
            self._apply_sensor_cache()
        return True

class App(Adw.Application):
    def __init__(self):
        super().__init__(application_id="org.bagz.bluegpuzen.v7currentcardappfix", flags=Gio.ApplicationFlags.DEFAULT_FLAGS)
        self.win=None
    def do_activate(self):
        css=Gtk.CssProvider(); css.load_from_data(CSS.encode())
        display=Gdk.Display.get_default()
        if display: Gtk.StyleContext.add_provider_for_display(display,css,Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        self.win=self.win or MainWindow(self); self.win.present()

if __name__=="__main__":
    App().run(sys.argv)

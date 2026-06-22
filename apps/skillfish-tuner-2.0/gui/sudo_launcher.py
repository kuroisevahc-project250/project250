#!/usr/bin/env python3
import os, sys, time, getpass, subprocess, traceback, socket
import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw, Gio, GLib, Gdk

APPDIR = os.environ.get("APPDIR") or os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SOCKET = os.environ.get("CYAN_SOCKET", "/tmp/bagz-blue-gpu-zen-v7-current-card-appfix.sock")
LOG = os.environ.get("BAGZ_LOG", "/tmp/bagz-blue-gpu-zen-v7-current-card-appfix.log")

CSS = """
window { background: #020712; }
.auth-root {
  background: radial-gradient(circle at 50% 0%, alpha(#00aaff,0.18), transparent 44%),
              linear-gradient(135deg, #020712, #061322 56%, #02050a);
  padding: 26px;
}
.auth-card {
  border-radius: 18px;
  padding: 22px;
  background: alpha(#07111d,0.94);
  border: 1px solid alpha(#00a6ff,0.42);
  box-shadow: 0 0 30px alpha(#00a6ff,0.18);
}
.title {
  color: #19d7ff;
  font-size: 30px;
  font-weight: 900;
  letter-spacing: 6px;
}
.subtitle {
  color: alpha(white,0.72);
  font-size: 12px;
  font-weight: 800;
}
.error {
  color: #ff4b4b;
  font-weight: 900;
}
.warn {
  color: #ffd84a;
  font-weight: 900;
}
.blue-button {
  background: linear-gradient(90deg, #005eff, #06b8ff);
  color: white;
  font-weight: 900;
}
"""

def log(msg):
    try:
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(str(msg) + "\n")
    except Exception:
        pass

def log_exc(prefix):
    log(prefix)
    log(traceback.format_exc())

def daemon_socket_responds(timeout=0.75):
    """Return True when an already-running Skillfish daemon owns the socket.

    This prevents multiple helper daemons from fighting over the same /tmp socket.
    """
    try:
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as sock:
            sock.settimeout(timeout)
            sock.connect(SOCKET)
            sock.sendall(b"status")
            try:
                sock.shutdown(socket.SHUT_WR)
            except OSError:
                pass
            data = sock.recv(4096)
            return bool(data) and not data.startswith(b"ERR")
    except Exception:
        return False

class AuthWindow(Adw.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app)
        self.set_title("bagz authentication")
        self.set_default_size(440, 310)
        self.set_resizable(False)

        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)
        root.add_css_class("auth-root")
        self.set_content(root)

        card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        card.add_css_class("auth-card")
        card.set_halign(Gtk.Align.CENTER)
        card.set_valign(Gtk.Align.CENTER)
        root.append(card)

        title = Gtk.Label(label="bagz")
        title.add_css_class("title")
        title.set_halign(Gtk.Align.CENTER)
        card.append(title)

        sub = Gtk.Label(label="blue all-in-one gpu zen")
        sub.add_css_class("subtitle")
        sub.set_halign(Gtk.Align.CENTER)
        card.append(sub)

        user = Gtk.Label(label=f"Current user: {getpass.getuser()}")
        user.add_css_class("subtitle")
        user.set_halign(Gtk.Align.CENTER)
        card.append(user)

        self.entry = Gtk.PasswordEntry()
        try:
            self.entry.set_show_peek_icon(True)
        except Exception:
            pass
        self.entry.connect("activate", self.on_unlock)
        self.entry.connect("changed", self.check_caps)
        card.append(self.entry)

        self.caps = Gtk.Label(label="")
        self.caps.add_css_class("warn")
        self.caps.set_halign(Gtk.Align.CENTER)
        card.append(self.caps)

        self.error = Gtk.Label(label="")
        self.error.add_css_class("error")
        self.error.set_halign(Gtk.Align.CENTER)
        self.error.set_wrap(True)
        card.append(self.error)

        btn = Gtk.Button(label="UNLOCK AND START")
        btn.add_css_class("blue-button")
        btn.connect("clicked", self.on_unlock)
        card.append(btn)

        log("auth window initialized")
        log(f"APPDIR={APPDIR}")
        log(f"SOCKET={SOCKET}")

    def check_caps(self, *_):
        txt = self.entry.get_text()
        if txt and txt.upper() == txt and any(c.isalpha() for c in txt):
            self.caps.set_label("Caps Lock may be ON")
        else:
            self.caps.set_label("")

    def set_error(self, msg):
        self.error.set_label(msg)
        log("ERROR: " + msg)

    def on_unlock(self, *_):
        password = self.entry.get_text()
        if not password:
            self.set_error("Enter your sudo password.")
            return
        self.error.set_label("Starting...")

        # Run in idle callback so UI updates before blocking work.
        GLib.idle_add(lambda: self.start_with_password(password))

    def start_with_password(self, password):
        try:
            return self._start_with_password(password)
        except Exception:
            log_exc("launcher fatal exception")
            self.set_error("Launcher failed. Check log.")
            return False

    def _start_with_password(self, password):
        daemon = os.path.join(APPDIR, "src", "daemon.py")
        gui = os.path.join(APPDIR, "gui", "app.py")

        if not os.path.exists(daemon):
            self.set_error(f"Missing daemon.py: {daemon}")
            return False
        if not os.path.exists(gui):
            self.set_error(f"Missing app.py: {gui}")
            return False

        env = os.environ.copy()
        env["APPDIR"] = APPDIR
        env["PYTHONPATH"] = os.path.join(APPDIR, "src")
        env["CYAN_SOCKET"] = SOCKET
        env["BAGZ_LOG"] = LOG

        # Validate sudo. This avoids the daemon prompt hanging silently.
        log("validating sudo")
        proc = subprocess.run(
            ["sudo", "-S", "-v"],
            input=password + "\n",
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=15,
            env=env,
        )
        if proc.returncode != 0:
            log("sudo validation failed")
            log(proc.stderr)
            self.entry.set_text("")
            self.set_error("Wrong sudo password.")
            return False

        reuse_existing_daemon = False
        if os.path.exists(SOCKET):
            if daemon_socket_responds():
                log("existing daemon socket is alive; reusing daemon")
                reuse_existing_daemon = True
            else:
                log("stale daemon socket detected; removing with sudo")
                rm_proc = subprocess.run(
                    ["sudo", "-S", "rm", "-f", SOCKET],
                    input=password + "\n",
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    env=env,
                )
                if rm_proc.returncode != 0:
                    log("could not remove stale socket with sudo")
                    log(rm_proc.stderr)

        if not reuse_existing_daemon:
            log("starting daemon")
            log(f"daemon={daemon}")
            daemon_log = open(LOG, "a", encoding="utf-8")
            d = subprocess.Popen(
                ["sudo", "-S", "-E", "env",
                 f"PYTHONPATH={env['PYTHONPATH']}",
                 f"CYAN_SOCKET={SOCKET}",
                 "python3", daemon],
                stdin=subprocess.PIPE,
                stdout=daemon_log,
                stderr=subprocess.STDOUT,
                text=True,
                env=env,
                start_new_session=True,
            )
            try:
                d.stdin.write(password + "\n")
                d.stdin.flush()
                d.stdin.close()
            except Exception as e:
                log(f"daemon stdin close/write issue: {e}")

            # Wait for daemon socket to exist and process to not exit.
            ready = False
            for i in range(50):
                if d.poll() is not None:
                    log(f"daemon exited early with code {d.returncode}")
                    break
                if os.path.exists(SOCKET) and daemon_socket_responds(timeout=0.25):
                    ready = True
                    break
                time.sleep(0.1)

            if not ready:
                self.set_error("Daemon did not create a usable socket. Check log.")
                return False

        log("starting gui")
        log(f"gui={gui}")
        gui_log = open(LOG, "a", encoding="utf-8")
        subprocess.Popen(
            ["python3", gui],
            stdout=gui_log,
            stderr=subprocess.STDOUT,
            env=env,
            start_new_session=True,
        )

        self.set_visible(False)
        GLib.timeout_add(300, self.get_application().quit)
        return False

class AuthApp(Adw.Application):
    def __init__(self):
        super().__init__(application_id="org.bagz.bluegpuzen.auth.currentcardappfix", flags=Gio.ApplicationFlags.DEFAULT_FLAGS)
        self.win = None

    def do_activate(self):
        css = Gtk.CssProvider()
        css.load_from_data(CSS.encode())
        display = Gdk.Display.get_default()
        if display:
            Gtk.StyleContext.add_provider_for_display(display, css, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        self.win = self.win or AuthWindow(self)
        self.win.present()

if __name__ == "__main__":
    AuthApp().run(sys.argv)

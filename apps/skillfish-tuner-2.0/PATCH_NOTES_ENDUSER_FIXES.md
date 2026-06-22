# Skillfish Tuner 2.0 End-User Fix Pack

This build includes stability and user-feedback fixes based on latest runtime logs:

- Prevents multiple daemon instances from fighting over the same Unix socket.
- Reuses an already-running daemon when possible.
- Removes stale root-owned socket files through sudo after authentication.
- Keeps the daemon from crashing on closed GUI sockets / BrokenPipeError.
- Adds a daemon-side reboot command so restart dialogs do not bypass the helper.
- Uses modern restart dialog handling where available, with fallback for older Adwaita.
- Keeps percentage loading feedback for long-running actions.
- Preserves CU/topology reboot-required workflow.
- Removes Python cache files before packaging.

Recommended before installing this build over older test builds:

```bash
pkill -f skillfish-tuner-2.0/src/daemon.py || true
sudo rm -f /tmp/bagz-blue-gpu-zen-v7-current-card-appfix.sock
```

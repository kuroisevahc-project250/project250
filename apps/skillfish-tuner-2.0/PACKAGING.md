# Skillfish Tuner RPM Packaging

This package contains a Fedora/Bazzite RPM packaging skeleton.

## Build locally

Install RPM build tools on a mutable Fedora system or toolbox/container:

```bash
sudo dnf install rpm-build rsync
./packaging/rpm/build-rpm.sh
```

The RPM will be written to:

```text
~/rpmbuild/RPMS/x86_64/
```

## Install on Bazzite

For a local RPM build:

```bash
rpm-ostree install ./skillfish-tuner-2.0-1*.x86_64.rpm
systemctl reboot
```

## Installed paths

```text
/usr/bin/skillfish-tuner
/opt/skillfish-tuner/
/usr/share/applications/skillfish-tuner.desktop
/usr/share/icons/hicolor/256x256/apps/skillfish-tuner.png
/etc/skillfish-tuner/
/var/log/skillfish-tuner/
```

The app uses one fishbone icon for the launcher/tray/notifications.

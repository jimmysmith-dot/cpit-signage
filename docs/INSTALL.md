# CPIT Signage Installation Guide

This guide documents the known working installation pattern used for the QSR DX-3000 proof-of-concept appliance.

## 1. Hardware

Known proof-of-concept hardware:

- QSR DX-3000
- Manufactured in 2018
- Originally shipped with Windows 7 Embedded
- Debian installed from USB
- Internal storage replaced or bypassed as needed
- HDMI-connected television
- Network connection through a Cradlepoint
- Remote access through Tailscale

The software design is not specific to the DX-3000. Any x86-64 system capable of running Debian, Chromium, Python, and a graphical session should be usable.

## 2. Operating System

Install Debian 13 with:

- A graphical environment
- XFCE or another lightweight desktop
- Network support
- OpenSSH server
- A standard non-root user

Recommended packages:

```bash
sudo apt update
sudo apt install -y \
    chromium \
    curl \
    git \
    openssh-server \
    python3 \
    python3-pip \
    python3-venv \
    sqlite3 \
    unclutter
```

Install fonts used by the sign renderer:

```bash
sudo apt install -y \
    fonts-dejavu-core \
    fonts-liberation2
```

## 3. Enable SSH

```bash
sudo systemctl enable --now ssh
sudo systemctl status ssh
```

Test from another computer:

```powershell
ssh user@PLAYER-IP
```

## 4. Optional: Install Tailscale

Use the current official Tailscale installation instructions for Debian, then authenticate the appliance to the intended tailnet.

After enrollment, verify:

```bash
tailscale status
tailscale ip -4
```

Do not depend solely on a public port-forwarding configuration at the customer site. Tailscale is the preferred remote-support path for this project.

## 5. Create the Application Directory

```bash
sudo mkdir -p /opt/cpit-signage
sudo chown -R user:user /opt/cpit-signage
cd /opt/cpit-signage
```

Replace `user:user` with the actual Debian account and group.

## 6. Create the Python Environment

```bash
python3 -m venv venv
source venv/bin/activate
pip install Flask Pillow requests watchdog
```

Record dependencies after the application is stable:

```bash
pip freeze > requirements.txt
```

## 7. Application Structure

Expected directories:

```bash
mkdir -p \
    app/routes \
    app/services \
    app/static/js \
    app/templates \
    cache \
    config \
    logs \
    media \
    scripts \
    deployment
```

## 8. SQLite Initialization

The application creates the SQLite database at:

```text
/opt/cpit-signage/config/signage.db
```

To initialize or import existing media:

```bash
cd /opt/cpit-signage
./venv/bin/python -m app.init_database
```

If the installed code uses a direct script invocation instead:

```bash
./venv/bin/python app/init_database.py
```

Use the invocation that matches the installed module structure.

## 9. systemd Service

Service name:

```text
cpit-player.service
```

Recommended service file:

```ini
[Unit]
Description=CPIT Signage Player
After=network.target

[Service]
Type=simple
User=user
Group=user
WorkingDirectory=/opt/cpit-signage
ExecStart=/opt/cpit-signage/venv/bin/python -m app.app
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Install it:

```bash
sudo cp deployment/cpit-player.service \
    /etc/systemd/system/cpit-player.service

sudo systemctl daemon-reload
sudo systemctl enable --now cpit-player
sudo systemctl status cpit-player
```

## 10. Chromium Kiosk Script

Expected location:

```text
/opt/cpit-signage/scripts/start-kiosk.sh
```

Example:

```bash
#!/bin/bash

sleep 5

xset s off
xset -dpms
xset s noblank

pkill chromium 2>/dev/null
unclutter -idle 1 &

exec chromium \
    --user-data-dir=/home/user/.config/cpit-signage-chromium \
    --kiosk \
    --no-first-run \
    --disable-session-crashed-bubble \
    --disable-infobars \
    --noerrdialogs \
    http://localhost:5000
```

Make it executable:

```bash
chmod +x /opt/cpit-signage/scripts/start-kiosk.sh
```

## 11. Desktop Autostart

Create:

```text
~/.config/autostart/cpit-signage.desktop
```

Example:

```ini
[Desktop Entry]
Type=Application
Name=CPIT Signage
Exec=/opt/cpit-signage/scripts/start-kiosk.sh
Terminal=false
Hidden=false
X-GNOME-Autostart-enabled=true
```

## 12. Validate the Installation

```bash
curl http://127.0.0.1:5000/
curl http://127.0.0.1:5000/api/slides
sudo systemctl status cpit-player
```

Reboot:

```bash
sudo reboot
```

Expected behavior:

1. Debian boots.
2. The graphical user logs in.
3. The Flask service is already running.
4. Chromium opens in kiosk mode.
5. The player begins displaying the active playlist.

## 13. Remote Administration

From Windows PowerShell:

```powershell
ssh -N -L 5000:127.0.0.1:5000 user@PLAYER-IP
```

Then browse to:

```text
http://127.0.0.1:5000/admin/
```

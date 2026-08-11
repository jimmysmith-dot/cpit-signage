# CPIT Signage Studio

A lightweight, self-hosted digital signage platform for hospitality and commercial environments.

CPIT Signage Studio provides a remotely manageable signage appliance with local media storage, browser-based administration, sign creation, reusable branding, background libraries, playlist management, and automatic player updates.

## Current Release

- Current release: `v1.0.0`
- Release state: production
- Supported platforms tested: QSR DX3000 and Bematech LC8810
- Core workflows: Studio, Upload, Playlist
- Deployment: automated installer, upgrade tools, and health diagnostics

## Core Features

- Debian 13 appliance
- Chromium kiosk playback
- Flask application service
- SQLite media database
- Browser-based administration
- Studio workspace for sign creation
- Reusable sign templates
- Logo library
- Background library
- Separate playlist and background asset types
- Live 16:9 preview
- Server-rendered 1920 × 1080 PNG signs
- Multi-image uploads
- Drag-and-drop playlist ordering
- Duration editing
- Enable/disable controls
- Media deletion
- Health-check diagnostics
- Automated installer and upgrade tools
- SSH and Tailscale remote management
- Offline playback
- Git-based version control

## Proven Remote-Management Scenario

The development player is connected through a Cradlepoint rather than the developer's local network. Administration and development have been performed over Tailscale and SSH. This validates the intended remote-support model for customer deployments behind third-party networks, carrier connections, or firewalls.

## Architecture Summary

```text
Administrator Browser
        |
        | SSH tunnel or Tailscale
        v
Flask Administration and REST API
        |
        +---- SQLite media and playlist database
        |
        +---- Local media directory
        |
        +---- Sign generator (Pillow)
        |
        v
Chromium player at http://127.0.0.1:5000/
        |
        v
Hotel lobby television
```

## Repository Layout

```text
/opt/cpit-signage
├── app/
│   ├── __init__.py
│   ├── app.py
│   ├── init_database.py
│   ├── routes/
│   │   ├── admin.py
│   │   ├── api.py
│   │   └── player.py
│   ├── services/
│   │   ├── database.py
│   │   └── slide_generator.py
│   ├── static/
│   │   └── js/
│   │       ├── admin.js
│   │       └── player.js
│   └── templates/
│       ├── admin.html
│       └── index.html
├── config/
│   └── signage.db
├── media/
├── scripts/
│   └── start-kiosk.sh
├── deployment/
│   └── cpit-player.service
├── .gitignore
└── README.md
```

## Local URLs

Player:

```text
http://127.0.0.1:5000/
```

Administration:

```text
http://127.0.0.1:5000/admin/
```

REST API base:

```text
http://127.0.0.1:5000/api/
```

## Remote Administration with an SSH Tunnel

From Windows PowerShell:

```powershell
ssh -N -L 5000:127.0.0.1:5000 user@PLAYER-IP
```

Then open:

```text
http://127.0.0.1:5000/admin/
```

For the current proof-of-concept player:

```powershell
ssh -N -L 5000:127.0.0.1:5000 user@100.64.19.95
```

## System Service

```bash
sudo systemctl status cpit-player
sudo systemctl restart cpit-player
sudo journalctl -u cpit-player -n 100 --no-pager
```

## Documentation

Detailed documentation is available in the `docs/` directory:

- `INSTALL.md`
- `ARCHITECTURE.md`
- `API.md`
- `OPERATIONS.md`
- `DEVELOPMENT.md`
- `ROADMAP.md`
- `CHANGELOG.md`
- `RELEASE_CHECKLIST.md`
- `SECURITY.md`

## Immediate Next Step

.......PENDING

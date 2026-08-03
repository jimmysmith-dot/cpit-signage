# CPIT Signage

**A lightweight, self-hosted digital signage platform for hospitality and commercial environments.**

CPIT Signage began as a low-cost solution for a hotel lobby television that needed to display remodel renderings and informational content. It now provides a remotely manageable signage appliance with local media storage, browser-based administration, image uploads, drag-and-drop playlist ordering, message-slide creation, and automatic player updates.

## Current Development Status

- Current development line: `v0.5.1`
- Current feature branch: `feature/create-slide-designer`
- Current release state: development / pre-tag
- Production candidate scope: image playback, remote management, media administration, and Create Sign

The project is already capable of satisfying the original hotel request:

- Display pictures on a lobby television
- Add, remove, reorder, and disable content remotely
- Create informational message slides without external design software
- Continue playback from locally stored content
- Support both local and off-premises administration

## Core Features

- Debian 13 appliance
- Chromium kiosk playback
- Flask application service
- SQLite media database
- Image slideshow with fade transitions
- Automatic 15-second playlist polling
- Browser-based administration
- Multi-image uploads
- Drag-and-drop playlist ordering
- Duration editing
- Enable and disable controls
- Media deletion
- Create Sign designer
- Server-rendered 1920×1080 PNG signs
- Live 16:9 sign preview
- SSH management
- Tailscale remote access
- Offline playback after content is stored locally
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

The recommended stopping point is to:

1. Validate the redesigned Create Sign interface.
2. Confirm upload, delete, reorder, duration, enable/disable, polling, and sign generation.
3. Commit the `v0.5.1` work.
4. Merge the feature branch into `main`.
5. Tag `v0.5.1`.
6. Deploy the appliance for the hotel proof of concept.

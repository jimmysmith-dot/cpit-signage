# CPIT Signage Operations Guide

## Routine Service Commands

Status:

```bash
sudo systemctl status cpit-player --no-pager -l
```

Restart:

```bash
sudo systemctl restart cpit-player
```

Recent logs:

```bash
sudo journalctl -u cpit-player -n 100 --no-pager
```

Follow logs:

```bash
sudo journalctl -u cpit-player -f
```

## Confirm Local Application Health

```bash
curl -I http://127.0.0.1:5000/
curl -s http://127.0.0.1:5000/api/slides \
    | python3 -m json.tool
```

## Remote Access

Preferred methods:

1. Tailscale
2. SSH
3. SSH local port forwarding for the admin page

Windows PowerShell tunnel:

```powershell
ssh -N -L 5000:127.0.0.1:5000 user@PLAYER-IP
```

Open:

```text
http://127.0.0.1:5000/admin/
```

## Kiosk Recovery

If Chromium is closed:

```bash
pkill chromium
/opt/cpit-signage/scripts/start-kiosk.sh \
    >/tmp/cpit-kiosk.log 2>&1 &
```

If the kiosk does not start after reboot:

```bash
cat ~/.config/autostart/cpit-signage.desktop
ls -l /opt/cpit-signage/scripts/start-kiosk.sh
cat /tmp/cpit-kiosk.log
```

## Verify Polling

```bash
sudo journalctl -u cpit-player -f
```

The player should request:

```text
GET /api/slides
```

approximately every 15 seconds.

## Database Backup

Stop the service for the cleanest simple backup:

```bash
sudo systemctl stop cpit-player

cp /opt/cpit-signage/config/signage.db \
   /opt/cpit-signage/config/signage.db.backup-$(date +%Y%m%d-%H%M%S)

sudo systemctl start cpit-player
```

SQLite's backup command is preferable when avoiding downtime:

```bash
sqlite3 /opt/cpit-signage/config/signage.db \
    ".backup '/opt/cpit-signage/config/signage-backup.db'"
```

## Media Backup

```bash
tar -czf \
    /opt/cpit-signage/media-backup-$(date +%Y%m%d-%H%M%S).tar.gz \
    -C /opt/cpit-signage media
```

## Full Application Backup

```bash
sudo tar -czf \
    /opt/cpit-signage-full-$(date +%Y%m%d-%H%M%S).tar.gz \
    /opt/cpit-signage
```

Consider excluding the Python virtual environment from long-term source backups because it can be recreated from `requirements.txt`.

## Restore Database

```bash
sudo systemctl stop cpit-player

cp /path/to/signage.db.backup \
   /opt/cpit-signage/config/signage.db

sudo chown user:user \
   /opt/cpit-signage/config/signage.db

sudo systemctl start cpit-player
```

## Disk Usage

```bash
df -h
du -sh /opt/cpit-signage/media
du -sh /opt/cpit-signage/config
```

## Tailscale Checks

```bash
tailscale status
tailscale ip -4
sudo systemctl status tailscaled
```

## Network Checks

```bash
ip addr
ip route
ping -c 4 1.1.1.1
ping -c 4 debian.org
```

## Media Troubleshooting

List database records:

```bash
sqlite3 -header -column \
    /opt/cpit-signage/config/signage.db \
    "SELECT id, filename, duration, sort_order, enabled FROM media ORDER BY sort_order;"
```

List files:

```bash
find /opt/cpit-signage/media \
    -maxdepth 1 \
    -type f \
    -printf '%f\n' \
    | sort
```

A database record without a matching file will fail to display. A file without a database record will not display unless the import function is run.

## Deployment Acceptance Test

Before leaving a site:

- Power-cycle the appliance.
- Confirm automatic login.
- Confirm Chromium kiosk startup.
- Confirm the correct TV input.
- Confirm all active slides display.
- Upload a test image remotely.
- Reorder the playlist remotely.
- Create a test message sign.
- Delete the test content.
- Confirm the player updates within 15 seconds.
- Confirm SSH and Tailscale access.
- Record the player hostname and Tailscale IP.
- Record the appliance location and connected TV.

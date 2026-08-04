# CPIT Signage Studio Installation

## Supported release target

The v1.0 installer is designed and tested for:

- Debian 13
- XFCE
- LightDM
- Chromium
- x86-64 hardware
- A local non-root desktop user

## Fresh installation

Clone or copy the repository to the Debian device, then run:

```bash
cd cpit-signage
chmod +x install.sh upgrade.sh uninstall.sh scripts/*.sh
sudo ./install.sh
sudo reboot
```

The installer uses the account that invoked `sudo` as the kiosk and service user. To select another existing account:

```bash
sudo CPIT_USER=signage ./install.sh
```

## URLs

Player:

```text
http://127.0.0.1:5000/
```

Administration:

```text
http://127.0.0.1:5000/admin/
```

## Remote administration

With Tailscale, open the player's Tailscale address on port 5000.

With an SSH tunnel from Windows PowerShell:

```powershell
ssh -N -L 5000:127.0.0.1:5000 user@PLAYER-IP
```

Then browse to:

```text
http://127.0.0.1:5000/admin/
```

## Upgrade

From a freshly updated repository checkout:

```bash
sudo ./upgrade.sh
```

The upgrade script preserves:

- `config/signage.db`
- `media/`
- `branding/logos/`

## Health check

```bash
sudo /opt/cpit-signage/scripts/health-check.sh
```

## Uninstall

```bash
sudo ./uninstall.sh
```

The uninstaller asks whether customer content should be retained.

# CPIT Signage Studio Installer v2

This revision prevents the incomplete-package failure found during the first LC8810 test.

## Important rule

`install.sh` must be run from the root of the **complete project checkout**.

The same directory must contain:

```text
app/
deployment/
scripts/
install.sh
requirements.txt
VERSION
```

If `app/app.py` is missing, the installer stops immediately before modifying the system.

## Build a complete release package

From the working repository:

```bash
chmod +x scripts/build-release.sh
./scripts/build-release.sh
```

The complete ZIP and TAR.GZ files are created in:

```text
dist/
```

Copy one of those complete release archives to the target machine, extract it, and run:

```bash
cd cpit-signage-studio-<version>
sudo ./install.sh
```

## LC8810 clean test

```bash
sudo systemctl stop cpit-player 2>/dev/null || true
sudo rm -rf /opt/cpit-signage
cd ~/cpit-signage-studio-<version>
sudo ./install.sh
sudo reboot
```

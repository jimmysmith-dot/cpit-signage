\
#!/usr/bin/env bash
set -Eeuo pipefail

APP_DIR="/opt/cpit-signage"
SERVICE_NAME="cpit-player"

if [[ "${EUID}" -ne 0 ]]; then
    echo "Run with sudo: sudo ./uninstall.sh" >&2
    exit 1
fi

CPIT_USER="${CPIT_USER:-${SUDO_USER:-user}}"
CPIT_HOME="$(getent passwd "${CPIT_USER}" | cut -d: -f6)"

read -r -p "Keep customer media, logos, and database? [Y/n] " KEEP_DATA
KEEP_DATA="${KEEP_DATA:-Y}"

systemctl disable --now "${SERVICE_NAME}" 2>/dev/null || true
rm -f "/etc/systemd/system/${SERVICE_NAME}.service"
rm -f /etc/lightdm/lightdm.conf.d/50-cpit-signage-autologin.conf
rm -f "${CPIT_HOME}/.config/autostart/cpit-signage.desktop"
systemctl daemon-reload

if [[ "${KEEP_DATA}" =~ ^[Nn]$ ]]; then
    rm -rf "${APP_DIR}"
    echo "Application and customer data removed."
else
    BACKUP_DIR="/var/backups/cpit-signage/uninstall-$(date +%Y%m%d-%H%M%S)"
    mkdir -p "${BACKUP_DIR}"

    for runtime_path in config media branding; do
        if [[ -e "${APP_DIR}/${runtime_path}" ]]; then
            cp -a "${APP_DIR}/${runtime_path}" "${BACKUP_DIR}/"
        fi
    done

    rm -rf "${APP_DIR}"
    echo "Application removed."
    echo "Customer data retained at: ${BACKUP_DIR}"
fi

echo "Uninstall complete. Reboot if this device will no longer operate as a kiosk."

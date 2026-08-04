\
#!/usr/bin/env bash
set -Eeuo pipefail

APP_DIR="/opt/cpit-signage"
SOURCE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVICE_NAME="cpit-player"
BACKUP_ROOT="/var/backups/cpit-signage"

if [[ "${EUID}" -ne 0 ]]; then
    echo "Run with sudo: sudo ./upgrade.sh" >&2
    exit 1
fi

CPIT_USER="${CPIT_USER:-${SUDO_USER:-user}}"
CPIT_GROUP="$(id -gn "${CPIT_USER}")"

echo "Upgrading CPIT Signage Studio..."

mkdir -p "${BACKUP_ROOT}"
BACKUP_DIR="${BACKUP_ROOT}/upgrade-$(date +%Y%m%d-%H%M%S)"
mkdir -p "${BACKUP_DIR}"

for runtime_path in config media branding; do
    if [[ -e "${APP_DIR}/${runtime_path}" ]]; then
        cp -a "${APP_DIR}/${runtime_path}" "${BACKUP_DIR}/"
    fi
done

systemctl stop "${SERVICE_NAME}" || true

rsync -a \
    --delete \
    --exclude '.git/' \
    --exclude 'venv/' \
    --exclude '__pycache__/' \
    --exclude '*.pyc' \
    --exclude 'config/signage.db' \
    --exclude 'media/*' \
    --exclude 'branding/logos/*' \
    "${SOURCE_DIR}/" "${APP_DIR}/"

chown -R "${CPIT_USER}:${CPIT_GROUP}" "${APP_DIR}"

if [[ ! -x "${APP_DIR}/venv/bin/python" ]]; then
    sudo -u "${CPIT_USER}" python3 -m venv "${APP_DIR}/venv"
fi

sudo -u "${CPIT_USER}" "${APP_DIR}/venv/bin/python" -m pip install --upgrade pip wheel
sudo -u "${CPIT_USER}" "${APP_DIR}/venv/bin/pip" install -r "${APP_DIR}/requirements.txt"

if [[ -f "${APP_DIR}/app/init_database.py" ]]; then
    (
        cd "${APP_DIR}"
        sudo -u "${CPIT_USER}" "${APP_DIR}/venv/bin/python" -m app.init_database
    )
fi

systemctl daemon-reload
systemctl restart "${SERVICE_NAME}"
sleep 3

"${APP_DIR}/scripts/health-check.sh"

echo "Upgrade complete."
echo "Runtime backup: ${BACKUP_DIR}"

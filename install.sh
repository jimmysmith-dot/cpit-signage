#!/usr/bin/env bash
set -Eeuo pipefail

APP_NAME="CPIT Signage Studio"
APP_DIR="/opt/cpit-signage"
SERVICE_NAME="cpit-player"
SOURCE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="/var/log/cpit-signage-install.log"
BACKUP_ROOT="/var/backups/cpit-signage"

exec > >(tee -a "${LOG_FILE}") 2>&1

step() {
    printf "\n\033[1;34m==> %s\033[0m\n" "$1"
}

ok() {
    printf "\033[1;32m[OK]\033[0m %s\n" "$1"
}

warn() {
    printf "\033[1;33m[WARN]\033[0m %s\n" "$1"
}

die() {
    printf "\033[1;31m[ERROR]\033[0m %s\n" "$1" >&2
    exit 1
}

require_source_file() {
    local relative_path="$1"

    if [[ ! -e "${SOURCE_DIR}/${relative_path}" ]]; then
        die "Release package is incomplete: missing ${relative_path}

This installer must be run from the ROOT OF THE COMPLETE CPIT SIGNAGE REPOSITORY.
The package must contain app/, deployment/, scripts/, requirements.txt, and install.sh.

Do not run the standalone installer-tools ZIP as the application release."
    fi
}

if [[ "${EUID}" -ne 0 ]]; then
    die "Run this installer with sudo: sudo ./install.sh"
fi

step "Validating release package"
require_source_file "app/__init__.py"
require_source_file "app/app.py"
require_source_file "app/init_database.py"
require_source_file "app/routes/api.py"
require_source_file "app/services/database.py"
require_source_file "app/templates/admin.html"
require_source_file "deployment/cpit-player.service"
require_source_file "deployment/cpit-signage.desktop"
require_source_file "deployment/50-autologin.conf"
require_source_file "scripts/start-kiosk.sh"
require_source_file "scripts/health-check.sh"
require_source_file "requirements.txt"

if [[ "${SOURCE_DIR}" == "${APP_DIR}" ]]; then
    die "Run install.sh from a staging checkout, not from ${APP_DIR}.
Example:
  cd ~/cpit-signage
  sudo ./install.sh"
fi

CPIT_USER="${CPIT_USER:-${SUDO_USER:-}}"

if [[ -z "${CPIT_USER}" || "${CPIT_USER}" == "root" ]]; then
    read -r -p "Desktop user for kiosk autologin: " CPIT_USER
fi

id "${CPIT_USER}" >/dev/null 2>&1 || die "User '${CPIT_USER}' does not exist."

CPIT_GROUP="$(id -gn "${CPIT_USER}")"
CPIT_HOME="$(getent passwd "${CPIT_USER}" | cut -d: -f6)"

[[ -n "${CPIT_HOME}" && -d "${CPIT_HOME}" ]] \
    || die "Could not determine the home directory for ${CPIT_USER}."

if [[ ! -f /etc/os-release ]]; then
    die "This installer requires Debian Linux."
fi

# shellcheck disable=SC1091
source /etc/os-release

[[ "${ID:-}" == "debian" ]] || die "This installer is intended for Debian."

if [[ "${VERSION_ID:-0}" != "13" ]]; then
    warn "Tested on Debian 13; detected Debian ${VERSION_ID:-unknown}."
fi

echo
echo "================================================"
echo "       ${APP_NAME} Installer"
echo "================================================"
echo "Source:      ${SOURCE_DIR}"
echo "Destination: ${APP_DIR}"
echo "Kiosk user:  ${CPIT_USER}"
echo "================================================"

step "Installing operating-system dependencies"
export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get install -y \
    python3 \
    python3-venv \
    python3-pip \
    chromium \
    lightdm \
    xfce4 \
    unclutter \
    x11-xserver-utils \
    curl \
    git \
    rsync \
    sqlite3 \
    unzip \
    fonts-dejavu-core \
    fonts-liberation
ok "Dependencies installed"

step "Stopping any existing service"
systemctl stop "${SERVICE_NAME}" 2>/dev/null || true
ok "Existing service stopped"

step "Backing up existing runtime data"
mkdir -p "${BACKUP_ROOT}"

if [[ -d "${APP_DIR}" ]]; then
    BACKUP_DIR="${BACKUP_ROOT}/pre-install-$(date +%Y%m%d-%H%M%S)"
    mkdir -p "${BACKUP_DIR}"

    for runtime_path in config media branding; do
        if [[ -e "${APP_DIR}/${runtime_path}" ]]; then
            cp -a "${APP_DIR}/${runtime_path}" "${BACKUP_DIR}/"
        fi
    done

    ok "Existing runtime data backed up to ${BACKUP_DIR}"
else
    ok "No previous installation found"
fi

step "Installing application source"
mkdir -p "${APP_DIR}"

rsync -a \
    --delete \
    --exclude '.git/' \
    --exclude 'venv/' \
    --exclude '__pycache__/' \
    --exclude '*.pyc' \
    --exclude 'backups/' \
    --exclude 'config/signage.db' \
    --exclude 'media/*' \
    --exclude 'branding/logos/*' \
    "${SOURCE_DIR}/" "${APP_DIR}/"

mkdir -p \
    "${APP_DIR}/config" \
    "${APP_DIR}/media" \
    "${APP_DIR}/branding/logos" \
    "${APP_DIR}/logs"

touch \
    "${APP_DIR}/media/.gitkeep" \
    "${APP_DIR}/branding/logos/.gitkeep"

chown -R "${CPIT_USER}:${CPIT_GROUP}" "${APP_DIR}"

[[ -f "${APP_DIR}/app/app.py" ]] \
    || die "Application copy failed: ${APP_DIR}/app/app.py is missing."

ok "Complete application source installed"

step "Creating Python virtual environment"
rm -rf "${APP_DIR}/venv"
sudo -u "${CPIT_USER}" python3 -m venv "${APP_DIR}/venv"

sudo -u "${CPIT_USER}" \
    "${APP_DIR}/venv/bin/python" -m pip install --upgrade pip wheel

sudo -u "${CPIT_USER}" \
    "${APP_DIR}/venv/bin/pip" install -r "${APP_DIR}/requirements.txt"

ok "Python environment created"

step "Compiling Python source"
(
    cd "${APP_DIR}"
    sudo -u "${CPIT_USER}" \
        "${APP_DIR}/venv/bin/python" -m compileall -q app
)
ok "Python source compiled"

step "Initializing database"
(
    cd "${APP_DIR}"
    sudo -u "${CPIT_USER}" \
        "${APP_DIR}/venv/bin/python" -m app.init_database
)
ok "Database initialized"

step "Installing systemd service"
sed \
    -e "s/@CPIT_USER@/${CPIT_USER}/g" \
    -e "s/@CPIT_GROUP@/${CPIT_GROUP}/g" \
    "${APP_DIR}/deployment/cpit-player.service" \
    > "/etc/systemd/system/${SERVICE_NAME}.service"

chmod 0644 "/etc/systemd/system/${SERVICE_NAME}.service"
systemctl daemon-reload
systemctl enable "${SERVICE_NAME}"
systemctl restart "${SERVICE_NAME}"
ok "Application service installed"

step "Waiting for application startup"
for attempt in {1..20}; do
    if curl --silent --fail --max-time 2 \
        http://127.0.0.1:5000/ >/dev/null 2>&1; then
        ok "Application is responding on port 5000"
        break
    fi

    if [[ "${attempt}" -eq 20 ]]; then
        journalctl -u "${SERVICE_NAME}" -n 100 --no-pager || true
        die "Application did not start successfully."
    fi

    sleep 1
done

step "Configuring LightDM autologin"
mkdir -p /etc/lightdm/lightdm.conf.d

sed \
    -e "s/@CPIT_USER@/${CPIT_USER}/g" \
    "${APP_DIR}/deployment/50-autologin.conf" \
    > /etc/lightdm/lightdm.conf.d/50-cpit-signage-autologin.conf

groupadd -f autologin
/usr/sbin/usermod -aG autologin "${CPIT_USER}"
ok "LightDM autologin configured"

step "Configuring Chromium kiosk startup"
chmod 0755 \
    "${APP_DIR}/scripts/start-kiosk.sh" \
    "${APP_DIR}/scripts/health-check.sh"

AUTOSTART_DIR="${CPIT_HOME}/.config/autostart"
mkdir -p "${AUTOSTART_DIR}"

install -m 0644 \
    "${APP_DIR}/deployment/cpit-signage.desktop" \
    "${AUTOSTART_DIR}/cpit-signage.desktop"

mkdir -p "${CPIT_HOME}/.config/cpit-signage-chromium"
chown -R "${CPIT_USER}:${CPIT_GROUP}" "${CPIT_HOME}/.config"
ok "Kiosk startup configured"

step "Enabling graphical boot"
systemctl set-default graphical.target
systemctl enable lightdm
ok "Graphical startup enabled"

step "Running health check"
"${APP_DIR}/scripts/health-check.sh"
ok "Health check passed"

echo
echo "================================================"
echo " Installation complete"
echo "================================================"
echo " Player: http://127.0.0.1:5000/"
echo " Admin:  http://127.0.0.1:5000/admin/"
echo
echo " Reboot to test autologin and kiosk mode:"
echo "   sudo reboot"
echo
echo " Installer log:"
echo "   ${LOG_FILE}"
echo "================================================"

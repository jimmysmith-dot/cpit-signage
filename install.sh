\
#!/usr/bin/env bash
set -Eeuo pipefail

APP_NAME="CPIT Signage Studio"
APP_DIR="/opt/cpit-signage"
SERVICE_NAME="cpit-player"
SOURCE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKUP_ROOT="/var/backups/cpit-signage"
LOG_FILE="/var/log/cpit-signage-install.log"

exec > >(tee -a "${LOG_FILE}") 2>&1

step() {
    printf "\n\033[1;34m==> %s\033[0m\n" "$1"
}

success() {
    printf "\033[1;32m[OK]\033[0m %s\n" "$1"
}

die() {
    printf "\033[1;31m[ERROR]\033[0m %s\n" "$1" >&2
    exit 1
}

if [[ "${EUID}" -ne 0 ]]; then
    die "Run this installer with sudo: sudo ./install.sh"
fi

CPIT_USER="${CPIT_USER:-${SUDO_USER:-}}"

if [[ -z "${CPIT_USER}" || "${CPIT_USER}" == "root" ]]; then
    read -r -p "Desktop user for kiosk autologin: " CPIT_USER
fi

id "${CPIT_USER}" >/dev/null 2>&1 || die "User '${CPIT_USER}' does not exist."

CPIT_GROUP="$(id -gn "${CPIT_USER}")"
CPIT_HOME="$(getent passwd "${CPIT_USER}" | cut -d: -f6)"

[[ -n "${CPIT_HOME}" && -d "${CPIT_HOME}" ]] || die "Could not determine home directory for ${CPIT_USER}."

if [[ ! -f /etc/os-release ]]; then
    die "This installer requires Debian Linux."
fi

# shellcheck disable=SC1091
source /etc/os-release

[[ "${ID:-}" == "debian" ]] || die "This release is intended for Debian."
if [[ "${VERSION_ID:-0}" != "13" ]]; then
    printf "\033[1;33m[WARN]\033[0m Tested on Debian 13; detected Debian %s.\n" "${VERSION_ID:-unknown}"
fi

echo
echo "================================================"
echo "       ${APP_NAME} Installer"
echo "================================================"
echo "Source:       ${SOURCE_DIR}"
echo "Destination:  ${APP_DIR}"
echo "Kiosk user:   ${CPIT_USER}"
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
    fonts-dejavu-core \
    fonts-liberation
success "Dependencies installed"

step "Preparing application destination"
mkdir -p "${APP_DIR}" "${BACKUP_ROOT}"

if [[ -d "${APP_DIR}/app" ]]; then
    BACKUP_DIR="${BACKUP_ROOT}/pre-install-$(date +%Y%m%d-%H%M%S)"
    mkdir -p "${BACKUP_DIR}"
    for runtime_path in config media branding; do
        if [[ -e "${APP_DIR}/${runtime_path}" ]]; then
            cp -a "${APP_DIR}/${runtime_path}" "${BACKUP_DIR}/"
        fi
    done
    success "Existing runtime data backed up to ${BACKUP_DIR}"
fi

if [[ "${SOURCE_DIR}" != "${APP_DIR}" ]]; then
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
fi

mkdir -p \
    "${APP_DIR}/config" \
    "${APP_DIR}/media" \
    "${APP_DIR}/branding/logos" \
    "${APP_DIR}/logs" \
    "${APP_DIR}/scripts" \
    "${APP_DIR}/deployment"

touch "${APP_DIR}/media/.gitkeep" "${APP_DIR}/branding/logos/.gitkeep"
chown -R "${CPIT_USER}:${CPIT_GROUP}" "${APP_DIR}"
success "Application files prepared"

step "Creating Python environment"
if [[ ! -x "${APP_DIR}/venv/bin/python" ]]; then
    sudo -u "${CPIT_USER}" python3 -m venv "${APP_DIR}/venv"
fi

sudo -u "${CPIT_USER}" "${APP_DIR}/venv/bin/python" -m pip install --upgrade pip wheel

if [[ -f "${APP_DIR}/requirements.txt" ]]; then
    sudo -u "${CPIT_USER}" "${APP_DIR}/venv/bin/pip" install -r "${APP_DIR}/requirements.txt"
else
    sudo -u "${CPIT_USER}" "${APP_DIR}/venv/bin/pip" install Flask Pillow Werkzeug
fi
success "Python dependencies installed"

step "Initializing application data"
if [[ -f "${APP_DIR}/app/init_database.py" ]]; then
    (
        cd "${APP_DIR}"
        sudo -u "${CPIT_USER}" "${APP_DIR}/venv/bin/python" -m app.init_database
    ) || die "Database initialization failed."
else
    printf "\033[1;33m[WARN]\033[0m app/init_database.py not found; application may initialize the database on first start.\n"
fi

chown -R "${CPIT_USER}:${CPIT_GROUP}" \
    "${APP_DIR}/config" \
    "${APP_DIR}/media" \
    "${APP_DIR}/branding" \
    "${APP_DIR}/logs"
success "Runtime directories initialized"

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
success "Application service installed and started"

step "Configuring LightDM autologin"
mkdir -p /etc/lightdm/lightdm.conf.d
sed \
    -e "s/@CPIT_USER@/${CPIT_USER}/g" \
    "${APP_DIR}/deployment/50-autologin.conf" \
    > /etc/lightdm/lightdm.conf.d/50-cpit-signage-autologin.conf

groupadd -f autologin
usermod -aG autologin "${CPIT_USER}"
success "LightDM autologin configured"

step "Configuring Chromium kiosk startup"
install -m 0755 "${APP_DIR}/scripts/start-kiosk.sh" "${APP_DIR}/scripts/start-kiosk.sh"

AUTOSTART_DIR="${CPIT_HOME}/.config/autostart"
mkdir -p "${AUTOSTART_DIR}"
install -m 0644 \
    "${APP_DIR}/deployment/cpit-signage.desktop" \
    "${AUTOSTART_DIR}/cpit-signage.desktop"

mkdir -p "${CPIT_HOME}/.config/cpit-signage-chromium"
chown -R "${CPIT_USER}:${CPIT_GROUP}" "${CPIT_HOME}/.config"
success "Kiosk startup configured"

step "Setting graphical boot target"
systemctl set-default graphical.target
systemctl enable lightdm
success "Graphical startup enabled"

step "Running health check"
sleep 3
if "${APP_DIR}/scripts/health-check.sh"; then
    success "Health check passed"
else
    printf "\033[1;33m[WARN]\033[0m Health check reported an issue. Review: journalctl -u ${SERVICE_NAME} -n 100\n"
fi

echo
echo "================================================"
echo " Installation complete"
echo "================================================"
echo " Player: http://127.0.0.1:5000/"
echo " Admin:  http://127.0.0.1:5000/admin/"
echo
echo " Recommended next step:"
echo "   sudo reboot"
echo
echo " Installer log:"
echo "   ${LOG_FILE}"
echo "================================================"

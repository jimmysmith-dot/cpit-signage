#!/usr/bin/env bash
set -Eeuo pipefail

SOURCE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VERSION="$(tr -d '[:space:]' < "${SOURCE_DIR}/VERSION")"
OUTPUT_DIR="${SOURCE_DIR}/dist"
RELEASE_NAME="cpit-signage-studio-${VERSION}"
STAGING_DIR="${OUTPUT_DIR}/${RELEASE_NAME}"

required=(
    "app/app.py"
    "app/__init__.py"
    "app/routes/api.py"
    "app/services/database.py"
    "app/templates/admin.html"
    "deployment/cpit-player.service"
    "scripts/start-kiosk.sh"
    "install.sh"
    "requirements.txt"
    "VERSION"
)

for relative_path in "${required[@]}"; do
    if [[ ! -e "${SOURCE_DIR}/${relative_path}" ]]; then
        echo "Missing required release file: ${relative_path}" >&2
        exit 1
    fi
done

rm -rf "${STAGING_DIR}"
mkdir -p "${STAGING_DIR}"

rsync -a \
    --exclude '.git/' \
    --exclude 'venv/' \
    --exclude '__pycache__/' \
    --exclude '*.pyc' \
    --exclude 'backups/' \
    --exclude 'dist/' \
    --exclude 'config/signage.db' \
    --exclude 'media/*' \
    --exclude 'branding/logos/*' \
    "${SOURCE_DIR}/" "${STAGING_DIR}/"

mkdir -p \
    "${STAGING_DIR}/config" \
    "${STAGING_DIR}/media" \
    "${STAGING_DIR}/branding/logos"

touch \
    "${STAGING_DIR}/media/.gitkeep" \
    "${STAGING_DIR}/branding/logos/.gitkeep"

(
    cd "${OUTPUT_DIR}"
    tar -czf "${RELEASE_NAME}.tar.gz" "${RELEASE_NAME}"
    zip -qr "${RELEASE_NAME}.zip" "${RELEASE_NAME}"
    sha256sum \
        "${RELEASE_NAME}.tar.gz" \
        "${RELEASE_NAME}.zip" \
        > "${RELEASE_NAME}-SHA256SUMS.txt"
)

echo "Release built:"
echo "  ${OUTPUT_DIR}/${RELEASE_NAME}.tar.gz"
echo "  ${OUTPUT_DIR}/${RELEASE_NAME}.zip"
echo "  ${OUTPUT_DIR}/${RELEASE_NAME}-SHA256SUMS.txt"

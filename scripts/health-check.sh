#!/usr/bin/env bash
set -u

APP_DIR="${CPIT_APP_DIR:-/opt/cpit-signage}"
SERVICE_NAME="${CPIT_SERVICE_NAME:-cpit-player}"

PASS=0
WARN=0
FAIL=0

ok() {
    printf "  [ OK ] %s\n" "$1"
    PASS=$((PASS + 1))
}

warn() {
    printf "  [WARN] %s\n" "$1"
    WARN=$((WARN + 1))
}

fail() {
    printf "  [FAIL] %s\n" "$1"
    FAIL=$((FAIL + 1))
}

echo
echo "CPIT Signage Studio Health Check"
echo "================================"

[[ -f "${APP_DIR}/app/app.py" ]] \
    && ok "Application source exists" \
    || fail "Missing app/app.py"

[[ -f "${APP_DIR}/app/__init__.py" ]] \
    && ok "Application package exists" \
    || fail "Missing app/__init__.py"

[[ -x "${APP_DIR}/venv/bin/python" ]] \
    && ok "Python virtual environment exists" \
    || fail "Virtual environment is missing"

[[ -d "${APP_DIR}/media" ]] \
    && ok "Media directory exists" \
    || fail "Media directory is missing"

[[ -d "${APP_DIR}/branding/logos" ]] \
    && ok "Logo directory exists" \
    || fail "Logo directory is missing"

if "${APP_DIR}/venv/bin/python" -c \
    "import sys; sys.path.insert(0, '${APP_DIR}'); import app.app" \
    >/dev/null 2>&1; then
    ok "Python can import app.app"
else
    fail "Python cannot import app.app"
fi

if systemctl is-enabled "${SERVICE_NAME}" >/dev/null 2>&1; then
    ok "${SERVICE_NAME} is enabled"
else
    warn "${SERVICE_NAME} is not enabled"
fi

if systemctl is-active "${SERVICE_NAME}" >/dev/null 2>&1; then
    ok "${SERVICE_NAME} is running"
else
    fail "${SERVICE_NAME} is not running"
fi

if curl --silent --fail --max-time 5 \
    http://127.0.0.1:5000/ >/dev/null; then
    ok "Player URL responds"
else
    fail "Player URL does not respond"
fi

if curl --silent --fail --max-time 5 \
    http://127.0.0.1:5000/admin/ >/dev/null; then
    ok "Admin URL responds"
else
    fail "Admin URL does not respond"
fi

command -v chromium >/dev/null 2>&1 \
    && ok "Chromium is installed" \
    || fail "Chromium is not installed"

command -v lightdm >/dev/null 2>&1 \
    && ok "LightDM is installed" \
    || fail "LightDM is not installed"

AUTOLOGIN_DROPIN="/etc/lightdm/lightdm.conf.d/50-cpit-signage-autologin.conf"
AUTOLOGIN_MAIN="/etc/lightdm/lightdm.conf"

if [[ -f "${AUTOLOGIN_DROPIN}" ]] \
    && grep -Eq '^[[:space:]]*autologin-user[[:space:]]*=[[:space:]]*[^#[:space:]]+' \
        "${AUTOLOGIN_DROPIN}"; then
    ok "Autologin configuration exists (LightDM drop-in)"
elif [[ -f "${AUTOLOGIN_MAIN}" ]] \
    && grep -Eq '^[[:space:]]*autologin-user[[:space:]]*=[[:space:]]*[^#[:space:]]+' \
        "${AUTOLOGIN_MAIN}"; then
    ok "Autologin configuration exists (lightdm.conf)"
else
    warn "Autologin configuration is missing"
fi

echo
printf "Results: %d passed, %d warnings, %d failed\n" \
    "${PASS}" "${WARN}" "${FAIL}"

(( FAIL == 0 ))

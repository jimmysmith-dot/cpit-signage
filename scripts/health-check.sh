\
#!/usr/bin/env bash
set -u

APP_DIR="${CPIT_APP_DIR:-/opt/cpit-signage}"
SERVICE_NAME="${CPIT_SERVICE_NAME:-cpit-player}"
PLAYER_URL="${CPIT_PLAYER_URL:-http://127.0.0.1:5000}"
ADMIN_URL="${CPIT_ADMIN_URL:-http://127.0.0.1:5000/admin/}"

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

check_command() {
    local command_name="$1"
    if command -v "${command_name}" >/dev/null 2>&1; then
        ok "${command_name} is installed"
    else
        fail "${command_name} is not installed"
    fi
}

echo
echo "CPIT Signage Studio Health Check"
echo "================================"

[[ -d "${APP_DIR}" ]] && ok "Application directory exists" || fail "Missing ${APP_DIR}"
[[ -x "${APP_DIR}/venv/bin/python" ]] && ok "Python virtual environment exists" || fail "Virtual environment is missing"
[[ -f "${APP_DIR}/app/app.py" ]] && ok "Application entry point exists" || fail "Missing app/app.py"
[[ -d "${APP_DIR}/media" ]] && ok "Media directory exists" || fail "Media directory is missing"
[[ -d "${APP_DIR}/branding/logos" ]] && ok "Logo directory exists" || fail "Logo directory is missing"
[[ -d "${APP_DIR}/config" ]] && ok "Config directory exists" || fail "Config directory is missing"

check_command chromium
check_command curl
check_command lightdm

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

if curl --silent --show-error --fail --max-time 5 "${PLAYER_URL}" >/dev/null; then
    ok "Player URL responds"
else
    fail "Player URL did not respond: ${PLAYER_URL}"
fi

if curl --silent --show-error --fail --max-time 5 "${ADMIN_URL}" >/dev/null; then
    ok "Administration URL responds"
else
    fail "Administration URL did not respond: ${ADMIN_URL}"
fi

if [[ -f /etc/lightdm/lightdm.conf.d/50-cpit-signage-autologin.conf ]]; then
    ok "LightDM autologin configuration exists"
else
    warn "LightDM autologin configuration was not found"
fi

echo
printf "Results: %d passed, %d warnings, %d failed\n" "${PASS}" "${WARN}" "${FAIL}"

if (( FAIL > 0 )); then
    exit 1
fi

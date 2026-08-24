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

DISPLAY_MANAGER=""

if [[ -r /etc/X11/default-display-manager ]]; then
    DISPLAY_MANAGER="$(
        basename "$(
            tr -d '[:space:]' < /etc/X11/default-display-manager
        )"
    )"
fi

if [[ "${DISPLAY_MANAGER}" != "gdm3" && "${DISPLAY_MANAGER}" != "lightdm" ]]; then
    if systemctl is-active gdm3 >/dev/null 2>&1; then
        DISPLAY_MANAGER="gdm3"
    elif systemctl is-active lightdm >/dev/null 2>&1; then
        DISPLAY_MANAGER="lightdm"
    fi
fi

case "${DISPLAY_MANAGER}" in
    gdm3)
        command -v gdm3 >/dev/null 2>&1 \
            && ok "Display manager detected: GDM3" \
            || fail "GDM3 is configured but not installed"
        ;;
    lightdm)
        command -v lightdm >/dev/null 2>&1 \
            && ok "Display manager detected: LightDM" \
            || fail "LightDM is configured but not installed"
        ;;
    *)
        warn "Supported display manager could not be detected"
        ;;
esac

case "${DISPLAY_MANAGER}" in
    gdm3)
        GDM_CONFIG="/etc/gdm3/daemon.conf"
        if [[ -f "${GDM_CONFIG}" ]] \
            && grep -Eqi '^[[:space:]]*AutomaticLoginEnable[[:space:]]*=[[:space:]]*true[[:space:]]*$' "${GDM_CONFIG}" \
            && grep -Eqi '^[[:space:]]*AutomaticLogin[[:space:]]*=[[:space:]]*[^#[:space:]]+' "${GDM_CONFIG}"; then
            ok "Autologin configuration exists (GDM3)"
        else
            warn "GDM3 autologin configuration is missing"
        fi
        ;;
    lightdm)
        AUTOLOGIN_DROPIN="/etc/lightdm/lightdm.conf.d/50-cpit-signage-autologin.conf"
        AUTOLOGIN_MAIN="/etc/lightdm/lightdm.conf"

        if [[ -f "${AUTOLOGIN_DROPIN}" ]] \
            && grep -Eq '^[[:space:]]*autologin-user[[:space:]]*=[[:space:]]*[^#[:space:]]+' "${AUTOLOGIN_DROPIN}"; then
            ok "Autologin configuration exists (LightDM drop-in)"
        elif [[ -f "${AUTOLOGIN_MAIN}" ]] \
            && grep -Eq '^[[:space:]]*autologin-user[[:space:]]*=[[:space:]]*[^#[:space:]]+' "${AUTOLOGIN_MAIN}"; then
            ok "Autologin configuration exists (lightdm.conf)"
        else
            warn "LightDM autologin configuration is missing"
        fi
        ;;
    *)
        warn "Autologin could not be validated"
        ;;
esac

echo
printf "Results: %d passed, %d warnings, %d failed\n" \
    "${PASS}" "${WARN}" "${FAIL}"

(( FAIL == 0 ))

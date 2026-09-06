#!/bin/bash
set -u

sleep 5

if [[ "${XDG_SESSION_TYPE:-}" == "wayland" || -n "${WAYLAND_DISPLAY:-}" ]]; then
    if command -v wlopm >/dev/null 2>&1; then
        wlopm --on '*' >/dev/null 2>&1 || true
    fi
else
    if command -v xset >/dev/null 2>&1; then
        xset s off 2>/dev/null || true
        xset -dpms 2>/dev/null || true
        xset s noblank 2>/dev/null || true
    fi
    if command -v unclutter >/dev/null 2>&1; then
        unclutter -idle 1 &
    fi
fi

pkill chromium 2>/dev/null || true

exec chromium \
  --user-data-dir="${HOME}/.config/cpit-signage-chromium" \
  --kiosk \
  --start-fullscreen \
  --no-first-run \
  --password-store=basic \
  --disable-session-crashed-bubble \
  --disable-infobars \
  --noerrdialogs \
  http://localhost:5000

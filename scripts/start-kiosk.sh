#!/bin/bash

sleep 5

xset s off
xset -dpms
xset s noblank

pkill chromium 2>/dev/null
unclutter -idle 1 &

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

#!/bin/bash

sleep 5

xset s off
xset -dpms
xset s noblank

pkill chromium 2>/dev/null
unclutter -idle 1 &

exec chromium \
  --user-data-dir=/home/user/.config/cpit-signage-chromium \
  --kiosk \
  --no-first-run \
  --disable-session-crashed-bubble \
  --disable-infobars \
  --noerrdialogs \
  http://localhost:5000

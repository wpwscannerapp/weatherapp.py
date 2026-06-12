#!/bin/bash
#=======================================================================
# 🖥️ KIOSK INTERFACE INITIALIZATION ENGINE (Labwc / Wayland Compatible)
#=======================================================================

# Explicitly pass structural display target parameters back to the active thread
export WAYLAND_DISPLAY=wayland-0
export XDG_RUNTIME_DIR=/run/user/$(id -u)

echo "⏳ Holding launcher threads while background web layers initialize..."
# Give the local Flask background service and network stack 12 seconds to boot
sleep 12

echo "🚀 Maximizing dashboard interface into standalone Kiosk Mode..."
# --kiosk: Activates absolute true hardware fullscreen frame layout wrapper
# --noerrdialogs: Squashes unexpected system recovery crash popup alerts
# --disable-infobars: Suppresses automated web software tracking banners
# --check-for-update-interval: Prevents unnecessary network update pings on low-power CPUs
chromium-browser \
    --kiosk \
    --noerrdialogs \
    --disable-infobars \
    --check-for-update-interval=31536000 \
    --ozone-platform=wayland \
    http://localhost:5000 &

echo "✅ Kiosk operational deployment complete."

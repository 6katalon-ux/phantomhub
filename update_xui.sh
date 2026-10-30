#!/usr/bin/env bash
# Quick patch updater for 3X-UI client & provisioner
set -e

APP_DIR="/opt/vpn_store"
if [ ! -d "$APP_DIR" ]; then
    APP_DIR="$(pwd)"
fi

echo "Updating VPN Store 3X-UI integration in $APP_DIR..."

# Remove stale pyc cache
find "$APP_DIR" -name "*.pyc" -delete 2>/dev/null || true
find "$APP_DIR" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true

# Kill any stuck python processes
pkill -9 -f uvicorn 2>/dev/null || true
pkill -9 -f "app.bot.bot" 2>/dev/null || true

# Restart systemd services
systemctl daemon-reload 2>/dev/null || true
systemctl restart vpnstore-web.service 2>/dev/null || true
systemctl restart vpnstore-bot.service 2>/dev/null || true

echo "Done! Services restarted successfully."

#!/usr/bin/env bash
#
# VPN Store — Instant Diagnostic and Repair Script
# Run: sudo bash fix.sh
#

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${CYAN}======================================================"
echo -e "       🔍 VPN Store Diagnostics & Auto-Repair"
echo -e "======================================================${NC}"

if [ "$EUID" -ne 0 ]; then
  echo -e "${RED}[ERROR] Please run with: sudo bash fix.sh${NC}"
  exit 1
fi

APP_DIR="/opt/vpn_store"
if [ ! -d "$APP_DIR" ]; then
  APP_DIR="$(pwd)"
fi

cd "$APP_DIR"
echo -e "${GREEN}[1/5] Checking Python Virtual Environment in ${APP_DIR}/.venv...${NC}"
if [ ! -f "${APP_DIR}/.venv/bin/python" ]; then
  echo -e "${YELLOW}Re-creating virtual environment...${NC}"
  python3 -m venv "${APP_DIR}/.venv"
  "${APP_DIR}/.venv/bin/pip" install --upgrade pip
  "${APP_DIR}/.venv/bin/pip" install -r requirements.txt
fi

echo -e "${GREEN}[2/5] Testing FastAPI direct import...${NC}"
"${APP_DIR}/.venv/bin/python" -c "from app.main import app; print('FastAPI imported cleanly!')"

echo -e "${GREEN}[3/5] Updating and reloading Systemd services...${NC}"
python3 setup.py --repair 2>/dev/null || true
systemctl daemon-reload
systemctl restart vpnstore-web.service
systemctl restart vpnstore-bot.service || true
systemctl restart vpnstore-worker.service || true

echo -e "${GREEN}[4/5] Reloading Nginx reverse proxy...${NC}"
systemctl restart nginx || true

echo -e "${GREEN}[5/5] Checking local HTTP response on port 8000...${NC}"
sleep 2
if curl -s -f http://127.0.0.1:8000/health > /dev/null; then
  echo -e "${GREEN}[✓] SUCCESS: Web application is responding on port 8000!${NC}"
  echo -e "Response from /health: $(curl -s http://127.0.0.1:8000/health)"
else
  echo -e "${RED}[!] Web service is not yet responding. Showing last 20 log lines:${NC}"
  journalctl -u vpnstore-web.service -n 20 --no-pager
fi

echo -e "\n${CYAN}======================================================${NC}"
echo -e "${GREEN}Status check complete. Open http://$(curl -s ifconfig.me) in browser.${NC}"

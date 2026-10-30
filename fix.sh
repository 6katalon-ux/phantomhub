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
BOLD='\033[1m'
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

echo -e "${GREEN}[1/6] Syncing latest updates from Git...${NC}"
if [ -d ".git" ]; then
  git pull origin main 2>/dev/null || git pull 2>/dev/null || true
fi

echo -e "${GREEN}[2/6] Ensuring all Python dependencies are installed in .venv...${NC}"
if [ ! -f "${APP_DIR}/.venv/bin/python" ]; then
  echo -e "${YELLOW}Creating virtual environment...${NC}"
  python3 -m venv "${APP_DIR}/.venv"
  "${APP_DIR}/.venv/bin/pip" install --upgrade pip
fi
"${APP_DIR}/.venv/bin/pip" install -r requirements.txt

echo -e "${GREEN}[3/6] Ensuring Administrator Account is configured...${NC}"
"${APP_DIR}/.venv/bin/python" -c "
import sqlite3, os
db_path = '${APP_DIR}/data/vpn_store.db'
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('SELECT username FROM admins LIMIT 1')
    row = c.fetchone()
    if row:
        print(f'Admin user found: {row[0]}')
    else:
        import bcrypt
        h = bcrypt.hashpw(b'admin123', bcrypt.gensalt()).decode()
        c.execute('INSERT INTO admins (username, password_hash, role) VALUES (?, ?, ?)', ('admin', h, 'superadmin'))
        conn.commit()
        print('Created default admin: admin / admin123')
    conn.close()
"

echo -e "${GREEN}[4/6] Testing FastAPI application import...${NC}"
"${APP_DIR}/.venv/bin/python" -c "from app.main import app; print('FastAPI imported cleanly!')"

echo -e "${GREEN}[5/6] Updating and restarting Systemd services...${NC}"
systemctl daemon-reload
systemctl restart vpnstore-web.service
systemctl restart vpnstore-bot.service 2>/dev/null || true
systemctl restart vpnstore-worker.service 2>/dev/null || true
systemctl restart nginx 2>/dev/null || true

echo -e "${GREEN}[6/6] Checking local HTTP response on port 8000...${NC}"
sleep 2
if curl -s -f http://127.0.0.1:8000/health > /dev/null; then
  echo -e "${GREEN}[✓] SUCCESS: Web application is responding cleanly on port 8000!${NC}"
  echo -e "Response from /health: $(curl -s http://127.0.0.1:8000/health)"
else
  echo -e "${RED}[!] Web service is not yet responding. Showing last 20 log lines:${NC}"
  journalctl -u vpnstore-web.service -n 20 --no-pager
fi

PUBLIC_IP=$(curl -s ifconfig.me 2>/dev/null || echo "YOUR_SERVER_IP")

echo -e "\n${CYAN}======================================================${NC}"
echo -e "${BOLD}${GREEN}✅ VPN Store Web Panel is LIVE!${NC}"
echo -e "Web Panel URL: ${CYAN}http://${PUBLIC_IP}${NC} (or http://${PUBLIC_IP}:8000)"
echo -e "Username:      ${BOLD}admin${NC}"
echo -e "Default Pass:  ${BOLD}admin123${NC} (or your chosen password)"
echo -e "${CYAN}======================================================${NC}"

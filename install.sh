#!/usr/bin/env bash
#
# VPN Store — One-line Fast Installer for Ubuntu 24.04 / Debian 12
# Usage:
#   curl -sSL https://raw.githubusercontent.com/username/vpn-store/main/install.sh | sudo bash
#   or:
#   sudo bash install.sh
#

set -e

# ANSI Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${CYAN}======================================================"
echo -e "       🛡️  VPN Store Automated Quick Installer"
echo -e "======================================================${NC}"

if [ "$EUID" -ne 0 ]; then
  echo -e "${RED}[ERROR] This script must be run as root. Please run with sudo.${NC}"
  exit 1
fi

echo -e "${GREEN}[1/4] Ensuring Python 3 and Git are installed...${NC}"
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y -qq python3 python3-pip python3-venv git curl sqlite3

# If setup.py is present in current directory, run it directly
if [ -f "setup.py" ] && [ -d "app" ]; then
    echo -e "${GREEN}[2/4] Found local project files, running setup.py...${NC}"
    python3 setup.py
    exit 0
fi

# Otherwise clone to /opt/vpn_store
TARGET_DIR="/opt/vpn_store"
echo -e "${GREEN}[2/4] Preparing installation directory in ${TARGET_DIR}...${NC}"
mkdir -p "$TARGET_DIR"

if [ -d "$TARGET_DIR/.git" ]; then
    echo -e "${CYAN}Existing git repository detected in ${TARGET_DIR}. Updating...${NC}"
    cd "$TARGET_DIR"
    git pull || true
else
    echo -e "${CYAN}Running setup directly in ${TARGET_DIR}...${NC}"
fi

cd "$TARGET_DIR"
python3 setup.py

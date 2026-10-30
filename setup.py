#!/usr/bin/env python3
"""
VPN Store - Automated One-Command Production Installer
Target OS: Ubuntu 24.04 LTS (Noble Numbat) / Debian 12
Python Version: 3.12+

Usage:
    sudo python3 setup.py
"""

import os
import sys
import subprocess
import shutil
import secrets
import string
import socket
import json
import sqlite3
import getpass
from pathlib import Path
from datetime import datetime

# ANSI Terminal Colors
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'

def log(msg, color=Colors.CYAN, prefix="[*]"):
    print(f"{color}{prefix} {msg}{Colors.END}")

def success(msg):
    print(f"{Colors.GREEN}[✓] {msg}{Colors.END}")

def warn(msg):
    print(f"{Colors.YELLOW}[!] {msg}{Colors.END}")

def error(msg, fatal=True):
    print(f"\n{Colors.RED}[✗] ERROR: {msg}{Colors.END}")
    if fatal:
        sys.exit(1)

def run_cmd(cmd, check=True, cwd=None, capture_output=False, env=None):
    """Run a shell command safely"""
    try:
        res = subprocess.run(
            cmd,
            shell=isinstance(cmd, str),
            check=check,
            cwd=cwd,
            text=True,
            capture_output=capture_output,
            env=env or os.environ.copy()
        )
        return res
    except subprocess.CalledProcessError as e:
        error(f"Command failed: {cmd}\nExit code: {e.returncode}\n{e.stderr if capture_output else ''}")

def generate_secret(length=32):
    chars = string.ascii_letters + string.digits
    return ''.join(secrets.choice(chars) for _ in range(length))

def get_public_ip():
    """Attempt to detect public IP address"""
    methods = [
        "curl -s --max-time 3 https://api.ipify.org",
        "curl -s --max-time 3 https://ifconfig.me",
        "curl -s --max-time 3 https://icanhazip.com"
    ]
    for m in methods:
        try:
            res = subprocess.run(m, shell=True, capture_output=True, text=True, timeout=4)
            ip = res.stdout.strip()
            if ip and len(ip.split('.')) == 4:
                return ip
        except Exception:
            continue
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

def print_banner():
    print(f"""{Colors.CYAN}{Colors.BOLD}
========================================================================
             🛡️  VPN STORE — ONE-COMMAND INSTALLER
     Production VPN Management & Sales Platform (3X-UI + Telegram)
                 Designed for Ubuntu 24.04 LTS
========================================================================{Colors.END}
""")

def step1_check_root():
    log("Checking administrator privileges...", prefix="[1/16]")
    if os.geteuid() != 0:
        error("This installer requires root privileges. Please run with: sudo python3 setup.py")
    success("Running as root.")

def step2_check_os_and_python():
    log("Validating Operating System and Python version...", prefix="[2/16]")
    
    # Check Python version >= 3.12
    v = sys.version_info
    log(f"Current Python version: {v.major}.{v.minor}.{v.micro}")
    if v.major < 3 or (v.major == 3 and v.minor < 10):
        error(f"Python 3.10+ required (Python 3.12+ recommended). Found: {v.major}.{v.minor}")
    
    # Detect OS release
    os_info = "Linux"
    if os.path.exists("/etc/os-release"):
        with open("/etc/os-release", "r", encoding="utf-8") as f:
            lines = f.readlines()
            for line in lines:
                if line.startswith("PRETTY_NAME="):
                    os_info = line.strip().split("=")[1].replace('"', '')
                    break
    log(f"Detected OS: {os_info}")
    success("System validation passed.")

def step3_install_system_packages():
    log("Updating system packages and installing OS dependencies...", prefix="[3/16]")
    packages = [
        "python3-full",
        "python3-venv",
        "python3-pip",
        "sqlite3",
        "curl",
        "ufw",
        "nginx",
        "libssl-dev",
        "libffi-dev"
    ]
    log(f"Installing: {', '.join(packages)}")
    
    # Avoid interactive prompts during apt
    env = os.environ.copy()
    env["DEBIAN_FRONTEND"] = "noninteractive"
    
    run_cmd("apt-get update -y", env=env)
    run_cmd(f"apt-get install -y {' '.join(packages)}", env=env)
    success("System packages installed successfully.")

def step4_create_directories(base_dir):
    log("Creating application directory structure...", prefix="[4/16]")
    dirs = [
        base_dir / "data",
        base_dir / "backups",
        base_dir / "logs",
        base_dir / "systemd",
        base_dir / "nginx"
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
    success(f"Directories verified in {base_dir}")

def step5_setup_virtualenv(base_dir):
    log("Configuring Python virtual environment...", prefix="[5/16]")
    venv_dir = base_dir / ".venv"
    if not (venv_dir / "bin" / "python").exists():
        log("Creating clean venv at .venv...")
        run_cmd([sys.executable, "-m", "venv", str(venv_dir)])
    success(f"Virtualenv ready: {venv_dir}")
    return venv_dir

def step6_install_python_deps(base_dir, venv_dir):
    log("Installing Python dependencies from requirements.txt...", prefix="[6/16]")
    pip_bin = venv_dir / "bin" / "pip"
    req_file = base_dir / "requirements.txt"
    
    # Upgrade pip & wheel
    run_cmd([str(pip_bin), "install", "--upgrade", "pip", "setuptools", "wheel"])
    
    if req_file.exists():
        run_cmd([str(pip_bin), "install", "-r", str(req_file)])
    else:
        # Fallback list if standalone script without requirements.txt
        pkgs = [
            "fastapi>=0.115.0",
            "uvicorn[standard]>=0.30.0",
            "aiogram>=3.13.0",
            "aiohttp>=3.10.0",
            "pydantic>=2.8.0",
            "pydantic-settings>=2.4.0",
            "sqlalchemy>=2.0.30",
            "aiosqlite>=0.20.0",
            "bcrypt>=4.2.0",
            "pyjwt>=2.9.0",
            "apscheduler>=3.10.4",
            "qrcode>=7.4.2",
            "pillow>=10.4.0",
            "jinja2>=3.1.4",
            "python-multipart>=0.0.9",
            "requests>=2.32.0",
            "psutil>=6.0.0"
        ]
        run_cmd([str(pip_bin), "install"] + pkgs)
    success("All Python packages installed into virtual environment.")

def step7_generate_secrets(base_dir):
    log("Generating cryptographic keys and secrets...", prefix="[7/16]")
    secrets_file = base_dir / "data" / "secrets.json"
    if secrets_file.exists():
        with open(secrets_file, "r") as f:
            sec = json.load(f)
    else:
        sec = {
            "jwt_secret": generate_secret(64),
            "session_secret": generate_secret(32),
            "subscription_salt": generate_secret(24),
            "created_at": datetime.now().isoformat()
        }
        with open(secrets_file, "w") as f:
            json.dump(sec, f, indent=2)
        os.chmod(secrets_file, 0o600)
    success("Security secrets generated and stored with restrictive permissions (0600).")
    return sec

def step8_9_setup_database(base_dir, venv_dir, secrets_data):
    log("Initializing SQLite database with WAL mode and schema...", prefix="[8 & 9/16]")
    db_file = base_dir / "data" / "vpn_store.db"
    
    conn = sqlite3.connect(str(db_file))
    cur = conn.cursor()
    
    # Enable WAL mode and foreign keys
    cur.execute("PRAGMA journal_mode=WAL;")
    cur.execute("PRAGMA foreign_keys=ON;")
    
    # 1. Admins
    cur.execute("""
    CREATE TABLE IF NOT EXISTS admins (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'superadmin',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_login TIMESTAMP
    );
    """)
    
    # 2. Users
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        telegram_id INTEGER UNIQUE NOT NULL,
        username TEXT,
        first_name TEXT,
        last_name TEXT,
        wallet_balance INTEGER DEFAULT 0,
        trial_used INTEGER DEFAULT 0,
        is_blocked INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    
    # 3. Settings (Key-Value)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY,
        value TEXT,
        description TEXT,
        category TEXT DEFAULT 'general',
        is_secret INTEGER DEFAULT 0
    );
    """)
    
    # 4. Plans
    cur.execute("""
    CREATE TABLE IF NOT EXISTS plans (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT,
        price INTEGER NOT NULL,
        traffic_gb INTEGER NOT NULL,
        duration_days INTEGER NOT NULL,
        inbound_id INTEGER,
        protocol TEXT DEFAULT 'vless',
        max_ips INTEGER DEFAULT 2,
        is_active INTEGER DEFAULT 1,
        sort_order INTEGER DEFAULT 0
    );
    """)
    
    # 5. Services
    cur.execute("""
    CREATE TABLE IF NOT EXISTS services (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        telegram_id INTEGER NOT NULL,
        plan_id INTEGER,
        protocol TEXT DEFAULT 'vless',
        inbound_id INTEGER,
        client_uuid TEXT NOT NULL,
        client_email TEXT UNIQUE NOT NULL,
        config_link TEXT,
        sub_token TEXT UNIQUE,
        total_traffic_bytes INTEGER NOT NULL,
        used_traffic_bytes INTEGER DEFAULT 0,
        expire_time_ms INTEGER NOT NULL,
        is_active INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
    );
    """)
    
    # 6. Transactions
    cur.execute("""
    CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        amount INTEGER NOT NULL,
        balance_after INTEGER NOT NULL,
        type TEXT NOT NULL,
        description TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
    );
    """)
    
    # 7. Payments
    cur.execute("""
    CREATE TABLE IF NOT EXISTS payments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        amount INTEGER NOT NULL,
        method TEXT DEFAULT 'card',
        reference_id TEXT,
        receipt_note TEXT,
        status TEXT DEFAULT 'pending',
        admin_note TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        reviewed_at TIMESTAMP,
        FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
    );
    """)
    
    # 8. Gift Codes
    cur.execute("""
    CREATE TABLE IF NOT EXISTS gift_codes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        code TEXT UNIQUE NOT NULL,
        amount INTEGER NOT NULL,
        max_redemptions INTEGER DEFAULT 1,
        redeemed_count INTEGER DEFAULT 0,
        expire_at TIMESTAMP,
        is_active INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    
    # 9. Gift Redemptions
    cur.execute("""
    CREATE TABLE IF NOT EXISTS gift_redemptions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        gift_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        amount INTEGER NOT NULL,
        redeemed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(gift_id) REFERENCES gift_codes(id) ON DELETE CASCADE,
        FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
        UNIQUE(gift_id, user_id)
    );
    """)
    
    # 10. Inbounds Cache
    cur.execute("""
    CREATE TABLE IF NOT EXISTS inbounds_cache (
        id INTEGER PRIMARY KEY,
        inbound_id INTEGER UNIQUE NOT NULL,
        tag TEXT,
        protocol TEXT,
        port INTEGER,
        network TEXT,
        security TEXT,
        total_clients INTEGER DEFAULT 0,
        raw_data TEXT,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    
    # 11. Audit Logs
    cur.execute("""
    CREATE TABLE IF NOT EXISTS audit_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        admin_id INTEGER,
        action TEXT NOT NULL,
        target TEXT,
        details TEXT,
        ip_address TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    
    # 12. Notifications
    cur.execute("""
    CREATE TABLE IF NOT EXISTS notifications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        message TEXT NOT NULL,
        target_type TEXT DEFAULT 'all',
        target_id INTEGER,
        is_sent INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Seed Default Settings if missing
    default_settings = [
        # Bot Settings
        ("bot_token", "", "Telegram Bot Token from @BotFather", "bot", 1),
        ("bot_admin_ids", "123456789", "Comma-separated Telegram Admin IDs", "bot", 0),
        ("bot_enabled", "1", "Enable or disable Telegram bot service", "bot", 0),
        ("bot_welcome_msg", "سلام! به ربات خرید و مدیریت اشتراک خوش آمدید.\nبرای شروع، یکی از گزینه‌های زیر را انتخاب نمایید:", "Bot welcome message", "bot", 0),
        ("bot_support_username", "@support_vpn", "Support Telegram ID", "bot", 0),
        ("bot_maintenance", "0", "Enable bot maintenance mode", "bot", 0),
        
        # 3X-UI Settings
        ("xui_url", "http://127.0.0.1:2053", "3X-UI Base URL (e.g. http://server-ip:2053 or https://sub.domain.com:2053)", "xui", 0),
        ("xui_username", "admin", "3X-UI Admin Username", "xui", 0),
        ("xui_password", "admin", "3X-UI Admin Password", "xui", 1),
        ("xui_token", "", "Optional 3X-UI API Token", "xui", 1),
        ("xui_tls_verify", "0", "Verify SSL/TLS Certificate for 3X-UI", "xui", 0),
        ("xui_timeout", "10", "HTTP request timeout in seconds", "xui", 0),
        ("xui_default_inbound", "1", "Default Inbound ID for auto-provisioning", "xui", 0),
        ("vpn_server_host", get_public_ip(), "Public IP address or Domain for client config links", "xui", 0),
        
        # Free Trial Settings
        ("trial_enabled", "1", "Allow 1-time free trial for new users", "trial", 0),
        ("trial_traffic_gb", "1", "Free trial traffic limit in Gigabytes", "trial", 0),
        ("trial_duration_days", "3", "Free trial duration in days", "trial", 0),
        ("trial_inbound_id", "1", "Inbound ID used for trial subscriptions", "trial", 0),
        
        # General & Payment Settings
        ("site_name", "VPN Store", "Branding name in panel and bot", "general", 0),
        ("currency", "تومان", "Currency label (Toman / Rial / USD)", "general", 0),
        ("card_number", "6037-9975-0000-0000", "Bank Card Number for manual payments", "payment", 0),
        ("card_holder", "نام صاحب کارت", "Bank Card Owner Name", "payment", 0),
        ("crypto_wallet", "USDT (TRC20): T...", "Cryptocurrency payment address", "payment", 0),
        ("payment_instructions", "لطفاً پس از واریز مبلغ، تصویر فیش یا شماره پیگیری تراکنش را در این بخش ارسال فرمایید تا کیف پول شما شارژ گردد.", "Payment note displayed to users", "payment", 0),
        ("sync_interval_mins", "5", "Traffic sync worker frequency in minutes", "system", 0),
        ("backup_retention_days", "14", "Days to retain automatic backups", "system", 0)
    ]
    
    for k, v, d, c, s in default_settings:
        cur.execute("INSERT OR IGNORE INTO settings (key, value, description, category, is_secret) VALUES (?, ?, ?, ?, ?)",
                    (k, v, d, c, s))
    
    # Seed sample plans if none exist
    cur.execute("SELECT COUNT(*) FROM plans")
    if cur.fetchone()[0] == 0:
        sample_plans = [
            ("اشتراک پایه — ۳۰ گیگ", "سرعت بالا، نامحدود در اتصال ۲ کاربره", 120000, 30, 30, 1, "vless", 2, 1, 1),
            ("اشتراک نقره‌ای — ۶۰ گیگ", "محبوب‌ترین پلن، آی‌پی ثابت و پینگ پایین", 210000, 60, 30, 1, "vless", 2, 1, 2),
            ("اشتراک طلایی — ۱۰۰ گیگ", "ویژه استریم و گیم، پایداری ۱۰۰٪", 320000, 100, 30, 1, "vless", 3, 1, 3),
            ("اشتراک نامحدود — ۳ ماهه", "ترافیک ۲۵۰ گیگابایت سه ماهه ۳ کاربره", 750000, 250, 90, 1, "vless", 3, 1, 4),
        ]
        cur.executemany("""
        INSERT INTO plans (name, description, price, traffic_gb, duration_days, inbound_id, protocol, max_ips, is_active, sort_order)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, sample_plans)
    
    conn.commit()
    conn.close()
    success("Database schema created with all tables and initial plans.")
    return db_file

def step10_create_admin_account(base_dir, venv_dir):
    log("Setting up Web Administrator Account...", prefix="[10/16]")
    db_file = base_dir / "data" / "vpn_store.db"
    conn = sqlite3.connect(str(db_file))
    cur = conn.cursor()
    
    cur.execute("SELECT username FROM admins LIMIT 1")
    row = cur.fetchone()
    
    if row:
        log(f"Admin account already exists: {row[0]}")
        conn.close()
        return row[0], "(already configured)"
    
    # Prompt for admin credentials or generate secure defaults
    print(f"\n{Colors.BOLD}--- Administrator Account Setup ---{Colors.END}")
    admin_user = input(f"{Colors.YELLOW}Enter Admin Username [default: admin]: {Colors.END}").strip() or "admin"
    admin_pass = input(f"{Colors.YELLOW}Enter Admin Password [press Enter to auto-generate]: {Colors.END}").strip()
    
    if not admin_pass:
        admin_pass = generate_secret(16)
        log(f"Generated secure admin password: {Colors.BOLD}{admin_pass}{Colors.END}")
    
    # Hash with bcrypt using virtualenv python
    py_bin = venv_dir / "bin" / "python"
    hash_script = f"""
import bcrypt
password = {repr(admin_pass)}
hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
print(hashed)
"""
    res = subprocess.run([str(py_bin), "-c", hash_script], capture_output=True, text=True, check=True)
    password_hash = res.stdout.strip()
    
    cur.execute("INSERT INTO admins (username, password_hash, role) VALUES (?, ?, 'superadmin')",
                (admin_user, password_hash))
    conn.commit()
    conn.close()
    
    success(f"Admin account created: {admin_user}")
    return admin_user, admin_pass

def step11_generate_systemd_services(base_dir, venv_dir):
    log("Creating systemd service definitions...", prefix="[11/16]")
    py_bin = venv_dir / "bin" / "python"
    
    # 1. Web Service (FastAPI + Uvicorn)
    web_service = f"""[Unit]
Description=VPN Store Web Admin Panel & API
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory={base_dir}
ExecStart={py_bin} -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2
Restart=always
RestartSec=3
Environment="PYTHONPATH={base_dir}"
Environment="PYTHONUNBUFFERED=1"
StandardOutput=append:{base_dir}/logs/web.log
StandardError=append:{base_dir}/logs/web_error.log

[Install]
WantedBy=multi-user.target
"""
    with open("/etc/systemd/system/vpnstore-web.service", "w") as f:
        f.write(web_service)

    # 2. Telegram Bot Service (Aiogram 3)
    bot_service = f"""[Unit]
Description=VPN Store Aiogram 3 Telegram Bot
After=network.target vpnstore-web.service

[Service]
Type=simple
User=root
WorkingDirectory={base_dir}
ExecStart={py_bin} -m app.bot.bot
Restart=always
RestartSec=5
Environment="PYTHONPATH={base_dir}"
Environment="PYTHONUNBUFFERED=1"
StandardOutput=append:{base_dir}/logs/bot.log
StandardError=append:{base_dir}/logs/bot_error.log

[Install]
WantedBy=multi-user.target
"""
    with open("/etc/systemd/system/vpnstore-bot.service", "w") as f:
        f.write(bot_service)

    # 3. Traffic Sync & Worker Service
    worker_service = f"""[Unit]
Description=VPN Store Traffic Sync & Background Scheduler
After=network.target vpnstore-web.service

[Service]
Type=simple
User=root
WorkingDirectory={base_dir}
ExecStart={py_bin} -m app.workers.scheduler
Restart=always
RestartSec=10
Environment="PYTHONPATH={base_dir}"
Environment="PYTHONUNBUFFERED=1"
StandardOutput=append:{base_dir}/logs/worker.log
StandardError=append:{base_dir}/logs/worker_error.log

[Install]
WantedBy=multi-user.target
"""
    with open("/etc/systemd/system/vpnstore-worker.service", "w") as f:
        f.write(worker_service)

    run_cmd("systemctl daemon-reload")
    success("Systemd services created: vpnstore-web, vpnstore-bot, vpnstore-worker")

def step12_configure_startup():
    log("Enabling services to start automatically on system boot...", prefix="[12/16]")
    run_cmd("systemctl enable vpnstore-web.service")
    run_cmd("systemctl enable vpnstore-bot.service")
    run_cmd("systemctl enable vpnstore-worker.service")
    success("Automatic startup configured on reboot.")

def step13_14_start_services():
    log("Starting FastAPI web application & background workers...", prefix="[13 & 14/16]")
    run_cmd("systemctl restart vpnstore-web.service")
    run_cmd("systemctl restart vpnstore-worker.service")
    run_cmd("systemctl restart vpnstore-bot.service")
    success("Services started successfully.")

def step15_configure_firewall(public_ip):
    log("Configuring UFW firewall rules...", prefix="[15/16]")
    try:
        run_cmd("ufw allow 8000/tcp", check=False)
        run_cmd("ufw allow 80/tcp", check=False)
        run_cmd("ufw allow 443/tcp", check=False)
        run_cmd("ufw allow 22/tcp", check=False)
        success("Firewall ports opened: 8000 (Admin Web), 80, 443, 22 (SSH)")
    except Exception as e:
        warn(f"Firewall setup skipped: {e}")

def step16_display_summary(public_ip, admin_user, admin_pass):
    print(f"""
{Colors.GREEN}{Colors.BOLD}========================================================================
             🎉 VPN STORE INSTALLATION COMPLETED SUCCESSFULLY!
========================================================================{Colors.END}

{Colors.BOLD}📱 WEB ADMIN PANEL URL:{Colors.END}
    {Colors.CYAN}http://{public_ip}:8000{Colors.END}
    (Or open from mobile browser on your Android device)

{Colors.BOLD}🔑 ADMIN CREDENTIALS:{Colors.END}
    Username: {Colors.YELLOW}{admin_user}{Colors.END}
    Password: {Colors.YELLOW}{admin_pass}{Colors.END}

{Colors.BOLD}🚀 WHAT TO DO NEXT (From Your Mobile Browser):{Colors.END}
    1. Open {Colors.CYAN}http://{public_ip}:8000{Colors.END} on your phone.
    2. Log in with the credentials above.
    3. Go to {Colors.BOLD}"3X-UI Connection"{Colors.END} tab and set your 3X-UI panel URL, username, and password.
    4. Go to {Colors.BOLD}"Telegram Bot Settings"{Colors.END} tab and paste your Bot Token from @BotFather.
    5. Everything is ready! You never need SSH or Nano again.

{Colors.BOLD}🛠️ USEFUL SERVICE COMMANDS:{Colors.END}
    Check Web Status:     {Colors.CYAN}systemctl status vpnstore-web{Colors.END}
    Check Bot Status:     {Colors.CYAN}systemctl status vpnstore-bot{Colors.END}
    Check Worker Status:  {Colors.CYAN}systemctl status vpnstore-worker{Colors.END}
    View Live Web Logs:   {Colors.CYAN}tail -f /opt/vpn_store/logs/web.log{Colors.END}
    View Live Bot Logs:   {Colors.CYAN}tail -f /opt/vpn_store/logs/bot.log{Colors.END}

========================================================================
""")

def main():
    print_banner()
    
    # Determine base directory: if running inside cloned repo, use current dir; else /opt/vpn_store
    curr_dir = Path(__file__).resolve().parent
    if (curr_dir / "app").exists():
        base_dir = curr_dir
    else:
        base_dir = Path("/opt/vpn_store")
        base_dir.mkdir(parents=True, exist_ok=True)
    
    log(f"Application target root directory: {base_dir}")
    
    step1_check_root()
    step2_check_os_and_python()
    step3_install_system_packages()
    step4_create_directories(base_dir)
    venv_dir = step5_setup_virtualenv(base_dir)
    step6_install_python_deps(base_dir, venv_dir)
    sec = step7_generate_secrets(base_dir)
    step8_9_setup_database(base_dir, venv_dir, sec)
    admin_user, admin_pass = step10_create_admin_account(base_dir, venv_dir)
    step11_generate_systemd_services(base_dir, venv_dir)
    step12_configure_startup()
    step13_14_start_services()
    
    pub_ip = get_public_ip()
    step15_configure_firewall(pub_ip)
    step16_display_summary(pub_ip, admin_user, admin_pass)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInstallation cancelled by user.")
        sys.exit(1)
    except Exception as e:
        error(f"Installation failed: {e}\nPlease check system logs or report the issue.")

"""
Logging configuration with file rotation and log viewer utilities for the Admin Panel.
"""

import os
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
LOGS_DIR = BASE_DIR / "logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)

APP_LOG_PATH = LOGS_DIR / "app.log"
WEB_LOG_PATH = LOGS_DIR / "web.log"
BOT_LOG_PATH = LOGS_DIR / "bot.log"
WORKER_LOG_PATH = LOGS_DIR / "worker.log"

def setup_logger(name: str = "vpn_store", log_file: Path = APP_LOG_PATH, level=logging.INFO):
    logger = logging.getLogger(name)
    logger.setLevel(level)

    if not logger.handlers:
        formatter = logging.Formatter(
            '[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        # File Handler (5 MB per file, max 5 backups)
        file_handler = RotatingFileHandler(
            str(log_file),
            maxBytes=5 * 1024 * 1024,
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        # Console Handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    return logger

logger = setup_logger("vpn_store", APP_LOG_PATH)

def get_recent_logs(file_type: str = "web", lines_count: int = 150) -> list:
    """Read the last N lines from the requested log file or systemd journal for display in admin dashboard"""
    path_map = {
        "web": (WEB_LOG_PATH, "vpnstore-web.service"),
        "bot": (BOT_LOG_PATH, "vpnstore-bot.service"),
        "worker": (WORKER_LOG_PATH, "vpnstore-worker.service"),
        "app": (APP_LOG_PATH, None)
    }
    target_tuple = path_map.get(file_type, (APP_LOG_PATH, None))
    target_path, service_name = target_tuple

    # 1. Try reading target log file if exists and has content
    if target_path.exists() and target_path.stat().st_size > 0:
        try:
            with open(target_path, "r", encoding="utf-8", errors="replace") as f:
                all_lines = f.readlines()
                if all_lines:
                    return [line.strip() for line in all_lines[-lines_count:]]
        except Exception:
            pass

    # 2. If log file is empty/missing, try journalctl for the systemd unit
    if service_name:
        try:
            import subprocess
            res = subprocess.run(
                ["journalctl", "-u", service_name, "-n", str(lines_count), "--no-pager"],
                capture_output=True,
                text=True,
                timeout=4
            )
            if res.returncode == 0 and res.stdout.strip():
                lines = [line.strip() for line in res.stdout.strip().split("\n")]
                if lines:
                    return lines
        except Exception:
            pass

    return [f"لاگ فعالی برای {file_type} یافت نشد (سیستم در انتظار ثبت لاگ جدید است)."]


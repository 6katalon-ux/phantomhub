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
    """Read the last N lines from the requested log file for display in admin dashboard"""
    path_map = {
        "web": WEB_LOG_PATH,
        "bot": BOT_LOG_PATH,
        "worker": WORKER_LOG_PATH,
        "app": APP_LOG_PATH
    }
    target_path = path_map.get(file_type, APP_LOG_PATH)
    if not target_path.exists():
        return [f"Log file {target_path.name} is currently empty or does not exist yet."]
    
    try:
        with open(target_path, "r", encoding="utf-8", errors="replace") as f:
            all_lines = f.readlines()
            return [line.strip() for line in all_lines[-lines_count:]]
    except Exception as e:
        return [f"Error reading log file: {e}"]

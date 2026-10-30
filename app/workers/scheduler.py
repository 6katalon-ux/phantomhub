"""
Background Worker Scheduler.
Executes periodic 3X-UI traffic synchronization, service expiration checks,
and automated SQLite database backups.
"""

import os
import shutil
import asyncio
from datetime import datetime
from pathlib import Path
from app.services.traffic_sync import traffic_sync_service
from app.core.config import config
from app.core.logging import logger

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
BACKUPS_DIR = BASE_DIR / "backups"
DB_PATH = DATA_DIR / "vpn_store.db"

def perform_db_backup() -> str:
    """Create a point-in-time timestamped backup of the SQLite database"""
    BACKUPS_DIR.mkdir(parents=True, exist_ok=True)
    if not DB_PATH.exists():
        return ""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = BACKUPS_DIR / f"vpn_store_backup_{timestamp}.db"
    shutil.copy2(DB_PATH, backup_file)
    logger.info(f"Database backup created: {backup_file.name}")

    # Retention clean up
    retention_days = config.get_int("backup_retention_days", 14)
    now = datetime.now().timestamp()
    for f in BACKUPS_DIR.glob("vpn_store_backup_*.db"):
        if now - f.stat().st_mtime > retention_days * 86400:
            try:
                f.unlink()
                logger.info(f"Purged old backup file: {f.name}")
            except Exception:
                pass
    return str(backup_file)

async def traffic_sync_loop():
    logger.info("Traffic sync loop initialized.")
    while True:
        try:
            interval_mins = max(1, config.get_int("sync_interval_mins", 5))
            await traffic_sync_service.run_sync_cycle()
        except Exception as e:
            logger.error(f"Error in traffic sync loop: {e}")
        
        await asyncio.sleep(interval_mins * 60)

async def backup_loop():
    logger.info("Database backup loop initialized (24-hour interval).")
    while True:
        try:
            perform_db_backup()
        except Exception as e:
            logger.error(f"Error in backup loop: {e}")
        await asyncio.sleep(86400) # Every 24 hours

async def main():
    logger.info("Starting VPN Store background worker process...")
    await asyncio.gather(
        traffic_sync_loop(),
        backup_loop()
    )

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Background worker process stopped.")

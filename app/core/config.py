"""
Dynamic Configuration System backed by SQLite Settings Table.
Allows modifying Telegram bot, 3X-UI, and system settings directly from the Web Panel
without modifying .env or touching source code.
"""

import os
import json
import sqlite3
import asyncio
from pathlib import Path
from typing import Dict, Any, Optional

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "vpn_store.db"
SECRETS_PATH = DATA_DIR / "secrets.json"

class ConfigManager:
    _instance = None
    _cache: Dict[str, Any] = {}
    _secrets: Dict[str, Any] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
            cls._instance._last_refresh = 0.0
            cls._instance._load_secrets()
            cls._instance.refresh_cache_sync()
        return cls._instance

    def _load_secrets(self):
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        if SECRETS_PATH.exists():
            try:
                with open(SECRETS_PATH, "r") as f:
                    self._secrets = json.load(f)
            except Exception:
                self._secrets = {}
        else:
            import secrets
            self._secrets = {
                "jwt_secret": secrets.token_hex(32),
                "session_secret": secrets.token_hex(16),
                "subscription_salt": secrets.token_hex(12)
            }
            try:
                with open(SECRETS_PATH, "w") as f:
                    json.dump(self._secrets, f, indent=2)
                os.chmod(SECRETS_PATH, 0o600)
            except Exception:
                pass

    def get_secret(self, key: str, default: str = "") -> str:
        return self._secrets.get(key, default)

    def refresh_cache_sync(self):
        """Synchronously query SQLite and populate settings cache"""
        import time
        self._last_refresh = time.time()
        if not DB_PATH.exists():
            return
        try:
            conn = sqlite3.connect(str(DB_PATH), timeout=5)
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute("SELECT key, value, category, is_secret FROM settings")
            rows = cur.fetchall()
            new_cache = {}
            for r in rows:
                new_cache[r["key"]] = {
                    "value": r["value"] if r["value"] is not None else "",
                    "category": r["category"],
                    "is_secret": bool(r["is_secret"])
                }
            self._cache = new_cache
            conn.close()
        except Exception as e:
            # Table might not exist yet during initial setup
            pass

    def get(self, key: str, default: Any = "") -> Any:
        import time
        # Periodically refresh settings cache every 3 seconds to sync changes from web panel to bot process
        if time.time() - getattr(self, "_last_refresh", 0.0) > 3.0:
            self.refresh_cache_sync()

        if key in self._cache:
            return self._cache[key]["value"]
        # Fallback to direct DB query if not in cache
        try:
            conn = sqlite3.connect(str(DB_PATH), timeout=3)
            cur = conn.cursor()
            cur.execute("SELECT value FROM settings WHERE key = ?", (key,))
            row = cur.fetchone()
            conn.close()
            if row and row[0] is not None:
                return row[0]
        except Exception:
            pass
        return default

    def get_int(self, key: str, default: int = 0) -> int:
        val = self.get(key, default)
        try:
            return int(val)
        except (ValueError, TypeError):
            return default

    def get_bool(self, key: str, default: bool = False) -> bool:
        val = str(self.get(key, "1" if default else "0")).strip().lower()
        return val in ("1", "true", "yes", "on")

    def set(self, key: str, value: Any) -> bool:
        """Update or insert a setting in SQLite and update runtime cache"""
        val_str = str(value)
        try:
            conn = sqlite3.connect(str(DB_PATH), timeout=5)
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO settings (key, value) VALUES (?, ?)
                ON CONFLICT(key) DO UPDATE SET value = excluded.value
            """, (key, val_str))
            conn.commit()
            conn.close()
            if key in self._cache:
                self._cache[key]["value"] = val_str
            else:
                self._cache[key] = {"value": val_str, "category": "general", "is_secret": False}
            return True
        except Exception as e:
            print(f"[ConfigManager] Error setting {key}: {e}")
            return False

    def get_all_masked(self) -> Dict[str, Any]:
        """Return all settings for the Web UI, masking secret fields (passwords, tokens)"""
        self.refresh_cache_sync()
        result = {}
        for k, v in self._cache.items():
            val = v["value"]
            if v["is_secret"] and val:
                # Mask secret: keep first 3 and last 3 chars or bullet mask
                if len(val) > 8:
                    masked = val[:3] + "••••••••" + val[-3:]
                else:
                    masked = "••••••••"
                result[k] = {
                    "value": masked,
                    "is_masked": True,
                    "category": v["category"]
                }
            else:
                result[k] = {
                    "value": val,
                    "is_masked": False,
                    "category": v["category"]
                }
        return result

# Global singleton
config = ConfigManager()

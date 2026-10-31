"""
Helper service for sending Telegram notifications to users and admins via Bot API.
"""

import aiohttp
from typing import List, Optional
from app.core.config import config
from app.core.logging import logger

def get_admin_telegram_ids() -> List[int]:
    """Parse admin telegram IDs configured in settings"""
    raw = str(config.get("bot_admin_ids", "") or config.get("admin_telegram_id", "") or "")
    admin_ids = []
    for part in raw.replace(";", ",").split(","):
        part = part.strip()
        if part.isdigit():
            admin_ids.append(int(part))
    return admin_ids

async def send_telegram_notification(chat_id: int, text: str, reply_markup: Optional[dict] = None) -> bool:
    """Send a Markdown-formatted message to a Telegram chat"""
    token = str(config.get("bot_token", "")).strip()
    if not token or not chat_id:
        return False

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown"
    }
    if reply_markup:
        payload["reply_markup"] = reply_markup

    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=8)) as session:
            async with session.post(url, json=payload) as resp:
                data = await resp.json()
                if not data.get("ok"):
                    logger.warning(f"Telegram API warning to {chat_id}: {data.get('description')}")
                    return False
                return True
    except Exception as e:
        logger.error(f"Failed to send Telegram notification to {chat_id}: {e}")
        return False

"""
Aiogram 3 Bot Entrypoint and Lifespan Manager.
Gracefully waits if token is not yet configured in the Web Panel,
and handles auto-reconnects and polling.
"""

import asyncio
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from app.core.config import config
from app.core.logging import logger
from app.bot.handlers import router

async def main():
    logger.info("Initializing VPN Store Telegram Bot worker...")
    
    while True:
        token = config.get("bot_token", "").strip()
        is_enabled = config.get_bool("bot_enabled", True)

        if not token:
            logger.info("Telegram Bot Token is not configured yet. Open Web Admin Panel -> Telegram Bot Settings to paste token.")
            await asyncio.sleep(10)
            config.refresh_cache_sync()
            continue

        if not is_enabled:
            logger.info("Telegram Bot is disabled in settings. Waiting...")
            await asyncio.sleep(10)
            config.refresh_cache_sync()
            continue

        bot = None
        try:
            logger.info("Starting Aiogram 3 Bot polling...")
            bot = Bot(
                token=token,
                default=DefaultBotProperties(parse_mode=ParseMode.HTML)
            )
            dp = Dispatcher()
            dp.include_router(router)

            # Delete any existing webhook to ensure clean long polling
            await bot.delete_webhook(drop_pending_updates=True)
            logger.info("Aiogram 3 Polling started successfully. Listening for events...")
            await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
        except Exception as e:
            logger.error(f"Telegram Bot error: {e}. Retrying in 10 seconds...")
            await asyncio.sleep(10)
            config.refresh_cache_sync()
        finally:
            if bot is not None:
                try:
                    await bot.session.close()
                except Exception:
                    pass

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Telegram Bot stopped by system.")

"""
Aiogram 3 Bot Entrypoint and Lifespan Manager.
Gracefully waits if token is not yet configured in the Web Panel,
and handles auto-reconnects and polling.
"""

import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from app.core.config import config
from app.core.logging import logger
from app.bot.handlers import router

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s'
)

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
            logger.info("Creating Aiogram 3 Bot client...")
            bot = Bot(
                token=token,
                default=DefaultBotProperties(parse_mode=ParseMode.HTML)
            )
            me = await bot.get_me()
            logger.info(f"✅ Bot connected to Telegram as @{me.username} (ID: {me.id}, Name: {me.first_name})")

            dp = Dispatcher()

            # Global middleware to trace every single event and log any unhandled error
            @dp.update.outer_middleware()
            async def update_tracer_middleware(handler, event, data):
                event_type = getattr(event, "event_type", "unknown")
                user = getattr(getattr(event, "event", None), "from_user", None)
                user_desc = f"@{user.username} ({user.id})" if user else "anonymous"
                logger.info(f"📥 Received Telegram event: {event_type} from {user_desc}")
                try:
                    return await handler(event, data)
                except Exception as ex:
                    logger.exception(f"❌ Error in Telegram handler: {ex}")
                    raise ex

            dp.include_router(router)

            # Clear any stale webhooks
            await bot.delete_webhook(drop_pending_updates=True)
            logger.info("🚀 Aiogram 3 Polling started! Listening for messages & buttons...")

            # Explicitly listen for message and callback_query
            await dp.start_polling(
                bot,
                allowed_updates=["message", "callback_query"]
            )
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

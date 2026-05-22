import asyncio
import sys
from aiogram import Bot, Dispatcher
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.client.telegram import TelegramAPIServer

from src.config import Config
from src.logger import setup_logger
from src.handlers import router

async def main():
    # Setup logger first
    logger = setup_logger(log_level=Config.LOG_LEVEL)
    logger.info("Starting Telegram Bot Purchase Simulator...")

    # Validate config
    try:
        Config.validate()
    except Exception as e:
        logger.critical("Configuration validation failed: %s", e)
        sys.exit(1)

    # Initialize bot and dispatcher
    if Config.USE_PROXY_RELAY:
        logger.info("Proxy relay enabled. Routing all API calls to: %s", Config.LOCAL_PROXY_URL)
        # Note: double curly braces are used in f-string to output literal single curly braces for aiogram
        custom_server = TelegramAPIServer(
            base=f"{Config.LOCAL_PROXY_URL}/bot{{token}}/{{method}}",
            file=f"{Config.LOCAL_PROXY_URL}/file/bot{{token}}/{{path}}"
        )
        session = AiohttpSession(api=custom_server)
        bot = Bot(token=Config.BOT_TOKEN, session=session)
    else:
        bot = Bot(token=Config.BOT_TOKEN)

    dp = Dispatcher()

    # Register handlers router
    dp.include_router(router)

    # Clean up any pending updates before polling (skip_updates=True equivalent in v3)
    logger.info("Cleaning up pending updates...")
    await bot.delete_webhook(drop_pending_updates=True)

    # Start long polling
    logger.info("Bot is now polling. Press Ctrl+C to stop.")
    try:
        await dp.start_polling(bot)
    except Exception as e:
        logger.exception("An error occurred during bot polling: %s", str(e))
    finally:
        logger.info("Closing bot session...")
        await bot.session.close()
        logger.info("Bot session successfully closed. Goodbye!")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("Bot stopped by user or system signal.")

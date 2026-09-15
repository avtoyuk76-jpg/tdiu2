import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from . import config
from .handlers import routers
from .screenshot import start_browser, stop_browser

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    if not config.BOT_TOKEN:
        raise RuntimeError(
            "BOT_TOKEN muhit o'zgaruvchisi berilmagan. "
            ".env fayliga yoki Railway Variables bo'limiga BOT_TOKEN=... qo'shing."
        )

    bot = Bot(
        token=config.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher(storage=MemoryStorage())

    for router in routers:
        dp.include_router(router)

    await start_browser()
    logger.info("Playwright brauzeri ishga tushdi.")

    try:
        await bot.delete_webhook(drop_pending_updates=True)
        logger.info("Bot polling rejimida ishga tushmoqda...")
        await dp.start_polling(bot)
    finally:
        await stop_browser()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from app.config import settings
from app.handlers.router import router


def setup_logging() -> None:
    logging.basicConfig(
        level=getattr(
            logging,
            settings.LOG_LEVEL.upper(),
            logging.INFO
        ),
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )


async def main() -> None:
    setup_logging()

    bot = Bot(
        token=settings.BOT_TOKEN,
        default=DefaultBotProperties(
            parse_mode=ParseMode.HTML
        ),
    )

    dp = Dispatcher()
    dp.include_router(router)

    try:
        logging.info("SaraMatchBot ishga tushdi.")
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main)

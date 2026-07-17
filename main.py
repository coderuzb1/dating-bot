import asyncio
import logging

from aiogram import Bot, Dispatcher

from config import BOT_TOKEN
from database import create_db

from handlers.start import router as start_router
from handlers.register import router as register_router


async def main():
    logging.basicConfig(level=logging.INFO)

    await create_db()

    bot = Bot(BOT_TOKEN)

    dp = Dispatcher()

    dp.include_router(start_router)
    dp.include_router(register_router)

    print("✅ Sara Match Bot ishga tushdi")

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())

import asyncio
import os

from aiogram import Bot, Dispatcher

from handlers.start import router as start_router

TOKEN = os.getenv("8891233106:AAFpBIUtJnosv3ACH5cFHkuGGjd1i3Pvb8w")

bot = Bot("8891233106:AAFpBIUtJnosv3ACH5cFHkuGGjd1i3Pvb8w")
dp = Dispatcher()

dp.include_router(start_router)


async def main():
    print("Sara Match ishga tushdi ✅")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())

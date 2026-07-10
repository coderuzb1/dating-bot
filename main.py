import os
import asyncio
from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart
from aiogram.types import Message

TOKEN = os.getenv("8891233106:AAGh0K0Hw13a1jw-rTgGsWPM8xiUHS0bInk")

bot = Bot("8891233106:AAGh0K0Hw13a1jw-rTgGsWPM8xiUHS0bInk")
dp = Dispatcher()

@dp.message(CommandStart())
async def start(message: Message):
    await message.answer("🎉 Bot Railway orqali ishlayapti!")

async def main():
    print("Bot ishga tushdi")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

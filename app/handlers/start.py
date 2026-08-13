from aiogram import Router
from aiogram.types import Message

router = Router(name="start_router")


@router.message()
async def start_handler(message: Message):
    print("🔥 HANDLER ISHLADI:", message.text)
    await message.answer("✅ SaraMatchBot ishlayapti!")

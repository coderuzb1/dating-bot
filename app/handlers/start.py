from aiogram import Router
from aiogram.types import Message

router = Router()

@router.message()
async def handler(message: Message):
    await message.answer("✅ Bot ishlayapti!")

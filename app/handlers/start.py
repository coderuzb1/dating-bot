from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

router = Router()


@router.message(CommandStart())
async def start_handler(message: Message) -> None:
    await message.answer(
        "👋 Assalomu alaykum!\n\n"
        "SaraMatchBot ga xush kelibsiz.\n\n"
        "Davom etish uchun tilni tanlang."
    )

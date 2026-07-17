from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from database import get_user
from keyboards import main_menu

router = Router()


@router.message(CommandStart())
async def start_command(message: Message):
    user = await get_user(message.from_user.id)

    if user:
        await message.answer(
            f"👋 Xush kelibsiz, {user.name}!",
            reply_markup=main_menu
        )
    else:
        await message.answer(
            "❤️ Sara Match botiga xush kelibsiz!\n\n"
            "Bu yerda yangi tanishuvlar topishingiz mumkin.\n\n"
            "Ro'yxatdan o'tish uchun /register buyrug'ini yuboring."
        )

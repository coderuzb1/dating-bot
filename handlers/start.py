from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from database import Database
from keyboards import main_menu

router = Router()
db = Database()


@router.message(CommandStart())
async def start(message: Message):

    await db.create_tables()

    user = await db.get_user(message.from_user.id)

    if user:

        await message.answer(
            f"👋 Xush kelibsiz, {user['name']}!",
            reply_markup=main_menu
        )

    else:

        await message.answer(
            "💕 Sara Match botiga xush kelibsiz!\n\n"
            "Ro'yxatdan o'tish uchun ismingizni yuboring."
        )

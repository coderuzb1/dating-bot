from aiogram import Router
from aiogram.types import Message, CallbackQuery

router = Router()


@router.message()
async def message_handler(message: Message):
    await message.answer("✅ Bot ishlayapti!")


@router.callback_query()
async def callback_handler(callback: CallbackQuery):
    await callback.answer("✅ Tugma bosildi!", show_alert=False)

    if callback.message:
        await callback.message.answer(
            f"🔘 Callback qabul qilindi:\n"
            f"<code>{callback.data}</code>"
        )

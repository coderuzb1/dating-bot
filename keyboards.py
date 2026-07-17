from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
)


main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="❤️ Tanishuvni boshlash")
        ],
        [
            KeyboardButton(text="👤 Profil"),
            KeyboardButton(text="💬 Matchlar")
        ],
        [
            KeyboardButton(text="⭐ Premium"),
            KeyboardButton(text="⚙️ Sozlamalar")
        ],
    ],
    resize_keyboard=True
)


gender_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="👨 Erkak"),
            KeyboardButton(text="👩 Ayol")
        ]
    ],
    resize_keyboard=True,
    one_time_keyboard=True
)


looking_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="👩 Ayol"),
            KeyboardButton(text="👨 Erkak")
        ],
        [
            KeyboardButton(text="❤️ Farqi yo'q")
        ]
    ],
    resize_keyboard=True,
    one_time_keyboard=True
)


yes_no_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="✅ Ha"),
            KeyboardButton(text="❌ Yo'q")
        ]
    ],
    resize_keyboard=True,
    one_time_keyboard=True
)


search_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="❤️ Like"),
            KeyboardButton(text="⏭ O'tkazib yuborish")
        ],
        [
            KeyboardButton(text="🏠 Asosiy menyu")
        ]
    ],
    resize_keyboard=True
)


admin_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="📢 Xabar yuborish")
        ],
        [
            KeyboardButton(text="🚫 Ban"),
            KeyboardButton(text="✅ Unban")
        ],
        [
            KeyboardButton(text="📊 Statistika")
        ]
    ],
    resize_keyboard=True
)

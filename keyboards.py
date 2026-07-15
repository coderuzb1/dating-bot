from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)

# ==========================
# ASOSIY MENU
# ==========================

main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="❤️ Profil ko'rish")
        ],
        [
            KeyboardButton(text="👤 Mening profilim"),
            KeyboardButton(text="💘 Matchlar")
        ],
        [
            KeyboardButton(text="⭐ Premium"),
            KeyboardButton(text="⚙️ Sozlamalar")
        ]
    ],
    resize_keyboard=True
)

# ==========================
# JINS TANLASH
# ==========================

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

# ==========================
# KIM BILAN TANISHMOQCHI
# ==========================

looking_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="👨 Erkak")
        ],
        [
            KeyboardButton(text="👩 Ayol")
        ]
    ],
    resize_keyboard=True,
    one_time_keyboard=True
)

# ==========================
# PROFIL TUGMALARI
# ==========================

profile_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text="❤️ Like",
                callback_data="like"
            ),
            InlineKeyboardButton(
                text="❌ Skip",
                callback_data="skip"
            )
        ],
        [
            InlineKeyboardButton(
                text="🚩 Shikoyat",
                callback_data="report"
            )
        ]
    ]
)

# ==========================
# MATCH
# ==========================

match_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text="💬 Chatni boshlash",
                callback_data="chat"
            )
        ]
    ]
)

# ==========================
# SOZLAMALAR
# ==========================

settings_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="✏️ Profilni tahrirlash")
        ],
        [
            KeyboardButton(text="🗑 Profilni o'chirish")
        ],
        [
            KeyboardButton(text="🔙 Orqaga")
        ]
    ],
    resize_keyboard=True
)

# ==========================
# PREMIUM
# ==========================

premium_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text="⭐ Premium sotib olish",
                callback_data="buy_premium"
            )
        ]
    ]
)

# ==========================
# ADMIN
# ==========================

admin_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="📊 Statistika")
        ],
        [
            KeyboardButton(text="📢 Reklama yuborish")
        ],
        [
            KeyboardButton(text="🚫 Ban"),
            KeyboardButton(text="✅ Unban")
        ]
    ],
    resize_keyboard=True
)

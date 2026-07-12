import os

# Railway Variables ichida TOKEN nomi bilan saqlanadi
TOKEN = os.getenv("8891233106:AAFpBIUtJnosv3ACH5cFHkuGGjd1i3Pvb8w")

if TOKEN is None:
    raise Exception(
        "TOKEN topilmadi!\n"
        "Railway -> Variables -> TOKEN = BotFather tokenini kiriting."
    )

# Bot nomi
BOT_NAME = "Sara Match"

# Admin Telegram ID
# O'zingizning Telegram ID'ingizni keyin yozasiz
ADMIN_ID = 123456789

# SQLite bazasi
DATABASE_NAME = "dating.db"

# Premium narxi (keyin o'zgartirish mumkin)
PREMIUM_PRICE = 30000

# Maksimal rasm soni
MAX_PHOTOS = 5

# Minimal yosh
MIN_AGE = 18

# Maksimal yosh
MAX_AGE = 50

# Match qidirish limiti
SEARCH_LIMIT = 20

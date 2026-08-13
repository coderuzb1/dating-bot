import os
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ConversationHandler
from telegram import ReplyKeyboardMarkup, KeyboardButton
from database import init_db, get_db_connection

AGE, GENDER, BIO, PHOTO = range(4)

async def start(update, context):
    user = update.effective_user
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE user_id = %s", (user.id,))
    existing_user = cur.fetchone()
    cur.close()
    conn.close()
    
    if existing_user:
        await update.message.reply_text(f"Xush kelibsiz, {user.first_name}!\n\n/find - Yangi odam topish\n/profile - Profilim")
    else:
        await update.message.reply_text("Profil yaratish uchun yoshingizni kiriting:")
        return AGE

async def get_age(update, context):
    age = update.message.text
    if not age.isdigit() or int(age) < 16 or int(age) > 60:
        await update.message.reply_text("Iltimos, to'g'ri yosh kiriting (16-60):")
        return AGE
    context.user_data['age'] = int(age)
    await update.message.reply_text("Jinsingizni tanlang:", reply_markup=ReplyKeyboardMarkup([
        [KeyboardButton("Erkak"), KeyboardButton("Ayol")]
    ], resize_keyboard=True))
    return GENDER

async def get_gender(update, context):
    gender = update.message.text
    if gender not in ["Erkak", "Ayol"]:
        await update.message.reply_text("Iltimos, tugmalardan birini tanlang:")
        return GENDER
    context.user_data['gender'] = gender
    await update.message.reply_text("O'zingiz haqingizda qisqacha yozing:")
    return BIO

async def get_bio(update, context):
    bio = update.message.text
    context.user_data['bio'] = bio
    await update.message.reply_text("Profil rasmingizni yuboring (foto):")
    return PHOTO

async def get_photo(update, context):
    user = update.effective_user
    photo = update.message.photo[-1].file_id
    
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO users (user_id, username, first_name, age, gender, bio, photo)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (user_id) DO UPDATE SET age = %s, gender = %s, bio = %s, photo = %s
    """, (user.id, user.username, user.first_name, context.user_data['age'], 
          context.user_data['gender'], context.user_data['bio'], photo,
          context.user_data['age'], context.user_data['gender'], 
          context.user_data['bio'], photo))
    conn.commit()
    cur.close()
    conn.close()
    
    await update.message.reply_text("Profil yaratildi! ✅\n\n/find - Yangi odam topish\n/profile - Profilim", 
                                   reply_markup=ReplyKeyboardMarkup([[]], resize_keyboard=True))
    return ConversationHandler.END

async def find(update, context):
    user = update.effective_user
    
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE user_id != %s ORDER BY created_at DESC LIMIT 1", (user.id,))
    target = cur.fetchone()
    cur.close()
    conn.close()
    
    if not target:
        await update.message.reply_text("Hozircha boshqa foydalanuvchilar yo'q.")
        return
    
    target_id, username, first_name, age, gender, bio, photo, created_at = target
    
    await update.message.reply_photo(photo=photo, caption=f"{first_name}, {age}\n{bio}")
    await update.message.reply_text("Yoqdi mi?", reply_markup=ReplyKeyboardMarkup([
        [KeyboardButton("❤️ Yoqdi"), KeyboardButton("👎 Yoqmadi")],
        [KeyboardButton("🔍 Keyingi")]
    ], resize_keyboard=True))

async def profile(update, context):
    user = update.effective_user
    
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE user_id = %s", (user.id,))
    user_data = cur.fetchone()
    cur.close()
    conn.close()
    
    if user_data:
        user_id, username, first_name, age, gender, bio, photo, created_at = user_data
        await update.message.reply_photo(photo=photo, caption=f"{first_name}, {age}\n{bio}")
    else:
        await update.message.reply_text("Profil topilmadi. /start bilan qayta boshlang.")

def main():
    TOKEN = os.environ.get("BOT_TOKEN")
    if not TOKEN:
        print("XATO: BOT_TOKEN topilmadi!")
        return
    
    init_db()
    
    app = Application.builder().token(TOKEN).build()
    
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            AGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_age)],
            GENDER: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_gender)],
            BIO: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_bio)],
            PHOTO: [MessageHandler(filters.PHOTO, get_photo)],
        },
        fallbacks=[],
    )
    
    app.add_handler(conv_handler)
    app.add_handler(CommandHandler("find", find))
    app.add_handler(CommandHandler("profile", profile))
    
    print("Dating bot ishga tushdi...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()

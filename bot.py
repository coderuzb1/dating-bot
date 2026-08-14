import os
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ConversationHandler, CallbackQueryHandler
from telegram import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from database import init_db, get_db_connection

AGE, GENDER, BIO, PHOTO, EDIT_AGE, EDIT_BIO, EDIT_PHOTO = range(7)
ADMIN_ID =  # 6310532367

async def main_menu(update, context):
    keyboard = ReplyKeyboardMarkup([
        [KeyboardButton("🔍 Qidirish"), KeyboardButton("👤 Profil")],
        [KeyboardButton("❤️ Yoqtirganlar"), KeyboardButton("🎉 Matchlar")],
        [KeyboardButton("⚙️ Sozlamalar")]
    ], resize_keyboard=True)
    await update.message.reply_text("Bosh menyu:", reply_markup=keyboard)

async def start(update, context):
    user = update.effective_user
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE user_id = %s", (user.id,))
    existing_user = cur.fetchone()
    cur.close()
    conn.close()
    
    if existing_user:
        await main_menu(update, context)
    else:
        await update.message.reply_text("Profil yaratish uchun yoshingizni kiriting:")
        return AGE

async def get_age(update, context):
    age = update.message.text
    if not age.isdigit() or int(age) < 16 or int(age) > 60:
        await update.message.reply_text("Iltimos, to'g'ri yosh kiriting (16-60):")
        return AGE
    context.user_data['age'] = int(age)
    await update.message.reply_text("Jinsingizni tanlang:")
    return GENDER

async def get_gender(update, context):
    gender = update.message.text
    if gender not in ["Erkak", "Ayol"]:
        await update.message.reply_text("Iltimos, Erkak yoki Ayol deb yozing:")
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
    
    await update.message.reply_text("Profil yaratildi! ✅")
    await main_menu(update, context)
    return ConversationHandler.END

async def handle_message(update, context):
    text = update.message.text
    
    if text == "🔍 Qidirish":
        await find(update, context)
    elif text == "👤 Profil":
        await profile(update, context)
    elif text == "❤️ Yoqtirganlar":
        await likes(update, context)
    elif text == "🎉 Matchlar":
        await matches(update, context)
    elif text == "⚙️ Sozlamalar":
        await settings(update, context)

async def find(update, context):
    user = update.effective_user
    
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT * FROM users 
        WHERE user_id != %s 
        AND user_id NOT IN (SELECT to_user FROM likes WHERE from_user = %s)
        ORDER BY created_at DESC 
        LIMIT 1
    """, (user.id, user.id))
    target = cur.fetchone()
    cur.close()
    conn.close()if not target:
        await update.message.reply_text("Hozircha boshqa foydalanuvchilar yo'q.")
        return
    
    target_id, username, first_name, age, gender, bio, photo, created_at = target
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("❤️ Yoqdi", callback_data=f"like_{target_id}"),
         InlineKeyboardButton("👎 Yoqmadi", callback_data=f"skip_{target_id}")]
    ])
    
    await update.message.reply_photo(photo=photo, caption=f"{first_name}, {age}\n{bio}", reply_markup=keyboard)

async def handle_callback(update, context):
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    data = query.data
    
    if data.startswith("like_"):
        target_id = int(data.split("_")[1])
        
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("INSERT INTO likes (from_user, to_user) VALUES (%s, %s)", (user.id, target_id))
        
        cur.execute("SELECT * FROM likes WHERE from_user = %s AND to_user = %s", (target_id, user.id))
        mutual_like = cur.fetchone()
        
        if mutual_like:
            cur.execute("INSERT INTO matches (user1, user2) VALUES (%s, %s)", (user.id, target_id))
            cur.execute("SELECT first_name FROM users WHERE user_id = %s", (target_id,))
            target_name = cur.fetchone()[0]
            await query.message.reply_text(f"🎉 Match! {target_name} bilan mos keldingiz!")
        else:
            await query.message.reply_text("❤️ Yoqdi! Agar qarshi tomon ham yoqsa, match bo'ladi.")
        
        conn.commit()
        cur.close()
        conn.close()
        
        await find(update, context)
    
    elif data.startswith("skip_"):
        await query.message.reply_text("👎 O'tkazib yuborildi.")
        await find(update, context)
    
    elif data == "edit_age":
        await query.message.reply_text("Yangi yoshingizni kiriting:")
        return EDIT_AGE
    
    elif data == "edit_bio":
        await query.message.reply_text("Yangi bio yozing:")
        return EDIT_BIO
    
    elif data == "edit_photo":
        await query.message.reply_text("Yangi rasm yuboring:")
        return EDIT_PHOTO

async def edit_age(update, context):
    age = update.message.text
    if not age.isdigit() or int(age) < 16 or int(age) > 60:
        await update.message.reply_text("Iltimos, to'g'ri yosh kiriting (16-60):")
        return EDIT_AGE
    
    user = update.effective_user
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("UPDATE users SET age = %s WHERE user_id = %s", (int(age), user.id))
    conn.commit()
    cur.close()
    conn.close()
    
    await update.message.reply_text("Yosh yangilandi! ✅")
    await main_menu(update, context)
    return ConversationHandler.END

async def edit_bio(update, context):
    bio = update.message.text
    user = update.effective_user
    
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("UPDATE users SET bio = %s WHERE user_id = %s", (bio, user.id))
    conn.commit()
    cur.close()
    conn.close()
    
    await update.message.reply_text("Bio yangilandi! ✅")
    await main_menu(update, context)
    return ConversationHandler.END

async def edit_photo(update, context):
    photo = update.message.photo[-1].file_id
    user = update.effective_user
    
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("UPDATE users SET photo = %s WHERE user_id = %s", (photo, user.id))
    conn.commit()
    cur.close()
    conn.close()
    
    await update.message.reply_text("Rasm yangilandi! ✅")
    await main_menu(update, context)
    return ConversationHandler.END

async def settings(update, context):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("Yoshni o'zgartirish", callback_data="edit_age")],
        [InlineKeyboardButton("Bioni o'zgartirish", callback_data="edit_bio")],
        [InlineKeyboardButton("Rasmni o'zgartirish", callback_data="edit_photo")],
    ])
    await update.message.reply_text("⚙️ Sozlamalar:", reply_markup=keyboard)async def likes(update, context):
    user = update.effective_user
    
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT u.first_name, u.age FROM users u
        JOIN likes l ON u.user_id = l.to_user
        WHERE l.from_user = %s
    """, (user.id,))
    likes_list = cur.fetchall()
    cur.close()
    conn.close()
    
    if not likes_list:
        await update.message.reply_text("Hozircha yoqtirganlaringiz yo'q.")
        return
    
    text = "❤️ Yoqtirganlaringiz:\n\n"
    for like in likes_list:
        text += f"• {like[0]}, {like[1]}\n"
    
    await update.message.reply_text(text)

async def matches(update, context):
    user = update.effective_user
    
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT u.first_name, u.age, u.username FROM users u
        JOIN matches m ON u.user_id = CASE WHEN m.user1 = %s THEN m.user2 ELSE m.user1 END
        WHERE m.user1 = %s OR m.user2 = %s
    """, (user.id, user.id, user.id))
    matches_list = cur.fetchall()
    cur.close()
    conn.close()
    
    if not matches_list:
        await update.message.reply_text("Hozircha matchlar yo'q.")
        return
    
    text = "🎉 Matchlaringiz:\n\n"
    for match in matches_list:
        text += f"• {match[0]}, {match[1]}"
        if match[2]:
            text += f" (@{match[2]})"
        text += "\n"
    
    await update.message.reply_text(text)

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
        await update.message.reply_photo(photo=photo, caption=f"{first_name}, {age}\n👤 {gender}\n📝 {bio}")
    else:
        await update.message.reply_text("Profil topilmadi. /start bilan qayta boshlang.")

async def admin(update, context):
    user = update.effective_user
    if user.id != ADMIN_ID:
        await update.message.reply_text("Siz admin emassiz!")
        return
    
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM users")
    total_users = cur.fetchone()[0]
    
    cur.execute("SELECT COUNT(*) FROM matches")
    total_matches = cur.fetchone()[0]
    
    cur.execute("SELECT COUNT(*) FROM likes")
    total_likes = cur.fetchone()[0]
    cur.close()
    conn.close()
    
    text = f"📊 Statistika:\n\n👥 Foydalanuvchilar: {total_users}\n❤️ Likelar: {total_likes}\n🎉 Matchlar: {total_matches}"
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("👥 Foydalanuvchilar ro'yxati", callback_data="admin_users")],
    ])
    
    await update.message.reply_text(text, reply_markup=keyboard)

async def admin_users(update, context):
    query = update.callback_query
    await query.answer()
    
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT user_id, first_name, age, gender FROM users ORDER BY created_at DESC LIMIT 20")
    users = cur.fetchall()
    cur.close()
    conn.close()
    
    text = "👥 Foydalanuvchilar:\n\n"
    for user in users:
        text += f"• {user[1]}, {user[2]} ({user[3]}) - ID: {user[0]}\n"
    
    await query.message.reply_text(text)

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
            AGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_age)],GENDER: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_gender)],
            BIO: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_bio)],
            PHOTO: [MessageHandler(filters.PHOTO, get_photo)],
            EDIT_AGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_age)],
            EDIT_BIO: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_bio)],
            EDIT_PHOTO: [MessageHandler(filters.PHOTO, edit_photo)],
        },
        fallbacks=[],
    )
    
    app.add_handler(conv_handler)
    app.add_handler(CommandHandler("admin", admin))
    app.add_handler(CommandHandler("find", find))
    app.add_handler(CommandHandler("profile", profile))
    app.add_handler(CommandHandler("likes", likes))
    app.add_handler(CommandHandler("matches", matches))
    app.add_handler(CommandHandler("settings", settings))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(handle_callback))
    
    print("Dating bot ishga tushdi...")
    app.run_polling(drop_pending_updates=True)

if name == "main":
    main()

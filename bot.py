import os
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ConversationHandler, CallbackQueryHandler
from telegram import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from database import init_db, get_db_connection
from notifications import notify_new_user, notify_new_match, notify_like, notify_news
from datetime import datetime, timedelta

AGE, GENDER, BIO, PHOTO = range(4)
ADMIN_ID = 6310532367

async def get_main_keyboard():
    return ReplyKeyboardMarkup([
        [KeyboardButton("🔍 Qidirish"), KeyboardButton("👤 Profil")],
        [KeyboardButton("❤️ Yoqtirganlarim"), KeyboardButton("💞 Matchlarim")],
        [KeyboardButton("⚙️ Sozlamalar"), KeyboardButton("👑 Premium")]
    ], resize_keyboard=True)

async def start(update, context):
    user = update.effective_user
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE user_id = %s", (user.id,))
    existing_user = cur.fetchone()
    cur.close()
    conn.close()
    
    if existing_user:
        await update.message.reply_text(
            f"👋 Salom, {user.first_name}!\n\n"
            "🔍 Qidirish - yangi odamlar topish\n"
            "👤 Profil - profilingizni ko'rish\n"
            "❤️ Yoqtirganlarim - siz yoqtirganlar\n"
            "💞 Matchlarim - o'zaro matchlar\n"
            "⚙️ Sozlamalar - profilni tahrirlash\n"
            "👑 Premium - pullik obuna",
            reply_markup=await get_main_keyboard()
        )
    else:
        await update.message.reply_text("📝 Profil yaratish uchun yoshingizni kiriting (16-60):")
        return AGE

async def get_age(update, context):
    text = update.message.text
    if not text.isdigit() or int(text) < 16 or int(text) > 60:
        await update.message.reply_text("❌ Iltimos, to'g'ri yosh kiriting (16-60):")
        return AGE
    context.user_data['age'] = int(text)
    
    keyboard = ReplyKeyboardMarkup([
        [KeyboardButton("👨 Erkak"), KeyboardButton("👩 Ayol")]
    ], resize_keyboard=True, one_time_keyboard=True)
    
    await update.message.reply_text("Jinsingizni tanlang:", reply_markup=keyboard)
    return GENDER

async def get_gender(update, context):
    text = update.message.text
    gender = "Erkak" if "👨" in text else "Ayol" if "👩" in text else text
    
    if gender not in ["Erkak", "Ayol"]:
        await update.message.reply_text("❌ Iltimos, tugmalardan birini tanlang:")
        return GENDER
    
    context.user_data['gender'] = gender
    await update.message.reply_text("📝 O'zingiz haqingizda qisqacha yozing:")
    return BIO

async def get_bio(update, context):
    bio = update.message.text
    context.user_data['bio'] = bio
    await update.message.reply_text("📸 Profil rasmingizni yuboring:")
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
    
    await notify_new_user(context.bot, user.first_name, user.id)
    await update.message.reply_text("✅ Profil yaratildi!", reply_markup=await get_main_keyboard())
    return ConversationHandler.END

async def find(update, context):
    user = update.effective_userconn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT gender FROM users WHERE user_id = %s", (user.id,))
    user_data = cur.fetchone()
    
    if not user_data:
        await update.message.reply_text("❌ Avval profil yarating. /start bosing.")
        cur.close()
        conn.close()
        return
    
    my_gender = user_data[0]
    target_gender = "Ayol" if my_gender == "Erkak" else "Erkak"
    
    cur.execute("""
        SELECT * FROM users 
        WHERE user_id != %s 
        AND gender = %s
        AND user_id NOT IN (SELECT to_user FROM likes WHERE from_user = %s)
        AND user_id NOT IN (SELECT to_user FROM blocks WHERE from_user = %s)
        ORDER BY created_at DESC 
        LIMIT 1
    """, (user.id, target_gender, user.id, user.id))
    target = cur.fetchone()
    cur.close()
    conn.close()
    
    if not target:
        await update.message.reply_text(f"😔 Hozircha {target_gender} profillar yo'q.")
        return
    
    target_id, username, first_name, age, gender, bio, photo, created_at, premium_until = target
    
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("❌", callback_data=f"skip_{target_id}"),
            InlineKeyboardButton("❤️", callback_data=f"like_{target_id}")
        ],
        [
            InlineKeyboardButton("🚫 Bloklash", callback_data=f"block_{target_id}"),
            InlineKeyboardButton("⚠️ Report", callback_data=f"report_{target_id}")
        ]
    ])
    
    await update.message.reply_photo(
        photo=photo,
        caption=f"👤 {first_name}, {age}\n👤 {gender}\n📝 {bio}",
        reply_markup=keyboard
    )

async def view_profile(update, context):
    query = update.callback_query
    await query.answer()
    target_id = int(query.data.split("_")[2])
    
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE user_id = %s", (target_id,))
    user_data = cur.fetchone()
    cur.close()
    conn.close()
    
    if user_data:
        user_id, username, first_name, age, gender, bio, photo, created_at, premium_until = user_data
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("❤️ Yoqdi", callback_data=f"like_{target_id}")]
        ])
        await query.message.reply_photo(
            photo=photo,
            caption=f"👤 {first_name}, {age}\n👤 {gender}\n📝 {bio}",
            reply_markup=keyboard
        )

async def handle_premium_payment(update, context):
    query = update.callback_query
    await query.answer()
    user = query.from_user
    data = query.data
    
    durations = {
        "premium_1w": 7,
        "premium_1m": 30,
        "premium_3m": 90,
        "premium_1y": 365
    }
    
    if data in durations:
        days = durations[data]
        premium_until = datetime.now() + timedelta(days=days)
        
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("UPDATE users SET premium_until = %s WHERE user_id = %s", (premium_until, user.id))
        conn.commit()
        cur.close()
        conn.close()
        
        await query.message.reply_text(f"✅ Premium faollashtirildi!\n📅 Muddat: {days} kun")
    elif data == "cancel_premium":
        await query.message.reply_text("❌ Bekor qilindi.")

async def handle_callback(update, context):
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    data = query.data
    
    if data.startswith("premium_") or data == "cancel_premium":
        await handle_premium_payment(update, context)
        return
    
    if data.startswith("view_profile_"):
        await view_profile(update, context)
        return
    
    if data.startswith("like_"):
        target_id = int(data.split("_")[1])
        
        conn = get_db_connection()user_data = cur.fetchone()
    
    cur.execute("SELECT COUNT(*) FROM likes WHERE to_user = %s", (user.id,))
    likes_count = cur.fetchone()[0]
    
    cur.execute("SELECT COUNT(*) FROM matches WHERE user1 = %s OR user2 = %s", (user.id, user.id))
    matches_count = cur.fetchone()[0]
    cur.close()
    conn.close()
    
    if not user_data:
        await update.message.reply_text("❌ Profil topilmadi.")
        return
    
    user_id, username, first_name, age, gender, bio, photo, created_at, premium_until = user_data
    premium_status = "✅" if premium_until and premium_until > datetime.now() else "❌"
    
    await update.message.reply_photo(
        photo=photo,
        caption=f"👤 {first_name}, {age}\n👤 {gender}\n📝 {bio}\n\n❤️ {likes_count} like\n💞 {matches_count} match\n👑 Premium: {premium_status}"
    )

async def likes(update, context):
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
        await update.message.reply_text("❤️ Hozircha yoqtirganlaringiz yo'q.")
        return
    
    text = "❤️ Siz yoqtirganlar:\n\n"
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
        await update.message.reply_text("💞 Hozircha matchlar yo'q.")
        return
    
    text = "💞 Matchlaringiz:\n\n"
    for match in matches_list:
        text += f"• {match[0]}, {match[1]}"
        if match[2]:
            text += f" (@{match[2]})"
        text += "\n"
    
    await update.message.reply_text(text)

async def settings(update, context):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("👑 Premium sotib olish", callback_data="premium_buy")],
    ])
    await update.message.reply_text("⚙️ Sozlamalar:", reply_markup=keyboard)

async def handle_message(update, context):
    text = update.message.text
    
    if text == "🔍 Qidirish":
        await find(update, context)
    elif text == "👤 Profil":
        await profile(update, context)
    elif text == "❤️ Yoqtirganlarim":
        await likes(update, context)
    elif text == "💞 Matchlarim":
        await matches(update, context)
    elif text == "⚙️ Sozlamalar":
        await settings(update, context)
    elif text == "👑 Premium":
        await premium(update, context)

async def admin(update, context):
    user = update.effective_user
    if user.id != ADMIN_ID:
        await update.message.reply_text("⛔ Siz admin emassiz!")
        return
    
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM users")
    total_users = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM matches")
    total_matches = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM likes")
    total_likes = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM users WHERE premium_until > NOW()")
    premium_users = cur.fetchone()[0]
    cur.close()
    conn.close()
    
    await update.message.reply_text(
        f"📊 ADMIN PANEL:\n\n"
        f"👥 Foydalanuvchilar: {total_users}\n"
        f"❤️ Likelar: {total_likes}\n"
        f"💞 Matchlar: {total_matches}\n"
        f"👑 Premium: {premium_users}"
    )async def broadcast(update, context):
    user = update.effective_user
    if user.id != ADMIN_ID:
        await update.message.reply_text("⛔ Siz admin emassiz!")
        return
    
    text = update.message.text.replace("/broadcast ", "")
    await notify_news(context.bot, text)
    await update.message.reply_text("✅ Yuborildi!")

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
    app.add_handler(CommandHandler("admin", admin))
    app.add_handler(CommandHandler("broadcast", broadcast))
    app.add_handler(CommandHandler("find", find))
    app.add_handler(CommandHandler("profile", profile))
    app.add_handler(CommandHandler("likes", likes))
    app.add_handler(CommandHandler("matches", matches))
    app.add_handler(CommandHandler("settings", settings))
    app.add_handler(CommandHandler("premium", premium))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(handle_callback))
    
    print("Dating bot ishga tushdi...")
    app.run_polling(drop_pending_updates=True)

if name == "main":
    main()

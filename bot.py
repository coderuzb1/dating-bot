import os
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ConversationHandler, CallbackQueryHandler
from telegram import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from database import init_db, get_db_connection
from notifications import notify_new_user, notify_new_match, notify_like, notify_news
from datetime import datetime, timedelta

AGE, GENDER, BIO, PHOTO, CITY = range(5)
ADMIN_ID = 6310532367
BAD_WORDS = ["ahmoq", "jinni", "sotqin", "firibgar", "scam", "aldamoq", "pul", "karta", "parol"]

async def check_bad_words(text):
    return any(word in text.lower() for word in BAD_WORDS)

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
    cur.execute("SELECT is_active FROM users WHERE user_id = %s", (user.id,))
    user_status = cur.fetchone()
    cur.close()
    conn.close()
    
    if user_status:
        if not user_status[0]:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("UPDATE users SET is_active = TRUE WHERE user_id = %s", (user.id,))
            conn.commit()
            cur.close()
            conn.close()
            await update.message.reply_text("👻 Profil qayta faollashtirildi!")
        
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
    keyboard = ReplyKeyboardMarkup([
        [KeyboardButton("Toshkent"), KeyboardButton("Samarqand")],
        [KeyboardButton("Buxoro"), KeyboardButton("Andijon")],
        [KeyboardButton("Farg'ona"), KeyboardButton("Namangan")],
        [KeyboardButton("Qarshi"), KeyboardButton("Nukus")],
        [KeyboardButton("Xiva"), KeyboardButton("Jizzax")],
        [KeyboardButton("Guliston"), KeyboardButton("Termiz")],
        [KeyboardButton("Navoiy"), KeyboardButton("Boshqa")]
    ], resize_keyboard=True, one_time_keyboard=True)
    await update.message.reply_text("📍 Yashash shahringizni tanlang:", reply_markup=keyboard)
    return CITY

async def get_city(update, context):
    city = update.message.text
    if city == "Boshqa":
        await update.message.reply_text("📍 Shahringizni yozing:")
        return CITY
    context.user_data['city'] = city
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
        INSERT INTO users (user_id, username, first_name, age, gender, bio, photo, city)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (user_id) DO UPDATE SET age = %s, gender = %s, bio = %s, photo = %s, city = %s
    """, (user.id, user.username, user.first_name, context.user_data['age'],
          context.user_data['gender'], context.user_data['bio'], photo, context.user_data['city'],
          context.user_data['age'], context.user_data['gender'],
          context.user_data['bio'], photo, context.user_data['city']))
    conn.commit()
    cur.close()
    conn.close()
    try:
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"🆕 Yangi foydalanuvchi: {user.first_name}"
        )
    except:
        pass
    await update.message.reply_text("✅ Profil yaratildi!", reply_markup=await get_main_keyboard())
    return ConversationHandler.END

async def find(update, context):
    if update.callback_query:
        message = update.callback_query.message
        user = update.callback_query.from_user
    else:
        message = update.message
        user = update.effective_user
    
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT gender, city, premium_until FROM users WHERE user_id = %s", (user.id,))
    user_data = cur.fetchone()
    if not user_data:
        await message.reply_text("❌ Avval profil yarating. /start bosing.")
        cur.close()
        conn.close()
        return
    
    my_gender, my_city, premium_until = user_data
    is_premium = premium_until and premium_until > datetime.now()
    
    target_gender = "Ayol" if my_gender == "Erkak" else "Erkak"
    cur.execute("""
        SELECT user_id, username, first_name, age, gender, bio, photo, city, is_active, premium_until, created_at
        FROM users
        WHERE user_id != %s
        AND gender = %s
        AND is_active = TRUE
        AND user_id NOT IN (SELECT to_user FROM likes WHERE from_user = %s)
        ORDER BY CASE WHEN city = %s THEN 0 ELSE 1 END, created_at DESC
        LIMIT 1
    """, (user.id, target_gender, user.id, my_city))
    target = cur.fetchone()
    cur.close()
    conn.close()
    
    if not target:
        await message.reply_text(f"😔 Hozircha {target_gender} profillar yo'q.")
        return
    
    target_id, username, first_name, age, gender, bio, photo, city, is_active, premium_until, created_at = target
    is_premium_user = premium_until and premium_until > datetime.now()
    premium_badge = " ⭐" if is_premium_user else ""
    
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("👎 Yoqmadi", callback_data=f"skip_{target_id}"),
            InlineKeyboardButton("❤️ Yoqdi", callback_data=f"like_{target_id}")
        ]
    ])
    await message.reply_photo(
        photo=photo,
        caption=f"👤 {first_name}, {age}{premium_badge}\n👤 {gender}\n📍 {city}\n📝 {bio}",
        reply_markup=keyboard
    )

async def handle_callback(update, context):
    query = update.callback_query
    await query.answer()
    user = query.from_user
    data = query.data
    
    if data == "premium_buy":
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("1 hafta - 30 571 so'm", callback_data="premium_1w")],
            [InlineKeyboardButton("1 oy - 63 429 so'm ⭐️", callback_data="premium_1m")],
            [InlineKeyboardButton("3 oy - 137 714 so'm", callback_data="premium_3m")],[InlineKeyboardButton("1 yil - 282 000 so'm", callback_data="premium_1y")],
            [InlineKeyboardButton("❌ Bekor qilish", callback_data="cancel_premium")]
        ])
        await query.message.reply_text(
            "👑 PREMIUM\n\n"
            "⚡️ Imkoniyatlaringizni 5× oshiring\n\n"
            "📈 Doim yuqorida ko'rinish\n"
            "❤️ Cheksiz layklar\n"
            "👀 Kim yoqtirganini ko'rish\n"
            "💬 Match bo'lmasdan xabar yozish\n\n"
            "📅 Muddatni tanlang:",
            reply_markup=keyboard
        )
        return
    
    if data.startswith("premium_"):
        durations = {"premium_1w": 7, "premium_1m": 30, "premium_3m": 90, "premium_1y": 365}
        prices = {"premium_1w": "30 571", "premium_1m": "63 429", "premium_3m": "137 714", "premium_1y": "282 000"}
        if data in durations:
            days = durations[data]
            price = prices[data]
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ To'lov qildim", callback_data=f"confirm_{data}")],
                [InlineKeyboardButton("❌ Bekor qilish", callback_data="cancel_premium")]
            ])
            await query.message.reply_text(
                f"💳 TO'LOV\n\n"
                f"📅 Muddat: {days} kun\n"
                f"💰 Summa: {price} so'm\n\n"
                f"💳 Karta: 9860 0866 0148 0972\n\n"
                f"To'lov qilgach '✅ To'lov qildim' ni bosing.",
                reply_markup=keyboard
            )
        return
    
    if data.startswith("confirm_"):
        plan = data.replace("confirm_", "")
        durations = {"premium_1w": 7, "premium_1m": 30, "premium_3m": 90, "premium_1y": 365}
        days = durations.get(plan, 0)
        try:
            await context.bot.send_message(chat_id=ADMIN_ID, text=f"💳 To'lov so'rovi!\n👤 {user.first_name}\n📅 {days} kun")
        except:
            pass
        await query.message.reply_text("✅ To'lov so'rovi yuborildi! Admin tasdiqlagach Premium faollashadi.")
        return
    
    if data == "cancel_premium":
        await query.message.reply_text("❌ Bekor qilindi.")
        return
    
    if data == "deactivate":
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("UPDATE users SET is_active = FALSE WHERE user_id = %s", (user.id,))
        conn.commit()
        cur.close()
        conn.close()
        await query.message.reply_text("👻 Profil muzlatildi. /start bilan qayta faollashtiring.")
        return
    
    if data == "edit_menu":
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("👤 Ismni o'zgartirish", callback_data="edit_name")],
            [InlineKeyboardButton("🎂 Yoshni o'zgartirish", callback_data="edit_age")],
            [InlineKeyboardButton("📝 Bioni o'zgartirish", callback_data="edit_bio")],
            [InlineKeyboardButton("📍 Shaharni o'zgartirish", callback_data="edit_city")],
            [InlineKeyboardButton("📸 Rasmni o'zgartirish", callback_data="edit_photo")]
        ])
        await query.message.reply_text("✏️ Nima o'zgartirmoqchisiz?", reply_markup=keyboard)
        return
    
    if data == "edit_name":
        context.user_data['edit_field'] = 'name'
        await query.message.reply_text("Yangi ismingizni yozing:")
        return
    
    if data == "edit_age":
        context.user_data['edit_field'] = 'age'
        await query.message.reply_text("Yangi yoshingizni kiriting (16-60):")
        return
    
    if data == "edit_bio":
        context.user_data['edit_field'] = 'bio'
        await query.message.reply_text("Yangi bio yozing:")
        return
    
    if data == "edit_city":
        context.user_data['edit_field'] = 'city'
        await query.message.reply_text("Yangi shahringizni yozing:")
        return
    
    if data == "edit_photo":
        context.user_data['edit_field'] = 'photo'
        await query.message.reply_text("Yangi rasm yuboring:")
        return
    
    if data.startswith("skip_"):
        await query.message.delete()
        await find(query, context)
        return
    
    if data.startswith("like_"):
        target_id = int(data.split("_")[1])
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("INSERT INTO likes (from_user, to_user) VALUES (%s, %s)", (user.id, target_id))
        cur.execute("SELECT * FROM likes WHERE from_user = %s AND to_user = %s", (target_id, user.id))
        mutual_like = cur.fetchone()
        cur.execute("SELECT first_name FROM users WHERE user_id = %s", (target_id,))
        target_info = cur.fetchone()
        if mutual_like:
            cur.execute("INSERT INTO matches (user1, user2) VALUES (%s, %s)", (user.id, target_id))
            await query.message.reply_text(f"🎉 MATCH! {target_info[0]} bilan mos keldingiz!")
        else:
            await query.message.reply_text("❤️ Yoqdi!")
        conn.commit()
        cur.close()
        conn.close()
        await query.message.delete()
        await find(query, context)
        return

async def save_edit(update, context):
    user = update.effective_user
    text = update.message.text
    field = context.user_data.get('edit_field')
    conn = get_db_connection()
    cur = conn.cursor()
    
    if field == 'name':
        cur.execute("UPDATE users SET first_name = %s WHERE user_id = %s", (text, user.id))
        await update.message.reply_text("✅ Ism yangilandi!")
    elif field == 'age':
        if text.isdigit() and 16 <= int(text) <= 60:
            cur.execute("UPDATE users SET age = %s WHERE user_id = %s", (int(text), user.id))
            await update.message.reply_text("✅ Yosh yangilandi!")
        else:
            await update.message.reply_text("❌ Yosh 16-60 oralig'ida!")
    elif field == 'bio':
        cur.execute("UPDATE users SET bio = %s WHERE user_id = %s", (text, user.id))
        await update.message.reply_text("✅ Bio yangilandi!")
    elif field == 'city':
        cur.execute("UPDATE users SET city = %s WHERE user_id = %s", (text, user.id))
        await update.message.reply_text("✅ Shahar yangilandi!")
    
    conn.commit()
    cur.close()
    conn.close()
    del context.user_data['edit_field']
    await update.message.reply_text("Bosh menyu:", reply_markup=await get_main_keyboard())
    return ConversationHandler.END

async def save_edit_photo(update, context):
    user = update.effective_user
    photo = update.message.photo[-1].file_id
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("UPDATE users SET photo = %s WHERE user_id = %s", (photo, user.id))
    conn.commit()
    cur.close()
    conn.close()
    del context.user_data['edit_field']
    await update.message.reply_text("✅ Rasm yangilandi!", reply_markup=await get_main_keyboard())
    return ConversationHandler.END

async def profile(update, context):
    user = update.effective_user
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE user_id = %s", (user.id,))
    user_data = cur.fetchone()
    cur.execute("SELECT COUNT(*) FROM likes WHERE to_user = %s", (user.id,))
    likes_count = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM matches WHERE user1 = %s OR user2 = %s", (user.id, user.id))
    matches_count = cur.fetchone()[0]
    cur.close()
    conn.close()
    if not user_data:
        await update.message.reply_text("❌ Profil topilmadi.")
        return
    
    if len(user_data) >= 11:
        user_id, username, first_name, age, gender, bio, photo, city, is_active, premium_until, created_at = user_data[:11]
    else:
        user_id, username, first_name, age, gender, bio, photo, city = user_data[:8]
        is_active = True
        premium_until = None
    
    premium_status = "✅" if premium_until and premium_until > datetime.now() else "❌"
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("✏️ Tahrirlash", callback_data="edit_menu")],
        [InlineKeyboardButton("👑 Premium", callback_data="premium_buy")]
    ])
    await update.message.reply_photo(
        photo=photo,
        caption=f"👤 {first_name}, {age}\n👤 {gender}\n📍 {city}\n📝 {bio}\n\n"
                f"❤️ {likes_count} like\n💞 {matches_count} match\n👑 Premium: {premium_status}",
        reply_markup=keyboard
    )

async def likes(update, context):
    user = update.effective_user
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT u.first_name, u.age FROM users u JOIN likes l ON u.user_id = l.to_user WHERE l.from_user = %s", (user.id,))
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
        SELECT u.first_name, u.age FROM users u
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
        text += f"• {match[0]}, {match[1]}\n"
    await update.message.reply_text(text)

async def settings(update, context):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("✏️ Profilni tahrirlash", callback_data="edit_menu")],
        [InlineKeyboardButton("👑 Premium", callback_data="premium_buy")],
        [InlineKeyboardButton("👻 Profilni muzlatish", callback_data="deactivate")]
    ])
    await update.message.reply_text("⚙️ Sozlamalar:", reply_markup=keyboard)

async def handle_message(update, context):
    text = update.message.text
    
    if 'edit_field' in context.user_data:
        return await save_edit(update, context)
    
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
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("1 hafta - 30 571 so'm", callback_data="premium_1w")],
            [InlineKeyboardButton("1 oy - 63 429 so'm ⭐️", callback_data="premium_1m")],
            [InlineKeyboardButton("3 oy - 137 714 so'm", callback_data="premium_3m")],
            [InlineKeyboardButton("1 yil - 282 000 so'm", callback_data="premium_1y")]
        ])
        await update.message.reply_text("👑 PREMIUM\n\nMuddatni tanlang:", reply_markup=keyboard)

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
    cur.close()
    conn.close()
    await update.message.reply_text(
        f"📊 ADMIN PANEL:\n\n"
        f"👥 Foydalanuvchilar: {total_users}\n"
        f"❤️ Likelar: {total_likes}\n"
        f"💞 Matchlar: {total_matches}"
    )

async def approve(update, context):
    user = update.effective_user
    if user.id != ADMIN_ID:
        await update.message.reply_text("⛔ Siz admin emassiz!")
        return
    try:
        parts = update.message.text.split()
        user_id = int(parts[1])
        days = int(parts[2])
        premium_until = datetime.now() + timedelta(days=days)
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("UPDATE users SET premium_until = %s WHERE user_id = %s", (premium_until, user_id))
        conn.commit()
        cur.close()
        conn.close()
        await update.message.reply_text(f"✅ Premium tasdiqlandi! {days} kun")
    except:
        await update.message.reply_text("❌ Format: /approve USER_ID KUNLAR")

async def broadcast(update, context):
    user = update.effective_user
    if user.id != ADMIN_ID:
        await update.message.reply_text("⛔ Siz admin emassiz!")
        return
    text = update.message.text.replace("/broadcast ", "")
    await notify_news(context.bot, text)
    await update.message.reply_text("✅ Yuborildi!")

def main():
    from flask import Flask
    flask_app = Flask(name)
    
    @flask_app.route('/')
    def home():
        return "Bot ishlayapti!"
    
    import threading
    threading.Thread(target=lambda: flask_app.run(host='0.0.0.0', port=8080), daemon=True).start()
    
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
            CITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_city)],
            BIO: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_bio)],
            PHOTO: [MessageHandler(filters.PHOTO, get_photo)],
        },
        fallbacks=[],
    )
    
    app.add_handler(conv_handler)
    app.add_handler(CommandHandler("admin", admin))
    app.add_handler(CommandHandler("approve", approve))
    app.add_handler(CommandHandler("broadcast", broadcast))
    app.add_handler(CommandHandler("find", find))
    app.add_handler(CommandHandler("profile", profile))
    app.add_handler(CommandHandler("likes", likes))
    app.add_handler(CommandHandler("matches", matches))
    app.add_handler(CommandHandler("settings", settings))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(handle_callback))
    
    print("Dating bot ishga tushdi...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()

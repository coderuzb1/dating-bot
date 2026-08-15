import os
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ConversationHandler, CallbackQueryHandler
from telegram import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from database import init_db, get_db_connection
from notifications import notify_new_user, notify_new_match, notify_like, notify_news
from datetime import datetime, timedelta

AGE, GENDER, BIO, PHOTO = range(4)
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
    try:
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"🆕 YANGI FOYDALANUVCHI\n\n"
                 f"👤 Ism: {user.first_name}\n"
                 f"📱 Username: @{user.username or 'yoq'}\n"
                 f"🆔 ID: {user.id}\n"
                 f"🎂 Yosh: {context.user_data.get('age', '?')}\n"
                 f"👤 Jins: {context.user_data.get('gender', '?')}\n"
                 f"📍 Shahar: {context.user_data.get('city', '?')}\n"
                 f"📝 Bio: {context.user_data.get('bio', '?')}\n"
                 f"🌍 Til: {context.user_data.get('language', 'uz')}"
        )
    except:
        pass
    await update.message.reply_text("✅ Profil yaratildi!", reply_markup=await get_main_keyboard())
    return ConversationHandler.END

async def find(update, context):
    message = update.message if update.message else update.callback_query.message
    user = update.effective_user
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT gender FROM users WHERE user_id = %s", (user.id,))
    user_data = cur.fetchone()
    if not user_data:
        await message.reply_text("❌ Avval profil yarating. /start bosing.")
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
        await message.reply_text(f"😔 Hozircha {target_gender} profillar yo'q.")
        return
    target_id, username, first_name, age, gender, bio, photo, city, is_active, premium_until, created_at = target
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("👎 Yoqmadi", callback_data=f"skip_{target_id}"),
            InlineKeyboardButton("❤️ Yoqdi", callback_data=f"like_{target_id}")
        ],
        [
            InlineKeyboardButton("➡️ O'tkazib yuborish", callback_data=f"skip_{target_id}")
        ]
    ])
    await message.reply_photo(photo=photo, caption=f"👤 {first_name}, {age}\n👤 {gender}\n📝 {bio}", reply_markup=keyboard)

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
        user_id, username, first_name, age, gender, bio, photo, city, is_active, premium_until, created_at = user_data
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("❤️ Yoqdi", callback_data=f"like_{target_id}")]])
        await query.message.reply_photo(photo=photo, caption=f"👤 {first_name}, {age}\n👤 {gender}\n📝 {bio}", reply_markup=keyboard)

async def handle_callback(update, context):
    query = update.callback_query
    await query.answer()
    user = query.from_user
    data = query.data
    if data.startswith("premium_"):
        durations = {"premium_1w": 7, "premium_1m": 30, "premium_3m": 90, "premium_1y": 365}
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
        return
    if data == "cancel_premium":
        await query.message.reply_text("❌ Bekor qilindi.")
        return
    if data.startswith("view_profile_"):
        await view_profile(update, context)
        return
    if data.startswith("chat_"):
        target_id = int(data.split("_")[1])
        context.user_data['chat_with'] = target_id
        await query.message.reply_text("💬 Xabaringizni yozing:")
        return

    if data.startswith("message_"):
        target_id = int(data.split("_")[1])
        cur = get_db_connection()
        cursor = cur.cursor()
        cursor.execute("SELECT premium_until FROM users WHERE user_id = %s", (user.id,))
        premium_data = cursor.fetchone()
        is_premium = premium_data and premium_data[0] and premium_data[0] > datetime.now()
        cur.close()
        if not is_premium:
            keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("👑 Premium olish", callback_data="premium_buy")]])
            await query.message.reply_text("❌ Xabar yozish uchun Premium kerak!", reply_markup=keyboard)
            return
        await query.message.reply_text("💬 Xabaringizni yozing:")
        context.user_data['message_to'] = target_id
        return

    if data.startswith("like_"):
        target_id = int(data.split("_")[1])
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("INSERT INTO likes (from_user, to_user) VALUES (%s, %s)", (user.id, target_id))
        cur.execute("UPDATE users SET views_today = views_today + 1 WHERE user_id = %s", (user.id,))
        cur.execute("SELECT * FROM likes WHERE from_user = %s AND to_user = %s", (target_id, user.id))
        mutual_like = cur.fetchone()
        cur.execute("SELECT first_name, photo FROM users WHERE user_id = %s", (user.id,))
        user_info = cur.fetchone()
        user_name = user_info[0]
        user_photo = user_info[1]
        cur.execute("SELECT first_name, photo FROM users WHERE user_id = %s", (target_id,))
        target_info = cur.fetchone()
        target_name = target_info[0]
        target_photo = target_info[1]
        if mutual_like:
            cur.execute("INSERT INTO matches (user1, user2) VALUES (%s, %s)", (user.id, target_id))
            await notify_new_match(context.bot, user.id, user_name, user_photo, target_id, target_name, target_photo)
            await query.message.reply_text(f"🎉 TABRIKLAYMIZ! MATCH!\n\nSiz {target_name} bilan mos keldingiz!")
        else:
            await notify_like(context.bot, target_id, user.id, user_name, user_photo)
            await query.message.reply_text("❤️ Yoqdi! Agar qarshi tomon ham yoqsa, match bo'ladi.")
        conn.commit()
        cur.close()
        conn.close()
        await query.message.delete()
        await find(query, context)
        return
    if data.startswith("skip_"):
        await query.message.delete()
        await find(query, context)
        return
    if data.startswith("block_"):
        target_id = int(data.split("_")[1])
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("INSERT INTO blocks (from_user, to_user) VALUES (%s, %s)", (user.id, target_id))
        conn.commit()
        cur.close()
        conn.close()
        await query.message.reply_text("🚫 Foydalanuvchi bloklandi.")
        await query.message.delete()
        await find(query, context)
        return
    if data.startswith("report_"):
        target_id = int(data.split("_")[1])
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("INSERT INTO reports (from_user, to_user, reason) VALUES (%s, %s, %s)", (user.id, target_id, "Report"))
        conn.commit()
        cur.close()
        conn.close()
        await query.message.reply_text("⚠️ Foydalanuvchi report qilindi.")
        await query.message.delete()
        await find(query, context)
        return

async def buy_premium(query, context):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("1 hafta - 30 571 so'm", callback_data="premium_1w")],
        [InlineKeyboardButton("1 oy - 63 429 so'm ⭐️", callback_data="premium_1m")],
        [InlineKeyboardButton("3 oy - 137 714 so'm", callback_data="premium_3m")],
        [InlineKeyboardButton("1 yil - 282 000 so'm", callback_data="premium_1y")],
        [InlineKeyboardButton("❌ Bekor qilish", callback_data="cancel_premium")]
    ])
    await query.message.reply_text(
        "👑 PREMIUM\n\n"
        "⚡️ Imkoniyatlaringizni 5× oshiring\n\n"
        "🔥 325+ kishi allaqachon Premium'da\n\n"
        "📈 Doim yuqorida ko'rinish\n"
        "💕 2-3× ko'proq tanishuv\n"
        "❤️ Cheksiz layklar\n"
        "👀 Kim yoqtirganini darhol bilib oling\n\n"
        "💳 To'lov usullari:\n"
        "1. Click\n"
        "2. Payme\n"
        "3. Karta",
        reply_markup=keyboard
    )

async def premium(update, context):
    await buy_premium(update, context)

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
    user_id, username, first_name, age, gender, bio, photo, city, is_active, premium_until, created_at = user_data
    premium_status = "✅" if premium_until and premium_until > datetime.now() else "❌"
    await update.message.reply_photo(photo=photo, caption=f"👤 {first_name}, {age}\n👤 {gender}\n📝 {bio}\n\n❤️ {likes_count} like\n💞 {matches_count} match\n👑 Premium: {premium_status}")

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
        SELECT u.user_id, u.first_name, u.age, u.username FROM users u
        JOIN matches m ON u.user_id = CASE WHEN m.user1 = %s THEN m.user2 ELSE m.user1 END
        WHERE m.user1 = %s OR m.user2 = %s
    """, (user.id, user.id, user.id))
    matches_list = cur.fetchall()
    cur.close()
    conn.close()
    if not matches_list:
        await update.message.reply_text("💞 Hozircha matchlar yo'q.")
        return
    keyboard = InlineKeyboardMarkup([])
    for match in matches_list[:10]:
        keyboard.inline_keyboard.append([
            InlineKeyboardButton(f"💬 {match[1]}, {match[2]}", callback_data=f"chat_{match[0]}")
        ])
    await update.message.reply_text("💞 Matchlaringiz:\n\nXabar yozish uchun bosing:", reply_markup=keyboard)

async def settings(update, context):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("👑 Premium sotib olish", callback_data="premium_buy")]
    ])
    await update.message.reply_text("⚙️ Sozlamalar:", reply_markup=keyboard)

async def save_edit(update, context):
    user = update.effective_user
    field = context.user_data.get('edit_field')
    conn = get_db_connection()
    cur = conn.cursor()
    
    if field == 'age':
        value = update.message.text
        if not value.isdigit() or int(value) < 16 or int(value) > 60:
            await update.message.reply_text("❌ Yoshi 16-60 oralig'ida bo'lishi kerak:")
            return AGE
        cur.execute("UPDATE users SET age = %s WHERE user_id = %s", (int(value), user.id))
    elif field == 'bio':
        value = update.message.text
        cur.execute("UPDATE users SET bio = %s WHERE user_id = %s", (value, user.id))
    elif field == 'gender':
        value = update.message.text
        gender = "Erkak" if "👨" in value else "Ayol" if "👩" in value else value
        cur.execute("UPDATE users SET gender = %s WHERE user_id = %s", (gender, user.id))
    elif field == 'city':
        value = update.message.text
        cur.execute("UPDATE users SET city = %s WHERE user_id = %s", (value, user.id))
    
    conn.commit()
    cur.close()
    conn.close()
    
    del context.user_data['edit_field']
    await update.message.reply_text("✅ Profil yangilandi!", reply_markup=await get_main_keyboard())
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

async def handle_message(update, context):
    text = update.message.text
    
    if 'edit_field' in context.user_data:
        return await save_edit(update, context)
    
    if await check_bad_words(text):
        await update.message.reply_text("⚠️ Xabaringizda taqiqlangan so'z bor!")
        return
    
    if 'chat_with' in context.user_data:
        target_id = context.user_data['chat_with']
        user = update.effective_user
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT first_name FROM users WHERE user_id = %s", (user.id,))
        from_name = cur.fetchone()[0]
        cur.execute("INSERT INTO messages (from_user, to_user, text) VALUES (%s, %s, %s)", (user.id, target_id, text))
        conn.commit()
        cur.close()
        conn.close()
        try:
            await context.bot.send_message(chat_id=target_id, text=f"💬 {from_name} dan:\n\n{text}")
            await update.message.reply_text("✅ Xabar yuborildi!")
        except:
            await update.message.reply_text("❌ Xabar yuborilmadi.")
        del context.user_data['chat_with']
        return

    if 'message_to' in context.user_data:
        target_id = context.user_data['message_to']
        user = update.effective_user
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT premium_until FROM users WHERE user_id = %s", (user.id,))
        premium_data = cur.fetchone()
        is_premium = premium_data and premium_data[0] and premium_data[0] > datetime.now()
        
        if not is_premium:
            await update.message.reply_text("❌ Xabar yozish uchun Premium kerak.")
            cur.close()
            conn.close()
            del context.user_data['message_to']
            return
        
        cur.execute("SELECT first_name FROM users WHERE user_id = %s", (user.id,))
        from_name = cur.fetchone()[0]
        
        today = datetime.now().date()
        cur.execute("SELECT COUNT(*) FROM messages WHERE from_user = %s AND created_at::date = %s", (user.id, today))
        msg_count = cur.fetchone()[0]
        cur.close()
        conn.close()
        
        if msg_count >= 10:
            await update.message.reply_text("⚠️ Kunlik xabar limiti tugadi!")
            del context.user_data['message_to']
            return
        
        try:
            await context.bot.send_message(
                chat_id=target_id,
                text=f"💬 {from_name} dan xabar:\n\n{text}"
            )
            await update.message.reply_text("✅ Xabar yuborildi!")
        except:
            await update.message.reply_text("❌ Xabar yuborilmadi.")
        
        del context.user_data['message_to']
        return
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
    )

async def broadcast(update, context):
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
        EDIT_PHOTO: [MessageHandler(filters.PHOTO, save_edit_photo)],
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

if __name__ == "__main__":
    main()

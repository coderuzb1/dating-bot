import psycopg2
import os

def get_db_connection():
    DATABASE_URL = os.environ.get("DATABASE_URL")
    return psycopg2.connect(DATABASE_URL)

async def send_notification_to_all(bot, text, exclude_user_id=None):
    conn = get_db_connection()
    cur = conn.cursor()
    if exclude_user_id:
        cur.execute("SELECT user_id FROM users WHERE user_id != %s", (exclude_user_id,))
    else:
        cur.execute("SELECT user_id FROM users")
    users = cur.fetchall()
    cur.close()
    conn.close()
    
    for user in users:
        try:
            await bot.send_message(chat_id=user[0], text=text)
        except:
            pass

async def notify_new_user(bot, new_user_name, new_user_id):
    text = f"🆕 Yangi foydalanuvchi qo'shildi!\n\n👤 {new_user_name}\n\n🔍 Qidirish tugmasini bosing va tanishib chiqing!"
    await send_notification_to_all(bot, text, exclude_user_id=new_user_id)

async def notify_like(bot, to_user_id, from_user_id, from_user_name, from_user_photo):
    from telegram import InlineKeyboardMarkup, InlineKeyboardButton
    
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT first_name, age, photo FROM users WHERE user_id = %s", (from_user_id,))
    user_info = cur.fetchone()
    cur.close()
    conn.close()
    
    if user_info:
        name, age, photo = user_info
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("👤 Profilni ko'rish", callback_data=f"view_profile_{from_user_id}")]
        ])
        
        try:
            await bot.send_photo(
                chat_id=to_user_id,
                photo=photo,
                caption=f"❤️ Sizni {name} yoqtirdi!\n\n👤 {name}, {age}\n\nJavob qaytaring!",
                reply_markup=keyboard
            )
        except:
            try:
                await bot.send_message(
                    chat_id=to_user_id,
                    text=f"❤️ Sizni {name} yoqtirdi!\n\nJavob qaytaring!"
                )
            except:
                pass

async def notify_new_match(bot, user1_id, user1_name, user1_photo, user2_id, user2_name, user2_photo):
    from telegram import InlineKeyboardMarkup, InlineKeyboardButton
    
    keyboard1 = InlineKeyboardMarkup([
        [InlineKeyboardButton("👤 Profilni ko'rish", callback_data=f"view_profile_{user2_id}")]
    ])
    
    keyboard2 = InlineKeyboardMarkup([
        [InlineKeyboardButton("👤 Profilni ko'rish", callback_data=f"view_profile_{user1_id}")]
    ])
    
    try:
        await bot.send_photo(
            chat_id=user1_id,
            photo=user2_photo,
            caption=f"🎉 MATCH!\n\nSiz {user2_name} bilan mos keldingiz!\n\n💞 Matchlarim bo'limidan ko'rishingiz mumkin.",
            reply_markup=keyboard1
        )
    except:
        try:
            await bot.send_message(
                chat_id=user1_id,
                text=f"🎉 MATCH!\n\nSiz {user2_name} bilan mos keldingiz!"
            )
        except:
            pass
    
    try:
        await bot.send_photo(
            chat_id=user2_id,
            photo=user1_photo,
            caption=f"🎉 MATCH!\n\nSiz {user1_name} bilan mos keldingiz!\n\n💞 Matchlarim bo'limidan ko'rishingiz mumkin.",
            reply_markup=keyboard2
        )
    except:
        try:
            await bot.send_message(
                chat_id=user2_id,
                text=f"🎉 MATCH!\n\nSiz {user1_name} bilan mos keldingiz!"
            )
        except:
            pass

async def notify_news(bot, text):
    await send_notification_to_all(bot, f"📢 Yangilik:\n\n{text}")

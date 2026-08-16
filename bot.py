import os
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ConversationHandler, CallbackQueryHandler
from telegram import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from database import init_db, get_db_connection
from notifications import (
    notify_new_user,
    notify_new_match,
    notify_like,
    notify_news,
    notify_inactive_users_3_days,
    notify_inactive_users_7_days,
    notify_premium_promotion,
    notify_new_user_in_city,
    retention_job,
)
from datetime import datetime, timedelta

LANGUAGE, AGE, GENDER, BIO, PHOTO, CITY = range(6)
ADMIN_ID = 6310532367
HUMO_CARD = "9860086601480972"
VISA_CARD = "4916990302424491"
BAD_WORDS = ["ahmoq", "jinni", "sotqin", "firibgar", "scam", "aldamoq", "pul", "karta", "parol"]


def save_premium_history(
    cur,
    user_id,
    action,
    days=0,
    source="unknown",
    admin_id=None,
    old_premium_until=None,
    new_premium_until=None
):
    cur.execute(
        """
        INSERT INTO premium_history (
            user_id,
            action,
            days,
            source,
            admin_id,
            old_premium_until,
            new_premium_until
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """,
        (
            user_id,
            action,
            days,
            source,
            admin_id,
            old_premium_until,
            new_premium_until
        )
    )


async def scheduled_notifications(context):
    print("🔔 Notification scheduler tekshiruvi...")

    try:
        await notify_inactive_users_3_days(context.bot)
    except Exception as e:
        print(f"3-day notification error: {e}")

    try:
        await notify_inactive_users_7_days(context.bot)
    except Exception as e:
        print(f"7-day notification error: {e}")

    try:
        await notify_premium_promotion(context.bot)
    except Exception as e:
        print(f"Premium notification error: {e}")

    print("✅ Notification scheduler tugadi")


async def check_bad_words(text):
    return any(word in text.lower() for word in BAD_WORDS)

async def get_main_keyboard():
    return ReplyKeyboardMarkup([
        [KeyboardButton("🔍 Qidirish"), KeyboardButton("👤 Profil")],
        [KeyboardButton("❤️ Yoqtirganlarim"), KeyboardButton("💞 Matchlarim")],
        [KeyboardButton("⚙️ Sozlamalar"), KeyboardButton("👑 Premium")],
        [KeyboardButton("🎁 Referal")]
    ], resize_keyboard=True)

async def start(update, context):
    user = update.effective_user

    if context.args and context.args[0].startswith("ref_"):
        try:
            referrer_id = int(context.args[0].replace("ref_", ""))
            if referrer_id != user.id:
                context.user_data["referrer_id"] = referrer_id
        except ValueError:
            pass
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT is_active FROM users WHERE user_id = %s", (user.id,))
    user_status = cur.fetchone()
    cur.close()
    conn.close()
    
    if user_status:
        # Foydalanuvchi botga kirgan vaqtni yangilash
        try:
            active_conn = get_db_connection()
            active_cur = active_conn.cursor()

            active_cur.execute(
                """
                UPDATE users
                SET last_active = NOW()
                WHERE user_id = %s
                """,
                (user.id,)
            )

            active_conn.commit()
            active_cur.close()
            active_conn.close()

        except Exception as e:
            print(f"Last active update error: {e}")

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
        keyboard = ReplyKeyboardMarkup([
            [KeyboardButton("🇺🇿 O'zbek tili")],
            [KeyboardButton("🇷🇺 Русский")],
            [KeyboardButton("🇺🇿 Узбек (Кирилл)")]
        ], resize_keyboard=True, one_time_keyboard=True)

        await update.message.reply_text(
            "🌐 Tilni tanlang / Выберите язык:",
            reply_markup=keyboard
        )
        return LANGUAGE

async def get_language(update, context):
    text = update.message.text

    languages = {
        "🇺🇿 O'zbek tili": "uz",
        "🇷🇺 Русский": "ru",
        "🇺🇿 Узбек (Кирилл)": "uz_cyr",
    }

    if text not in languages:
        await update.message.reply_text(
            "🌐 Iltimos, tilni tanlang / Пожалуйста, выберите язык:"
        )
        return LANGUAGE

    context.user_data["language"] = languages[text]

    await update.message.reply_text(
        "📝 Profil yaratish uchun yoshingizni kiriting (16-60):"
    )
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
    city = update.message.text.strip()

    cities = {
        "Toshkent",
        "Samarqand",
        "Buxoro",
        "Andijon",
        "Farg'ona",
        "Namangan",
        "Qarshi",
        "Nukus",
        "Xiva",
        "Jizzax",
        "Guliston",
        "Termiz",
        "Navoiy",
    }

    # Oddiy tugma orqali tanlangan shahar
    if city in cities:
        context.user_data['city'] = city
        context.user_data.pop('custom_city', None)

        await update.message.reply_text(
            "📝 O'zingiz haqingizda qisqacha yozing:"
        )
        return BIO

    # "Boshqa" tanlansa, keyingi xabar shahar nomi bo'ladi
    if city == "Boshqa":
        context.user_data['custom_city'] = True

        await update.message.reply_text(
            "📍 Shahringiz nomini yozing:"
        )
        return CITY

    # Boshqa matn faqat "Boshqa" oldin tanlangan bo'lsa qabul qilinadi
    if context.user_data.get('custom_city'):
        if len(city) < 2 or len(city) > 50:
            await update.message.reply_text(
                "❌ Shahar nomi 2-50 ta belgidan iborat bo'lishi kerak."
            )
            return CITY

        context.user_data['city'] = city
        context.user_data.pop('custom_city', None)

        await update.message.reply_text(
            "📝 O'zingiz haqingizda qisqacha yozing:"
        )
        return BIO

    await update.message.reply_text(
        "❌ Iltimos, shaharni tugmalardan tanlang yoki "
        "«Boshqa» tugmasini bosing."
    )
    return CITY

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
        INSERT INTO users (
            user_id, username, first_name, age, gender, bio, photo, city, language
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (user_id) DO UPDATE SET
            age = %s,
            gender = %s,
            bio = %s,
            photo = %s,
            city = %s,
            language = %s
    """, (
        user.id,
        user.username,
        user.first_name,
        context.user_data['age'],
        context.user_data['gender'],
        context.user_data['bio'],
        photo,
        context.user_data['city'],
        context.user_data.get('language', 'uz'),
        context.user_data['age'],
        context.user_data['gender'],
        context.user_data['bio'],
        photo,
        context.user_data['city'],
        context.user_data.get('language', 'uz')
    ))
    # =========================
    # REFERAL TIZIMI
    # =========================
    referrer_id = context.user_data.get("referrer_id")

    if referrer_id and referrer_id != user.id:
        cur.execute(
            """
            SELECT user_id
            FROM users
            WHERE user_id = %s
            """,
            (referrer_id,)
        )
        referrer_exists = cur.fetchone()

        if referrer_exists:
            cur.execute(
                """
                UPDATE users
                SET referred_by = %s
                WHERE user_id = %s
                  AND referred_by IS NULL
                """,
                (referrer_id, user.id)
            )

            # Faqat yangi referal biriktirilgan bo'lsa mukofot hisoblanadi
            if cur.rowcount > 0:
                cur.execute(
                    """
                    SELECT COUNT(*)
                    FROM users
                    WHERE referred_by = %s
                    """,
                    (referrer_id,)
                )
                referral_count = cur.fetchone()[0]

                rewards = {
                    5: 1,
                    10: 7,
                    25: 30,
                    50: 90,
                    100: 365
                }

                if referral_count in rewards:
                    premium_days = rewards[referral_count]

                    cur.execute(
                        """
                        INSERT INTO referral_rewards
                        (user_id, referrals_count, premium_days)
                        VALUES (%s, %s, %s)
                        ON CONFLICT (user_id, referrals_count)
                        DO NOTHING
                        """,
                        (referrer_id, referral_count, premium_days)
                    )

                    if cur.rowcount > 0:
                        cur.execute(
                            "SELECT premium_until FROM users WHERE user_id = %s",
                            (referrer_id,)
                        )
                        old_premium_until = cur.fetchone()[0]

                        cur.execute(
                            """
                            UPDATE users
                            SET premium_until =
                                CASE
                                    WHEN premium_until IS NOT NULL
                                         AND premium_until > NOW()
                                    THEN premium_until + (%s * INTERVAL '1 day')
                                    ELSE NOW() + (%s * INTERVAL '1 day')
                                END
                            WHERE user_id = %s
                            """,
                            (premium_days, premium_days, referrer_id)
                        )

                        cur.execute(
                            "SELECT premium_until FROM users WHERE user_id = %s",
                            (referrer_id,)
                        )
                        new_premium_until = cur.fetchone()[0]

                        save_premium_history(
                            cur,
                            referrer_id,
                            action="add",
                            days=premium_days,
                            source="referral",
                            admin_id=None,
                            old_premium_until=old_premium_until,
                            new_premium_until=new_premium_until
                        )

                        try:
                            await context.bot.send_message(
                                chat_id=referrer_id,
                                text=(
                                    "🎉 REFERAL MUKOFOTI!\n\n"
                                    f"👥 Referallaringiz: {referral_count} ta\n"
                                    f"🎁 Mukofot: {premium_days} kun Premium\n\n"
                                    "👑 Premium avtomatik faollashtirildi!"
                                )
                            )
                        except:
                            pass

    context.user_data.pop("referrer_id", None)

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
                 f"📝 Bio: {context.user_data.get('bio', '?')}"
        )
    except:
        pass
    # Yangi profilning hududiga mos Smart Notification
    try:
        await notify_new_user_in_city(
            context.bot,
            user.id
        )
    except Exception as e:
        print(f"Smart city notification error: {e}")

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

    cur.execute(
        "SELECT gender, city, premium_until FROM users WHERE user_id = %s",
        (user.id,),
    )
    user_data = cur.fetchone()

    if not user_data:
        await message.reply_text("❌ Avval profil yarating. /start bosing.")
        cur.close()
        conn.close()
        return

    my_gender, my_city, premium_until = user_data

    cur.execute(
        """
        SELECT EXISTS(
            SELECT 1
            FROM users
            WHERE user_id = %s
              AND premium_until IS NOT NULL
              AND premium_until > NOW()
        )
        """,
        (user.id,),
    )

    is_premium = bool(cur.fetchone()[0])

    if not is_premium:
        cur.execute(
            """
            SELECT COUNT(*)
            FROM profile_views
            WHERE user_id = %s
            AND viewed_at >= CURRENT_DATE
            """,
            (user.id,),
        )

        today_count = cur.fetchone()[0]

        if today_count >= 15:
            cur.close()
            conn.close()
            await message.reply_text(
                "🚫 Bugungi 15 ta profil limitingiz tugadi.\n\n"
                "👑 Premiumga o'tib, profillarni cheksiz ko'rishingiz mumkin."
            )
            return

    cur.execute(
        """
        SELECT
            user_id, username, first_name, age, gender, bio,
            photo, city, is_active, premium_until, created_at
        FROM users
        WHERE user_id != %s
        AND is_active = TRUE

        AND user_id NOT IN (
            SELECT to_user FROM likes WHERE from_user = %s
        )

        AND user_id NOT IN (
            SELECT to_user FROM skips WHERE from_user = %s
        )

        AND user_id NOT IN (
            SELECT viewed_user_id
            FROM profile_views
            WHERE user_id = %s
        )

        ORDER BY
            CASE WHEN city = %s THEN 0 ELSE 1 END,
            created_at DESC

        LIMIT 1
        """,
        (
            user.id,
            user.id,
            user.id,
            user.id,
            my_city,
        ),
    )

    target = cur.fetchone()

    if not target:
        cur.close()
        conn.close()
        await message.reply_text(
            f"😔 Hozircha {target_gender} profillar qolmagan."
        )
        return

    (
        target_id,
        username,
        first_name,
        age,
        gender,
        bio,
        photo,
        city,
        is_active,
        target_premium_until,
        created_at,
    ) = target

    cur.execute(
        """
        INSERT INTO profile_views (user_id, viewed_user_id)
        VALUES (%s, %s)
        """,
        (user.id, target_id),
    )

    conn.commit()
    cur.close()
    conn.close()

    target_is_premium = (
        target_premium_until is not None
        and target_premium_until > datetime.now()
    )

    premium_badge = " ⭐" if target_is_premium else ""

    buttons = [
        [
            InlineKeyboardButton(
                "👎 Yoqmadi",
                callback_data=f"skip_{target_id}"
            ),
            InlineKeyboardButton(
                "❤️ Yoqdi",
                callback_data=f"like_{target_id}"
            ),
        ]
    ]

    if is_premium:
        buttons.append([
            InlineKeyboardButton(
                "✉️ Yozish",
                callback_data=f"write_{target_id}"
            )
        ])

    keyboard = InlineKeyboardMarkup(buttons)

    await message.reply_photo(
        photo=photo,
        caption=(
            f"👤 {first_name}, {age}{premium_badge}\n"
            f"👤 {gender}\n"
            f"📍 {city}\n"
            f"📝 {bio or 'Bio yozilmagan'}"
        ),
        reply_markup=keyboard,
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
            [InlineKeyboardButton("3 oy - 137 714 so'm", callback_data="premium_3m")],
            [InlineKeyboardButton("1 yil - 282 000 so'm", callback_data="premium_1y")],
            [InlineKeyboardButton("❌ Bekor qilish", callback_data="cancel_premium")]
        ])

        await query.message.reply_text(
            "👑 PREMIUM\n\n"
            "✨ Premium imkoniyatlari:\n\n"
            "♾️ Cheksiz profil ko'rish\n"
            "❤️ Cheksiz like\n"
            "✉️ Match bo'lmasdan yozish\n"
            "👀 Kim sizni yoqtirganini ko'rish\n"
            "⭐️ Premium belgisi\n"
            "🚀 Profilingizga ustuvorlik\n\n"
            "📅 Muddatni tanlang:",
            reply_markup=keyboard
        )
        return

    if data.startswith("premium_"):
        durations = {
            "premium_1w": 7,
            "premium_1m": 30,
            "premium_3m": 90,
            "premium_1y": 365
        }

        prices = {
            "premium_1w": "30 571",
            "premium_1m": "63 429",
            "premium_3m": "137 714",
            "premium_1y": "282 000"
        }

        if data not in durations:
            return

        days = durations[data]
        price = prices[data]

        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "💳 HUMO",
                    callback_data=f"pay_humo_{data}"
                ),
                InlineKeyboardButton(
                    "💳 VISA",
                    callback_data=f"pay_visa_{data}"
                )
            ],
            [
                InlineKeyboardButton(
                    "❌ Bekor qilish",
                    callback_data="cancel_premium"
                )
            ]
        ])

        await query.message.reply_text(
            "💳 TO'LOV USULINI TANLANG\n\n"
            f"📅 Muddat: {days} kun\n"
            f"💰 Summa: {price} so'm\n\n"
            "Quyidagi to'lov usullaridan birini tanlang:",
            reply_markup=keyboard
        )
        return

    if data.startswith("pay_humo_") or data.startswith("pay_visa_"):
        parts = data.split("_", 2)

        if len(parts) != 3:
            await query.message.reply_text("❌ To'lov ma'lumotlari xato.")
            return

        payment_method = parts[1].upper()
        plan = parts[2]

        durations = {
            "premium_1w": 7,
            "premium_1m": 30,
            "premium_3m": 90,
            "premium_1y": 365
        }

        prices = {
            "premium_1w": "30 571",
            "premium_1m": "63 429",
            "premium_3m": "137 714",
            "premium_1y": "282 000"
        }

        if plan not in durations:
            await query.message.reply_text("❌ Tarif topilmadi.")
            return

        days = durations[plan]
        price = prices[plan]

        if payment_method == "HUMO":
            card = HUMO_CARD
        else:
            card = VISA_CARD

        if not card:
            await query.message.reply_text(
                "❌ Ushbu to'lov usuli hozircha sozlanmagan."
            )
            return

        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "✅ To'lov qildim",
                    callback_data=f"confirm_{payment_method}_{plan}"
                )
            ],
            [
                InlineKeyboardButton(
                    "❌ Bekor qilish",
                    callback_data="cancel_premium"
                )
            ]
        ])

        await query.message.reply_text(
            "💳 TO'LOV\n\n"
            f"💳 Usul: {payment_method}\n"
            f"📅 Muddat: {days} kun\n"
            f"💰 Summa: {price} so'm\n\n"
            f"💳 Karta: {card}\n\n"
            "To'lovni amalga oshirgach, "
            "«✅ To'lov qildim» tugmasini bosing.",
            reply_markup=keyboard
        )
        return

    if data.startswith("confirm_"):
        parts = data.split("_", 2)

        if len(parts) != 3:
            await query.message.reply_text("❌ To'lov ma'lumotlari xato.")
            return

        payment_method = parts[1].upper()
        plan = parts[2]

        durations = {
            "premium_1w": 7,
            "premium_1m": 30,
            "premium_3m": 90,
            "premium_1y": 365
        }

        prices = {
            "premium_1w": "30 571",
            "premium_1m": "63 429",
            "premium_3m": "137 714",
            "premium_1y": "282 000"
        }

        if plan not in durations:
            await query.message.reply_text("❌ Tarif topilmadi.")
            return

        days = durations[plan]
        price = prices[plan]

        conn = get_db_connection()
        cur = conn.cursor()

        try:
            cur.execute(
                """
                INSERT INTO payments
                    (user_id, amount, days, status)
                VALUES
                    (%s, %s, %s, 'pending')
                RETURNING id
                """,
                (user.id, price, days)
            )

            payment_id = cur.fetchone()[0]
            conn.commit()

        except Exception as e:
            conn.rollback()
            print(f"Payment DB error: {e}")
            await query.message.reply_text(
                "❌ To'lov so'rovini saqlashda xatolik yuz berdi."
            )
            return

        finally:
            cur.close()
            conn.close()

        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "✅ TASDIQLASH",
                    callback_data=f"admin_approve_{payment_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    "❌ RAD ETISH",
                    callback_data=f"admin_reject_{payment_id}"
                )
            ]
        ])

        try:
            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=(
                    "💳 YANGI PREMIUM TO'LOVI\n\n"
                    f"🧾 To'lov ID: #{payment_id}\n"
                    f"👤 Ism: {user.first_name}\n"
                    f"📱 Username: @{user.username or 'yoq'}\n"
                    f"🆔 ID: {user.id}\n\n"
                    f"📅 Tarif: {days} kun\n"
                    f"💰 Summa: {price} so'm\n"
                    f"💳 To'lov usuli: {payment_method}\n\n"
                    "⚠️ To'lovni tekshirgandan keyin "
                    "tasdiqlang yoki rad eting."
                ),
                reply_markup=keyboard
            )

            await query.message.reply_text(
                "✅ To'lov so'rovingiz adminga yuborildi!\n\n"
                f"🧾 To'lov ID: #{payment_id}\n"
                f"💳 To'lov usuli: {payment_method}\n"
                f"📅 Muddat: {days} kun\n"
                f"💰 Summa: {price} so'm\n\n"
                "⏳ Admin to'lovni tekshiradi. "
                "Tasdiqlangandan keyin Premium avtomatik faollashadi."
            )

        except Exception as e:
            print(f"Payment notification error: {e}")

            conn = get_db_connection()
            cur = conn.cursor()

            try:
                cur.execute(
                    """
                    DELETE FROM payments
                    WHERE id = %s AND status = 'pending'
                    """,
                    (payment_id,)
                )
                conn.commit()
            except Exception:
                conn.rollback()
            finally:
                cur.close()
                conn.close()

            await query.message.reply_text(
                "❌ To'lov so'rovini yuborishda xatolik yuz berdi."
            )

        return

    if data.startswith("admin_approve_"):
        if user.id != ADMIN_ID:
            await query.answer(
                "Sizda bu amalni bajarish huquqi yo'q!",
                show_alert=True
            )
            return

        try:
            parts = data.split("_")
            payment_id = int(parts[2])

            conn = get_db_connection()
            cur = conn.cursor()

            # To'lovni tekshirish
            cur.execute(
                """
                SELECT
                    p.user_id,
                    p.amount,
                    p.days,
                    p.status,
                    u.first_name,
                    u.premium_until
                FROM payments p
                LEFT JOIN users u ON u.user_id = p.user_id
                WHERE p.id = %s
                """,
                (payment_id,)
            )

            payment = cur.fetchone()

            if not payment:
                cur.close()
                conn.close()
                await query.answer(
                    "❌ To'lov topilmadi!",
                    show_alert=True
                )
                return

            target_id, amount, days, payment_status, first_name, old_until = payment

            # Ikkinchi marta tasdiqlashni bloklash
            if payment_status != "pending":
                cur.close()
                conn.close()
                await query.answer(
                    f"⚠️ Bu to'lov allaqachon: {payment_status}",
                    show_alert=True
                )
                return

            # Premium muddatini avtomatik uzaytirish
            if old_until is not None and old_until > datetime.now():
                premium_until = old_until + timedelta(days=days)
            else:
                premium_until = datetime.now() + timedelta(days=days)

            cur.execute(
                """
                UPDATE users
                SET premium_until = %s
                WHERE user_id = %s
                """,
                (premium_until, target_id)
            )

            # To'lov holatini approved qilish
            cur.execute(
                """
                UPDATE payments
                SET status = 'approved'
                WHERE id = %s AND status = 'pending'
                """,
                (payment_id,)
            )

            # Premium tarixiga yozish
            save_premium_history(
                cur,
                target_id,
                action="add",
                days=days,
                source="payment",
                admin_id=user.id,
                old_premium_until=old_until,
                new_premium_until=premium_until
            )

            conn.commit()

            cur.close()
            conn.close()

            # Foydalanuvchiga xabar
            try:
                await context.bot.send_message(
                    chat_id=target_id,
                    text=(
                        "🎉 PREMIUM FAOLLASHTIRILDI!\\n\\n"
                        f"📅 Muddat: {days} kun\\n"
                        f"💰 To'lov: {amount} so'm\\n"
                        f"🧾 To'lov ID: #{payment_id}\\n\\n"
                        f"📅 Premiumgacha: "
                        f"{premium_until.strftime('%d.%m.%Y %H:%M')}\\n\\n"
                        "👑 Premium imkoniyatlaringiz faollashdi!"
                    )
                )
            except Exception as e:
                print(f"⚠️ Premium foydalanuvchiga xabar yuborishda xato: {e}")

            # Admin xabarini yangilash
            try:
                await query.message.edit_text(
                    "✅ PREMIUM TO'LOVI TASDIQLANDI\n\n"
                    f"🧾 To'lov ID: #{payment_id}\n"
                    f"👤 Foydalanuvchi: {first_name_display}\\n"
                    f"🆔 ID: {target_id}\n"
                    f"📅 Qo'shilgan: {days} kun\n"
                    f"💰 Summa: {amount} so'm\n"
                    f"📅 Premiumgacha: {premium_until.strftime('%d.%m.%Y %H:%M')}"
                )
            except Exception as e:
                print(f"⚠️ Admin xabarini yangilashda xato: {e}")
        except Exception as e:
            print(f"Premium approval error: {e}")
            await query.message.reply_text(
                "❌ To'lovni tasdiqlashda xatolik yuz berdi."
            )

        return


    if data.startswith("admin_reject_"):
        if user.id != ADMIN_ID:
            await query.answer(
                "Sizda bu amalni bajarish huquqi yo'q!",
                show_alert=True
            )
            return

        try:
            parts = data.split("_")
            payment_id = int(parts[2])

            conn = get_db_connection()
            cur = conn.cursor()

            # To'lovni topish
            cur.execute(
                """
                SELECT
                    p.user_id,
                    p.amount,
                    p.days,
                    p.status,
                    u.first_name
                FROM payments p
                LEFT JOIN users u ON u.user_id = p.user_id
                WHERE p.id = %s
                """,
                (payment_id,)
            )

            payment = cur.fetchone()

            if not payment:
                cur.close()
                conn.close()
                await query.answer(
                    "❌ To'lov topilmadi!",
                    show_alert=True
                )
                return

            target_id, amount, days, payment_status, first_name = payment

            # Ikkinchi marta rad/tasdiq qilishni bloklash
            if payment_status != "pending":
                cur.close()
                conn.close()
                await query.answer(
                    f"⚠️ Bu to'lov allaqachon: {payment_status}",
                    show_alert=True
                )
                return

            # To'lovni rejected qilish
            cur.execute(
                """
                UPDATE payments
                SET status = 'rejected'
                WHERE id = %s AND status = 'pending'
                """,
                (payment_id,)
            )

            conn.commit()

            cur.close()
            conn.close()

            # Foydalanuvchiga xabar
            try:
                await context.bot.send_message(
                    chat_id=target_id,
                    text=(
                        "❌ PREMIUM TO'LOVI RAD ETILDI!\\n\\n"
                        f"🧾 To'lov ID: #{payment_id}\\n"
                        f"📅 Tarif: {days} kun\\n"
                        f"💰 Summa: {amount} so'm\\n\\n"
                        "To'lovingiz admin tomonidan tasdiqlanmadi."
                    )
                )
            except Exception as e:
                print(f"Reject notification error: {e}")

            # Admin xabarini yangilash
            first_name_display = first_name or "Noma'lum"
            await query.message.edit_text(
                "❌ PREMIUM TO'LOVI RAD ETILDI\\n\\n"
                f"🧾 To'lov ID: #{payment_id}\\n"
                  f"👤 Foydalanuvchi: {first_name_display}\n" 
                f"🆔 ID: {target_id}\\n"
                f"📅 Tarif: {days} kun\\n"
                f"💰 Summa: {amount} so'm"
            )

        except Exception as e:
            print(f"Premium rejection error: {e}")
            await query.message.reply_text(
                "❌ To'lovni rad etishda xatolik yuz berdi."
            )

        return

    if data == "user_info":
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT user_id, first_name, username FROM users ORDER BY created_at DESC LIMIT 20")
        users = cur.fetchall()
        cur.close()
        conn.close()
        text = "👥 Foydalanuvchilar:\n\n"
        for u in users:
            text += f"• {u[1]} - ID: {u[0]}\n"
        await query.message.reply_text(text)
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
        context.user_data.pop('custom_edit_city', None)

        keyboard = ReplyKeyboardMarkup([
            [KeyboardButton("Toshkent"), KeyboardButton("Samarqand")],
            [KeyboardButton("Buxoro"), KeyboardButton("Andijon")],
            [KeyboardButton("Farg'ona"), KeyboardButton("Namangan")],
            [KeyboardButton("Qarshi"), KeyboardButton("Nukus")],
            [KeyboardButton("Xiva"), KeyboardButton("Jizzax")],
            [KeyboardButton("Guliston"), KeyboardButton("Termiz")],
            [KeyboardButton("Navoiy")]
        ], resize_keyboard=True, one_time_keyboard=True)

        await query.message.reply_text(
            "📍 Yangi shahringizni tanlang:",
            reply_markup=keyboard
        )
        return
    
    if data == "edit_photo":
        context.user_data['edit_field'] = 'photo'
        await query.message.reply_text("Yangi rasm yuboring:")
        return
    
    if data.startswith("write_"):
        target_id = int(data.split("_")[1])

        conn = get_db_connection()
        cur = conn.cursor()

        # Premium yoki Match ekanini tekshirish
        cur.execute(
            """
            SELECT EXISTS(
                SELECT 1 FROM users
                WHERE user_id = %s
                AND premium_until IS NOT NULL
                AND premium_until > NOW()
            )
            """,
            (user.id,),
        )
        is_premium = bool(cur.fetchone()[0])

        cur.execute(
            """
            SELECT EXISTS(
                SELECT 1 FROM matches
                WHERE (user1 = %s AND user2 = %s)
                   OR (user1 = %s AND user2 = %s)
            )
            """,
            (user.id, target_id, target_id, user.id),
        )
        is_match = bool(cur.fetchone()[0])

        if not is_premium and not is_match:
            cur.close()
            conn.close()
            await query.message.reply_text(
                "👑 Match bo'lmagan holda yozish faqat Premium uchun."
            )
            return

        cur.execute(
            "SELECT first_name FROM users WHERE user_id = %s",
            (target_id,),
        )
        target = cur.fetchone()

        cur.close()
        conn.close()

        if not target:
            await query.message.reply_text(
                "❌ Foydalanuvchi topilmadi."
            )
            return

        context.user_data["writing_to"] = target_id

        await query.message.reply_text(
            f"✉️ {target[0]} ga yubormoqchi bo'lgan xabaringizni yozing.\n\n"
            "❌ Bekor qilish: /cancel"
        )
        return

    if data.startswith("skip_"):
        await query.message.delete()
        await find(update, context)
        return
    
    if data.startswith("like_"):
        target_id = int(data.split("_")[1])

        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute(
            """
            SELECT EXISTS(
                SELECT 1
                FROM likes
                WHERE from_user = %s
                  AND to_user = %s
            )
            """,
            (user.id, target_id)
        )

        already_liked = bool(cur.fetchone()[0])

        if already_liked:
            cur.close()
            conn.close()

            await query.answer(
                "❤️ Siz allaqachon yoqtirgansiz!",
                show_alert=True
            )
            return

        cur.execute(
            """
            INSERT INTO likes
            (
                from_user,
                to_user
            )
            VALUES (%s, %s)
            """,
            (
                user.id,
                target_id
            )
        )

        cur.execute(
            """
            SELECT first_name, photo
            FROM users
            WHERE user_id = %s
            """,
            (user.id,)
        )

        sender_info = cur.fetchone()

        cur.execute(
            """
            SELECT first_name, photo
            FROM users
            WHERE user_id = %s
            """,
            (target_id,)
        )

        target_info = cur.fetchone()

        if not sender_info or not target_info:
            conn.commit()
            cur.close()
            conn.close()

            await query.message.reply_text(
                "❌ Foydalanuvchi topilmadi."
            )
            return

        sender_name = sender_info[0]
        sender_photo = sender_info[1]

        target_name = target_info[0]
        target_photo = target_info[1]

        cur.execute(
            """
            SELECT EXISTS(
                SELECT 1
                FROM likes
                WHERE from_user = %s
                  AND to_user = %s
            )
            """,
            (
                target_id,
                user.id
            )
        )

        mutual_like = bool(cur.fetchone()[0])

        is_new_match = False

        if mutual_like:

            cur.execute(
                """
                SELECT EXISTS(
                    SELECT 1
                    FROM matches
                    WHERE
                        (user1 = %s AND user2 = %s)
                        OR
                        (user1 = %s AND user2 = %s)
                )
                """,
                (
                    user.id,
                    target_id,
                    target_id,
                    user.id
                )
            )

            match_exists = bool(cur.fetchone()[0])

            if not match_exists:

                cur.execute(
                    """
                    INSERT INTO matches
                    (
                        user1,
                        user2
                    )
                    VALUES (%s, %s)
                    """,
                    (
                        user.id,
                        target_id
                    )
                )

                is_new_match = True

        conn.commit()
        cur.close()
        conn.close()

        if is_new_match:

            await notify_new_match(
                context.bot,
                user.id,
                sender_name,
                sender_photo,
                target_id,
                target_name,
                target_photo
            )

            await query.answer(
                "🎉 MATCH!",
                show_alert=False
            )

        else:

            await notify_like(
                context.bot,
                target_id,
                user.id,
                sender_name,
                sender_photo
            )

            await query.answer(
                "❤️ Yoqdi!",
                show_alert=False
            )

        try:
            await query.message.delete()
        except Exception:
            pass

        await find(
            update,
            context
        )

        return

async def save_edit(update, context):
    user = update.effective_user
    text = (update.message.text or "").strip()
    field = context.user_data.get("edit_field")

    if not field:
        return

    if field == "name":
        if len(text) < 2 or len(text) > 50:
            await update.message.reply_text(
                "❌ Ism 2-50 ta belgidan iborat bo'lishi kerak."
            )
            return

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "UPDATE users SET first_name = %s WHERE user_id = %s",
            (text, user.id)
        )
        conn.commit()
        cur.close()
        conn.close()

        context.user_data.pop("edit_field", None)

        await update.message.reply_text(
            "✅ Ism yangilandi!",
            reply_markup=await get_main_keyboard()
        )
        return ConversationHandler.END

    if field == "age":
        if not text.isdigit() or not 16 <= int(text) <= 60:
            await update.message.reply_text(
                "❌ Yosh 16-60 oralig'ida bo'lishi kerak."
            )
            return

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "UPDATE users SET age = %s WHERE user_id = %s",
            (int(text), user.id)
        )
        conn.commit()
        cur.close()
        conn.close()

        context.user_data.pop("edit_field", None)

        await update.message.reply_text(
            "✅ Yosh yangilandi!",
            reply_markup=await get_main_keyboard()
        )
        return ConversationHandler.END

    if field == "bio":
        if len(text) < 2 or len(text) > 500:
            await update.message.reply_text(
                "❌ Bio 2-500 ta belgidan iborat bo'lishi kerak."
            )
            return

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "UPDATE users SET bio = %s WHERE user_id = %s",
            (text, user.id)
        )
        conn.commit()
        cur.close()
        conn.close()

        context.user_data.pop("edit_field", None)

        await update.message.reply_text(
            "✅ Bio yangilandi!",
            reply_markup=await get_main_keyboard()
        )
        return ConversationHandler.END

    if field == "city":

        cities = {
            "Toshkent",
            "Samarqand",
            "Buxoro",
            "Andijon",
            "Farg'ona",
            "Namangan",
            "Qarshi",
            "Nukus",
            "Xiva",
            "Jizzax",
            "Guliston",
            "Termiz",
            "Navoiy",
        }

        forbidden_values = {
            "👑 Premium",
            "⚙️ Sozlamalar",
            "👤 Profil",
            "🔍 Qidirish",
            "❤️ Yoqtirganlarim",
            "💞 Matchlarim",
            "🎁 Referal",
            "✏️ Tahrirlash",
        }

        if text in cities:
            conn = get_db_connection()
            cur = conn.cursor()

            cur.execute(
                "UPDATE users SET city = %s WHERE user_id = %s",
                (text, user.id)
            )

            conn.commit()
            cur.close()
            conn.close()

            context.user_data.pop("edit_field", None)
            context.user_data.pop("custom_edit_city", None)

            await update.message.reply_text(
                "✅ Shahar yangilandi!",
                reply_markup=await get_main_keyboard()
            )
            return ConversationHandler.END

        if text == "Boshqa":
            context.user_data["custom_edit_city"] = True

            await update.message.reply_text(
                "📍 Shahringiz nomini yozing:\n\n"
                "Masalan: Qo'qon"
            )
            return

        if not context.user_data.get("custom_edit_city"):
            await update.message.reply_text(
                "❌ Iltimos, shaharni tugmalardan tanlang yoki "
                "«Boshqa» tugmasini bosing."
            )
            return

        if text in forbidden_values:
            await update.message.reply_text(
                "❌ Bu shahar nomi emas.\n"
                "📍 Iltimos, shahringiz nomini yozing."
            )
            return

        if (
            len(text) < 2
            or len(text) > 50
            or any(ch.isdigit() for ch in text)
        ):
            await update.message.reply_text(
                "❌ Noto'g'ri shahar nomi.\n"
                "📍 Masalan: Qo'qon"
            )
            return

        if not any(ch.isalpha() for ch in text):
            await update.message.reply_text(
                "❌ Shahar nomida harflar bo'lishi kerak."
            )
            return

        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute(
            "UPDATE users SET city = %s WHERE user_id = %s",
            (text, user.id)
        )

        conn.commit()
        cur.close()
        conn.close()

        context.user_data.pop("edit_field", None)
        context.user_data.pop("custom_edit_city", None)

        await update.message.reply_text(
            "✅ Shahar yangilandi!",
            reply_markup=await get_main_keyboard()
        )
        return ConversationHandler.END

    context.user_data.pop("edit_field", None)
    context.user_data.pop("custom_edit_city", None)

    await update.message.reply_text(
        "❌ O'zgartirish jarayoni bekor qilindi.",
        reply_markup=await get_main_keyboard()
    )
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
    
    # PostgreSQL ba'zan premium_until qiymatini string ko'rinishida qaytarishi mumkin
    if premium_until:
        try:
            if isinstance(premium_until, str):
                premium_until = datetime.fromisoformat(
                    premium_until.replace("Z", "+00:00")
                )

            if premium_until.tzinfo is not None:
                from datetime import timezone
                now_dt = datetime.now(timezone.utc)
            else:
                now_dt = datetime.now()

            premium_status = "✅" if premium_until > now_dt else "❌"
        except Exception as e:
            print(f"Premium date parsing error: {e}")
            premium_status = "❌"
    else:
        premium_status = "❌"
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

async def referral_panel(update, context):
    user = update.effective_user

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT COUNT(*)
        FROM users
        WHERE referred_by = %s
        """,
        (user.id,)
    )
    count = cur.fetchone()[0]

    cur.execute(
        """
        SELECT premium_until
        FROM users
        WHERE user_id = %s
        """,
        (user.id,)
    )
    row = cur.fetchone()

    cur.close()
    conn.close()

    rewards = [
        (5, 1),
        (10, 7),
        (25, 30),
        (50, 90),
        (100, 365),
    ]

    lines = []

    for required, days in rewards:
        if count >= required:
            status = "✅"
        else:
            status = "🔒"

        lines.append(
            f"{status} {required} ta — {days} kun Premium"
        )

    next_reward = None

    for required, days in rewards:
        if count < required:
            next_reward = (required, days)
            break

    if next_reward:
        required, days = next_reward
        remaining = required - count
        next_text = (
            f"🎯 Keyingi mukofot: {required} ta referal\n"
            f"➡️ Yana {remaining} ta kerak"
        )
    else:
        next_text = "🏆 Barcha referal mukofotlarini oldingiz!"

    username = context.bot.username

    link = (
        f"https://t.me/{username}?start=ref_{user.id}"
    )

    text = (
        "🎁 REFERAL DASTURI\n\n"
        f"👥 Sizning referallaringiz: {count} ta\n\n"
        "🏆 MUKOFOTLAR:\n"
        + "\n".join(lines)
        + "\n\n"
        + next_text
        + "\n\n"
        "🔗 SIZNING REFERAL HAVOLANGIZ:\n"
        f"{link}\n\n"
        "📤 Havolani do'stlaringizga yuboring!\n"
        "Do'stingiz profil yaratishni tugatsa, referal hisoblanadi."
    )

    await update.message.reply_text(text)


async def update_last_active(user_id):
    """
    Foydalanuvchi bot bilan har qanday faol interaction
    qilganda last_active yangilanadi.
    """

    try:
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute(
            """
            UPDATE users
            SET last_active = NOW()
            WHERE user_id = %s
            """,
            (user_id,)
        )

        conn.commit()
        cur.close()
        conn.close()

    except Exception as e:
        print(
            f"⚠️ last_active yangilash xatosi: {e}"
        )


async def activity_message_handler(update, context):
    """
    Har qanday oddiy message kelganda activityni yangilaydi.
    """

    if update.effective_user:
        await update_last_active(
            update.effective_user.id
        )


async def activity_callback_handler(update, context):
    """
    Har qanday tugma bosilganda activityni yangilaydi.
    """

    if update.effective_user:
        await update_last_active(
            update.effective_user.id
        )


async def handle_message(update, context):
    text = update.message.text

    # Premium foydalanuvchi profil egasiga xabar yozmoqda
    if "writing_to" in context.user_data:
        target_id = context.user_data["writing_to"]
        sender = update.effective_user

        if text == "/cancel":
            context.user_data.pop("writing_to", None)
            await update.message.reply_text(
                "❌ Xabar yuborish bekor qilindi."
            )
            return

        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute(
            "SELECT premium_until FROM users WHERE user_id = %s",
            (sender.id,)
        )
        row = cur.fetchone()

        is_premium = (
            row
            and row[0] is not None
            and row[0] > datetime.now()
        )

        if not is_premium:
            context.user_data.pop("writing_to", None)
            cur.close()
            conn.close()

            await update.message.reply_text(
                "❌ Premium muddati tugagan."
            )
            return

        cur.execute(
            """
            INSERT INTO messages (from_user, to_user, text)
            VALUES (%s, %s, %s)
            """,
            (sender.id, target_id, text)
        )

        cur.execute(
            "SELECT first_name FROM users WHERE user_id = %s",
            (target_id,)
        )
        target = cur.fetchone()

        conn.commit()
        cur.close()
        conn.close()

        context.user_data.pop("writing_to", None)

        if not target:
            await update.message.reply_text(
                "❌ Foydalanuvchi topilmadi."
            )
            return

        try:
            await context.bot.send_message(
                chat_id=target_id,
                text=(
                    "💌 Sizga SaraMatch'dan yangi xabar!\n\n"
                    f"👤 {sender.first_name}:\n"
                    f"{text}"
                )
            )

            await update.message.reply_text(
                "✅ Xabaringiz yuborildi!"
            )

        except Exception:
            await update.message.reply_text(
                "⚠️ Xabarni yetkazib bo'lmadi. "
                "Foydalanuvchi botni bloklagan bo'lishi mumkin."
            )

        return


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
    elif text == "🎁 Referal":
        await referral_panel(update, context)

    elif text == "👑 Premium":
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("1 hafta - 30 571 so'm", callback_data="premium_1w")],
            [InlineKeyboardButton("1 oy - 63 429 so'm ⭐️", callback_data="premium_1m")],
            [InlineKeyboardButton("3 oy - 137 714 so'm", callback_data="premium_3m")],
            [InlineKeyboardButton("1 yil - 282 000 so'm", callback_data="premium_1y")]
        ])
        await update.message.reply_text("👑 PREMIUM\n\nMuddatni tanlang:", reply_markup=keyboard)


async def givepremium(update, context):
    """Admin foydalanuvchiga qo'lda Premium beradi."""
    user = update.effective_user

    if user.id != ADMIN_ID:
        await update.message.reply_text("⛔ Siz admin emassiz!")
        return

    if len(context.args) != 2:
        await update.message.reply_text(
            "❌ Format:\n"
            "/givepremium USER_ID KUN\n\n"
            "Masalan:\n"
            "/givepremium 5634936318 30"
        )
        return

    try:
        target_id = int(context.args[0])
        days = int(context.args[1])

        if days <= 0:
            await update.message.reply_text(
                "❌ Kun soni 0 dan katta bo'lishi kerak."
            )
            return

        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute(
            """
            SELECT first_name, premium_until
            FROM users
            WHERE user_id = %s
            """,
            (target_id,)
        )
        target = cur.fetchone()

        if not target:
            cur.close()
            conn.close()
            await update.message.reply_text(
                f"❌ Foydalanuvchi topilmadi.\nID: {target_id}"
            )
            return

        old_until = target[1]

        cur.execute(
            """
            UPDATE users
            SET premium_until =
                CASE
                    WHEN premium_until IS NOT NULL
                         AND premium_until > NOW()
                    THEN premium_until + (%s * INTERVAL '1 day')
                    ELSE NOW() + (%s * INTERVAL '1 day')
                END
            WHERE user_id = %s
            """,
            (days, days, target_id)
        )

        cur.execute(
            "SELECT premium_until FROM users WHERE user_id = %s",
            (target_id,)
        )
        new_until = cur.fetchone()[0]

        save_premium_history(
            cur,
            target_id,
            action="add",
            days=days,
            source="admin",
            admin_id=user.id,
            old_premium_until=old_until,
            new_premium_until=new_until
        )

        conn.commit()

        cur.close()
        conn.close()

        await update.message.reply_text(
            "✅ PREMIUM BERILDI\n\n"
            f"👤 Foydalanuvchi: {target[0]}\n"
            f"🆔 ID: {target_id}\n"
            f"👑 Qo'shilgan: {days} kun\n"
            f"📅 Premiumgacha: {new_until.strftime('%d.%m.%Y %H:%M')}"
        )

        try:
            await context.bot.send_message(
                chat_id=target_id,
                text=(
                    "👑 PREMIUM FAOLLASHTIRILDI!\n\n"
                    f"🎁 Sizga {days} kun Premium berildi.\n"
                    f"📅 Amal qilish muddati: "
                    f"{new_until.strftime('%d.%m.%Y %H:%M')}"
                )
            )
        except Exception as e:
            print(f"Premium notification error: {e}")

    except ValueError:
        await update.message.reply_text(
            "❌ USER_ID va KUN son bo'lishi kerak.\n\n"
            "Masalan:\n"
            "/givepremium 5634936318 30"
        )
    except Exception as e:
        print(f"Give premium error: {e}")
        await update.message.reply_text(
            "❌ Premium berishda xatolik yuz berdi."
        )


async def removepremium(update, context):
    """Admin foydalanuvchining Premiumini bekor qiladi."""
    user = update.effective_user

    if user.id != ADMIN_ID:
        await update.message.reply_text("⛔ Siz admin emassiz!")
        return

    if len(context.args) != 1:
        await update.message.reply_text(
            "❌ Format:\n"
            "/removepremium USER_ID\n\n"
            "Masalan:\n"
            "/removepremium 5634936318"
        )
        return

    try:
        target_id = int(context.args[0])

        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute(
            """
            SELECT first_name, premium_until
            FROM users
            WHERE user_id = %s
            """,
            (target_id,)
        )
        target = cur.fetchone()

        if not target:
            cur.close()
            conn.close()
            await update.message.reply_text(
                f"❌ Foydalanuvchi topilmadi.\nID: {target_id}"
            )
            return

        old_until = target[1]

        cur.execute(
            """
            UPDATE users
            SET premium_until = NULL
            WHERE user_id = %s
            """,
            (target_id,)
        )

        save_premium_history(
            cur,
            target_id,
            action="remove",
            days=0,
            source="admin",
            admin_id=user.id,
            old_premium_until=old_until,
            new_premium_until=None
        )

        conn.commit()

        cur.close()
        conn.close()

        await update.message.reply_text(
            "✅ PREMIUM BEKOR QILINDI\n\n"
            f"👤 Foydalanuvchi: {target[0]}\n"
            f"🆔 ID: {target_id}\n"
            "👑 Premium: ❌"
        )

        try:
            await context.bot.send_message(
                chat_id=target_id,
                text=(
                    "ℹ️ Premium obunangiz admin tomonidan bekor qilindi."
                )
            )
        except Exception as e:
            print(f"Premium revoke notification error: {e}")

    except ValueError:
        await update.message.reply_text(
            "❌ USER_ID son bo'lishi kerak.\n\n"
            "Masalan:\n"
            "/removepremium 5634936318"
        )
    except Exception as e:
        print(f"Remove premium error: {e}")
        await update.message.reply_text(
            "❌ Premiumni bekor qilishda xatolik yuz berdi."
        )

async def admin(update, context):
    user = update.effective_user

    if user.id != ADMIN_ID:
        await update.message.reply_text("⛔ Siz admin emassiz!")
        return

    conn = get_db_connection()
    cur = conn.cursor()

    try:
        cur.execute("SELECT COUNT(*) FROM users")
        total_users = cur.fetchone()[0]

        cur.execute("""
            SELECT COUNT(*)
            FROM users
            WHERE is_active = TRUE
        """)
        active_users = cur.fetchone()[0]

        cur.execute("""
            SELECT COUNT(*)
            FROM users
            WHERE premium_until IS NOT NULL
              AND premium_until > NOW()
        """)
        premium_users = cur.fetchone()[0]

        cur.execute("""
            SELECT COUNT(*)
            FROM users
            WHERE created_at >= CURRENT_DATE
        """)
        today_users = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM likes")
        total_likes = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM matches")
        total_matches = cur.fetchone()[0]

        cur.execute("""
            SELECT COUNT(*)
            FROM users
            WHERE referred_by IS NOT NULL
        """)
        referral_users = cur.fetchone()[0]

    finally:
        cur.close()
        conn.close()

    text = (
        "📊 ADMIN PANEL\n\n"
        f"👥 Jami foydalanuvchilar: {total_users}\n"
        f"🟢 Aktiv foydalanuvchilar: {active_users}\n"
        f"👑 Premium foydalanuvchilar: {premium_users}\n"
        f"🆕 Bugun qo'shilganlar: {today_users}\n\n"
        f"❤️ Jami like: {total_likes}\n"
        f"💞 Jami match: {total_matches}\n\n"
        f"🎁 Referral orqali kelganlar: {referral_users}"
    )

    await update.message.reply_text(text)




async def premiumlist(update, context):
    """Admin uchun hozirgi Premium foydalanuvchilar ro'yxati."""
    user = update.effective_user

    if user.id != ADMIN_ID:
        await update.message.reply_text("⛔ Siz admin emassiz!")
        return

    conn = get_db_connection()
    cur = conn.cursor()

    try:
        cur.execute("""
            SELECT
                user_id,
                first_name,
                username,
                age,
                gender,
                city,
                premium_until
            FROM users
            WHERE premium_until IS NOT NULL
              AND premium_until > NOW()
            ORDER BY premium_until DESC
        """)

        rows = cur.fetchall()

    finally:
        cur.close()
        conn.close()

    if not rows:
        await update.message.reply_text(
            "👑 Hozirda aktiv Premium foydalanuvchilar yo'q."
        )
        return

    text = f"👑 PREMIUM FOYDALANUVCHILAR: {len(rows)} ta\n\n"

    for i, row in enumerate(rows, 1):
        user_id, first_name, username, age, gender, city, premium_until = row

        text += (
            f"{i}. 👤 {first_name}, {age}\n"
            f"🆔 ID: {user_id}\n"
            f"📱 @{username or 'yo‘q'}\n"
            f"👤 {gender}\n"
            f"📍 {city}\n"
            f"📅 Premiumgacha: "
            f"{premium_until.strftime('%d.%m.%Y %H:%M')}\n\n"
        )

    await update.message.reply_text(text)

async def checkpremium(update, context):
    user = update.effective_user

    if user.id != ADMIN_ID:
        await update.message.reply_text("⛔ Siz admin emassiz!")
        return

    if not context.args:
        await update.message.reply_text(
            "❗ Foydalanish:\n"
            "/checkpremium TELEGRAM_ID\n\n"
            "Masalan:\n"
            "/checkpremium 5634936318"
        )
        return

    try:
        target_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("❌ Telegram ID noto‘g‘ri.")
        return

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT user_id, first_name, username, city, premium_until
        FROM users
        WHERE user_id = %s
        """,
        (target_id,)
    )

    data = cur.fetchone()
    cur.close()
    conn.close()

    if not data:
        await update.message.reply_text(
            f"❌ {target_id} ID bilan foydalanuvchi topilmadi."
        )
        return

    user_id, first_name, username, city, premium_until = data

    premium_active = False

    if premium_until:
        try:
            if isinstance(premium_until, str):
                premium_until = datetime.fromisoformat(
                    premium_until.replace("Z", "+00:00")
                )

            now = (
                datetime.now(premium_until.tzinfo)
                if premium_until.tzinfo
                else datetime.now()
            )

            premium_active = premium_until > now

        except Exception:
            premium_active = False

    status = "✅ FAOL" if premium_active else "❌ FAOL EMAS"

    premium_date = (
        premium_until.strftime("%d.%m.%Y %H:%M")
        if premium_until else "Yo‘q"
    )

    await update.message.reply_text(
        f"🔎 PREMIUM TEKSHIRUVI\n\n"
        f"👤 Ism: {first_name}\n"
        f"🆔 ID: {user_id}\n"
        f"👤 Username: @{username if username else 'yo‘q'}\n"
        f"📍 Shahar: {city or 'Kiritilmagan'}\n\n"
        f"👑 Premium: {status}\n"
        f"📅 Premiumgacha: {premium_date}"
    )

async def premiumhistory(update, context):
    """Admin uchun foydalanuvchining Premium tarixini ko'rsatadi."""
    user = update.effective_user

    if user.id != ADMIN_ID:
        await update.message.reply_text("⛔ Siz admin emassiz!")
        return

    if len(context.args) != 1:
        await update.message.reply_text(
            "❗ Foydalanish:\n"
            "/premiumhistory USER_ID\n\n"
            "Masalan:\n"
            "/premiumhistory 5634936318"
        )
        return

    try:
        target_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("❌ USER_ID noto'g'ri.")
        return

    conn = get_db_connection()
    cur = conn.cursor()

    try:
        cur.execute(
            """
            SELECT first_name, username
            FROM users
            WHERE user_id = %s
            """,
            (target_id,)
        )
        target = cur.fetchone()

        if not target:
            await update.message.reply_text(
                f"❌ Foydalanuvchi topilmadi.\n🆔 ID: {target_id}"
            )
            return

        cur.execute(
            """
            SELECT
                action,
                days,
                source,
                admin_id,
                old_premium_until,
                new_premium_until,
                created_at
            FROM premium_history
            WHERE user_id = %s
            ORDER BY created_at DESC
            LIMIT 30
            """,
            (target_id,)
        )

        rows = cur.fetchall()

    finally:
        cur.close()
        conn.close()

    if not rows:
        await update.message.reply_text(
            "👑 PREMIUM TARIXI\n\n"
            f"👤 {target[0]}\n"
            f"🆔 ID: {target_id}\n\n"
            "📭 Premium tarixi mavjud emas."
        )
        return

    text = (
        "👑 PREMIUM TARIXI\n\n"
        f"👤 {target[0]}\n"
        f"📱 @{target[1] or 'yo‘q'}\n"
        f"🆔 ID: {target_id}\n\n"
    )

    for i, row in enumerate(rows, 1):
        action, days, source, admin_id, old_until, new_until, created_at = row

        if action == "remove":
            action_text = "❌ Premium bekor qilindi"
        else:
            action_text = f"✅ +{days} kun Premium"

        if source == "referral":
            source_text = "🎁 Referral"
        elif source == "admin":
            source_text = "👮 Admin"
        elif source == "approve":
            source_text = "💳 Approve"
        else:
            source_text = f"📌 {source}"

        created_text = (
            created_at.strftime("%d.%m.%Y %H:%M")
            if created_at else "Noma'lum"
        )

        old_text = (
            old_until.strftime("%d.%m.%Y %H:%M")
            if old_until else "Yo‘q"
        )

        new_text = (
            new_until.strftime("%d.%m.%Y %H:%M")
            if new_until else "Yo‘q"
        )

        text += (
            f"{i}. {action_text}\n"
            f"📌 Manba: {source_text}\n"
            f"📅 Amal vaqti: {created_text}\n"
            f"⏮ Eski Premium: {old_text}\n"
            f"⏭ Yangi Premium: {new_text}\n"
        )

        if admin_id:
            text += f"👮 Admin ID: {admin_id}\n"

        text += "\n"

    await update.message.reply_text(text)



async def premiumstats(update, context):
    """Admin uchun umumiy Premium statistikasi."""
    user = update.effective_user

    if user.id != ADMIN_ID:
        await update.message.reply_text("⛔ Siz admin emassiz!")
        return

    conn = get_db_connection()
    cur = conn.cursor()

    try:
        cur.execute("""
            SELECT COUNT(*)
            FROM users
            WHERE premium_until IS NOT NULL
              AND premium_until > NOW()
        """)
        active_premium = cur.fetchone()[0]

        cur.execute("""
            SELECT COUNT(*)
            FROM premium_history
            WHERE action = 'add'
              AND source = 'payment'
        """)
        payment_count = cur.fetchone()[0]

        cur.execute("""
            SELECT COUNT(*)
            FROM premium_history
            WHERE action = 'add'
              AND source = 'admin'
        """)
        admin_count = cur.fetchone()[0]

        cur.execute("""
            SELECT COUNT(*)
            FROM premium_history
            WHERE action = 'add'
              AND source = 'referral'
        """)
        referral_count = cur.fetchone()[0]

        cur.execute("""
            SELECT COUNT(*)
            FROM premium_history
            WHERE action = 'remove'
        """)
        removed_count = cur.fetchone()[0]

        cur.execute("""
            SELECT COUNT(*)
            FROM premium_history
        """)
        total_history = cur.fetchone()[0]

    finally:
        cur.close()
        conn.close()

    text = (
        "📊 PREMIUM STATISTIKA\n\n"
        f"👑 Aktiv Premium: {active_premium} ta\n\n"
        f"💳 To‘lov orqali: {payment_count} ta\n"
        f"👮 Admin orqali: {admin_count} ta\n"
        f"🎁 Referral orqali: {referral_count} ta\n"
        f"❌ Bekor qilingan: {removed_count} ta\n\n"
        f"📚 Jami tarix yozuvlari: {total_history} ta"
    )

    await update.message.reply_text(text)


async def approve(update, context):
    user = update.effective_user
    if user.id != ADMIN_ID:
        await update.message.reply_text("⛔ Siz admin emassiz!")
        return
    try:
        parts = update.message.text.split()
        user_id = int(parts[1])
        days = int(parts[2])
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute(
            "SELECT premium_until FROM users WHERE user_id = %s",
            (user_id,)
        )
        row = cur.fetchone()

        if not row:
            cur.close()
            conn.close()
            await update.message.reply_text("❌ Foydalanuvchi topilmadi.")
            return

        old_until = row[0]

        if old_until is not None and old_until > datetime.now():
            premium_until = old_until + timedelta(days=days)
        else:
            premium_until = datetime.now() + timedelta(days=days)

        cur.execute(
            "UPDATE users SET premium_until = %s WHERE user_id = %s",
            (premium_until, user_id)
        )

        save_premium_history(
            cur,
            user_id,
            action="add",
            days=days,
            source="approve",
            admin_id=user.id,
            old_premium_until=old_until,
            new_premium_until=premium_until
        )

        conn.commit()
        cur.close()
        conn.close()
        await update.message.reply_text(f"✅ Premium tasdiqlandi! {days} kun")
    except:
        await update.message.reply_text("❌ Format: /approve USER_ID KUNLAR")

async def block_user(update, context):
    user = update.effective_user
    if user.id != ADMIN_ID:
        await update.message.reply_text("⛔ Siz admin emassiz!")
        return
    try:
        parts = update.message.text.split()
        user_id = int(parts[1])
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("UPDATE users SET is_active = FALSE, is_blocked = TRUE WHERE user_id = %s", (user_id,))
        conn.commit()
        cur.close()
        conn.close()
        await update.message.reply_text(f"🚫 Foydalanuvchi bloklandi: {user_id}")
    except:
        await update.message.reply_text("❌ Format: /block USER_ID")

async def unblock_user(update, context):
    user = update.effective_user
    if user.id != ADMIN_ID:
        await update.message.reply_text("⛔ Siz admin emassiz!")
        return
    try:
        parts = update.message.text.split()
        user_id = int(parts[1])
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("UPDATE users SET is_active = TRUE, is_blocked = FALSE WHERE user_id = %s", (user_id,))
        conn.commit()
        cur.close()
        conn.close()
        await update.message.reply_text(f"✅ Foydalanuvchi blokdan chiqarildi: {user_id}")
    except:
        await update.message.reply_text("❌ Format: /unblock USER_ID")

async def block_user(update, context):
    user = update.effective_user
    if user.id != ADMIN_ID:
        await update.message.reply_text("⛔ Siz admin emassiz!")
        return
    try:
        parts = update.message.text.split()
        user_id = int(parts[1])
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("UPDATE users SET is_active = FALSE, is_blocked = TRUE WHERE user_id = %s", (user_id,))
        conn.commit()
        cur.close()
        conn.close()
        await update.message.reply_text(f"🚫 Foydalanuvchi bloklandi: {user_id}")
    except:
        await update.message.reply_text("❌ Format: /block USER_ID")

async def unblock_user(update, context):
    user = update.effective_user
    if user.id != ADMIN_ID:
        await update.message.reply_text("⛔ Siz admin emassiz!")
        return
    try:
        parts = update.message.text.split()
        user_id = int(parts[1])
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("UPDATE users SET is_active = TRUE, is_blocked = FALSE WHERE user_id = %s", (user_id,))
        conn.commit()
        cur.close()
        conn.close()
        await update.message.reply_text(f"✅ Foydalanuvchi blokdan chiqarildi: {user_id}")
    except:
        await update.message.reply_text("❌ Format: /unblock USER_ID")

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
    flask_app = Flask(__name__)
    
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
            LANGUAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_language)],
            AGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_age)],
            GENDER: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_gender)],
            CITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_city)],
            BIO: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_bio)],
            PHOTO: [MessageHandler(filters.PHOTO, get_photo)],
        },
        fallbacks=[],
    )
    
    # =========================================================
    # USER ACTIVITY TRACKING
    # Retention tizimi uchun last_active yangilanadi.
    # -1 guruhda ishlaydi, shuning uchun boshqa handlerlardan
    # oldin bajariladi.
    # =========================================================
    app.add_handler(
        MessageHandler(
            filters.ALL,
            activity_message_handler
        ),
        group=-1
    )

    app.add_handler(
        CallbackQueryHandler(
            activity_callback_handler
        ),
        group=-1
    )

    app.add_handler(conv_handler)
    app.add_handler(CommandHandler("admin", admin))
    app.add_handler(CommandHandler("givepremium", givepremium))
    app.add_handler(CommandHandler("removepremium", removepremium))

    app.add_handler(CommandHandler("checkpremium", checkpremium))
    app.add_handler(CommandHandler("premiumlist", premiumlist))
    app.add_handler(CommandHandler("premiumhistory", premiumhistory))
    app.add_handler(CommandHandler("premiumstats", premiumstats))
    app.add_handler(CommandHandler("approve", approve))
    app.add_handler(CommandHandler("broadcast", broadcast))
    app.add_handler(CommandHandler("find", find))
    app.add_handler(CommandHandler("profile", profile))
    app.add_handler(CommandHandler("likes", likes))
    app.add_handler(CommandHandler("matches", matches))
    app.add_handler(CommandHandler("settings", settings))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(handle_callback))
    
    # =========================================================
    # RETENTION NOTIFICATION JOB
    # =========================================================
    # Har 24 soatda bir marta tekshiradi.
    # Birinchi ishga tushish bot startidan 60 soniya keyin.
    if app.job_queue:
        app.job_queue.run_repeating(
            retention_job,
            interval=86400,
            first=60,
            name="retention_notifications"
        )
        print("✅ Retention notification job yoqildi!")
    else:
        print("⚠️ JobQueue mavjud emas!")

    print("Dating bot ishga tushdi...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()

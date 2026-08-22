from datetime import datetime

import os
import psycopg2

from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from telegram.error import Forbidden


def get_db_connection():
    database_url = os.environ.get("DATABASE_URL")

    if not database_url:
        raise RuntimeError("DATABASE_URL topilmadi")

    return psycopg2.connect(database_url)


def notification_already_sent(
    user_id,
    notification_type,
    reference_id=None,
    hours=24
):
    conn = get_db_connection()
    cur = conn.cursor()

    if reference_id is None:
        cur.execute(
            """
            SELECT EXISTS(
                SELECT 1
                FROM notification_logs
                WHERE user_id = %s
                  AND notification_type = %s
                  AND created_at >= NOW() - (%s * INTERVAL '1 hour')
            )
            """,
            (user_id, notification_type, hours)
        )
    else:
        cur.execute(
            """
            SELECT EXISTS(
                SELECT 1
                FROM notification_logs
                WHERE user_id = %s
                  AND notification_type = %s
                  AND reference_id = %s
            )
            """,
            (user_id, notification_type, reference_id)
        )

    result = cur.fetchone()[0]

    cur.close()
    conn.close()

    return bool(result)


def save_notification(
    user_id,
    notification_type,
    reference_id=None
):
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO notification_logs
        (
            user_id,
            notification_type,
            reference_id
        )
        VALUES (%s, %s, %s)
        """,
        (
            user_id,
            notification_type,
            reference_id
        )
    )

    conn.commit()
    cur.close()
    conn.close()




# =========================================================
# DAM OLISH KUNLARI PREMIUM KAMPANIYASI
# FAQAT 2026-08-22 VA 2026-08-23
# Toshkent vaqti bilan:
# 22-avgust 14:00
# 23-avgust 14:00, 20:00, 22:00
# =========================================================

async def weekend_premium_campaign(context):
    """
    Faqat shu hafta oxiri uchun bir martalik kampaniya.
    Free + Premium barcha faol foydalanuvchilarga yuboriladi.
    Har bir kampaniya vaqti uchun foydalanuvchiga faqat 1 marta.
    """

    bot = context.bot
    campaign_id = context.job.data

    # notification_logs.reference_id BIGINT bo‘lgani uchun
    # kampaniya ID'sini raqamli ko‘rinishga o'tkazamiz.
    campaign_reference_id = int(
        str(campaign_id).replace("-", "").replace("_", "")
    )

    campaigns = {
        "2026-08-22_14": (
            "🔥 DAM OLISH KUNLARI — PREMIUM -30%! "
            "💎 Premium bilan o‘zingizga mos insonni tez va oson toping! "
            "💬 Match kutmang! Vaqtingizni tejang — "
            "yoqqan profilingizga to‘g‘ridan-to‘g‘ri Telegram chat orqali yozing. "
            "♾️ Cheksiz profil ko‘rish "
            "❤️ Cheksiz Like "
            "👀 Sizni yoqtirganlarni ko‘rish "
            "⭐ Premium belgisi "
            "🚀 Profil ustuvorligi "
            "🎁 BONUS: Super Like — BEPUL! "
            "⏳ Faqat shu hafta oxiri — 30% chegirma! "
            "👉 Premiumni hoziroq oling!"
        ),
        "2026-08-23_14": (
            "🔥 PREMIUM -30% — CHEGIRMA DAVOM ETMOQDA! "
            "💎 Premium bilan o‘zingizga mos insonni tez va oson toping! "
            "💬 Match kutmang! Vaqtingizni tejang — "
            "yoqqan profilingizga to‘g‘ridan-to‘g‘ri Telegram chat orqali yozing. "
            "♾️ Cheksiz profil ko‘rish "
            "❤️ Cheksiz Like "
            "👀 Sizni yoqtirganlarni ko‘rish "
            "🎁 Super Like — BEPUL! "
            "⏳ Chegirma faqat shu hafta oxirigacha! "
            "👉 Premiumni hoziroq oling!"
        ),
        "2026-08-23_20": (
            "⏳ PREMIUM -30% — YANA 4 SOAT! "
            "💎 O‘zingizga mos insonni tez va oson toping. "
            "💬 Match kutmang! Vaqtingizni tejang — "
            "yoqqan profilingizga to‘g‘ridan-to‘g‘ri Telegram chat orqali yozing. "
            "🎁 Super Like — BEPUL! "
            "♾️ Cheksiz profil ko‘rish "
            "❤️ Cheksiz Like "
            "🔥 Premiumga hozir -30% chegirma bilan ega bo‘ling!"
        ),
        "2026-08-22_22": (
            "🔥 PREMIUM -30% — BUGUN FAQAT 22:00! "
            "💎 O‘zingizga mos insonni tez va oson toping. "
            "💬 Match kutmang! Yoqqan profilingizga "
            "to‘g‘ridan-to‘g‘ri Telegram chat orqali yozing. "
            "🎁 Super Like — BEPUL! "
            "♾️ Cheksiz profil ko‘rish "
            "❤️ Cheksiz Like "
            "⏰ Chegirma faqat hafta oxirida! "
            "👉 Premiumni hoziroq oling!"
        ),
        "2026-08-23_22": (
            "🚨 OXIRGI 2 SOAT! "
            "🔥 Premium -30% chegirma bilan — faqat bugun! "
            "💎 O‘zingizga mos insonni tez va oson toping. "
            "💬 Match kutmang! Yoqqan profilingizga "
            "to‘g‘ridan-to‘g‘ri Telegram chat orqali yozing. "
            "🎁 Super Like — BEPUL! "
            "♾️ Cheksiz profil ko‘rish "
            "❤️ Cheksiz Like "
            "⏰ 22:00 dan keyin chegirma tugaydi! "
            "👉 Oxirgi imkoniyat — Premiumni hoziroq oling!"
        ),
    }

    text = campaigns.get(campaign_id)

    if not text:
        print(f"⚠️ Noma'lum weekend kampaniya: {campaign_id}")
        return

    reference_id = f"weekend_premium_{campaign_id}"

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT user_id
        FROM users
        WHERE is_active = TRUE
        """
    )

    users = cur.fetchall()
    cur.close()
    conn.close()

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "👑 Premiumni olish — 30% chegirma",
                callback_data="weekend_premium_buy"
            )
        ]
    ])

    sent_count = 0
    skipped_count = 0

    for row in users:
        user_id = row[0]

        if notification_already_sent(
            user_id,
            "weekend_premium_campaign",
            reference_id=campaign_reference_id
        ):
            skipped_count += 1
            continue

        sent = await safe_send_message(
            bot,
            user_id,
            text,
            keyboard
        )

        if sent:
            save_notification(
                user_id,
                "weekend_premium_campaign",
                campaign_reference_id
            )
            sent_count += 1

    print(
        f"🔥 Weekend Premium {campaign_id}: "
        f"{sent_count} ta yuborildi, {skipped_count} ta o'tkazib yuborildi."
    )


async def safe_send_message(
    bot,
    user_id,
    text,
    reply_markup=None
):
    try:
        await bot.send_message(
            chat_id=user_id,
            text=text,
            reply_markup=reply_markup
        )
        return True

    except Forbidden:
        print(f"🚫 User blocked bot, deactivating: {user_id}")

        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute(
                "UPDATE users SET is_active = FALSE WHERE user_id = %s",
                (user_id,)
            )
            conn.commit()
            cur.close()
            conn.close()
        except Exception as db_error:
            print(
                f"❌ Could not deactivate blocked user "
                f"{user_id}: {db_error}"
            )

        return False

    except Exception as e:
        print(
            f"Notification error | user={user_id} | {e}"
        )
        return False


# =========================================================
# LIKE
# =========================================================

async def notify_like(
    bot,
    to_user_id,
    from_user_id,
    from_user_name,
    from_user_photo=None
):
    if notification_already_sent(
        to_user_id,
        "like",
        from_user_id,
        hours=24 * 30
    ):
        return

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "👀 Profilini ko‘rish",
                callback_data=f"view_profile_{from_user_id}"
            )
        ]
    ])

    text = (
        "💕 Sizni kimdir yoqtirdi!\n\n"
        f"👤 {from_user_name}\n\n"
        "👀 Kim ekanini ko‘rish"
    )

    try:
        if from_user_photo:
            await bot.send_photo(
                chat_id=to_user_id,
                photo=from_user_photo,
                caption=text,
                reply_markup=keyboard
            )
        else:
            await bot.send_message(
                chat_id=to_user_id,
                text=text,
                reply_markup=keyboard
            )

        save_notification(
            to_user_id,
            "like",
            from_user_id
        )

    except Forbidden:
        print(f"🚫 Like recipient blocked bot: {to_user_id}")

        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute(
                "UPDATE users SET is_active = FALSE WHERE user_id = %s",
                (to_user_id,)
            )
            conn.commit()
            cur.close()
            conn.close()
        except Exception as db_error:
            print(
                f"❌ Could not deactivate blocked like recipient "
                f"{to_user_id}: {db_error}"
            )

    except Exception as e:
        print(f"Like notification error: {e}")


# =========================================================
# MATCH
# =========================================================

async def notify_new_match(
    bot,
    user1_id,
    user1_name,
    user1_photo,
    user2_id,
    user2_name,
    user2_photo
):
    def get_user_info(user_id):
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute(
            """
            SELECT
                first_name,
                age,
                city,
                username,
                premium_until,
                language
            FROM users
            WHERE user_id = %s
            """,
            (user_id,)
        )

        row = cur.fetchone()
        cur.close()
        conn.close()

        if not row:
            return {
                "name": "Foydalanuvchi",
                "age": None,
                "city": None,
                "username": None,
                "premium": False,
                "language": "uz",
            }

        name, age, city, username, premium_until, language = row

        if username:
            username = str(username).strip().lstrip("@")

        premium = bool(
            premium_until is not None
            and premium_until > datetime.now()
        )

        return {
            "name": name or "Foydalanuvchi",
            "age": age,
            "city": city,
            "username": username,
            "premium": premium,
            "language": language or "uz",
        }

    def build_text(recipient, target):
        lang = recipient["language"]

        if lang == "ru":
            text = (
                "🎉 MATCH! ❤️\n\n"
                "Вы понравились друг другу!\n\n"
                f"👤 {target['name']}"
            )

            if target["age"]:
                text += f", {target['age']}"

            if target["city"]:
                text += f"\n📍 {target['city']}"

            text += "\n\n💬 Начните общение прямо сейчас."

            if recipient["premium"]:
                text += (
                    "\n\n👑 Вы Premium!\n"
                    "📨 Вы также можете написать этому человеку "
                    "в личный Telegram.\n"
                    "💡 Такой способ связи может привлечь больше внимания "
                    "и повысить шанс получить ответ."
                )
            else:
                text += (
                    "\n\n👑 Хотите больше шансов на общение?\n"
                    "📨 С Premium вы сможете писать прямо в личный "
                    "Telegram собеседника.\n"
                    "🔥 Это поможет привлечь больше внимания и увеличить "
                    "шанс получить ответ."
                )

            return text

        if lang == "uz_cyr":
            text = (
                "🎉 МАТЧ! ❤️\n\n"
                "Сизлар бир-бирингизга ёқдингиз!\n\n"
                f"👤 {target['name']}"
            )

            if target["age"]:
                text += f", {target['age']} ёш"

            if target["city"]:
                text += f"\n📍 {target['city']}"

            text += "\n\n💬 Ҳозироқ суҳбатни бошланг."

            if recipient["premium"]:
                text += (
                    "\n\n👑 Сиз Premiumсиз!\n"
                    "📨 Суҳбатдошингизга Telegram шахсий чати орқали "
                    "ҳам ёзишингиз мумкин.\n"
                    "💡 Бу хабарингизга кўпроқ эътибор қаратилиши ва "
                    "жавоб олиш эҳтимолини ошириши мумкин."
                )
            else:
                text += (
                    "\n\n👑 Кўпроқ имконият хоҳлайсизми?\n"
                    "📨 Premium билан Telegram шахсий чатига тўғридан-тўғри "
                    "ёзишингиз мумкин.\n"
                    "🔥 Бу кўпроқ эътибор ва жавоб олиш эҳтимолини ошириши мумкин."
                )

            return text

        text = (
            "🎉 MATCH! ❤️\n\n"
            "Sizlar bir-biringizga yoqdingiz!\n\n"
            f"👤 {target['name']}"
        )

        if target["age"]:
            text += f", {target['age']} yosh"

        if target["city"]:
            text += f"\n📍 {target['city']}"

        text += "\n\n💬 Hozir suhbatni boshlang."

        if recipient["premium"]:
            text += (
                "\n\n👑 Siz Premiumsiz!\n"
                "📨 Bu odamga Telegram shaxsiy chatiga to‘g‘ridan-to‘g‘ri "
                "yozishingiz mumkin.\n"
                "💡 Bu xabaringizga ko‘proq e’tibor berilishiga va "
                "javob olish ehtimolini oshirishga yordam berishi mumkin."
            )
        else:
            text += (
                "\n\n👑 Ko‘proq e’tibor va javob olishni xohlaysizmi?\n"
                "📨 Premium bilan Telegram shaxsiy chatiga to‘g‘ridan-to‘g‘ri "
                "yozishingiz mumkin.\n"
                "🔥 Bu xabaringizni ko‘rish va javob olish ehtimolini oshirishi mumkin."
            )

        return text

    def build_keyboard(recipient, target):
        buttons = [
            [
                InlineKeyboardButton(
                    "💬 Suhbatni boshlash",
                    callback_data=f"write_{target['id']}"
                )
            ]
        ]

        if recipient["premium"]:
            if target["username"]:
                buttons.append([
                    InlineKeyboardButton(
                        "📨 Telegram chatiga yozish",
                        url=f"https://t.me/{target['username']}"
                    )
                ])
            else:
                buttons.append([
                    InlineKeyboardButton(
                        "📨 Telegram chatiga yozish",
                        callback_data=f"telegram_chat_{target['id']}"
                    )
                ])
        else:
            buttons.append([
                InlineKeyboardButton(
                    "👑 Premium olish",
                    callback_data="premium_buy"
                )
            ])

        return InlineKeyboardMarkup(buttons)

    recipient1 = get_user_info(user1_id)
    target1 = get_user_info(user2_id)

    recipient2 = get_user_info(user2_id)
    target2 = get_user_info(user1_id)

    target1["id"] = user2_id
    target2["id"] = user1_id

    keyboard1 = build_keyboard(recipient1, target1)
    keyboard2 = build_keyboard(recipient2, target2)

    text1 = build_text(recipient1, target1)
    text2 = build_text(recipient2, target2)

    try:
        if not notification_already_sent(
            user1_id, "match", user2_id, hours=24 * 30
        ):
            if user2_photo:
                await bot.send_photo(
                    chat_id=user1_id,
                    photo=user2_photo,
                    caption=text1,
                    parse_mode="HTML",
                    reply_markup=keyboard1
                )
            else:
                await bot.send_message(
                    chat_id=user1_id,
                    text=text1,
                    parse_mode="HTML",
                    reply_markup=keyboard1
                )

            save_notification(user1_id, "match", user2_id)

    except Forbidden:
        print(f"🚫 Match user1 blocked bot: {user1_id}")

    except Exception as e:
        print(f"Match user1 error: {e}")

    try:
        if not notification_already_sent(
            user2_id, "match", user1_id, hours=24 * 30
        ):
            if user1_photo:
                await bot.send_photo(
                    chat_id=user2_id,
                    photo=user1_photo,
                    caption=text2,
                    parse_mode="HTML",
                    reply_markup=keyboard2
                )
            else:
                await bot.send_message(
                    chat_id=user2_id,
                    text=text2,
                    parse_mode="HTML",
                    reply_markup=keyboard2
                )

            save_notification(user2_id, "match", user1_id)

    except Forbidden:
        print(f"🚫 Match user2 blocked bot: {user2_id}")

    except Exception as e:
        print(f"Match user2 error: {e}")


# =========================================================
# YANGI PROFIL — FOYDALANUVCHINING CITY'SI
# =========================================================

async def notify_new_user_in_city(
    bot,
    new_user_id
):
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT first_name, gender, city
        FROM users
        WHERE user_id = %s
        """,
        (new_user_id,)
    )

    new_user = cur.fetchone()

    if not new_user:
        cur.close()
        conn.close()
        return

    new_name, new_gender, city = new_user

    if not city:
        cur.close()
        conn.close()
        return

    # Yangi profil ayol bo'lsa erkaklarga,
    # erkak bo'lsa ayollarga.
    if new_gender == "Ayol":
        target_gender = "Erkak"
    elif new_gender == "Erkak":
        target_gender = "Ayol"
    else:
        target_gender = None

    if target_gender:
        cur.execute(
            """
            SELECT user_id
            FROM users
            WHERE city = %s
              AND gender = %s
              AND user_id != %s
              AND is_active = TRUE
            """,
            (
                city,
                target_gender,
                new_user_id
            )
        )
    else:
        cur.execute(
            """
            SELECT user_id
            FROM users
            WHERE city = %s
              AND user_id != %s
              AND is_active = TRUE
            """,
            (
                city,
                new_user_id
            )
        )

    target_users = cur.fetchall()

    cur.close()
    conn.close()

    if not target_users:
        return

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "🔍 Ko‘rish",
                callback_data="new_city_profiles"
            )
        ]
    ])

    # Foydalanuvchi tiliga qarab notification
    texts = {
        "uz": (
            "🔥 Shaharingizda yangi profillar paydo bo‘ldi!\n\n"
            f"💕 {city} shahrida yangi tanishuv sizni kutmoqda.\n\n"
            "🔍 Yangi profillarni ko‘rish"
        ),
        "ru": (
            "🔥 В вашем городе появились новые профили!\n\n"
            f"💕 В городе {city} вас ждёт новое знакомство.\n\n"
            "🔍 Посмотреть новые профили"
        ),
        "uz_cyr": (
            "🔥 Шаҳрингизда янги профиллар пайдо бўлди!\n\n"
            f"💕 {city} шаҳрида янги танишув сизни кутмоқда.\n\n"
            "🔍 Янги профилларни кўриш"
        ),
    }


    for row in target_users:
        user_id = row[0]

        if notification_already_sent(
            user_id,
            "new_city_profiles",
            None,
            hours=24
        ):
            continue

        # Har bir foydalanuvchiga uning tilida yuborish
        user_conn = get_db_connection()
        user_cur = user_conn.cursor()
        user_cur.execute(
            "SELECT language FROM users WHERE user_id = %s",
            (user_id,)
        )
        language_row = user_cur.fetchone()
        user_cur.close()
        user_conn.close()

        language = (
            language_row[0]
            if language_row and language_row[0] in texts
            else "uz"
        )

        text = texts[language]

        sent = await safe_send_message(
            bot,
            user_id,
            text,
            keyboard
        )

        if sent:
            save_notification(
                user_id,
                "new_city_profiles"
            )


# Eski API bilan moslik
async def notify_new_user(
    bot,
    new_user_name,
    new_user_id
):
    await notify_new_user_in_city(
        bot,
        new_user_id
    )


# =========================================================
# 3 KUN
# =========================================================

async def notify_inactive_users_3_days(bot):
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT user_id
        FROM users
        WHERE is_active = TRUE
          AND last_active <= NOW() - INTERVAL '3 days'
          AND last_active > NOW() - INTERVAL '30 days'
        """
    )

    users = cur.fetchall()

    cur.close()
    conn.close()

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "🔍 Ko‘rib chiqish",
                callback_data="new_city_profiles"
            )
        ]
    ])

    text = (
        "👋 Sizni sog‘indik!\n\n"
        "🔥 Siz yo‘qligingizda yangi profillar qo‘shildi.\n\n"
        "💕 Balki sizni kutayotgan tanishuv bordir."
    )

    for row in users:
        user_id = row[0]

        if notification_already_sent(
            user_id,
            "inactive_3_days",
            None,
            hours=72
        ):
            continue

        sent = await safe_send_message(
            bot,
            user_id,
            text,
            keyboard
        )

        if sent:
            save_notification(
                user_id,
                "inactive_3_days"
            )


# =========================================================
# 7 KUN
# =========================================================

async def notify_inactive_users_7_days(bot):
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT user_id
        FROM users
        WHERE is_active = TRUE
          AND last_active <= NOW() - INTERVAL '7 days'
          AND last_active > NOW() - INTERVAL '30 days'
        """
    )

    users = cur.fetchall()

    cur.close()
    conn.close()

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "🔥 Profillarni ko‘rish",
                callback_data="new_city_profiles"
            )
        ]
    ])

    text = (
        "👋 Sizni sog‘indik!\n\n"
        "🔥 Bir haftadan beri ko‘rinmadingiz.\n\n"
        "💕 Sizning hududingizda yangi tanishuvlar paydo bo‘ldi.\n\n"
        "🔍 Balki aynan siz izlayotgan inson shu yerda."
    )

    for row in users:
        user_id = row[0]

        if notification_already_sent(
            user_id,
            "inactive_7_days",
            None,
            hours=168
        ):
            continue

        sent = await safe_send_message(
            bot,
            user_id,
            text,
            keyboard
        )

        if sent:
            save_notification(
                user_id,
                "inactive_7_days"
            )


# =========================================================
# PREMIUM REKLAMA
# FAQAT PREMIUM EMAS
# =========================================================

async def notify_premium_promotion(bot):
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT user_id
        FROM users
        WHERE is_active = TRUE
          AND (
              premium_until IS NULL
              OR premium_until <= NOW()
          )
        """
    )

    users = cur.fetchall()

    cur.close()
    conn.close()

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "👑 Premiumni ko‘rish",
                callback_data="premium_buy"
            )
        ]
    ])

    text = (
        "👑 SARA MATCH PREMIUM\n\n"
        "✨ Premium imkoniyatlari:\n\n"
        "♾️ Cheksiz profil ko‘rish\n"
        "❤️ Cheksiz like\n"
        "✉️ Match bo‘lmasdan yozish\n"
        "👀 Kim sizni yoqtirganini ko‘rish\n"
        "⭐️ Premium belgisi\n"
        "🚀 Profilingizga ustuvorlik\n\n"
        "💎 Premiumni hoziroq ko‘ring!"
    )

    for row in users:
        user_id = row[0]

        if notification_already_sent(
            user_id,
            "premium_promotion",
            None,
            hours=168
        ):
            continue

        sent = await safe_send_message(
            bot,
            user_id,
            text,
            keyboard
        )

        if sent:
            save_notification(
                user_id,
                "premium_promotion"
            )


# =========================================================
# NEWS
# =========================================================

async def notify_news(bot, text):
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT user_id
        FROM users
        WHERE is_active = TRUE
        """
    )

    users = cur.fetchall()

    cur.close()
    conn.close()

    for row in users:
        await safe_send_message(
            bot,
            row[0],
            f"📢 Yangilik:\n\n{text}"
        )

# =========================================================

# =========================================================
# RETENTION / SMART NOTIFICATIONS
# =========================================================
#
# Maqsad:
# 1) Yangi foydalanuvchini darhol bezovta qilmaslik
# 2) 2 kun botga kirmagan foydalanuvchini qayta jalb qilish
# 3) Keyingi xabarlarni har 2 kunda yuborish
# 4) Yangi profillar sonini avtomatik hisoblash
# 5) Botni bloklagan foydalanuvchini avtomatik o'chirish
# 6) Foydalanuvchi qaytib kirsa notification siklini to'xtatish
#

RETENTION_FIRST_DAYS = 2
RETENTION_REPEAT_DAYS = 2


def get_inactive_users():
    """
    2 kundan ko'proq faol bo'lmagan foydalanuvchilarni qaytaradi.
    """
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT
            user_id,
            first_name,
            last_active
        FROM users
        WHERE is_active = TRUE
          AND last_active IS NOT NULL
          AND last_active <= NOW() - INTERVAL '2 days'
        ORDER BY last_active ASC
        """
    )

    users = cur.fetchall()

    cur.close()
    conn.close()

    return users


def get_new_profiles_count(user_id, last_active):
    """
    Foydalanuvchi oxirgi marta botga kirganidan keyin
    qo'shilgan yangi faol profillar sonini hisoblaydi.
    """

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT COUNT(*)
        FROM users
        WHERE user_id != %s
          AND is_active = TRUE
          AND created_at > %s
        """,
        (user_id, last_active)
    )

    count = cur.fetchone()[0]

    cur.close()
    conn.close()

    return int(count or 0)


def get_last_retention_notification(user_id):
    """
    Ushbu foydalanuvchiga oxirgi retention xabari qachon
    yuborilganini qaytaradi.
    """

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT created_at
        FROM notification_logs
        WHERE user_id = %s
          AND notification_type = 'retention'
        ORDER BY created_at DESC
        LIMIT 1
        """,
        (user_id,)
    )

    row = cur.fetchone()

    cur.close()
    conn.close()

    return row[0] if row else None


async def notify_retention_user(bot, user_id, first_name, last_active):
    """
    Bitta faol bo'lmagan foydalanuvchini qayta jalb qilish.
    """

    # Oxirgi retention xabarini tekshiramiz
    last_notification = get_last_retention_notification(user_id)

    now = datetime.now()

    # Birinchi xabar: 2 kundan keyin
    if last_notification is None:
        if last_active > now:
            return False

        inactive_days = (now - last_active).days

        if inactive_days < RETENTION_FIRST_DAYS:
            return False

    # Keyingi xabarlar: har 2 kunda
    else:
        days_since_notification = (now - last_notification).days

        if days_since_notification < RETENTION_REPEAT_DAYS:
            return False

    # Yangi profillar soni
    new_profiles_count = get_new_profiles_count(
        user_id,
        last_active
    )

    # Foydalanuvchi nomi
    display_name = first_name or "do'stim"

    # Foydalanuvchi tilini aniqlash
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT language FROM users WHERE user_id = %s",
        (user_id,)
    )
    language_row = cur.fetchone()
    cur.close()
    conn.close()

    language = language_row[0] if language_row and language_row[0] else "uz"

    texts = {
        "uz": {
            "text": (
                f"👋 Salom, {display_name}!\n\n"
                "❤️ Sizni SaraMatch'da sog'indik!\n\n"
                "✨ Yangi tanishuvlar sizni kutmoqda.\n"
                f"🔥 Siz yo'q paytingizda {new_profiles_count} ta "
                "yangi profil qo'shilgan.\n\n"
                "💕 Botga qayting va tanishuvni davom ettiring!"
            ),
            "button": "🔥 Profillarni ko'rish"
        },
        "ru": {
            "text": (
                f"👋 Привет, {display_name}!\n\n"
                "❤️ Мы скучаем по вам в SaraMatch!\n\n"
                "✨ Новые знакомства уже ждут вас.\n"
                f"🔥 Пока вас не было, появилось новых профилей: "
                f"{new_profiles_count}.\n\n"
                "💕 Возвращайтесь и продолжайте знакомиться!"
            ),
            "button": "🔥 Смотреть профили"
        },
        "uz_cyr": {
            "text": (
                f"👋 Салом, {display_name}!\n\n"
                "❤️ Сизни SaraMatch'да соғиндик!\n\n"
                "✨ Янги танишувлар сизни кутмоқда.\n"
                f"🔥 Сиз йўқ пайтингизда {new_profiles_count} та "
                "янги профиль қўшилди.\n\n"
                "💕 Ботга қайтинг ва танишувни давом эттиринг!"
            ),
            "button": "🔥 Профилларни кўриш"
        }
    }

    t = texts.get(language, texts["uz"])

    text = t["text"]

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                t["button"],
                callback_data="retention_profiles"
            )
        ]
    ])

    try:
        await bot.send_message(
            chat_id=user_id,
            text=text,
            reply_markup=keyboard
        )

        save_notification(
            user_id,
            "retention"
        )

        print(
            f"✅ Retention yuborildi: "
            f"user={user_id}, "
            f"new_profiles={new_profiles_count}"
        )

        return True

    except Forbidden:
        print(
            f"🚫 Retention paytida bot bloklangan: {user_id}"
        )

        try:
            conn = get_db_connection()
            cur = conn.cursor()

            cur.execute(
                """
                UPDATE users
                SET is_active = FALSE
                WHERE user_id = %s
                """,
                (user_id,)
            )

            conn.commit()
            cur.close()
            conn.close()

        except Exception as e:
            print(
                f"❌ Blocklangan userni o'chirishda xato: {e}"
            )

        return False

    except Exception as e:
        print(
            f"❌ Retention notification error "
            f"user={user_id}: {e}"
        )

        return False


async def run_retention_notifications(bot):
    """
    Barcha mos foydalanuvchilarni tekshiradi.
    """

    print("🔔 Retention notification tekshiruvi boshlandi...")

    try:
        users = get_inactive_users()

        print(
            f"👥 5+ kun faol bo'lmaganlar: "
            f"{len(users)} ta"
        )

        sent_count = 0

        for user_id, first_name, last_active in users:

            sent = await notify_retention_user(
                bot,
                user_id,
                first_name,
                last_active
            )

            if sent:
                sent_count += 1

        print(
            f"✅ Retention tekshiruvi tugadi. "
            f"Yuborildi: {sent_count} ta"
        )

    except Exception as e:
        print(
            f"❌ Retention job xatosi: {e}"
        )


async def retention_job(context):
    """
    JobQueue uchun wrapper.
    Har 24 soatda ishga tushadi.
    Ichida 5 kun + 3 kunlik limit tekshiriladi.
    """

    await run_retention_notifications(
        context.bot
    )


# =========================================================
# PREMIUM TUGASHIGA 1 KUN QOLGANDA
# FAQAT OXIRGI KUN — 20% CHEGIRMA
# =========================================================

async def notify_premium_expiring_1_day(bot):
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT user_id, language, premium_until
        FROM users
        WHERE is_active = TRUE
          AND premium_until IS NOT NULL
          AND premium_until > NOW()
          AND premium_until <= NOW() + INTERVAL '24 hours'
        """
    )

    users = cur.fetchall()

    cur.close()
    conn.close()

    texts = {
        "uz": (
            "🚨 Premiumingiz ertaga tugaydi!\n\n"
            "👑 Premium imkoniyatlaringizni yo‘qotib qo‘ymang.\n\n"
            "🔥 Faqat BUGUN — 20% CHEGIRMA!\n\n"
            "♾️ Cheksiz profil ko‘rish\n"
            "❤️ Cheksiz like\n"
            "⭐ Bepul Superlike\n"
            "👀 Kim Superlike bosganini ko‘rish\n"
            "📨 Telegram shaxsiy chatiga yozish\n"
            "💬 Match bo‘lmasdan xabar yozish\n"
            "🚀 Qidiruvda ustuvor ko‘rinish\n\n"
            "⏰ Chegirma faqat bugun amal qiladi!"
        ),
        "ru": (
            "🚨 Ваш Premium заканчивается завтра!\n\n"
            "👑 Не теряйте возможности Premium.\n\n"
            "🔥 ТОЛЬКО СЕГОДНЯ — СКИДКА 20%!\n\n"
            "♾️ Безлимитный просмотр профилей\n"
            "❤️ Безлимитные лайки\n"
            "⭐ Бесплатный Superlike\n"
            "👀 Видеть кто поставил Superlike\n"
            "📨 Писать в личный Telegram\n"
            "💬 Писать без взаимного матча\n"
            "🚀 Приоритет в поиске\n\n"
            "⏰ Скидка действует только сегодня!"
        ),
        "uz_cyr": (
            "🚨 Premium’ингиз эртага тугайди!\n\n"
            "👑 Premium имкониятларингизни йўқотиб қўйманг.\n\n"
            "🔥 ФАҚАТ БУГУН — 20% ЧЕГИРМА!\n\n"
            "♾️ Чексиз профил кўриш\n"
            "❤️ Чексиз лайк\n"
            "⭐ Бепул Superlike\n"
            "👀 Ким Superlike босганини кўриш\n"
            "📨 Telegram шахсий чатига ёзиш\n"
            "💬 Match бўлмасдан хабар ёзиш\n"
            "🚀 Қидирувда устувор кўриниш\n\n"
            "⏰ Чегирма фақат бугун амал қилади!"
        ),
    }

    keyboards = {
        "uz": InlineKeyboardMarkup([
            [InlineKeyboardButton(
                "🔥 20% chegirma bilan Premium",
                callback_data="premium_expiring_discount"
            )]
        ]),
        "ru": InlineKeyboardMarkup([
            [InlineKeyboardButton(
                "🔥 Premium со скидкой 20%",
                callback_data="premium_expiring_discount"
            )]
        ]),
        "uz_cyr": InlineKeyboardMarkup([
            [InlineKeyboardButton(
                "🔥 20% чегирма билан Premium",
                callback_data="premium_expiring_discount"
            )]
        ]),
    }

    for user_id, language, premium_until in users:
        if notification_already_sent(
            user_id,
            "premium_expiring_1_day",
            None,
            hours=30
        ):
            continue

        language = language if language in texts else "uz"

        sent = await safe_send_message(
            bot,
            user_id,
            texts[language],
            keyboards[language]
        )

        if sent:
            save_notification(
                user_id,
                "premium_expiring_1_day"
            )

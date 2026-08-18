
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
        "💕 Sizni kimdir yoqtirdi!\\n\\n"
        f"👤 {from_user_name}\\n\\n"
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
    keyboard1 = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "💬 Suhbatni boshlash",
                callback_data=f"write_{user2_id}"
            )
        ]
    ])

    keyboard2 = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "💬 Suhbatni boshlash",
                callback_data=f"write_{user1_id}"
            )
        ]
    ])

    text1 = (
        "🎉 MATCH!\n\n"
        "Sizlar bir-biringizga yoqdingiz ❤️\n\n"
        f"👤 {user2_name}"
    )

    text2 = (
        "🎉 MATCH!\n\n"
        "Sizlar bir-biringizga yoqdingiz ❤️\n\n"
        f"👤 {user1_name}"
    )

    try:
        if not notification_already_sent(
            user1_id,
            "match",
            user2_id,
            hours=24 * 30
        ):
            if user2_photo:
                await bot.send_photo(
                    chat_id=user1_id,
                    photo=user2_photo,
                    caption=text1,
                    reply_markup=keyboard1
                )
            else:
                await bot.send_message(
                    chat_id=user1_id,
                    text=text1,
                    reply_markup=keyboard1
                )

            save_notification(
                user1_id,
                "match",
                user2_id
            )

    except Forbidden:
        print(f"🚫 Match user1 blocked bot: {user1_id}")
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute(
                "UPDATE users SET is_active = FALSE WHERE user_id = %s",
                (user1_id,)
            )
            conn.commit()
            cur.close()
            conn.close()
        except Exception as db_error:
            print(f"❌ Could not deactivate user {user1_id}: {db_error}")

    except Exception as e:
        print(f"Match user1 error: {e}")

    try:
        if not notification_already_sent(
            user2_id,
            "match",
            user1_id,
            hours=24 * 30
        ):
            if user1_photo:
                await bot.send_photo(
                    chat_id=user2_id,
                    photo=user1_photo,
                    caption=text2,
                    reply_markup=keyboard2
                )
            else:
                await bot.send_message(
                    chat_id=user2_id,
                    text=text2,
                    reply_markup=keyboard2
                )

            save_notification(
                user2_id,
                "match",
                user1_id
            )

    except Forbidden:
        print(f"🚫 Match user2 blocked bot: {user2_id}")
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute(
                "UPDATE users SET is_active = FALSE WHERE user_id = %s",
                (user2_id,)
            )
            conn.commit()
            cur.close()
            conn.close()
        except Exception as db_error:
            print(f"❌ Could not deactivate user {user2_id}: {db_error}")

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

    # Oxirgi 24 soatdagi yangi profillar soni
    cur.execute(
        """
        SELECT COUNT(*)
        FROM users
        WHERE city = %s
          AND user_id != %s
          AND is_active = TRUE
          AND created_at >= NOW() - INTERVAL '24 hours'
        """,
        (city, new_user_id)
    )

    count = cur.fetchone()[0]

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
                callback_data="find_profiles"
            )
        ]
    ])

    text = (
        "🔥 Sizning hududingizda yangi profil!\n\n"
        f"💕 {city} hududida yangi tanishuv sizni kutmoqda.\n\n"
        f"👥 {count} ta yangi profil qo‘shildi.\n\n"
        "🔍 Ko‘rish"
    )

    for row in target_users:
        user_id = row[0]

        if notification_already_sent(
            user_id,
            "new_city_profiles",
            None,
            hours=24
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
                callback_data="find_profiles"
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
                callback_data="find_profiles"
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
                callback_data="find_profiles"
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

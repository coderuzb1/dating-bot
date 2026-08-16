#!/data/data/com.termux/files/usr/bin/bash

set -e

echo "========================================"
echo "  SARA MATCH NOTIFICATION INSTALLER"
echo "========================================"

# -----------------------------------------
# BACKUP
# -----------------------------------------

BACKUP_DIR="backup_notifications_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

cp bot.py "$BACKUP_DIR/bot.py"
cp database.py "$BACKUP_DIR/database.py"
cp notifications.py "$BACKUP_DIR/notifications.py"

echo "✅ Backup yaratildi: $BACKUP_DIR"

# -----------------------------------------
# DATABASE
# -----------------------------------------

python - <<'PY'
from pathlib import Path

p = Path("database.py")
s = p.read_text()

if "CREATE TABLE IF NOT EXISTS notification_logs" not in s:

    marker = """
    conn.commit()
    cur.close()
    conn.close()
"""

    addition = """
    # =========================
    # NOTIFICATION LOGS
    # =========================
    cur.execute(\"\"\"
        CREATE TABLE IF NOT EXISTS notification_logs (
            id SERIAL PRIMARY KEY,
            user_id BIGINT NOT NULL,
            notification_type TEXT NOT NULL,
            reference_id BIGINT,
            created_at TIMESTAMP DEFAULT NOW()
        )
    \"\"\")

    cur.execute(\"\"\"
        CREATE INDEX IF NOT EXISTS idx_notification_logs_user_type
        ON notification_logs(user_id, notification_type)
    \"\"\")

    cur.execute(\"\"\"
        CREATE INDEX IF NOT EXISTS idx_notification_logs_created
        ON notification_logs(created_at)
    \"\"\")

    cur.execute(\"\"\"
        CREATE INDEX IF NOT EXISTS idx_users_city_created
        ON users(city, created_at)
    \"\"\")

    cur.execute(\"\"\"
        ALTER TABLE users
        ADD COLUMN IF NOT EXISTS last_active TIMESTAMP DEFAULT NOW()
    \"\"\")

    cur.execute(\"\"\"
        UPDATE users
        SET last_active = COALESCE(last_active, created_at, NOW())
        WHERE last_active IS NULL
    \"\"\")

"""

    if marker not in s:
        raise SystemExit(
            "❌ database.py ichidan kerakli joy topilmadi. "
            "Fayl o'zgartirilmadi."
        )

    s = s.replace(marker, addition + marker)

    p.write_text(s)

    print("✅ database.py yangilandi")

else:
    print("ℹ️ database.py allaqachon notification_logsga ega")

# -----------------------------------------
# NOTIFICATIONS.PY
# -----------------------------------------

Path("notifications.py").write_text(r'''
import os
import psycopg2

from telegram import InlineKeyboardMarkup, InlineKeyboardButton


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
                "👀 Kim ekanini ko‘rish",
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
''')

print("✅ notifications.py yangilandi")

PY

# -----------------------------------------
# BOT IMPORT
# -----------------------------------------

python - <<'PY'
from pathlib import Path

p = Path("bot.py")
s = p.read_text()

old = """from notifications import notify_new_user, notify_new_match, notify_like, notify_news"""

new = """from notifications import (
    notify_new_user,
    notify_new_match,
    notify_like,
    notify_news,
    notify_inactive_users_3_days,
    notify_inactive_users_7_days,
    notify_premium_promotion,
    notify_new_user_in_city,
)"""

if old in s:
    s = s.replace(old, new)

elif "notify_inactive_users_3_days" not in s:
    raise SystemExit(
        "❌ bot.py notification import qatori topilmadi."
    )

p.write_text(s)

print("✅ bot.py import yangilandi")
PY

# -----------------------------------------
# SCHEDULER FUNKSIYASI
# -----------------------------------------

python - <<'PY'
from pathlib import Path

p = Path("bot.py")
s = p.read_text()

if "async def scheduled_notifications(context):" not in s:

    marker = "async def check_bad_words(text):"

    addition = '''
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


'''

    if marker not in s:
        raise SystemExit(
            "❌ bot.py ichidan scheduler qo‘yiladigan joy topilmadi."
        )

    s = s.replace(
        marker,
        addition + marker,
        1
    )

    p.write_text(s)

    print("✅ Scheduler funksiyasi qo‘shildi")

else:
    print("ℹ️ Scheduler funksiyasi allaqachon mavjud")

PY

# -----------------------------------------
# LAST ACTIVE
# -----------------------------------------

python - <<'PY'
from pathlib import Path

p = Path("bot.py")
s = p.read_text()

if "SET last_active = NOW()" not in s:

    marker = """    if user_status:
"""

    addition = """    if user_status:
        # Foydalanuvchi botga kirgan vaqtni yangilash
        try:
            active_conn = get_db_connection()
            active_cur = active_conn.cursor()

            active_cur.execute(
                \"\"\"
                UPDATE users
                SET last_active = NOW()
                WHERE user_id = %s
                \"\"\",
                (user.id,)
            )

            active_conn.commit()
            active_cur.close()
            active_conn.close()

        except Exception as e:
            print(f"Last active update error: {e}")

"""

    if marker not in s:
        raise SystemExit(
            "❌ start() ichidagi user_status qismi topilmadi."
        )

    s = s.replace(
        marker,
        addition,
        1
    )

    p.write_text(s)

    print("✅ last_active yangilanishi qo‘shildi")

else:
    print("ℹ️ last_active yangilanishi allaqachon mavjud")

PY

# -----------------------------------------
# SMART NOTIFICATION
# -----------------------------------------

python - <<'PY'
from pathlib import Path

p = Path("bot.py")
s = p.read_text()

if "await notify_new_user_in_city(" not in s:

    marker = """    await update.message.reply_text("✅ Profil yaratildi!", reply_markup=await get_main_keyboard())
"""

    addition = """    # Yangi profilning hududiga mos Smart Notification
    try:
        await notify_new_user_in_city(
            context.bot,
            user.id
        )
    except Exception as e:
        print(f"Smart city notification error: {e}")

"""

    if marker not in s:
        raise SystemExit(
            "❌ Profil yaratildi qatori topilmadi."
        )

    s = s.replace(
        marker,
        addition + marker,
        1
    )

    p.write_text(s)

    print("✅ Smart city notification qo‘shildi")

else:
    print("ℹ️ Smart city notification allaqachon mavjud")

PY

# -----------------------------------------
# LIKE BLOCK
# -----------------------------------------

python - <<'PY'
from pathlib import Path

p = Path("bot.py")
s = p.read_text()

start = s.find('    if data.startswith("like_"):')

if start == -1:
    print("⚠️ like_ block topilmadi. Qo‘lda tekshirish kerak.")
else:

    end = s.find(
        "async def save_edit(",
        start
    )

    if end == -1:
        print(
            "⚠️ like_ block oxiri aniqlanmadi. "
            "Like kodi o‘zgartirilmadi."
        )
    else:

        new_block = r'''    if data.startswith("like_"):
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

'''

        s = s[:start] + new_block + s[end:]

        p.write_text(s)

        print("✅ Like/Match tizimi yangilandi")

PY

# -----------------------------------------
# JOB QUEUE
# -----------------------------------------

if grep -q 'python-telegram-bot==' requirements.txt; then
    sed -i 's/^python-telegram-bot==\([0-9.]*\)$/python-telegram-bot[job-queue]==\1/' requirements.txt
    echo "✅ requirements.txt job-queue bilan yangilandi"
fi

# -----------------------------------------
# SCHEDULER REGISTRATION
# -----------------------------------------

python - <<'PY'
from pathlib import Path

p = Path("bot.py")
s = p.read_text()

if "application.job_queue.run_repeating(" not in s:

    # run_polling oldin scheduler qo'yamiz
    marker = "application.run_polling()"

    if marker in s:

        addition = """application.job_queue.run_repeating(
    scheduled_notifications,
    interval=3600,
    first=60
)

"""

        s = s.replace(
            marker,
            addition + marker,
            1
        )

        p.write_text(s)

        print("✅ Scheduler Application'ga ulandi")

    else:
        print(
            "⚠️ application.run_polling() topilmadi. "
            "Scheduler qo‘lda ulanishi kerak."
        )

else:
    print("ℹ️ Scheduler allaqachon ulangan")

PY

# -----------------------------------------
# SYNTAX CHECK
# -----------------------------------------

echo ""
echo "========================================"
echo "  SYNTAX TEKSHIRILMOQDA"
echo "========================================"

python -m py_compile database.py
python -m py_compile notifications.py
python -m py_compile bot.py

echo ""
echo "========================================"
echo "  ✅ TAYYOR"
echo "========================================"
echo ""
echo "Backup: $BACKUP_DIR"
echo ""
echo "Keyingi qadam:"
echo "python bot.py"
echo ""

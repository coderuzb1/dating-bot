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
    notify_premium_expiring_1_day,
    notify_new_user_in_city,
    retention_job,
)
from datetime import datetime, timedelta

LANGUAGE, NAME, AGE, GENDER, CITY, BIO, PHOTO = range(7)
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

    try:
        await notify_premium_expiring_1_day(context.bot)
    except Exception as e:
        print(f"Premium expiring notification error: {e}")

    print("✅ Notification scheduler tugadi")


async def check_bad_words(text):
    return any(word in text.lower() for word in BAD_WORDS)

TRANSLATIONS = {
    "uz": {
        "search": "🔍 Qidirish",
        "profile": "👤 Profil",
        "likes": "👀 Meni yoqtirganlar",
        "matches": "💞 Matchlarim",
        "superlike": "⭐ Superlike",
        "premium": "👑 Premium",
        "settings": "⚙️ Sozlamalar",
        "referral": "🎁 Referal",

        "step": "{step}/7",
        "enter_name": "Ismingizni kiriting:",
        "name_error": "❌ Ism 2-30 ta belgidan iborat bo'lishi kerak.",
        "name_letter_error": "❌ Ismda harflar bo'lishi kerak.",
        "enter_age": "Yoshingizni kiriting (16-60):",
        "age_error": "❌ Iltimos, to'g'ri yosh kiriting (16-60):",
        "choose_gender": "Jinsingizni tanlang:",
        "gender_error": "❌ Iltimos, tugmalardan birini tanlang:",
        "male": "👨 Erkak",
        "female": "👩 Ayol",
        "choose_city": "Yashash shahringizni tanlang:",
        "other": "Boshqa",
        "enter_city": "📍 Shahringiz nomini yozing:",
        "city_error": "❌ Shahar nomi 2-50 ta belgidan iborat bo'lishi kerak.",
        "city_choose_error": "❌ Iltimos, shaharni tugmalardan tanlang yoki «Boshqa» tugmasini bosing.",
        "enter_bio": "O'zingiz haqingizda qisqacha yozing:",
        "send_photo": "Profil rasmingizni yuboring:",
        "profile_created": "✅ Profil yaratildi!",

        "not_found_profile": "❌ Avval profil yarating. /start bosing.",
        "limit_reached": "🚫 Bugungi 20 ta profil limitingiz tugadi.\n\n👑 Premiumga o'tib, profillarni cheksiz ko'rishingiz mumkin.",
        "no_profiles": "😔 Hozircha boshqa profillar qolmagan.",
        "dislike": "👎 Yoqmadi",
        "like": "❤️ Yoqdi",
        "write": "✉️ Yozish",
        "bio_empty": "Bio yozilmagan",

        "premium_title": "👑 <b>PREMIUM</b>",
        "premium_intro": "💎 Premium bilan tanishuv imkoniyatlaringizni yanada kengaytiring!",
        "premium_unlimited_profiles": "♾️ <b>Cheksiz profil ko'rish</b> — ko'proq odamlarni kashf eting",
        "premium_unlimited_likes": "❤️ <b>Cheksiz Like</b> — imkoniyatlarni o'tkazib yubormang",
        "premium_direct_message": "✉️ <b>Matchni kutmasdan yozing</b> — yoqqan insoningiz bilan darhol suhbat boshlang",
        "premium_who_liked": "👀 <b>Sizni kim yoqtirganini ko'ring</b> — kim sizga qiziqayotganini biling",
        "premium_badge": "⭐️ <b>Premium belgisi</b> — profilingizni ajratib turing",
        "premium_priority": "🚀 <b>Profil ustuvorligi</b> — ko'proq ko'rinishga ega bo'ling",
        "premium_more": "🔥 <b>Ko'proq ko'rinish → ko'proq Like → ko'proq Match!</b>",
        "premium_choose": "✨ O'zingizga mos Premium tarifini tanlang:",
        "choose_duration": "📅 <b>Muddatni tanlang:</b>",

        "plan_1w": "📅 1 hafta - 25 000 so'm • QULAY",
        "plan_2w": "🔥 14 kun - 39 000 so'm • ENG QULAY",
        "plan_1m": "⭐️ 1 oy - 59 000 so'm • OMMABOP",
        "plan_3m": "👑 3 oy - 129 000 so'm • TEJAMKOR",
        "cancel": "❌ Bekor qilish",

        "payment_method": "💳 TO'LOV USULINI TANLANG",
        "period": "📅 Muddat: {days} kun",
        "amount": "💰 Summa: {price} so'm",
        "choose_payment": "Quyidagi to'lov usullaridan birini tanlang:",
        "payment_error": "❌ To'lov ma'lumotlari xato.",
        "plan_not_found": "❌ Tarif topilmadi.",
        "payment_not_configured": "❌ Ushbu to'lov usuli hozircha sozlanmagan.",
        "payment": "💳 TO'LOV",
        "method": "💳 Usul: {method}",
        "card": "💳 Karta: {card}",
        "payment_done": "To'lovni amalga oshirgach, «✅ To'lov qildim» tugmasini bosing.",
        "paid": "✅ To'lov qildim",
        "send_receipt": "📸📄 TO'LOV CHEKINI YUBORING",
        "receipt_info": "🖼 Rasm yoki 📄 PDF/fayl yuborishingiz mumkin.",
        "receipt_warning": "⚠️ Faqat haqiqiy to‘lov chekini yuboring!\n🚫 Soxta chek yuborsangiz, darhol botdan bloklanasiz va Premium berilmaydi.",
        "receipt_wait": "⏳ Chek yuborilgach admin tekshiradi.",
    },

    "ru": {
        "search": "🔍 Поиск",
        "profile": "👤 Профиль",
        "likes": "👀 Кто меня лайкнул",
        "matches": "💞 Мои совпадения",
        "superlike": "⭐ Суперлайк",
        "premium": "👑 Премиум",
        "settings": "⚙️ Настройки",
        "referral": "🎁 Referal",

        "step": "{step}/7",
        "enter_name": "Введите ваше имя:",
        "name_error": "❌ Имя должно содержать от 2 до 30 символов.",
        "name_letter_error": "❌ Имя должно содержать буквы.",
        "enter_age": "Введите ваш возраст (16-60):",
        "age_error": "❌ Пожалуйста, введите правильный возраст (16-60):",
        "choose_gender": "Выберите ваш пол:",
        "gender_error": "❌ Пожалуйста, выберите один из вариантов:",
        "male": "👨 Мужчина",
        "female": "👩 Женщина",
        "choose_city": "Выберите город проживания:",
        "other": "Другой",
        "enter_city": "📍 Введите название вашего города:",
        "city_error": "❌ Название города должно содержать от 2 до 50 символов.",
        "city_choose_error": "❌ Пожалуйста, выберите город из кнопок или нажмите «Другой».",
        "enter_bio": "Кратко расскажите о себе:",
        "send_photo": "Отправьте фотографию профиля:",
        "profile_created": "✅ Профиль создан!",

        "not_found_profile": "❌ Сначала создайте профиль. Нажмите /start.",
        "limit_reached": "🚫 Вы достигли дневного лимита в 20 профилей.\n\n👑 С Премиумом вы сможете просматривать профили без ограничений.",
        "no_profiles": "😔 Пока других профилей нет.",
        "dislike": "👎 Не нравится",
        "like": "❤️ Нравится",
        "write": "✉️ Написать",
        "bio_empty": "Биография не указана",

        "premium_title": "👑 <b>ПРЕМИУМ</b>",
        "premium_intro": "💎 С Премиумом ваши возможности для знакомств станут намного шире!",
        "premium_unlimited_profiles": "♾️ <b>Безлимитный просмотр профилей</b> — находите больше людей",
        "premium_unlimited_likes": "❤️ <b>Безлимитные лайки</b> — не упускайте возможности",
        "premium_direct_message": "✉️ <b>Пишите без ожидания совпадения</b> — начинайте общение сразу",
        "premium_who_liked": "👀 <b>Узнавайте, кто вас лайкнул</b> — знайте, кто вами интересуется",
        "premium_badge": "⭐️ <b>Значок Премиум</b> — выделяйте свой профиль",
        "premium_priority": "🚀 <b>Приоритет профиля</b> — получайте больше просмотров",
        "premium_more": "🔥 <b>Больше просмотров → больше лайков → больше совпадений!</b>",
        "premium_choose": "✨ Выберите подходящий тариф Премиум:",
        "choose_duration": "📅 <b>Выберите срок:</b>",

        "plan_1w": "📅 1 неделя - 25 000 сум • ВЫГОДНО",
        "plan_2w": "🔥 14 дней - 39 000 сум • ЛУЧШИЙ ВЫБОР",
        "plan_1m": "⭐️ 1 месяц - 59 000 сум • ПОПУЛЯРНЫЙ",
        "plan_3m": "👑 3 месяца - 129 000 сум • ЭКОНОМНЫЙ",
        "cancel": "❌ Отмена",

        "payment_method": "💳 ВЫБЕРИТЕ СПОСОБ ОПЛАТЫ",
        "period": "📅 Срок: {days} дней",
        "amount": "💰 Сумма: {price} сум",
        "choose_payment": "Выберите один из способов оплаты:",
        "payment_error": "❌ Ошибка в данных платежа.",
        "plan_not_found": "❌ Тариф не найден.",
        "payment_not_configured": "❌ Этот способ оплаты пока не настроен.",
        "payment": "💳 ОПЛАТА",
        "method": "💳 Способ: {method}",
        "card": "💳 Карта: {card}",
        "payment_done": "После оплаты нажмите кнопку «✅ Я оплатил».",
        "paid": "✅ Я оплатил",
        "send_receipt": "📸📄 ОТПРАВЬТЕ ЧЕК ОБ ОПЛАТЕ",
        "receipt_info": "🖼 Можно отправить изображение или 📄 PDF/файл.",
        "receipt_warning": "⚠️ Отправляйте только настоящий чек об оплате!\n🚫 За поддельный чек вы будете заблокированы, а Премиум не будет выдан.",
        "receipt_wait": "⏳ После отправки чек проверит администратор.",
    },

    "uz_cyr": {
        "search": "🔍 Қидириш",
        "profile": "👤 Профил",
        "likes": "❤️ Ёқтирганларим",
        "matches": "💞 Мэтчларим",
        "superlike": "⭐ Суперлайк",
        "premium": "👑 Премиум",
        "settings": "⚙️ Созламалар",
        "referral": "🎁 Referal",

        "step": "{step}/7",
        "enter_name": "Исмингизни киритинг:",
        "name_error": "❌ Исм 2-30 та белгидан иборат бўлиши керак.",
        "name_letter_error": "❌ Исмда ҳарфлар бўлиши керак.",
        "enter_age": "Ёшингизни киритинг (16-60):",
        "age_error": "❌ Илтимос, тўғри ёш киритинг (16-60):",
        "choose_gender": "Жинсингизни танланг:",
        "gender_error": "❌ Илтимос, тугмалардан бирини танланг:",
        "male": "👨 Эркак",
        "female": "👩 Аёл",
        "choose_city": "Яшаш шаҳарингизни танланг:",
        "other": "Бошқа",
        "enter_city": "📍 Шаҳрингиз номини ёзинг:",
        "city_error": "❌ Шаҳар номи 2-50 та белгидан иборат бўлиши керак.",
        "city_choose_error": "❌ Илтимос, шаҳарни тугмалардан танланг ёки «Бошқа» тугмасини босинг.",
        "enter_bio": "Ўзингиз ҳақингизда қисқача ёзинг:",
        "send_photo": "Профил расмингизни юборинг:",
        "profile_created": "✅ Профил яратилди!",

        "not_found_profile": "❌ Аввал профил яратинг. /start ни босинг.",
        "limit_reached": "🚫 Бугунги 20 та профиль лимитингиз тугади.\n\n👑 Премиум орқали профилларни чекловсиз кўришингиз мумкин.",
        "no_profiles": "😔 Ҳозирча бошқа профиллар қолмаган.",
        "dislike": "👎 Ёқмади",
        "like": "❤️ Ёқди",
        "write": "✉️ Ёзиш",
        "bio_empty": "Био ёзилмаган",

        "premium_title": "👑 <b>ПРЕМИУМ</b>",
        "premium_intro": "💎 Премиум билан танишув имкониятларингизни янада кенгайтиринг!",
        "premium_unlimited_profiles": "♾️ <b>Чексиз профиль кўриш</b> — кўпроқ одамларни кашф этинг",
        "premium_unlimited_likes": "❤️ <b>Чексиз лайк</b> — имкониятларни ўтказиб юборманг",
        "premium_direct_message": "✉️ <b>Мэтчни кутмасдан ёзинг</b> — ёққан инсонгиз билан дарҳол суҳбат бошланг",
        "premium_who_liked": "👀 <b>Сизни ким ёқтирганини кўринг</b> — ким сизга қизиқayotganини билинг",
        "premium_badge": "⭐️ <b>Премиум белгиси</b> — профилингизни ажратиб туринг",
        "premium_priority": "🚀 <b>Профиль устуворлиги</b> — кўпроқ кўринишга эга бўлинг",
        "premium_more": "🔥 <b>Кўпроқ кўриниш → кўпроқ лайк → кўпроқ мэтч!</b>",
        "premium_choose": "✨ Ўзингизга мос Премиум тарифини танланг:",
        "choose_duration": "📅 <b>Муддатни танланг:</b>",

        "plan_1w": "📅 1 ҳафта - 25 000 сўм • ҚУЛАЙ",
        "plan_2w": "🔥 14 кун - 39 000 сўм • ЭНГ ҚУЛАЙ",
        "plan_1m": "⭐️ 1 ой - 59 000 сўм • ОММАБОП",
        "plan_3m": "👑 3 ой - 129 000 сўм • ТЕЖАМКОР",
        "cancel": "❌ Бекор қилиш",

        "payment_method": "💳 ТЎЛОВ УСУЛИНИ ТАНЛАНГ",
        "period": "📅 Муддат: {days} кун",
        "amount": "💰 Сумма: {price} сўм",
        "choose_payment": "Қуйидаги тўлов усулларидан бирини танланг:",
        "payment_error": "❌ Тўлов маълумотлари хато.",
        "plan_not_found": "❌ Тариф топилмади.",
        "payment_not_configured": "❌ Ушбу тўлов усули ҳозирча созланмаган.",
        "payment": "💳 ТЎЛОВ",
        "method": "💳 Усул: {method}",
        "card": "💳 Карта: {card}",
        "payment_done": "Тўловни амалга оширгач, «✅ Тўлов қилдим» тугмасини босинг.",
        "paid": "✅ Тўлов қилдим",
        "send_receipt": "📸📄 ТЎЛОВ ЧЕКИНИ ЮБОРИНГ",
        "receipt_info": "🖼 Расм ёки 📄 PDF/файл юборишингиз мумкин.",
        "receipt_warning": "⚠️ Фақат ҳақиқий тўлов чекини юборинг!\n🚫 Сохта чек юборсангиз, дарҳол ботдан блокланасиз ва Премиум берилмайди.",
        "receipt_wait": "⏳ Чек юборилгандан сўнг администратор текширади.",
    },
}

def get_user_language(user_id):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "SELECT language FROM users WHERE user_id = %s",
            (user_id,)
        )
        result = cur.fetchone()
        cur.close()
        conn.close()

        if result and result[0] in TRANSLATIONS:
            return result[0]
    except Exception as e:
        print(f"Language error: {e}")

    return "uz"


def tr(language, key):
    if language not in TRANSLATIONS:
        language = "uz"
    return TRANSLATIONS[language].get(
        key,
        TRANSLATIONS["uz"].get(key, key)
    )


async def get_main_keyboard(language="uz"):
    return ReplyKeyboardMarkup([
        [
            KeyboardButton(tr(language, "search")),
            KeyboardButton(tr(language, "profile"))
        ],
        [
            KeyboardButton(tr(language, "likes")),
            KeyboardButton(tr(language, "matches"))
        ],
        [
            KeyboardButton(tr(language, "superlike")),
            KeyboardButton(tr(language, "premium"))
        ],
        [
            KeyboardButton(tr(language, "settings")),
            KeyboardButton(tr(language, "referral"))
        ]
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
            reply_markup=await get_main_keyboard(get_user_language(user.id))
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

async def create_profile(update, context):
    query = update.callback_query
    await query.answer()

    keyboard = ReplyKeyboardMarkup([
        [KeyboardButton("🇺🇿 O'zbek tili")],
        [KeyboardButton("🇷🇺 Русский")],
        [KeyboardButton("🇺🇿 Узбек (Кирилл)")]
    ], resize_keyboard=True, one_time_keyboard=True)

    await query.message.reply_text(
        "🌐 <b>Tilni tanlang / Выберите язык / Тилни танланг</b>",
        reply_markup=keyboard,
        parse_mode="HTML"
    )

    return LANGUAGE


async def get_language(update, context):
    text = update.message.text.strip()

    languages = {
        "🇺🇿 O'zbek tili": "uz",
        "🇷🇺 Русский": "ru",
        "🇺🇿 Узбек (Кирилл)": "uz_cyr",
    }

    if text not in languages:
        await update.message.reply_text(
            "🌐 Iltimos, tilni tanlang / Выберите язык / Тилни танланг:"
        )
        return LANGUAGE

    language = languages[text]
    context.user_data["language"] = language

    try:
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute(
            "UPDATE users SET language = %s WHERE user_id = %s",
            (language, update.effective_user.id)
        )

        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Language save error: {e}")

    await update.message.reply_text(
        f"✨ <b>1/5 — Profilni boshlaymiz</b> ✨\n\n"
        f"{tr(language, 'enter_name')}",
        parse_mode="HTML"
    )

    return NAME


async def get_name(update, context):
    language = context.user_data.get("language", "uz")
    name = update.message.text.strip()

    if len(name) < 2 or len(name) > 30:
        await update.message.reply_text(tr(language, "name_error"))
        return NAME

    if not any(ch.isalpha() for ch in name):
        await update.message.reply_text(tr(language, "name_letter_error"))
        return NAME

    context.user_data["profile_name"] = name

    await update.message.reply_text(
        f"🎂 <b>2/5 — Ismingiz</b>\n\n"
        f"{tr(language, 'enter_age')}",
        parse_mode="HTML"
    )
    return AGE


async def get_age(update, context):
    language = context.user_data.get("language", "uz")
    text = update.message.text.strip()

    if not text.isdigit() or int(text) < 16 or int(text) > 60:
        await update.message.reply_text(tr(language, "age_error"))
        return AGE

    context.user_data["age"] = int(text)

    keyboard = ReplyKeyboardMarkup(
        [[
            KeyboardButton(tr(language, "male")),
            KeyboardButton(tr(language, "female"))
        ]],
        resize_keyboard=True,
        one_time_keyboard=True
    )

    await update.message.reply_text(
        f"🎂 <b>3/5 — Yosh va jins</b>\n\n"
        f"{tr(language, 'choose_gender')}",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    return GENDER


async def get_gender(update, context):
    language = context.user_data.get("language", "uz")
    text = update.message.text

    if "👨" in text:
        gender = "Erkak"
    elif "👩" in text:
        gender = "Ayol"
    else:
        gender = text

    if gender not in ["Erkak", "Ayol"]:
        await update.message.reply_text(tr(language, "gender_error"))
        return GENDER

    context.user_data["gender"] = gender

    keyboard = ReplyKeyboardMarkup([
        [KeyboardButton("Toshkent"), KeyboardButton("Samarqand")],
        [KeyboardButton("Buxoro"), KeyboardButton("Andijon")],
        [KeyboardButton("Farg'ona"), KeyboardButton("Namangan")],
        [KeyboardButton("Qarshi"), KeyboardButton("Nukus")],
        [KeyboardButton("Xiva"), KeyboardButton("Jizzax")],
        [KeyboardButton("Guliston"), KeyboardButton("Termiz")],
        [KeyboardButton("Navoiy"), KeyboardButton(tr(language, "other"))]
    ], resize_keyboard=True, one_time_keyboard=True)

    await update.message.reply_text(
        f"📍 <b>4/5 — Joylashuv</b>\n\n"
        f"{tr(language, 'choose_city')}",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    return CITY


async def get_city(update, context):
    language = context.user_data.get("language", "uz")
    city = update.message.text.strip()

    cities = {
        "Toshkent", "Samarqand", "Buxoro", "Andijon",
        "Farg'ona", "Namangan", "Qarshi", "Nukus",
        "Xiva", "Jizzax", "Guliston", "Termiz", "Navoiy",
    }

    if city in cities:
        context.user_data["city"] = city
        context.user_data.pop("custom_city", None)

        skip_text = {
            "uz": "⏭ O'tkazib yuborish",
            "ru": "⏭ Пропустить",
            "uz_cyr": "⏭ Ўтказиб юбориш",
        }[language]

        keyboard = ReplyKeyboardMarkup(
            [[KeyboardButton(skip_text)]],
            resize_keyboard=True,
            one_time_keyboard=True
        )

        await update.message.reply_text(
            f"📝 <b>4/5 — Bio</b>\n\n"
            f"{tr(language, 'enter_bio')}\n\n"
            f"{'Ixtiyoriy — xohlasangiz o‘tkazib yuboring.' if language == 'uz' else 'Необязательно — можно пропустить.' if language == 'ru' else 'Ихтиёрий — хоҳласангиз ўтказиб юборинг.'}",
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        return BIO

    if city == tr(language, "other"):
        context.user_data["custom_city"] = True
        await update.message.reply_text(tr(language, "enter_city"))
        return CITY

    if context.user_data.get("custom_city"):
        if len(city) < 2 or len(city) > 50:
            await update.message.reply_text(tr(language, "city_error"))
            return CITY

        context.user_data["city"] = city
        context.user_data.pop("custom_city", None)

        skip_text = {
            "uz": "⏭ O'tkazib yuborish",
            "ru": "⏭ Пропустить",
            "uz_cyr": "⏭ Ўтказиб юбориш",
        }[language]

        keyboard = ReplyKeyboardMarkup(
            [[KeyboardButton(skip_text)]],
            resize_keyboard=True,
            one_time_keyboard=True
        )

        await update.message.reply_text(
            f"📝 <b>4/5 — Bio</b>\n\n"
            f"{tr(language, 'enter_bio')}",
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        return BIO

    await update.message.reply_text(tr(language, "city_choose_error"))
    return CITY


async def get_bio(update, context):
    language = context.user_data.get("language", "uz")
    text = update.message.text.strip()

    skip_texts = {
        "uz": "⏭ O'tkazib yuborish",
        "ru": "⏭ Пропустить",
        "uz_cyr": "⏭ Ўтказиб юбориш",
    }

    if text == skip_texts[language]:
        context.user_data["bio"] = None
    else:
        context.user_data["bio"] = text[:500]

    photo_skip_text = {
        "uz": "⏭ O'tkazib yuborish",
        "ru": "⏭ Пропустить",
        "uz_cyr": "⏭ Ўтказиб юбориш",
    }[language]

    keyboard = ReplyKeyboardMarkup(
        [[KeyboardButton(photo_skip_text)]],
        resize_keyboard=True,
        one_time_keyboard=True
    )

    await update.message.reply_text(
        f"📸 <b>5/5 — Suratlar</b>\n\n"
        f"{tr(language, 'send_photo')}\n\n"
        f"⭐ 1-asosiy foto — <b>majburiy</b>\n"
        f"➕ 2- va 3-foto — <b>ixtiyoriy</b>\n\n"
        f"💡 Yaxshi surat profilga ko‘proq qiziqish olib keladi.\n"
        f"📌 Jami 3 tagacha surat qo‘shishingiz mumkin.",
        reply_markup=keyboard,
        parse_mode="HTML"
    )

    context.user_data["photo_step"] = 1
    return PHOTO


async def get_photo(update, context):
    user = update.effective_user
    language = context.user_data.get("language", "uz")
    step = context.user_data.get("photo_step", 1)

    skip_texts = {
        "uz": "⏭ O'tkazib yuborish",
        "ru": "⏭ Пропустить",
        "uz_cyr": "⏭ Ўтказиб юбориш",
    }

    # 1-asosiy foto majburiy
    if step == 1:
        if not update.message.photo:
            await update.message.reply_text(
                {
                    "uz": "📸 Asosiy foto majburiy. Iltimos, rasmingizni yuboring.",
                    "ru": "📸 Основная фотография обязательна. Отправьте фотографию.",
                    "uz_cyr": "📸 Асосий фото мажбурий. Илтимос, расмингизни юборинг.",
                }[language]
            )
            return PHOTO

    # 2/3-foto ixtiyoriy
    if step > 1 and not update.message.photo:
        if update.message.text and update.message.text.strip() == skip_texts[language]:
            await finish_registration(update, context)
            return ConversationHandler.END

        await update.message.reply_text(
            {
                "uz": "📸 Iltimos, foto yuboring yoki «O'tkazib yuborish»ni bosing.",
                "ru": "📸 Отправьте фото или нажмите «Пропустить».",
                "uz_cyr": "📸 Илтимос, фото юборинг ёки «Ўтказиб юбориш»ни босинг.",
            }[language]
        )
        return PHOTO

    photo = update.message.photo[-1].file_id

    conn = get_db_connection()
    cur = conn.cursor()

    try:
        # Birinchi foto users.photo ga ham yoziladi — eski tizim buzilmasligi uchun
        if step == 1:
            cur.execute("""
                INSERT INTO users (
                    user_id, username, first_name, age, gender,
                    bio, photo, city, language
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (user_id) DO UPDATE SET
                    first_name = EXCLUDED.first_name,
                    age = EXCLUDED.age,
                    gender = EXCLUDED.gender,
                    bio = EXCLUDED.bio,
                    photo = EXCLUDED.photo,
                    city = EXCLUDED.city,
                    language = EXCLUDED.language
            """, (
                user.id,
                user.username,
                context.user_data.get("profile_name", user.first_name),
                context.user_data["age"],
                context.user_data["gender"],
                context.user_data.get("bio"),
                photo,
                context.user_data["city"],
                language,
            ))

            # Oldingi rasmlarni tozalaymiz
            cur.execute(
                "DELETE FROM user_photos WHERE user_id = %s",
                (user.id,)
            )

        # Foto tartibi: 1 asosiy, 2 qo‘shimcha, 3 qo‘shimcha
        cur.execute("""
            INSERT INTO user_photos (user_id, photo, position)
            VALUES (%s, %s, %s)
            ON CONFLICT (user_id, position)
            DO UPDATE SET photo = EXCLUDED.photo
        """, (user.id, photo, step))

        conn.commit()

    except Exception as e:
        conn.rollback()
        print(f"Photo save error: {e}")
        await update.message.reply_text(
            {
                "uz": "❌ Rasmni saqlashda xatolik yuz berdi. Qaytadan urinib ko‘ring.",
                "ru": "❌ Ошибка сохранения фотографии. Попробуйте ещё раз.",
                "uz_cyr": "❌ Расмни сақлашда хатолик юз берди. Қайтадан уриниб кўринг.",
            }[language]
        )
        return PHOTO

    finally:
        cur.close()
        conn.close()

    if step < 3:
        context.user_data["photo_step"] = step + 1

        next_text = {
            2: {
                "uz": "📸 <b>2/3 — Qo‘shimcha foto</b>\n\nSurat yuboring yoki ⏭ O‘tkazib yuboring.",
                "ru": "📸 <b>2/3 — Дополнительное фото</b>\n\nОтправьте фото или нажмите ⏭ Пропустить.",
                "uz_cyr": "📸 <b>2/3 — Қўшимча фото</b>\n\nРасм юборинг ёки ⏭ Ўтказиб юборинг.",
            },
            3: {
                "uz": "📸 <b>3/3 — So‘nggi foto</b>\n\nSurat yuboring yoki ⏭ O‘tkazib yuboring.",
                "ru": "📸 <b>3/3 — Последнее фото</b>\n\nОтправьте фото или нажмите ⏭ Пропустить.",
                "uz_cyr": "📸 <b>3/3 — Сўнгги фото</b>\n\nРасм юборинг ёки ⏭ Ўтказиб юборинг.",
            },
        }[step + 1][language]

        keyboard = ReplyKeyboardMarkup(
            [[KeyboardButton(skip_texts[language])]],
            resize_keyboard=True,
            one_time_keyboard=True
        )

        await update.message.reply_text(
            next_text,
            reply_markup=keyboard
        )
        return PHOTO

    await finish_registration(update, context)
    return ConversationHandler.END


async def finish_registration(update, context):
    user = update.effective_user
    language = context.user_data.get("language", "uz")

    # Referral tizimi eski get_photo funksiyasidan saqlanadi
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        referrer_id = context.user_data.get("referrer_id")

        if referrer_id and referrer_id != user.id:
            cur.execute(
                "SELECT user_id FROM users WHERE user_id = %s",
                (referrer_id,)
            )
            referrer_exists = cur.fetchone()

            if referrer_exists:
                cur.execute("""
                    UPDATE users
                    SET referred_by = %s
                    WHERE user_id = %s
                      AND referred_by IS NULL
                """, (referrer_id, user.id))

                if cur.rowcount > 0:
                    cur.execute(
                        "SELECT COUNT(*) FROM users WHERE referred_by = %s",
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

                        cur.execute("""
                            INSERT INTO referral_rewards
                            (user_id, referrals_count, premium_days)
                            VALUES (%s, %s, %s)
                            ON CONFLICT (user_id, referrals_count)
                            DO NOTHING
                        """, (referrer_id, referral_count, premium_days))

                        if cur.rowcount > 0:
                            cur.execute(
                                "SELECT premium_until FROM users WHERE user_id = %s",
                                (referrer_id,)
                            )
                            old_premium_until = cur.fetchone()[0]

                            cur.execute("""
                                UPDATE users
                                SET premium_until =
                                    CASE
                                        WHEN premium_until IS NOT NULL
                                             AND premium_until > NOW()
                                        THEN premium_until + (%s * INTERVAL '1 day')
                                        ELSE NOW() + (%s * INTERVAL '1 day')
                                    END
                                WHERE user_id = %s
                            """, (
                                premium_days,
                                premium_days,
                                referrer_id
                            ))

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
                            except Exception:
                                pass

        context.user_data.pop("referrer_id", None)
        conn.commit()

    except Exception as e:
        conn.rollback()
        print(f"Referral finish error: {e}")

    finally:
        cur.close()
        conn.close()

    # Admin notification
    try:
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=(
                "🆕 YANGI FOYDALANUVCHI\n\n"
                f"👤 Ism: {context.user_data.get('profile_name', user.first_name)}\n"
                f"📱 Username: @{user.username or 'yoq'}\n"
                f"🆔 ID: {user.id}\n"
                f"🎂 Yosh: {context.user_data.get('age', '?')}\n"
                f"👤 Jins: {context.user_data.get('gender', '?')}\n"
                f"📍 Shahar: {context.user_data.get('city', '?')}\n"
                f"📝 Bio: {context.user_data.get('bio') or 'yoq'}"
            )
        )
    except Exception as e:
        print(f"❌ ADMIN NEW USER NOTIFICATION ERROR: {e}")

    try:
        await notify_new_user_in_city(context.bot, user.id)
    except Exception as e:
        print(f"Smart city notification error: {e}")

    welcome = {
        "uz": (
            "💫 <b>SaraMatchBot'ga xush kelibsiz!</b>\n\n"
            "Bu yerda siz yangi insonlar bilan tanishishingiz mumkin.\n\n"
            "❤️ Layk bosing — agar siz ham yoqsangiz, match bo‘ladi.\n"
            "👎 Yoqmasa — o‘tkazib yuboring.\n\n"
            "✨ <b>Tanishuvni hoziroq boshlang 👇</b>"
        ),
        "ru": (
            "💫 <b>Добро пожаловать в SaraMatchBot!</b>\n\n"
            "Здесь вы можете знакомиться с новыми людьми.\n\n"
            "❤️ Ставьте лайк — если симпатия взаимна, будет match.\n"
            "👎 Не нравится — пропускайте.\n\n"
            "✨ <b>Начните знакомство прямо сейчас 👇</b>"
        ),
        "uz_cyr": (
            "💫 <b>SaraMatchBot'га хуш келибсиз!</b>\n\n"
            "Бу ерда сиз янги инсонлар билан танишишингиз мумкин.\n\n"
            "❤️ Лайк босинг — агар сиз ҳам ёқсангиз, матч бўлади.\n"
            "👎 Ёқмаса — ўтказиб юборинг.\n\n"
            "✨ <b>Танишувни ҳозироқ бошланг 👇</b>"
        ),
    }

    await update.message.reply_text(
        welcome.get(language, welcome["uz"]),
        reply_markup=await get_main_keyboard(language),
        parse_mode="HTML"
    )

    # vaqtinchalik registration ma'lumotlarini tozalash
    for key in [
        "profile_name", "age", "gender", "city", "bio",
        "language", "custom_city", "photo_step"
    ]:
        context.user_data.pop(key, None)


async def find(update, context):
    if update.callback_query:
        message = update.callback_query.message
        user = update.callback_query.from_user
    else:
        message = update.message
        user = update.effective_user

    language = get_user_language(user.id)

    texts = {
        "uz": {
            "no_profile": "❌ Avval profil yarating. /start bosing.",
            "limit": "🚫 Bugungi 20 ta profil limitingiz tugadi.\n\n👑 Premiumga o'tib, profillarni cheksiz ko'rishingiz mumkin.",
            "no_profiles": "😔 Hozircha yangi profillar qolmagan.",
            "dislike": "👎 Yoqmadi",
            "like": "❤️ Yoqdi",
            "superlike": "⭐ Superlike",
            "write": "✉️ Yozish",
            "no_bio": "Bio yozilmagan",
        },
        "ru": {
            "no_profile": "❌ Сначала создайте профиль. Нажмите /start.",
            "limit": "🚫 Вы достигли дневного лимита в 20 профилей.\n\n👑 С Премиумом вы сможете просматривать профили без ограничений.",
            "no_profiles": "😔 Новых профилей пока нет.",
            "dislike": "👎 Не нравится",
            "like": "❤️ Нравится",
            "superlike": "⭐ Суперлайк",
            "write": "✉️ Написать",
            "no_bio": "Биография не указана",
        },
        "uz_cyr": {
            "no_profile": "❌ Аввал профил яратинг. /start босинг.",
            "limit": "🚫 Бугунги 20 та профиль лимитингиз тугади.\n\n👑 Premium билан профилларни чексиз кўришингиз мумкин.",
            "no_profiles": "😔 Ҳозирча янги профиллар қолмаган.",
            "dislike": "👎 Ёқмади",
            "like": "❤️ Ёқди",
            "superlike": "⭐ Суперлайк",
            "write": "✉️ Ёзиш",
            "no_bio": "Био ёзилмаган",
        },
        }

    t = texts.get(language, texts["uz"])

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute(
        "SELECT gender, city, premium_until FROM users WHERE user_id = %s",
        (user.id,),
    )
    user_data = cur.fetchone()

    if not user_data:
        cur.close()
        conn.close()
        await message.reply_text(t["no_profile"])
        return

    my_gender, my_city, premium_until = user_data

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

        if today_count >= 20:
            cur.close()
            conn.close()
            await message.reply_text(t["limit"])
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
        (user.id, user.id, user.id, user.id, my_city),
    )

    target = cur.fetchone()

    if not target:
        cur.close()
        conn.close()
        await message.reply_text(t["no_profiles"])
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

    premium_badge = "\n👑 PREMIUM" if target_is_premium else ""

    buttons = [[
        InlineKeyboardButton(
            t["dislike"],
            callback_data=f"skip_{target_id}"
        ),
        InlineKeyboardButton(
            t["like"],
            callback_data=f"like_{target_id}"
        ),
        InlineKeyboardButton(
            t["superlike"],
            callback_data=f"superlike_{target_id}"
        ),
    ]]

    if is_premium:
        buttons.append([
            InlineKeyboardButton(
                t["write"],
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
            f"📝 {bio or t['no_bio']}"
        ),
        reply_markup=keyboard,
    )

async def handle_callback(update, context):
    query = update.callback_query
    await query.answer()
    user = query.from_user
    language = get_user_language(user.id)
    data = query.data
    
    if data.startswith("like_back_"):
        try:
            target_id = int(data.split("_", 2)[2])
        except (ValueError, IndexError):
            await query.answer("❌ Xato.", show_alert=True)
            return

        conn = get_db_connection()
        cur = conn.cursor()
        match_created = False

        try:
            # Like qaytarishni qo'shamiz
            cur.execute("""
                INSERT INTO likes (from_user, to_user)
                VALUES (%s, %s)
                ON CONFLICT DO NOTHING
            """, (user.id, target_id))

            # Qarshi tomon ham Like qilganmi?
            cur.execute("""
                SELECT EXISTS(
                    SELECT 1
                    FROM likes
                    WHERE from_user = %s
                      AND to_user = %s
                )
            """, (target_id, user.id))

            mutual_like = bool(cur.fetchone()[0])

            if mutual_like:
                # Match allaqachon mavjudmi?
                cur.execute("""
                    SELECT EXISTS(
                        SELECT 1
                        FROM matches
                        WHERE
                            (user1 = %s AND user2 = %s)
                            OR
                            (user1 = %s AND user2 = %s)
                    )
                """, (user.id, target_id, target_id, user.id))

                match_exists = bool(cur.fetchone()[0])

                if not match_exists:
                    cur.execute("""
                        INSERT INTO matches (user1, user2)
                        VALUES (%s, %s)
                    """, (user.id, target_id))

                    match_created = True

            conn.commit()

        except Exception:
            conn.rollback()
            raise

        finally:
            cur.close()
            conn.close()

        if match_created:
            # Ikkala tomon uchun ism
            conn = get_db_connection()
            cur = conn.cursor()

            cur.execute(
                "SELECT first_name FROM users WHERE user_id = %s",
                (target_id,)
            )
            target_row = cur.fetchone()
            target_name = (
                target_row[0]
                if target_row and target_row[0]
                else "Foydalanuvchi"
            )

            cur.execute(
                "SELECT first_name FROM users WHERE user_id = %s",
                (user.id,)
            )
            sender_row = cur.fetchone()
            sender_name = (
                sender_row[0]
                if sender_row and sender_row[0]
                else "Foydalanuvchi"
            )

            cur.close()
            conn.close()

            await query.answer("🎉 MATCH! ❤️", show_alert=True)

            # Ikkala tomon uchun Match xabari + "Suhbatni boshlash" tugmasi
            await notify_new_match(
                context.bot,
                user.id,
                sender_name,
                None,
                target_id,
                target_name,
                None
            )

        else:
            await query.answer(
                "❤️ Like qaytarildi!",
                show_alert=False
            )

        return

    if data.startswith("who_like:"):
        try:
            target_id = int(data.split(":", 1)[1])
        except (ValueError, IndexError):
            await query.answer("❌ Xato.", show_alert=True)
            return

        conn = get_db_connection()
        cur = conn.cursor()

        match_created = False
        already_liked = False

        try:
            # Biz targetga oldin Like bosganmizmi?
            cur.execute("""
                SELECT EXISTS(
                    SELECT 1
                    FROM likes
                    WHERE from_user = %s
                      AND to_user = %s
                )
            """, (user.id, target_id))

            already_liked = bool(cur.fetchone()[0])

            # Agar hali Like bosmagan bo'lsak — Like qo'shamiz
            if not already_liked:
                cur.execute("""
                    INSERT INTO likes (from_user, to_user)
                    VALUES (%s, %s)
                    ON CONFLICT DO NOTHING
                """, (user.id, target_id))

            # Target ham bizga Like bosganmi?
            cur.execute("""
                SELECT EXISTS(
                    SELECT 1
                    FROM likes
                    WHERE from_user = %s
                      AND to_user = %s
                )
            """, (target_id, user.id))

            other_like = bool(cur.fetchone()[0])

            # Ikkala tomon Like bosgan bo'lsa — MATCH
            if other_like:
                cur.execute("""
                    SELECT EXISTS(
                        SELECT 1
                        FROM matches
                        WHERE
                            (user1 = %s AND user2 = %s)
                            OR
                            (user1 = %s AND user2 = %s)
                    )
                """, (user.id, target_id, target_id, user.id))

                match_exists = bool(cur.fetchone()[0])

                if not match_exists:
                    cur.execute("""
                        INSERT INTO matches (user1, user2)
                        VALUES (%s, %s)
                    """, (user.id, target_id))

                    match_created = True

            conn.commit()

        except Exception:
            conn.rollback()
            raise

        finally:
            cur.close()
            conn.close()

        if match_created:
            # Qarshi tomonning ismini olish
            conn = get_db_connection()
            cur = conn.cursor()

            cur.execute(
                "SELECT first_name FROM users WHERE user_id = %s",
                (target_id,)
            )
            target_row = cur.fetchone()
            target_name = target_row[0] if target_row and target_row[0] else "Foydalanuvchi"

            cur.execute(
                "SELECT first_name FROM users WHERE user_id = %s",
                (user.id,)
            )
            sender_row = cur.fetchone()
            sender_name = sender_row[0] if sender_row and sender_row[0] else "Foydalanuvchi"

            cur.close()
            conn.close()

            # Sizga
            await query.answer("🎉 MATCH! ❤️", show_alert=True)

            # Ikkala tomon uchun Match xabari + "Suhbatni boshlash" tugmasi
            await notify_new_match(
                context.bot,
                user.id,
                sender_name,
                None,
                target_id,
                target_name,
                None
            )

        elif already_liked:
            await query.answer(
                "❤️ Siz allaqachon Like bosgansiz.",
                show_alert=False
            )
        else:
            await query.answer(
                "❤️ Like yuborildi!",
                show_alert=False
            )

        return

    if data == "who_liked_menu":
        await who_liked_me(update, context)
        return

    if data == "change_language":
        await change_language_menu(update, context)
        return

    if data == "set_language_uz":
        await save_language(update, context, "uz")
        return

    if data == "set_language_ru":
        await save_language(update, context, "ru")
        return

    if data == "set_language_uz_cyr":
        await save_language(update, context, "uz_cyr")
        return

    if data == "cancel_language":
        await query.answer()
        await query.message.reply_text(
            "⚙️ Sozlamalar:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(
                    "🌐 Tilni o'zgartirish",
                    callback_data="change_language"
                )],
                [InlineKeyboardButton(
                    "👑 Premium",
                    callback_data="premium_buy"
                )]
            ])
        )
        return

    if data == "premium_buy":
        language = get_user_language(user.id)
        if language == "ru":
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("1 неделя - 25 000 сум", callback_data="premium_1w")],
                [InlineKeyboardButton("14 дней - 39 000 сум", callback_data="premium_2w")],
                [InlineKeyboardButton("1 месяц - 59 000 сум", callback_data="premium_1m")],
                [InlineKeyboardButton("3 месяца - 129 000 сум", callback_data="premium_3m")],
                [InlineKeyboardButton("❌ Отмена", callback_data="cancel")]
            ])
            await query.message.reply_text("👑 ПРЕМИУМ\n\n♾️ Безлимитный просмотр профилей\n❤️ Безлимитные лайки\n⭐ Superlike бесплатно\n💬 Сообщения без матча\n📨 Сообщения в личный Telegram\n👀 Видеть кто отправил вам Superlike\n🚀 Ваш профиль показывается одним из первых\n👀 Видеть кто вас лайкнул\n📈 Всегда наверху\n⚡️ Увеличьте возможности в 5 раз\n\n📅 Выберите срок:", reply_markup=keyboard)
        elif language == "uz_cyr":
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("1 ҳафта - 25 000 сўм", callback_data="premium_1w")],
                [InlineKeyboardButton("14 кун - 39 000 сўм", callback_data="premium_2w")],
                [InlineKeyboardButton("1 ой - 59 000 сўм", callback_data="premium_1m")],
                [InlineKeyboardButton("3 ой - 129 000 сўм", callback_data="premium_3m")],
                [InlineKeyboardButton("❌ Бекор қилиш", callback_data="cancel")]
            ])
            await query.message.reply_text("👑 ПРЕМИУМ\n\n♾️ Чексиз профиль кўриш\n❤️ Чексиз лайк\n⭐ Superlike бепул\n💬 Матчсиз ёзиш\n📨 Telegram шахсий чатига ёзиш\n👀 Сизга ким Superlike юборганини кўриш\n🚀 Профилингиз қидирувда энг биринчи кўрсатилади\n👀 Сизни ким ёқтирганини кўриш\n📈 Доим юқорида кўриниш\n⚡️ Имкониятларингизни 5× ошириш\n\n📅 Муддатни танланг:", reply_markup=keyboard)
        else:
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("1 hafta - 25 000 so'm", callback_data="premium_1w")],
                [InlineKeyboardButton("14 kun - 39 000 so'm", callback_data="premium_2w")],
                [InlineKeyboardButton("1 oy - 59 000 so'm", callback_data="premium_1m")],
                [InlineKeyboardButton("3 oy - 129 000 so'm", callback_data="premium_3m")],
                [InlineKeyboardButton("❌ Bekor qilish", callback_data="cancel")]
            ])
            await query.message.reply_text("👑 PREMIUM\n\n♾️ Cheksiz profil ko‘rish\n❤️ Cheksiz layk\n⭐ Superlike bepul\n💬 Match bo‘lmasdan yozish\n📨 Telegram shaxsiy chatiga yozish\n👀 Sizga kim Superlike yuborganini ko‘rish\n🚀 Profilingiz qidiruvda eng birinchilardan ko‘rsatiladi\n👀 Sizni kim yoqtirganini ko‘rish\n📈 Doim yuqorida ko‘rinish\n⚡️ Imkoniyatlaringizni 5× oshiring\n\n📅 Muddatni tanlang:", reply_markup=keyboard)
        return

        premium_texts = {
            "ru": {
                "title": "👑 <b>ПРЕМИУМ</b>",
                "intro": "💎 Расширьте свои возможности знакомств!",
                "features": (
                    "♾️ <b>Безлимитный просмотр</b> — открывайте больше людей\n"
                    "❤️ <b>Безлимитные лайки</b> — не упускайте возможности\n"
                    "✉️ <b>Пишите без матча</b> — сразу начинайте общение\n"
                    "👀 <b>Видеть кто лайкнул</b> — знайте кто вами интересуется\n"
                    "⭐️ <b>Значок Premium</b> — выделяйтесь\n"
                    "🚀 <b>Приоритет профиля</b> — больше просмотров"
                ),
                "reason": "🔥 <b>Больше просмотров → больше лайков → больше матчей!</b>",
                "choose": "✨ Выберите подходящий тариф:",
                "duration": "📅 <b>Выберите срок:</b>",
                "week": "📅 1 неделя - 25 000 сум • УДОБНО",
                "two_weeks": "🔥 14 дней - 39 000 сум • ВЫГОДНО",
                "month": "⭐️ 1 месяц - 59 000 сум • ПОПУЛЯРНО",
                "three_months": "👑 3 месяца - 129 000 сум • ЭКОНОМНО",
                "cancel": "❌ Отмена",
            },
            "uz_cyr": {
                "title": "👑 <b>ПРЕМИУМ</b>",
                "intro": "💎 Танишув имкониятларингизни кенгайтиринг!",
                "features": (
                    "♾️ <b>Чексиз профил кўриш</b> — кўпроқ одамларни кашф этинг\n"
                    "❤️ <b>Чексиз Like</b> — имкониятларни қўлдан бой берманг\n"
                    "✉️ <b>Матчни кутмасдан ёзинг</b> — ёққан инсонингиз билан дарҳол суҳбат бошланг\n"
                    "👀 <b>Сизни ким ёқтирганини кўринг</b> — ким сизга қизиқаётганини билинг\n"
                    "⭐️ <b>Premium белгиси</b> — профилингизни ажратиб туринг\n"
                    "🚀 <b>Профил устуворлиги</b> — кўпроқ кўринишга эга бўлинг"
                ),
                "reason": "🔥 <b>Кўпроқ кўриниш → кўпроқ Like → кўпроқ Match!</b>",
                "choose": "✨ Ўзингизга мос Premium тарифини танланг:",
                "duration": "📅 <b>Муддатни танланг:</b>",
                "week": "📅 1 ҳафта - 25 000 сўм • ҚУЛАЙ",
                "two_weeks": "🔥 14 кун - 39 000 сўм • ЭНГ ҚУЛАЙ",
                "month": "⭐️ 1 ой - 59 000 сўм • ОММАБОП",
                "three_months": "👑 3 ой - 129 000 сўм • ТЕЖАМКОР",
                "cancel": "❌ Бекор қилиш",
            },
            "uz": {
                "title": "👑 <b>PREMIUM</b>",
                "intro": (
                    "💎 Premium bilan tanishuv imkoniyatlaringizni "
                    "yanada kengaytiring!"
                ),
                "features": (
                    "♾️ <b>Cheksiz profil ko'rish</b> — ko'proq odamlarni kashf eting\n"
                    "❤️ <b>Cheksiz Like</b> — imkoniyatlarni o'tkazib yubormang\n"
                    "✉️ <b>Matchni kutmasdan yozing</b> — yoqqan insoningiz bilan darhol suhbat boshlang\n"
                    "👀 <b>Sizni kim yoqtirganini ko'ring</b> — kim sizga qiziqayotganini biling\n"
                    "⭐️ <b>Premium belgisi</b> — profilingizni ajratib turing\n"
                    "🚀 <b>Profil ustuvorligi</b> — ko'proq ko'rinishga ega bo'ling"
                ),
                "reason": "🔥 <b>Ko'proq ko'rinish → ko'proq Like → ko'proq Match!</b>",
                "choose": "✨ O'zingizga mos Premium tarifini tanlang:",
                "duration": "📅 <b>Muddatni tanlang:</b>",
                "week": "📅 1 hafta - 25 000 so'm • QULAY",
                "two_weeks": "🔥 14 kun - 39 000 so'm • ENG QULAY",
                "month": "⭐️ 1 oy - 59 000 so'm • OMMABOP",
                "three_months": "👑 3 oy - 129 000 so'm • TEJAMKOR",
                "cancel": "❌ Bekor qilish",
            },
            }

        t = premium_texts.get(language, premium_texts["uz"])

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(t["week"], callback_data="premium_1w")],
            [InlineKeyboardButton(t["two_weeks"], callback_data="premium_2w")],
            [InlineKeyboardButton(t["month"], callback_data="premium_1m")],
            [InlineKeyboardButton(t["three_months"], callback_data="premium_3m")],
            [InlineKeyboardButton(t["cancel"], callback_data="cancel_premium")]
        ])

        await query.message.reply_text(
            f'{t["title"]}\n\n'
            f'{t["intro"]}\n\n'
            f'{t["features"]}\n\n'
            f'{t["reason"]}\n\n'
            f'{t["choose"]}\n\n'
            f'{t["duration"]}',
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        return

    if data == "premium_expiring_discount":
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            """
            SELECT premium_until
            FROM users
            WHERE user_id = %s
              AND premium_until IS NOT NULL
              AND premium_until > NOW()
              AND premium_until <= NOW() + INTERVAL '24 hours'
            """,
            (user.id,)
        )
        valid = cur.fetchone()
        cur.close()
        conn.close()

        if not valid:
            texts = {
                "uz": "❌ 20% chegirma faqat Premium tugashiga 1 kun qolganda amal qiladi.",
                "ru": "❌ Скидка 20% действует только в последний день Premium.",
                "uz_cyr": "❌ 20% чегирма фақат Premiumнинг охирги куни амал қилади."
            }
            await query.message.reply_text(
                texts.get(language, texts["uz"])
            )
            return

        if language == "ru":
            text = (
                "🔥 20% СКИДКА — ТОЛЬКО СЕГОДНЯ!\n\n"
                "👑 Ваш Premium заканчивается в течение 1 дня.\n"
                "💎 Успейте продлить Premium со скидкой 20%!\n\n"
                "📅 Выберите срок:"
            )
            buttons = [
                ["1 неделя - 20 000 сум 🔥", "discount_premium_1w"],
                ["14 дней - 31 200 сум 🔥", "discount_premium_2w"],
                ["1 месяц - 47 200 сум 🔥", "discount_premium_1m"],
                ["3 месяца - 103 200 сум 🔥", "discount_premium_3m"],
            ]
            cancel = "❌ Отмена"

        elif language == "uz_cyr":
            text = (
                "🔥 20% ЧЕГИРМА — ФАҚАТ БУГУН!\n\n"
                "👑 Premiumингиз 1 кун ичида тугайди.\n"
                "💎 Premiumни 20% чегирма билан узайтиришга улгуринг!\n\n"
                "📅 Муддатни танланг:"
            )
            buttons = [
                ["1 ҳафта - 20 000 сўм 🔥", "discount_premium_1w"],
                ["14 кун - 31 200 сўм 🔥", "discount_premium_2w"],
                ["1 ой - 47 200 сўм 🔥", "discount_premium_1m"],
                ["3 ой - 103 200 сўм 🔥", "discount_premium_3m"],
            ]
            cancel = "❌ Бекор қилиш"

        else:
            text = (
                "🔥 20% CHEGIRMA — FAQAT BUGUN!\n\n"
                "👑 Premiumingiz 1 kun ichida tugaydi.\n"
                "💎 Premiumni 20% chegirma bilan uzaytirishga ulgurib qoling!\n\n"
                "📅 Muddatni tanlang:"
            )
            buttons = [
                ["1 hafta - 20 000 so'm 🔥", "discount_premium_1w"],
                ["14 kun - 31 200 so'm 🔥", "discount_premium_2w"],
                ["1 oy - 47 200 so'm 🔥", "discount_premium_1m"],
                ["3 oy - 103 200 so'm 🔥", "discount_premium_3m"],
            ]
            cancel = "❌ Bekor qilish"

        keyboard = InlineKeyboardMarkup(
            [[InlineKeyboardButton(label, callback_data=data)] for label, data in buttons]
            + [[InlineKeyboardButton(cancel, callback_data="cancel_premium")]]
        )

        await query.message.reply_text(
            text,
            reply_markup=keyboard
        )
        return

    if data.startswith("discount_premium_"):
        plan = data.replace("discount_", "", 1)

        durations = {
            "premium_1w": 7,
            "premium_2w": 14,
            "premium_1m": 30,
            "premium_3m": 90
        }

        prices = {
            "premium_1w": "20 000",
            "premium_2w": "31 200",
            "premium_1m": "47 200",
            "premium_3m": "103 200"
        }

        if plan not in durations:
            return

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            """
            SELECT premium_until
            FROM users
            WHERE user_id = %s
              AND premium_until IS NOT NULL
              AND premium_until > NOW()
              AND premium_until <= NOW() + INTERVAL '24 hours'
            """,
            (user.id,)
        )
        valid = cur.fetchone()
        cur.close()
        conn.close()

        if not valid:
            texts = {
                "uz": "❌ 20% chegirma faqat Premiumning oxirgi kunida amal qiladi.",
                "ru": "❌ Скидка 20% действует только в последний день Premium.",
                "uz_cyr": "❌ 20% чегирма фақат Premiumнинг охирги куни амал қилади."
            }
            await query.message.reply_text(
                texts.get(language, texts["uz"])
            )
            return

        days = durations[plan]
        price = prices[plan]

        payment_texts = {
            "uz": ("💳 TO‘LOV USULINI TANLANG", "📅 Muddat", "💰 Chegirmali summa",
                   "Quyidagi to‘lov usullaridan birini tanlang:", "❌ Bekor qilish"),
            "ru": ("💳 ВЫБЕРИТЕ СПОСОБ ОПЛАТЫ", "📅 Срок", "💰 Сумма со скидкой",
                   "Выберите способ оплаты:", "❌ Отмена"),
            "uz_cyr": ("💳 ТЎЛОВ УСУЛИНИ ТАНЛАНГ", "📅 Муддат", "💰 Чегирмали сумма",
                       "Қуйидаги тўлов усулларидан бирини танланг:", "❌ Бекор қилиш")
        }

        title, duration_text, price_text, choose_text, cancel_text = payment_texts.get(
            language, payment_texts["uz"]
        )

        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "💳 HUMO",
                    callback_data=f"discount_pay_humo_{plan}"
                ),
                InlineKeyboardButton(
                    "💳 VISA",
                    callback_data=f"discount_pay_visa_{plan}"
                )
            ],
            [
                InlineKeyboardButton(
                    cancel_text,
                    callback_data="cancel_premium"
                )
            ]
        ])

        await query.message.reply_text(
            f"{title}\n\n"
            f"{duration_text}: {days} kun\n"
            f"{price_text}: {price} so'm\n\n"
            f"{choose_text}",
            reply_markup=keyboard
        )
        return

    if data.startswith("premium_"):
        durations = {
            "premium_1w": 7,
            "premium_2w": 14,
            "premium_1m": 30,
            "premium_3m": 90
        }

        prices = {
            "premium_1w": "25 000",
            "premium_2w": "39 000",
            "premium_1m": "59 000",
            "premium_3m": "129 000"
        }

        if data not in durations:
            return

        days = durations[data]
        price = prices[data]

        payment_texts = {
            "ru": {
                "title": "💳 ВЫБЕРИТЕ СПОСОБ ОПЛАТЫ",
                "duration": "📅 Срок",
                "price": "💰 Сумма",
                "choose": "Выберите способ оплаты:",
                "cancel": "❌ Отмена",
            },
            "uz_cyr": {
                "title": "💳 ТЎЛОВ УСУЛИНИ ТАНЛАНГ",
                "duration": "📅 Муддат",
                "price": "💰 Сумма",
                "choose": "Қуйидаги тўлов усулларидан бирини танланг:",
                "cancel": "❌ Бекор қилиш",
            },
            "uz": {
                "title": "💳 TO'LOV USULINI TANLANG",
                "duration": "📅 Muddat",
                "price": "💰 Summa",
                "choose": "Quyidagi to'lov usullaridan birini tanlang:",
                "cancel": "❌ Bekor qilish",
            },
            }

        pt = payment_texts.get(language, payment_texts["uz"])

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
                    pt["cancel"],
                    callback_data="cancel_premium"
                )
            ]
        ])

        await query.message.reply_text(
            f'{pt["title"]}\n\n'
            f'{pt["duration"]}: {days} kun\n'
            f'{pt["price"]}: {price} so\'m\n\n'
            f'{pt["choose"]}',
            reply_markup=keyboard
        )
        return

    if data.startswith("discount_pay_humo_") or data.startswith("discount_pay_visa_"):
        parts = data.split("_", 3)

        if len(parts) != 4:
            await query.message.reply_text("❌ To‘lov ma’lumotlari xato.")
            return

        payment_method = parts[2].upper()
        plan = parts[3]

        durations = {
            "premium_1w": 7,
            "premium_2w": 14,
            "premium_1m": 30,
            "premium_3m": 90
        }

        prices = {
            "premium_1w": "20 000",
            "premium_2w": "31 200",
            "premium_1m": "47 200",
            "premium_3m": "103 200"
        }

        if plan not in durations:
            await query.message.reply_text("❌ Tarif topilmadi.")
            return

        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute(
            """
            SELECT premium_until
            FROM users
            WHERE user_id = %s
              AND premium_until IS NOT NULL
              AND premium_until > NOW()
              AND premium_until <= NOW() + INTERVAL '24 hours'
            """,
            (user.id,)
        )

        valid = cur.fetchone()
        cur.close()
        conn.close()

        if not valid:
            texts = {
                "uz": "❌ 20% chegirma faqat Premium tugashiga 1 kun qolganda amal qiladi.",
                "ru": "❌ Скидка 20% действует только в последние 24 часа Premium.",
                "uz_cyr": "❌ 20% чегирма фақат Premium тугашига 1 кун қолганда амал қилади."
            }

            await query.message.reply_text(
                texts.get(language, texts["uz"])
            )
            return

        days = durations[plan]
        price = prices[plan]

        card = HUMO_CARD if payment_method == "HUMO" else VISA_CARD

        if not card:
            await query.message.reply_text(
                "❌ Ushbu to‘lov usuli hozircha sozlanmagan."
            )
            return

        context.user_data["pending_payment"] = {
            "type": "premium",
            "days": days,
            "plan": plan,
            "price": price,
            "payment_method": payment_method,
            "user_id": user.id,
            "discount": 20,
            "discounted": True,
        }

        receipt_texts = {
            "uz": (
                "🔥 20% CHEGIRMALI PREMIUM\n\n"
                f"👑 Premium: {days} kun\n"
                f"💰 Chegirmali summa: {price} so'm\n"
                f"💳 To‘lov usuli: {payment_method}\n\n"
                f"💳 Karta: {card}\n\n"
                "📸📄 To‘lov chekini yuboring.\n\n"
                "🖼 Rasm yoki 📄 PDF/fayl yuborishingiz mumkin.\n\n"
                "⚠️ Faqat haqiqiy to‘lov chekini yuboring!\n"
                "⏳ Chek yuborilgach admin tekshiradi."
            ),
            "ru": (
                "🔥 PREMIUM СО СКИДКОЙ 20%\n\n"
                f"👑 Premium: {days} дней\n"
                f"💰 Сумма со скидкой: {price} сум\n"
                f"💳 Способ оплаты: {payment_method}\n\n"
                f"💳 Карта: {card}\n\n"
                "📸📄 Отправьте чек об оплате.\n\n"
                "🖼 Можно отправить изображение или 📄 PDF/файл.\n\n"
                "⚠️ Отправляйте только настоящий чек!\n"
                "⏳ После отправки чек проверит администратор."
            ),
            "uz_cyr": (
                "🔥 20% ЧЕГИРМАЛИ PREMIUM\n\n"
                f"👑 Premium: {days} кун\n"
                f"💰 Чегирмали сумма: {price} сўм\n"
                f"💳 Тўлов усули: {payment_method}\n\n"
                f"💳 Карта: {card}\n\n"
                "📸📄 Тўлов чекини юборинг.\n\n"
                "🖼 Расм ёки 📄 PDF/файл юборишингиз мумкин.\n\n"
                "⚠️ Фақат ҳақиқий тўлов чекини юборинг!\n"
                "⏳ Чек юборилгандан сўнг администратор текширади."
            )
        }

        await query.message.reply_text(
            receipt_texts.get(language, receipt_texts["uz"])
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
            "premium_2w": 14,
            "premium_1m": 30,
            "premium_3m": 90
        }

        prices = {
            "premium_1w": "25 000",
            "premium_2w": "39 000",
            "premium_1m": "59 000",
            "premium_3m": "129 000"
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

        payment_texts = {
            "ru": {
                "title": "💳 ОПЛАТА",
                "method": "💳 Способ",
                "duration": "📅 Срок",
                "price": "💰 Сумма",
                "card": "💳 Карта",
                "done": "После оплаты нажмите «✅ Я оплатил».",
                "paid": "✅ Я оплатил",
                "cancel": "❌ Отмена",
            },
            "uz_cyr": {
                "title": "💳 ТЎЛОВ",
                "method": "💳 Усул",
                "duration": "📅 Муддат",
                "price": "💰 Сумма",
                "card": "💳 Карта",
                "done": "Тўловни амалга оширгач, «✅ Тўлов қилдим» тугмасини босинг.",
                "paid": "✅ Тўлов қилдим",
                "cancel": "❌ Бекор қилиш",
            },
            "uz": {
                "title": "💳 TO'LOV",
                "method": "💳 Usul",
                "duration": "📅 Muddat",
                "price": "💰 Summa",
                "card": "💳 Karta",
                "done": "To'lovni amalga oshirgach, «✅ To'lov qildim» tugmasini bosing.",
                "paid": "✅ To'lov qildim",
                "cancel": "❌ Bekor qilish",
            },
            }

        pt = payment_texts.get(language, payment_texts["uz"])

        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    pt["paid"],
                    callback_data=f"confirm_{payment_method}_{plan}"
                )
            ],
            [
                InlineKeyboardButton(
                    pt["cancel"],
                    callback_data="cancel_premium"
                )
            ]
        ])

        await query.message.reply_text(
            f'{pt["title"]}\n\n'
            f'{pt["method"]}: {payment_method}\n'
            f'{pt["duration"]}: {days} kun\n'
            f'{pt["price"]}: {price} so\'m\n\n'
            f'{pt["card"]}: {card}\n\n'
            f'{pt["done"]}',
            reply_markup=keyboard
        )
        return

    if data.startswith("confirm_"):
        parts = data.split("_", 2)

        if len(parts) != 3:
            await query.message.reply_text(
                "❌ To'lov ma'lumotlari xato."
            )
            return

        payment_method = parts[1].upper()
        plan = parts[2]

        durations = {
            "premium_1w": 7,
            "premium_2w": 14,
            "premium_1m": 30,
            "premium_3m": 90,
        }

        prices = {
            "premium_1w": "25 000",
            "premium_2w": "39 000",
            "premium_1m": "59 000",
            "premium_3m": "129 000",
        }

        if plan not in durations:
            await query.message.reply_text(
                "❌ Tarif topilmadi."
            )
            return

        days = durations[plan]
        price = prices[plan]

        # Chek yuborilgunga qadar foydalanuvchining
        # tanlagan Premium tarifini saqlab qo'yamiz.
        # Chek yuborilgunga qadar to'lov ma'lumotlarini saqlaymiz.
        # handle_payment_check aynan pending_payment ni kutadi.
        context.user_data["pending_payment"] = {
            "type": "premium",
            "days": days,
            "plan": plan,
            "price": price,
            "payment_method": payment_method,
            "user_id": user.id,
        }

        receipt_texts = {
            "uz": (
                "📸📄 TO'LOV CHEKINI YUBORING\n\n"
                f"👑 Premium: {days} kun\n"
                f"💰 Summa: {price} so'm\n"
                f"💳 To'lov usuli: {payment_method}\n\n"
                "🖼 Rasm yoki 📄 PDF/fayl yuborishingiz mumkin.\n\n"
                "⚠️ Faqat haqiqiy to'lov chekini yuboring!\n"
                "🚫 Soxta chek yuborsangiz, darhol botdan bloklanasiz va Premium berilmaydi.\n\n"
                "⏳ Chek yuborilgach admin tekshiradi."
            ),
            "ru": (
                "📸📄 ОТПРАВЬТЕ ЧЕК ОБ ОПЛАТЕ\n\n"
                f"👑 Premium: {days} дней\n"
                f"💰 Сумма: {price} сум\n"
                f"💳 Способ оплаты: {payment_method}\n\n"
                "🖼 Можно отправить изображение или 📄 PDF/файл.\n\n"
                "⚠️ Отправляйте только настоящий чек об оплате!\n"
                "🚫 За поддельный чек вы будете заблокированы, а Premium не будет выдан.\n\n"
                "⏳ После отправки чека его проверит администратор."
            ),
            "uz_cyr": (
                "📸📄 ТЎЛОВ ЧЕКИНИ ЮБОРИНГ\n\n"
                f"👑 Premium: {days} кун\n"
                f"💰 Сумма: {price} сўм\n"
                f"💳 Тўлов усули: {payment_method}\n\n"
                "🖼 Расм ёки 📄 PDF/файл юборишингиз мумкин.\n\n"
                "⚠️ Фақат ҳақиқий тўлов чекини юборинг!\n"
                "🚫 Сохта чек юборсангиз, дарҳол блокланасиз ва Premium берилмайди.\n\n"
                "⏳ Чек юборилгандан сўнг администратор текширади."
            ),
        }

        await query.message.reply_text(
            receipt_texts.get(language, receipt_texts["uz"])
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
    
    if data == "buy_superlikes":
        await buy_superlikes(update, context)
        return

    if data.startswith("sl_"):
        amount = int(data.split("_")[1])

        prices = {
            1: "1 000",
            5: "4 000",
            10: "7 000",
        }

        price = prices[amount]

        language = get_user_language(user.id)
        texts = {
            "uz": {
                "paid": "✅ To'lov qildim",
                "cancel": "❌ Bekor",
                "title": "💳 TO'LOV",
                "amount": f"⭐ {amount} ta Superlike",
                "price": f"💰 Summa: {price} so'm",
                "card": "💳 Karta: 9860 0866 0148 0972",
                "hint": "To'lovni amalga oshiring va «✅ To'lov qildim» tugmasini bosing."
            },
            "ru": {
                "paid": "✅ Я оплатил",
                "cancel": "❌ Отмена",
                "title": "💳 ОПЛАТА",
                "amount": f"⭐ {amount} шт. Superlike",
                "price": f"💰 Сумма: {price} сум",
                "card": "💳 Карта: 9860 0866 0148 0972",
                "hint": "Оплатите и нажмите «✅ Я оплатил»."
            },
            "uz_cyr": {
                "paid": "✅ Тўлов қилдим",
                "cancel": "❌ Бекор",
                "title": "💳 ТЎЛОВ",
                "amount": f"⭐ {amount} та Superlike",
                "price": f"💰 Сумма: {price} сўм",
                "card": "💳 Карта: 9860 0866 0148 0972",
                "hint": "Тўловни амалга оширинг ва «✅ Тўлов қилдим» тугмасини босинг."
            }
        }
        t = texts.get(language, texts["uz"])
        
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    t["paid"],
                    callback_data=f"confirmsl_{amount}"
                )
            ],
            [
                InlineKeyboardButton(
                    t["cancel"],
                    callback_data="cancel_sl"
                )
            ]
        ])

        await query.message.reply_text(
            f"{t['title']}\n\n"
            f"{t['amount']}\n"
            f"{t['price']}\n\n"
            f"{t['card']}\n\n"
            f"{t['hint']}",
            reply_markup=keyboard
        )
        return

    if data.startswith("confirmsl_"):
        amount = int(data.split("_")[1])

        prices = {
            1: "1 000",
            5: "4 000",
            10: "7 000",
        }

        price = prices.get(amount, "?")

        # Foydalanuvchi endi chek yuborishi kerak.
        # Rasm ham, PDF/fayl ham qabul qilinadi.
        context.user_data["pending_payment"] = {
            "type": "superlike",
            "amount": amount,
            "user_id": user.id,
            "price": price,
        }

        language = get_user_language(user.id)

        receipt_prompt = {
            "uz": (
                "📸📄 SUPERLIKE TO'LOV CHEKINI YUBORING\n\n"
                f"⭐ Miqdor: {amount} ta Superlike\n"
                f"💰 Summa: {price} so'm\n\n"
                "🖼 Rasm yoki 📄 PDF/fayl yuborishingiz mumkin.\n\n"
                "⏳ Chek yuborilgach admin tekshiradi."
            ),
            "ru": (
                "📸📄 ОТПРАВЬТЕ ЧЕК ОБ ОПЛАТЕ SUPERLIKE\n\n"
                f"⭐ Количество: {amount} Superlike\n"
                f"💰 Сумма: {price} сум\n\n"
                "🖼 Можно отправить изображение или 📄 PDF/файл.\n\n"
                "⏳ После отправки чек проверит администратор."
            ),
            "uz_cyr": (
                "📸📄 SUPERLIKE ТЎЛОВ ЧЕКИНИ ЮБОРИНГ\n\n"
                f"⭐ Миқдор: {amount} та Superlike\n"
                f"💰 Сумма: {price} сўм\n\n"
                "🖼 Расм ёки 📄 PDF/файл юборишингиз мумкин.\n\n"
                "⏳ Чек юборилгандан сўнг администратор текширади."
            ),
        }

        await query.message.reply_text(
            receipt_prompt.get(language, receipt_prompt["uz"])
        )
        return

    if data.startswith("ok_sl_"):
        try:
            parts = data.split("_")
            user_id = int(parts[2])
            amount = int(parts[3])
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS superlike_balance INTEGER DEFAULT 0")
            cur.execute("UPDATE users SET superlike_balance = COALESCE(superlike_balance, 0) + %s WHERE user_id = %s", (amount, user_id))
            conn.commit()
            cur.close()
            conn.close()
            await query.message.reply_text(f"✅ {amount} ta Superlike tasdiqlandi!")
            try:
                await context.bot.send_message(chat_id=user_id, text=f"🎉 {amount} ta Superlike hisobingizga qo'shildi!")
            except:
                pass
        except Exception as e:
            await query.message.reply_text(f"❌ Xato: {e}")
        return

    if data.startswith("no_sl_"):
        user_id = int(data.split("_")[2])
        await query.message.reply_text("❌ Rad etildi.")
        try:
            await context.bot.send_message(chat_id=user_id, text="❌ To'lovingiz rad etildi.")
        except:
            pass
        return

    if data.startswith("ok_prem_"):
        parts = data.split("_")
        user_id = int(parts[2])
        days = int(parts[3])
        premium_until = datetime.now() + timedelta(days=days)
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("UPDATE users SET premium_until = %s WHERE user_id = %s", (premium_until, user_id))
        conn.commit()
        cur.close()
        conn.close()
        await query.message.reply_text(f"✅ Premium tasdiqlandi! {days} kun")
        try:
            await context.bot.send_message(chat_id=user_id, text=f"🎉 Premium faollashtirildi! {days} kun")
        except:
            pass
        return

    if data.startswith("fake_prem_"):
        if user.id != ADMIN_ID:
            await query.answer(
                "⛔ Sizda bu amalni bajarish huquqi yo'q!",
                show_alert=True
            )
            return

        user_id = int(data.split("_")[2])

        conn = get_db_connection()
        cur = conn.cursor()

        try:
            cur.execute(
                """
                UPDATE users
                SET is_active = FALSE,
                    is_blocked = TRUE
                WHERE user_id = %s
                """,
                (user_id,)
            )

            conn.commit()

        except Exception as e:
            conn.rollback()
            print(f"Fake receipt block error: {e}")

            await query.answer(
                "❌ Foydalanuvchini bloklashda xatolik!",
                show_alert=True
            )

            cur.close()
            conn.close()
            return

        cur.close()
        conn.close()

        # Foydalanuvchiga xabar
        try:
            await context.bot.send_message(
                chat_id=user_id,
                text=(
                    "🚫 HISOBINGIZ BLOKLANDI!\n\n"
                    "Soxta to'lov cheki yuborilgani sababli "
                    "botdan foydalanish imkoniyatingiz bloklandi.\n\n"
                    "❌ Premium berilmadi."
                )
            )
        except Exception as e:
            print(f"Fake receipt user notification error: {e}")

        # Admin xabaridagi tugmalarni olib tashlash
        try:
            await query.message.edit_reply_markup(reply_markup=None)
        except Exception:
            pass

        await query.answer(
            "🚫 Foydalanuvchi bloklandi!",
            show_alert=True
        )

        await query.message.reply_text(
            "🚫 SOXTA CHEK — FOYDALANUVCHI BLOKLANDI\n\n"
            f"🆔 User ID: {user_id}\n"
            "🔒 Status: BLOCKED\n"
            "❌ Premium: berilmadi"
        )

        return

    if data.startswith("no_prem_"):
        user_id = int(data.split("_")[2])
        await query.message.reply_text("❌ Rad etildi.")
        try:
            await context.bot.send_message(chat_id=user_id, text="❌ To'lovingiz rad etildi.")
        except:
            pass
        return

    if data == "cancel_sl":
        await query.message.reply_text("❌ Bekor qilindi.")
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
        context.user_data["edit_field"] = "photo"

        language = get_user_language(user.id)

        texts = {
            "uz": (
                "📸 <b>Rasmni o‘zgartirish</b>\n\n"
                "Yangi profilingiz rasmini yuboring.\n"
                "✨ Yangi rasm avvalgi asosiy rasm o‘rniga saqlanadi."
            ),
            "ru": (
                "📸 <b>Изменение фотографии</b>\n\n"
                "Отправьте новую фотографию профиля.\n"
                "✨ Новая фотография заменит основную фотографию."
            ),
            "uz_cyr": (
                "📸 <b>Расмни ўзгартириш</b>\n\n"
                "Янги профил расмингизни юборинг.\n"
                "✨ Янги расм асосий расм ўрнига сақланади."
            ),
        }

        await query.message.reply_text(
            texts.get(language, texts["uz"]),
            parse_mode="HTML"
        )
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

    # =========================================================
    # CHAT: SUHBATNI TUGATISH
    # =========================================================
    if data == "end_chat":
        context.user_data.pop("writing_to", None)

        await query.answer("❌ Suhbat tugatildi.")
        await query.message.reply_text(
            "❌ Suhbat tugatildi.\n\n"
            "Yana yozish uchun Matchlarim bo‘limidan suhbatni boshlashingiz mumkin."
        )
        return

    # =========================================================
    # CHAT: JAVOB BERISH
    # =========================================================
    if data.startswith("reply_"):
        try:
            target_id = int(data.split("_", 1)[1])
        except (ValueError, IndexError):
            await query.answer("❌ Xato.", show_alert=True)
            return

        conn = get_db_connection()
        cur = conn.cursor()

        # Matchni tekshirish
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
            (user.id, target_id, target_id, user.id)
        )
        is_match = bool(cur.fetchone()[0])

        # Premiumni tekshirish
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
            (user.id,)
        )
        is_premium = bool(cur.fetchone()[0])

        cur.close()
        conn.close()

        # Faqat Match yoki Premium javob bera oladi
        if not is_match and not is_premium:
            await query.answer(
                "❌ Suhbat uchun Match yoki Premium kerak.",
                show_alert=True
            )
            return

        context.user_data["writing_to"] = target_id

        await query.answer("↩️ Javob berish yoqildi.")

        await query.message.reply_text(
            "💬 <b>Suhbat davom etmoqda</b>\n\n"
            "Xabaringizni yozing. Xabar suhbatdoshingizga yuboriladi.\n\n"
            "❌ Tugatish uchun pastdagi tugmani bosing.",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "❌ Suhbatni tugatish",
                        callback_data="end_chat"
                    )
                ]
            ])
        )
        return

    if data.startswith("skip_"):
        await query.message.delete()
        await find(update, context)
        return
    
    if data.startswith("superlike_"):
        target_id = int(data.split("_")[1])

        if target_id == user.id:
            await query.answer(
                "❌ O'zingizga Superlike yubora olmaysiz!",
                show_alert=True
            )
            return

        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute(
            """
            SELECT superlike_balance
            FROM users
            WHERE user_id = %s
            """,
            (user.id,)
        )
        result = cur.fetchone()
        balance = result[0] if result and result[0] else 0

        if balance <= 0:
            cur.close()
            conn.close()

            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton(
                    "⭐ Superlike sotib olish",
                    callback_data="buy_superlikes"
                )]
            ])

            await query.answer(
                "⭐ Superlike balansingiz tugagan!",
                show_alert=True
            )

            await query.message.reply_text(
                "⭐ <b>Superlike qolmadi</b>\n\n"
                "Profilni ajratib ko'rsatish uchun Superlike sotib oling.",
                reply_markup=keyboard,
                parse_mode="HTML"
            )
            return

        cur.execute(
            """
            SELECT first_name, photo
            FROM users
            WHERE user_id = %s
            """,
            (target_id,)
        )
        target_info = cur.fetchone()

        if not target_info:
            cur.close()
            conn.close()
            await query.answer(
                "❌ Foydalanuvchi topilmadi!",
                show_alert=True
            )
            return

        cur.execute(
            """
            SELECT first_name, photo
            FROM users
            WHERE user_id = %s
            """,
            (user.id,)
        )
        sender_info = cur.fetchone()

        if not sender_info:
            cur.close()
            conn.close()
            await query.answer(
                "❌ Profil ma'lumotlari topilmadi!",
                show_alert=True
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
            (user.id, target_id)
        )
        already_liked = bool(cur.fetchone()[0])

        if not already_liked:
            cur.execute(
                """
                INSERT INTO likes (from_user, to_user)
                VALUES (%s, %s)
                """,
                (user.id, target_id)
            )

        cur.execute(
            """
            UPDATE users
            SET superlike_balance = COALESCE(superlike_balance, 0) - 1
            WHERE user_id = %s
              AND COALESCE(superlike_balance, 0) > 0
            """,
            (user.id,)
        )

        cur.execute(
            """
            SELECT EXISTS(
                SELECT 1
                FROM likes
                WHERE from_user = %s
                  AND to_user = %s
            )
            """,
            (target_id, user.id)
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
                    INSERT INTO matches (user1, user2)
                    VALUES (%s, %s)
                    """,
                    (user.id, target_id)
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
                "🎉 MATCH! Superlike o'zaro qiziqishga aylandi!",
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
                "⭐ Superlike yuborildi!",
                show_alert=False
            )

        try:
            await query.message.delete()
        except Exception:
            pass

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

        # =========================
        # DAILY LIKE LIMIT
        # Oddiy foydalanuvchi: 3 Like/kun
        # Premium: cheksiz Like
        # =========================
        cur.execute(
            """
            SELECT premium_until
            FROM users
            WHERE user_id = %s
            """,
            (user.id,)
        )
        premium_result = cur.fetchone()

        is_premium = (
            premium_result
            and premium_result[0] is not None
            and premium_result[0] > datetime.now()
        )

        if not is_premium:
            cur.execute(
                """
                SELECT COUNT(*)
                FROM likes
                WHERE from_user = %s
                  AND created_at >= CURRENT_DATE
                  AND created_at < CURRENT_DATE + INTERVAL '1 day'
                """,
                (user.id,)
            )

            today_likes = cur.fetchone()[0]

            if today_likes >= 3:
                cur.close()
                conn.close()

                await query.answer(
                    "❤️ Bugungi 3 ta Like limitingiz tugadi!\n\n"
                    "👑 Premium bilan cheksiz Like bosing.",
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


async def save_edit_photo(update, context):
    user = update.effective_user
    language = get_user_language(user.id)

    texts = {
        "uz": {
            "send": "📸 Iltimos, yangi rasm yuboring.",
            "success": "✅ Rasm muvaffaqiyatli o‘zgartirildi!",
            "error": "❌ Rasmni saqlashda xatolik yuz berdi. Qaytadan urinib ko‘ring.",
            "not_found": "❌ Profil topilmadi.",
        },
        "ru": {
            "send": "📸 Пожалуйста, отправьте новое фото.",
            "success": "✅ Фото успешно изменено!",
            "error": "❌ Ошибка сохранения фото. Попробуйте ещё раз.",
            "not_found": "❌ Профиль не найден.",
        },
        "uz_cyr": {
            "send": "📸 Илтимос, янги расм юборинг.",
            "success": "✅ Расм муваффақиятли ўзгартирилди!",
            "error": "❌ Расмни сақлашда хатолик юз берди. Қайтадан уриниб кўринг.",
            "not_found": "❌ Профиль топилмади.",
        },
    }

    t = texts.get(language, texts["uz"])

    if not update.message or not update.message.photo:
        await update.message.reply_text(t["send"])
        return

    photo = update.message.photo[-1].file_id

    conn = None
    cur = None

    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Profil mavjudligini tekshirish
        cur.execute(
            "SELECT user_id FROM users WHERE user_id = %s",
            (user.id,)
        )

        if not cur.fetchone():
            await update.message.reply_text(t["not_found"])
            return

        # Asosiy profil rasmini yangilash
        cur.execute(
            "UPDATE users SET photo = %s WHERE user_id = %s",
            (photo, user.id)
        )

        # user_photos jadvali mavjud bo‘lsa, 1-rasmni ham yangilash
        cur.execute("""
            INSERT INTO user_photos (user_id, photo, position)
            VALUES (%s, %s, 1)
            ON CONFLICT (user_id, position)
            DO UPDATE SET photo = EXCLUDED.photo
        """, (user.id, photo))

        conn.commit()

        context.user_data.pop("edit_field", None)

        await update.message.reply_text(
            t["success"],
            reply_markup=await get_main_keyboard()
        )

    except Exception as e:
        if conn:
            conn.rollback()

        print(f"Edit photo save error: {e}")

        await update.message.reply_text(t["error"])

    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()



async def save_edit_photo(update, context):
    """Profil tahrirlash orqali asosiy rasmni almashtirish."""

    user = update.effective_user
    language = get_user_language(user.id)

    if not update.message or not update.message.photo:
        texts = {
            "uz": "📸 Iltimos, rasm yuboring.",
            "ru": "📸 Пожалуйста, отправьте фотографию.",
            "uz_cyr": "📸 Илтимос, расм юборинг.",
        }
        await update.message.reply_text(
            texts.get(language, texts["uz"])
        )
        return

    photo = update.message.photo[-1].file_id

    conn = get_db_connection()
    cur = conn.cursor()

    try:
        # users jadvalidagi asosiy rasmni yangilash
        cur.execute(
            """
            UPDATE users
            SET photo = %s
            WHERE user_id = %s
            """,
            (photo, user.id)
        )

        # user_photos mavjud bo‘lsa, 1-rasmni ham yangilaymiz.
        # Jadval hali yaratilmagan bo‘lsa ham profil tahrirlash ishlashda davom etadi.
        try:
            cur.execute(
                """
                INSERT INTO user_photos (user_id, photo, position)
                VALUES (%s, %s, 1)
                ON CONFLICT (user_id, position)
                DO UPDATE SET photo = EXCLUDED.photo
                """,
                (user.id, photo)
            )
        except Exception as photo_table_error:
            print(f"⚠️ user_photos update skipped: {photo_table_error}")
            conn.rollback()

            # users.photo yangilanishini qayta bajarib commit qilamiz
            cur.execute(
                """
                UPDATE users
                SET photo = %s
                WHERE user_id = %s
                """,
                (photo, user.id)
            )

        conn.commit()

        context.user_data.pop("edit_field", None)

        texts = {
            "uz": (
                "✅ <b>Rasm muvaffaqiyatli yangilandi!</b>\n\n"
                "✨ Yangi profilingiz rasmi saqlandi."
            ),
            "ru": (
                "✅ <b>Фотография успешно обновлена!</b>\n\n"
                "✨ Новая фотография профиля сохранена."
            ),
            "uz_cyr": (
                "✅ <b>Расм муваффақиятли янгиланди!</b>\n\n"
                "✨ Янги профил расми сақланди."
            ),
        }

        await update.message.reply_text(
            texts.get(language, texts["uz"]),
            reply_markup=await get_main_keyboard(),
            parse_mode="HTML"
        )

        return ConversationHandler.END

    except Exception as e:
        conn.rollback()
        print(f"❌ Edit photo save error: {e}")

        texts = {
            "uz": "❌ Rasmni saqlashda xatolik yuz berdi. Qaytadan urinib ko‘ring.",
            "ru": "❌ Ошибка сохранения фотографии. Попробуйте ещё раз.",
            "uz_cyr": "❌ Расмни сақлашда хатолик юз берди. Қайтадан уриниб кўринг.",
        }

        await update.message.reply_text(
            texts.get(language, texts["uz"])
        )

        return

    finally:
        cur.close()
        conn.close()


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
            "👀 Meni yoqtirganlar",
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

async def handle_payment_check(update, context):
    user = update.effective_user

    if not update.message:
        return

    # ========================================================
    # CHEK FAQAT RASM YOKI FAYL BO'LISHI MUMKIN
    # ========================================================

    photo = None
    document = None

    if update.message.photo:
        photo = update.message.photo[-1].file_id

    elif update.message.document:
        document = update.message.document

    else:
        if "pending_payment" in context.user_data:
            await update.message.reply_text(
                "❌ Chek faqat rasm yoki fayl ko'rinishida yuborilishi mumkin.\n\n"
                "🖼 Rasm: JPG, PNG va boshqa rasm formatlari\n"
                "📄 Fayl: PDF yoki boshqa document"
            )
        return

    # ========================================================
    # PROFIL RASMI VA TO'LOV CHEKINI AJRATISH
    # ========================================================
    # Ro'yxatdan o'tishdagi 1-3 ta profil rasmi
    # hech qachon to'lov cheki sifatida ishlanmasin.
    if context.user_data.get("photo_step") in (1, 2, 3):
        return

    # ========================================================
    # TO'LOV CHEKI KUTILAYAPTIMI?
    # ========================================================

    if "pending_payment" not in context.user_data:

        # Agar profil rasmini o'zgartirish jarayoni bo'lsa
        if "edit_field" in context.user_data and photo:
            return await save_edit_photo(update, context)

        await update.message.reply_text(
            "❌ Hozir to'lov cheki kutilmayapti."
        )
        return

    pending = context.user_data["pending_payment"]

    # ========================================================
    # SUPERLIKE CHEKI
    # ========================================================

    if pending.get("type") == "superlike":

        amount = pending["amount"]

        prices = {
            1: "1 000",
            5: "4 000",
            10: "7 000",
        }

        price = prices.get(amount, "?")

        language = get_user_language(user.id)

        superlike_receipt_texts = {
            "uz": {
                "approve": "✅ Tasdiqlash",
                "reject": "❌ Rad etish",
                "caption": (
                    "💳 SUPERLIKE TO'LOV CHEKI\\n\\n"
                    f"👤 {user.first_name}\\n"
                    f"🆔 ID: {user.id}\\n"
                    f"⭐ Miqdor: {amount} ta\\n"
                    f"💰 Summa: {price} so'm\\n\\n"
                    "📸/📄 Chek yuborildi.\\n"
                    "Admin tekshirishi va tasdiqlashi mumkin."
                ),
                "sent": (
                    "✅ To'lov cheki yuborildi!\\n\\n"
                    "Admin tekshiradi va tasdiqlasa "
                    "Superlike hisobingizga qo'shiladi."
                ),
                "error": (
                    "❌ Chekni admin'ga yuborishda "
                    "xatolik yuz berdi."
                ),
            },
            "ru": {
                "approve": "✅ Подтвердить",
                "reject": "❌ Отклонить",
                "caption": (
                    "💳 ЧЕК ОБ ОПЛАТЕ SUPERLIKE\\n\\n"
                    f"👤 {user.first_name}\\n"
                    f"🆔 ID: {user.id}\\n"
                    f"⭐ Количество: {amount} шт.\\n"
                    f"💰 Сумма: {price} сум\\n\\n"
                    "📸/📄 Чек отправлен.\\n"
                    "Администратор проверит и подтвердит оплату."
                ),
                "sent": (
                    "✅ Чек об оплате отправлен!\\n\\n"
                    "Администратор проверит его и после подтверждения "
                    "Superlike будут добавлены на ваш баланс."
                ),
                "error": (
                    "❌ Произошла ошибка при отправке "
                    "чека администратору."
                ),
            },
            "uz_cyr": {
                "approve": "✅ Тасдиқлаш",
                "reject": "❌ Рад этиш",
                "caption": (
                    "💳 SUPERLIKE ТЎЛОВ ЧЕКИ\\n\\n"
                    f"👤 {user.first_name}\\n"
                    f"🆔 ID: {user.id}\\n"
                    f"⭐ Миқдор: {amount} та\\n"
                    f"💰 Сумма: {price} сўм\\n\\n"
                    "📸/📄 Чек юборилди.\\n"
                    "Администратор текшириши ва тасдиқлаши мумкин."
                ),
                "sent": (
                    "✅ Тўлов чеки юборилди!\\n\\n"
                    "Администратор текширади ва тасдиқласа, "
                    "Superlike ҳисобингизга қўшилади."
                ),
                "error": (
                    "❌ Чекни администраторга юборишда "
                    "хатолик юз берди."
                ),
            },
        }

        t = superlike_receipt_texts.get(
            language,
            superlike_receipt_texts["uz"]
        )

        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    t["approve"],
                    callback_data=f"ok_sl_{user.id}_{amount}"
                ),
                InlineKeyboardButton(
                    t["reject"],
                    callback_data=f"no_sl_{user.id}"
                )
            ]
        ])

        caption = t["caption"]

        try:

            if photo:
                await context.bot.send_photo(
                    chat_id=ADMIN_ID,
                    photo=photo,
                    caption=caption,
                    reply_markup=keyboard
                )

            elif document:
                await context.bot.send_document(
                    chat_id=ADMIN_ID,
                    document=document.file_id,
                    caption=caption,
                    reply_markup=keyboard
                )

            await update.message.reply_text(t["sent"])

        except Exception as e:

            print(
                f"❌ Superlike chek yuborishda xato: {e}"
            )

            await update.message.reply_text(t["error"])

        context.user_data.pop(
            "pending_payment",
            None
        )

        return

    # ========================================================
    # PREMIUM CHEKI
    # ========================================================

    if pending.get("type") == "premium":

        days = pending["days"]
        plan = pending.get("plan")

        prices = {
            "premium_1w": "25 000",
            "premium_2w": "39 000",
            "premium_1m": "59 000",
            "premium_3m": "129 000",
        }

        # Chegirmali Premium bo‘lsa, pending_payment ichidagi
        # chegirmali summani ishlatamiz.
        if pending.get("discounted"):
            price = pending.get("price", "?")
        else:
            price = prices.get(plan, "?")

        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "✅ Tasdiqlash",
                    callback_data=f"ok_prem_{user.id}_{days}"
                ),
                InlineKeyboardButton(
                    "❌ Rad etish",
                    callback_data=f"no_prem_{user.id}"
                )
            ],
            [
                InlineKeyboardButton(
                    "🚫 Soxta chek — BLOKLASH",
                    callback_data=f"fake_prem_{user.id}"
                )
            ]
        ])

        caption = (
            "💳 PREMIUM TO'LOV CHEKI\n\n"
            f"👤 {user.first_name}\n"
            f"🆔 ID: {user.id}\n"
            f"📅 Muddat: {days} kun\n"
            f"💰 Summa: {price} so'm\n\n"
            "📸/📄 Chek yuborildi.\n"
            "Admin tekshirishi va tasdiqlashi mumkin."
        )

        try:

            if photo:
                await context.bot.send_photo(
                    chat_id=ADMIN_ID,
                    photo=photo,
                    caption=caption,
                    reply_markup=keyboard
                )

            elif document:
                await context.bot.send_document(
                    chat_id=ADMIN_ID,
                    document=document.file_id,
                    caption=caption,
                    reply_markup=keyboard
                )

            await update.message.reply_text(
                "✅ To'lov cheki yuborildi!\n\n"
                "Admin tekshiradi va tasdiqlasa "
                "Premium faollashadi."
            )

        except Exception as e:

            print(
                f"❌ Premium chek yuborishda xato: {e}"
            )

            await update.message.reply_text(
                "❌ Chekni admin'ga yuborishda "
                "xatolik yuz berdi."
            )

        context.user_data.pop(
            "pending_payment",
            None
        )

        return

    # Noma'lum to'lov turi
    await update.message.reply_text(
        "❌ To'lov ma'lumotlari topilmadi."
    )

    context.user_data.pop(
        "pending_payment",
        None
    )



async def profile(update, context):
    user = update.effective_user
    language = get_user_language(user.id)

    texts = {
        "uz": {
            "not_found": "❌ Profil topilmadi.",
            "edit": "✏️ Tahrirlash",
            "premium": "👑 Premium",
            "profile": "👤 {name}, {age}",
            "gender": "👤 {gender}",
            "city": "📍 {city}",
            "bio": "📝 {bio}",
            "likes": "❤️ {count} like",
            "matches": "💞 {count} match",
            "premium_status": "👑 Premium: {status}",
        },
        "ru": {
            "not_found": "❌ Профиль не найден.",
            "edit": "✏️ Редактировать",
            "premium": "👑 Премиум",
            "profile": "👤 {name}, {age}",
            "gender": "👤 {gender}",
            "city": "📍 {city}",
            "bio": "📝 {bio}",
            "likes": "❤️ {count} лайков",
            "matches": "💞 {count} совпадений",
            "premium_status": "👑 Премиум: {status}",
        },
        "uz_cyr": {
            "not_found": "❌ Профиль топилмади.",
            "edit": "✏️ Таҳрирлаш",
            "premium": "👑 Премиум",
            "profile": "👤 {name}, {age}",
            "gender": "👤 {gender}",
            "city": "📍 {city}",
            "bio": "📝 {bio}",
            "likes": "❤️ {count} лайк",
            "matches": "💞 {count} мэтч",
            "premium_status": "👑 Премиум: {status}",
        },
    }

    t = texts.get(language, texts["uz"])

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT
            user_id,
            username,
            first_name,
            age,
            gender,
            bio,
            photo,
            city,
            is_active,
            premium_until,
            created_at
        FROM users
        WHERE user_id = %s
        """,
        (user.id,)
    )
    user_data = cur.fetchone()

    cur.execute(
        "SELECT COUNT(*) FROM likes WHERE to_user = %s",
        (user.id,)
    )
    likes_count = cur.fetchone()[0]

    cur.execute(
        "SELECT COUNT(*) FROM matches WHERE user1 = %s OR user2 = %s",
        (user.id, user.id)
    )
    matches_count = cur.fetchone()[0]

    cur.close()
    conn.close()

    if not user_data:
        await update.message.reply_text(t["not_found"])
        return

    if len(user_data) >= 11:
        (
            user_id,
            username,
            first_name,
            age,
            gender,
            bio,
            photo,
            city,
            is_active,
            premium_until,
            created_at
        ) = user_data[:11]
    else:
        (
            user_id,
            username,
            first_name,
            age,
            gender,
            bio,
            photo,
            city
        ) = user_data[:8]

        is_active = True
        premium_until = None

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
        [
            InlineKeyboardButton(
                t["edit"],
                callback_data="edit_menu"
            )
        ],
        [
            InlineKeyboardButton(
                t["premium"],
                callback_data="premium_buy"
            )
        ]
    ])

    profile_badge = " ⭐" if premium_status == "✅" else ""

    caption = (
        t["profile"].format(
            name=first_name,
            age=age
        )
        + profile_badge
        + "\n"
        + t["gender"].format(gender=gender)
        + "\n"
        + t["city"].format(city=city)
        + "\n"
        + t["bio"].format(
            bio=bio or (
                "Bio yozilmagan"
                if language == "uz"
                else "Био не заполнено"
                if language == "ru"
                else "Био ёзилмаган"
            )
        )
        + "\n\n"
        + t["likes"].format(count=likes_count)
        + "\n"
        + t["matches"].format(count=matches_count)
        + "\n"
        + t["premium_status"].format(status=premium_status)
    )

    await update.message.reply_photo(
        photo=photo,
        caption=caption,
        reply_markup=keyboard
    )


async def who_liked_me(update, context):
    user = update.effective_user
    language = get_user_language(user.id)

    texts = {
        "uz": {
            "title": "👀 <b>SIZNI YOQTIRGANLAR</b>",
            "empty": "👀 Hozircha sizni hech kim yoqtirmagan.",
        },
        "ru": {
            "title": "👀 <b>КТО ВАС ЛАЙКНУЛ</b>",
            "empty": "👀 Пока никто вас не лайкнул.",

        },
        "uz_cyr": {
            "title": "👀 <b>СИЗНИ ЁҚТИРГАНЛАР</b>",
            "empty": "👀 Ҳозирча сизни ҳеч ким ёқтирмаган.",
        },
    }

    t = texts.get(language, texts["uz"])

    conn = get_db_connection()
    cur = conn.cursor()

    # Sizga like bosganlar
    cur.execute("""
        SELECT
            u.user_id,
            u.first_name,
            u.age,
            u.photo,
            u.city
        FROM likes l
        JOIN users u ON u.user_id = l.from_user
        WHERE l.to_user = %s
          AND u.is_active = TRUE
        ORDER BY l.created_at DESC
    """, (user.id,))

    rows = cur.fetchall()

    cur.close()
    conn.close()

    if not rows:
        await update.message.reply_text(t["empty"], parse_mode="HTML")
        return

    await update.message.reply_text(t["title"], parse_mode="HTML")

    for liker_id, first_name, age, photo, city in rows:
        caption = (
            f"👤 <b>{first_name}</b>, {age}\n"
            f"📍 {city or '—'}\n\n"
            "❤️ <b>Sizga Like bosgan</b>"
        )

        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "❤️ Like",
                    callback_data=f"who_like:{liker_id}"
                )
            ]
        ])

        if photo:
            try:
                await update.message.reply_photo(
                    photo=photo,
                    caption=caption,
                    reply_markup=keyboard,
                    parse_mode="HTML"
                )
            except Exception:
                await update.message.reply_text(
                    caption,
                    reply_markup=keyboard,
                    parse_mode="HTML"
                )
        else:
            await update.message.reply_text(
                caption,
                reply_markup=keyboard,
                parse_mode="HTML"
            )


async def likes(update, context):
    """
    Foydalanuvchiga KIMLAR LIKE BOSGANINI ko'rsatadi.
    """
    user = update.effective_user
    language = get_user_language(user.id)

    texts = {
        "uz": {
            "empty": "❤️ Hozircha sizga hech kim Like bosmagan.",
            "title": "❤️ SIZNI YOQTIRGANLAR",
            "like_back": "❤️ Like qaytarish",
            "skip": "👎 O'tkazib yuborish",
            "bio_empty": "Bio yozilmagan",
        },
        "ru": {
            "empty": "❤️ Пока вас никто не лайкнул.",
            "title": "❤️ ВАС ЛАЙКНУЛИ",
            "like_back": "❤️ Ответить лайком",
            "skip": "👎 Пропустить",
            "bio_empty": "Биография не указана",
        },
        "uz_cyr": {
            "empty": "❤️ Ҳозирча сизга ҳеч ким Like босмаган.",
            "title": "❤️ СИЗНИ ЁҚТИРГАНЛАР",
            "like_back": "❤️ Лайк қайтариш",
            "skip": "👎 Ўтказиб юбориш",
            "bio_empty": "Био ёзилмаган",
        },
    }

    t = texts.get(language, texts["uz"])

    conn = get_db_connection()
    cur = conn.cursor()

    # KIMLAR MENGA LIKE BOSGAN?
    cur.execute(
        """
        SELECT
            u.user_id,
            u.first_name,
            u.age,
            u.gender,
            u.bio,
            u.photo,
            u.city,
            u.premium_until
        FROM likes l
        JOIN users u ON u.user_id = l.from_user
        WHERE l.to_user = %s
          AND u.is_active = TRUE
        ORDER BY l.created_at DESC
        """,
        (user.id,)
    )

    likes_list = cur.fetchall()

    cur.close()
    conn.close()

    if not likes_list:
        await update.message.reply_text(t["empty"])
        return

    await update.message.reply_text(
        t["title"] + f"\n\n👥 {len(likes_list)} ta odam sizga qiziqmoqda."
    )

    for profile in likes_list:
        (
            target_id,
            first_name,
            age,
            gender,
            bio,
            photo,
            city,
            premium_until,
        ) = profile

        premium_badge = ""
        if premium_until:
            try:
                if premium_until > datetime.now():
                    premium_badge = " 👑"
            except Exception:
                pass

        caption = (
            f"👤 <b>{first_name}</b>{premium_badge}, {age}\n"
            f"📍 {city or '—'}\n"
            f"📝 {bio or t['bio_empty']}"
        )

        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    t["like_back"],
                    callback_data=f"like_back_{target_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    t["skip"],
                    callback_data=f"skip_liker_{target_id}"
                )
            ]
        ])

        try:
            if photo:
                await update.message.reply_photo(
                    photo=photo,
                    caption=caption,
                    reply_markup=keyboard,
                    parse_mode="HTML"
                )
            else:
                await update.message.reply_text(
                    caption,
                    reply_markup=keyboard,
                    parse_mode="HTML"
                )
        except Exception as e:
            print(f"Like profile display error: {e}")


async def matches(update, context):
    user = update.effective_user
    language = get_user_language(user.id)

    texts = {
        "uz": {
            "empty": "💞 Hozircha matchlar yo'q.",
            "title": "💞 Matchlaringiz:",
            "unread": "🔴 {count} ta yangi xabar",
        },
        "ru": {
            "empty": "💞 Пока совпадений нет.",
            "title": "💞 Ваши совпадения:",
            "unread": "🔴 {count} новых сообщений",
        },
        "uz_cyr": {
            "empty": "💞 Ҳозирча мэтчлар йўқ.",
            "title": "💞 Мэтчларингиз:",
            "unread": "🔴 {count} та янги хабар",
        },
    }

    t = texts.get(language, texts["uz"])

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            u.user_id,
            u.first_name,
            u.age,
            COUNT(msg.id) AS unread_count
        FROM users u
        JOIN matches m
          ON u.user_id = CASE
              WHEN m.user1 = %s THEN m.user2
              ELSE m.user1
          END
        LEFT JOIN messages msg
          ON msg.from_user = u.user_id
         AND msg.to_user = %s
         AND msg.is_read = FALSE
        WHERE m.user1 = %s OR m.user2 = %s
        GROUP BY u.user_id, u.first_name, u.age, m.created_at
        ORDER BY m.created_at DESC
    """, (
        user.id,
        user.id,
        user.id,
        user.id
    ))

    matches_list = cur.fetchall()

    cur.close()
    conn.close()

    if not matches_list:
        await update.message.reply_text(t["empty"])
        return

    text = t["title"] + "\n\n"

    for target_id, first_name, age, unread_count in matches_list:
        text += f"• {first_name}, {age}"

        if unread_count:
            text += f"\n  {t['unread'].format(count=unread_count)}"

        text += "\n"

    await update.message.reply_text(text)


async def settings(update, context):
    user = update.effective_user
    language = get_user_language(user.id)

    texts = {
        "uz": {
            "title": "⚙️ Sozlamalar:",
            "superlike": "⭐ Superlike: {balance} ta",
            "edit": "✏️ Profilni tahrirlash",
            "premium": "👑 Premium",
            "language": "🌐 Tilni o'zgartirish",
            "deactivate": "👻 Profilni muzlatish",
        },
        "ru": {
            "title": "⚙️ Настройки:",
            "superlike": "⭐ Суперлайк: {balance} шт.",
            "edit": "✏️ Редактировать профиль",
            "premium": "👑 Премиум",
            "language": "🌐 Изменить язык",
            "deactivate": "👻 Заморозить профиль",
        },
        "uz_cyr": {
            "title": "⚙️ Созламалар:",
            "superlike": "⭐ Суперлайк: {balance} та",
            "edit": "✏️ Профильни таҳрирлаш",
            "premium": "👑 Премиум",
            "language": "🌐 Тилни ўзгартириш",
            "deactivate": "👻 Профильни музлатиш",
        },
    }

    t = texts.get(language, texts["uz"])

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT superlike_balance FROM users WHERE user_id = %s",
        (user.id,)
    )
    result = cur.fetchone()
    balance = result[0] if result and result[0] else 0
    cur.close()
    conn.close()

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(
            t["edit"],
            callback_data="edit_menu"
        )],
        [InlineKeyboardButton(
            t["language"],
            callback_data="change_language"
        )],
        [InlineKeyboardButton(
            t["deactivate"],
            callback_data="deactivate"
        )],
    ])

    await update.message.reply_text(
        t["title"],
        reply_markup=keyboard
    )


async def change_language_menu(update, context):
    query = update.callback_query
    await query.answer()

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(
            "🇺🇿 O'zbek tili",
            callback_data="set_language_uz"
        )],
        [InlineKeyboardButton(
            "🇷🇺 Русский",
            callback_data="set_language_ru"
        )],
        [InlineKeyboardButton(
            "🇺🇿 Узбек (Кирилл)",
            callback_data="set_language_uz_cyr"
        )],
        [InlineKeyboardButton(
            "❌ Bekor qilish",
            callback_data="cancel_language"
        )],
    ])

    await query.message.reply_text(
        "🌐 <b>Tilni tanlang</b>\n\n"
        "Kerakli tilni tanlang:",
        reply_markup=keyboard,
        parse_mode="HTML"
    )


async def save_language(update, context, language):
    query = update.callback_query
    user = query.from_user

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute(
        "UPDATE users SET language = %s WHERE user_id = %s",
        (language, user.id)
    )

    conn.commit()
    cur.close()
    conn.close()

    context.user_data["language"] = language

    names = {
        "uz": "🇺🇿 O'zbek tili",
        "ru": "🇷🇺 Русский",
        "uz_cyr": "🇺🇿 Узбек (Кирилл)",
    }

    await query.answer(
        f"✅ Til o'zgartirildi: {names[language]}",
        show_alert=True
    )

    await query.message.reply_text(
        "✅ Til muvaffaqiyatli o'zgartirildi!",
        reply_markup=await get_main_keyboard(language)
    )


async def referral_panel(update, context):
    user = update.effective_user
    language = get_user_language(user.id)

    texts = {
        "uz": {
            "title": "🎁 REFERAL DASTURI",
            "referrals": "👥 Sizning referallaringiz: {count} ta",
            "rewards": "🏆 MUKOFOTLAR:",
            "reward": "{status} {required} ta — {days} kun Premium",
            "next": "🎯 Keyingi mukofot: {required} ta referal",
            "remaining": "➡️ Yana {remaining} ta kerak",
            "all": "🏆 Barcha referal mukofotlarini oldingiz!",
            "link": "🔗 SIZNING REFERAL HAVOLANGIZ:",
            "share": "📤 Havolani do'stlaringizga yuboring!",
            "finish": "Do'stingiz profil yaratishni tugatsa, referal hisoblanadi.",
        },
        "ru": {
            "title": "🎁 РЕФЕРАЛЬНАЯ ПРОГРАММА",
            "referrals": "👥 Ваши рефералы: {count}",
            "rewards": "🏆 НАГРАДЫ:",
            "reward": "{status} {required} рефералов — {days} дней Премиум",
            "next": "🎯 Следующая награда: {required} рефералов",
            "remaining": "➡️ Осталось ещё {remaining}",
            "all": "🏆 Вы получили все реферальные награды!",
            "link": "🔗 ВАША РЕФЕРАЛЬНАЯ ССЫЛКА:",
            "share": "📤 Отправьте ссылку своим друзьям!",
            "finish": "Реферал засчитывается после завершения создания профиля другом.",
        },
        "uz_cyr": {
            "title": "🎁 РЕФЕРАЛ ДАСТУРИ",
            "referrals": "👥 Сизнинг рефералларингиз: {count} та",
            "rewards": "🏆 МУКОФОТЛАР:",
            "reward": "{status} {required} та — {days} кун Премиум",
            "next": "🎯 Кейинги мукофот: {required} та реферал",
            "remaining": "➡️ Яна {remaining} та керак",
            "all": "🏆 Барча реферал мукофотларини олдингиз!",
            "link": "🔗 СИЗНИНГ РЕФЕРАЛ ҲАВОЛАНГИЗ:",
            "share": "📤 Ҳаволани дўстларингизга юборинг!",
            "finish": "Дўстингиз профиль яратишни тугатса, реферал ҳисобланади.",
        },
    }

    t = texts.get(language, texts["uz"])

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute(
        "SELECT COUNT(*) FROM users WHERE referred_by = %s",
        (user.id,)
    )
    count = cur.fetchone()[0]

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
        status = "✅" if count >= required else "🔒"
        lines.append(
            t["reward"].format(
                status=status,
                required=required,
                days=days
            )
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
            t["next"].format(required=required)
            + "\n"
            + t["remaining"].format(remaining=remaining)
        )
    else:
        next_text = t["all"]

    username = context.bot.username
    link = f"https://t.me/{username}?start=ref_{user.id}"

    text = (
        t["title"] + "\n\n"
        + t["referrals"].format(count=count)
        + "\n\n"
        + t["rewards"]
        + "\n"
        + "\n".join(lines)
        + "\n\n"
        + next_text
        + "\n\n"
        + t["link"]
        + "\n"
        + link
        + "\n\n"
        + t["share"]
        + "\n"
        + t["finish"]
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
    user = update.effective_user
    language = get_user_language(user.id)

    # 👀 Meni yoqtirganlar
    who_liked_buttons = {
        "uz": "👀 Meni yoqtirganlar",
        "ru": "👀 Кто меня лайкнул",
        "uz_cyr": "👀 Сизни ёқтирганлар",
    }

    if text == who_liked_buttons.get(language):
        await who_liked_me(update, context)
        return


    # =========================================================
    # CHAT / XABAR ALMASHISH
    # Match -> bot ichida suhbat
    # Premium -> Matchsiz ham yozish mumkin
    # Username majburiy emas
    # =========================================================
    if "writing_to" in context.user_data:
        target_id = context.user_data["writing_to"]
        sender = update.effective_user

        if text == "/cancel":
            context.user_data.pop("writing_to", None)
            await update.message.reply_text(
                "❌ Suhbat tugatildi."
            )
            return

        conn = get_db_connection()
        cur = conn.cursor()

        # Premium statusini tekshirish
        cur.execute(
            """
            SELECT EXISTS(
                SELECT 1 FROM users
                WHERE user_id = %s
                AND premium_until IS NOT NULL
                AND premium_until > NOW()
            )
            """,
            (sender.id,)
        )
        is_premium = bool(cur.fetchone()[0])

        # Match statusini tekshirish
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
            (sender.id, target_id, target_id, sender.id)
        )
        is_match = bool(cur.fetchone()[0])

        # Faqat Match yoki Premium yozishi mumkin
        if not is_match and not is_premium:
            context.user_data.pop("writing_to", None)
            cur.close()
            conn.close()

            await update.message.reply_text(
                "❌ Bu foydalanuvchiga yozish uchun Match yoki Premium kerak."
            )
            return

        # Xabarni saqlash
        cur.execute(
            """
            INSERT INTO messages (from_user, to_user, text)
            VALUES (%s, %s, %s)
            """,
            (sender.id, target_id, text)
        )

        # Qabul qiluvchi nomi
        cur.execute(
            "SELECT first_name FROM users WHERE user_id = %s",
            (target_id,)
        )
        target = cur.fetchone()

        conn.commit()
        cur.close()
        conn.close()

        if not target:
            context.user_data.pop("writing_to", None)
            await update.message.reply_text(
                "❌ Foydalanuvchi topilmadi."
            )
            return

        # Javob berish / suhbatni tugatish tugmalari
        reply_keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "↩️ Javob berish",
                    callback_data=f"reply_{sender.id}"
                )
            ],
            [
                InlineKeyboardButton(
                    "❌ Suhbatni tugatish",
                    callback_data="end_chat"
                )
            ]
        ])

        try:
            await context.bot.send_message(
                chat_id=target_id,
                text=(
                    "💌 <b>Sizga SaraMatch'dan yangi xabar!</b>\n\n"
                    f"👤 <b>{sender.first_name}</b>:\n"
                    f"{text}"
                ),
                parse_mode="HTML",
                reply_markup=reply_keyboard
            )

            await update.message.reply_text(
                "✅ Xabaringiz yuborildi!"
            )

        except Exception:
            await update.message.reply_text(
                "⚠️ Xabarni yetkazib bo‘lmadi. "
                "Foydalanuvchi botni bloklagan bo‘lishi mumkin."
            )

        # writing_to saqlanadi:
        # foydalanuvchi ketma-ket xabar yuborishi mumkin
        return


    text = update.message.text
    
    if 'edit_field' in context.user_data:
        return await save_edit(update, context)
    
    language = get_user_language(update.effective_user.id)

    if text in {
        tr("uz", "search"),
        tr("ru", "search"),
        tr("uz_cyr", "search"),
    }:
        await find(update, context)

    elif text in {
        tr("uz", "profile"),
        tr("ru", "profile"),
        tr("uz_cyr", "profile"),
    }:
        await profile(update, context)

    elif text in {
        tr("uz", "likes"),
        tr("ru", "likes"),
        tr("uz_cyr", "likes"),
    }:
        await likes(update, context)

    elif text in {
        tr("uz", "matches"),
        tr("ru", "matches"),
        tr("uz_cyr", "matches"),
    }:
        await matches(update, context)

    elif text in {
        tr("uz", "settings"),
        tr("ru", "settings"),
        tr("uz_cyr", "settings"),
    }:
        await settings(update, context)

    elif text in {
        tr("uz", "referral"),
        tr("ru", "referral"),
        tr("uz_cyr", "referral"),
    }:
        await referral_panel(update, context)

    elif text in {
        tr("uz", "superlike"),
        tr("ru", "superlike"),
        tr("uz_cyr", "superlike"),
    }:
        user = update.effective_user
        language = get_user_language(user.id)

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "SELECT superlike_balance FROM users WHERE user_id = %s",
            (user.id,)
        )
        result = cur.fetchone()
        balance = result[0] if result and result[0] else 0
        cur.close()
        conn.close()

        texts = {
            "uz": {
                "title": "⭐ SUPERLIKE",
                "balance": "📊 Mavjud: {balance} ta",
                "priority": "🔥 Profilingiz birinchi chiqadi!",
                "power": "💪 3x kuchliroq",
                "choose": "Paketni tanlang:",
                "p1": "1 ta - 1 000 so'm",
                "p5": "5 ta - 4 000 so'm",
                "p10": "10 ta - 7 000 so'm",
            },
            "ru": {
                "title": "⭐ СУПЕРЛАЙК",
                "balance": "📊 Доступно: {balance} шт.",
                "priority": "🔥 Ваш профиль будет показан первым!",
                "power": "💪 В 3 раза сильнее",
                "choose": "Выберите пакет:",
                "p1": "1 шт. - 1 000 сум",
                "p5": "5 шт. - 4 000 сум",
                "p10": "10 шт. - 7 000 сум",
            },
            "uz_cyr": {
                "title": "⭐ СУПЕРЛАЙК",
                "balance": "📊 Мавжуд: {balance} та",
                "priority": "🔥 Профилингиз биринчи чиқади!",
                "power": "💪 3 баравар кучлироқ",
                "choose": "Пакетни танланг:",
                "p1": "1 та - 1 000 сўм",
                "p5": "5 та - 4 000 сўм",
                "p10": "10 та - 7 000 сўм",
            },
        }

        t = texts.get(language, texts["uz"])

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(t["p1"], callback_data="sl_1")],
            [InlineKeyboardButton(t["p5"], callback_data="sl_5")],
            [InlineKeyboardButton(t["p10"], callback_data="sl_10")],
        ])

        await update.message.reply_text(
            f'{t["title"]}\n\n'
            f'{t["balance"].format(balance=balance)}\n\n'
            f'{t["priority"]}\n'
            f'{t["power"]}\n\n'
            f'{t["choose"]}',
            reply_markup=keyboard
        )

    elif text in {
        tr("uz", "premium"),
        tr("ru", "premium"),
        tr("uz_cyr", "premium"),
    }:
        language = get_user_language(update.effective_user.id)

        texts = {
            "uz": {
                "title": "👑 <b>PREMIUM</b>",
                "intro": "💎 Premium bilan tanishuv imkoniyatlaringizni yanada kengaytiring!",
                "unlimited_profiles": "♾️ <b>Cheksiz profil ko'rish</b> — ko'proq odamlarni kashf eting",
                "unlimited_likes": "❤️ <b>Cheksiz Like</b> — imkoniyatlarni o'tkazib yubormang",
                "direct": "✉️ <b>Matchni kutmasdan yozing</b> — yoqqan insoningiz bilan darhol suhbat boshlang",
                "who": "👀 <b>Sizni kim yoqtirganini ko'ring</b> — kim sizga qiziqayotganini biling",
                "badge": "⭐️ <b>Premium belgisi</b> — profilingizni ajratib turing",
                "priority": "🚀 <b>Profil ustuvorligi</b> — ko'proq ko'rinishga ega bo'ling",
                "more": "🔥 <b>Ko'proq ko'rinish → ko'proq Like → ko'proq Match!</b>",
                "choose": "✨ O'zingizga mos Premium tarifini tanlang:",
                "duration": "📅 <b>Muddatni tanlang:</b>",
                "p1": "📅 1 hafta - 25 000 so'm • QULAY",
                "p2": "🔥 14 kun - 39 000 so'm • ENG QULAY",
                "p3": "⭐️ 1 oy - 59 000 so'm • OMMABOP",
                "p4": "👑 3 oy - 129 000 so'm • TEJAMKOR",
                "cancel": "❌ Bekor qilish",
            },
            "ru": {
                "title": "👑 <b>ПРЕМИУМ</b>",
                "intro": "💎 Расширьте свои возможности для знакомств с Premium!",
                "unlimited_profiles": "♾️ <b>Безлимитный просмотр профилей</b> — открывайте больше людей",
                "unlimited_likes": "❤️ <b>Безлимитные Like</b> — не упускайте возможности",
                "direct": "✉️ <b>Пишите без ожидания Match</b> — начинайте общение сразу",
                "who": "👀 <b>Узнайте, кто вас лайкнул</b> — знайте, кто заинтересован",
                "badge": "⭐️ <b>Значок Premium</b> — выделите свой профиль",
                "priority": "🚀 <b>Приоритет профиля</b> — получайте больше просмотров",
                "more": "🔥 <b>Больше просмотров → больше Like → больше Match!</b>",
                "choose": "✨ Выберите подходящий тариф Premium:",
                "duration": "📅 <b>Выберите срок:</b>",
                "p1": "📅 1 неделя - 25 000 сум • ВЫГОДНО",
                "p2": "🔥 14 дней - 39 000 сум • ЛУЧШИЙ ВЫБОР",
                "p3": "⭐️ 1 месяц - 59 000 сум • ПОПУЛЯРНЫЙ",
                "p4": "👑 3 месяца - 129 000 сум • ЭКОНОМНО",
                "cancel": "❌ Отмена",
            },
            "uz_cyr": {
                "title": "👑 <b>PREMIUM</b>",
                "intro": "💎 Premium билан танишув имкониятларингизни янада кенгайтиринг!",
                "unlimited_profiles": "♾️ <b>Чексиз профиль кўриш</b> — кўпроқ одамларни кашф этинг",
                "unlimited_likes": "❤️ <b>Чексиз Like</b> — имкониятларни ўтказиб юборманг",
                "direct": "✉️ <b>Matchни кутмасдан ёзинг</b> — ёққан инсонгиз билан дарҳол суҳбат бошланг",
                "who": "👀 <b>Сизни ким ёқтирганини кўринг</b> — ким сизга қизиқиш билдирганини билинг",
                "badge": "⭐️ <b>Premium белгиси</b> — профилингизни ажратиб туринг",
                "priority": "🚀 <b>Профиль устуворлиги</b> — кўпроқ кўринишга эга бўлинг",
                "more": "🔥 <b>Кўпроқ кўриниш → кўпроқ Like → кўпроқ Match!</b>",
                "choose": "✨ Ўзингизга мос Premium тарифини танланг:",
                "duration": "📅 <b>Муддатни танланг:</b>",
                "p1": "📅 1 ҳафта - 25 000 сўм • ҚУЛАЙ",
                "p2": "🔥 14 кун - 39 000 сўм • ЭНГ ҚУЛАЙ",
                "p3": "⭐️ 1 ой - 59 000 сўм • ОММАБОП",
                "p4": "👑 3 ой - 129 000 сўм • ТЕЖАМКОР",
                "cancel": "❌ Бекор қилиш",
            },
        }

        t = texts.get(language, texts["uz"])

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(t["p1"], callback_data="premium_1w")],
            [InlineKeyboardButton(t["p2"], callback_data="premium_2w")],
            [InlineKeyboardButton(t["p3"], callback_data="premium_1m")],
            [InlineKeyboardButton(t["p4"], callback_data="premium_3m")],
            [InlineKeyboardButton(t["cancel"], callback_data="cancel_premium")],
        ])

        message = (
            f'{t["title"]}\n\n'
            f'{t["intro"]}\n\n'
            f'{t["unlimited_profiles"]}\n'
            f'{t["unlimited_likes"]}\n'
            f'{t["direct"]}\n'
            f'{t["who"]}\n'
            f'{t["badge"]}\n'
            f'{t["priority"]}\n\n'
            f'{t["more"]}\n\n'
            f'{t["choose"]}\n\n'
            f'{t["duration"]}'
        )

        await update.message.reply_text(
            message,
            reply_markup=keyboard,
            parse_mode="HTML"
        )

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
        # Foydalanuvchilar
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
            WHERE is_active = FALSE
        """)
        blocked_users = cur.fetchone()[0]

        # Premium
        cur.execute("""
            SELECT COUNT(*)
            FROM users
            WHERE premium_until IS NOT NULL
              AND premium_until > NOW()
        """)
        premium_users = cur.fetchone()[0]

        # Yangi foydalanuvchilar
        cur.execute("""
            SELECT COUNT(*)
            FROM users
            WHERE created_at >= CURRENT_DATE
        """)
        today_users = cur.fetchone()[0]

        cur.execute("""
            SELECT COUNT(*)
            FROM users
            WHERE created_at >= CURRENT_DATE - INTERVAL '2 days'
        """)
        three_days_users = cur.fetchone()[0]

        cur.execute("""
            SELECT COUNT(*)
            FROM users
            WHERE created_at >= CURRENT_DATE - INTERVAL '6 days'
        """)
        week_users = cur.fetchone()[0]

        cur.execute("""
            SELECT COUNT(*)
            FROM users
            WHERE created_at >= CURRENT_DATE - INTERVAL '14 days'
        """)
        fifteen_days_users = cur.fetchone()[0]

        cur.execute("""
            SELECT COUNT(*)
            FROM users
            WHERE created_at >= CURRENT_DATE - INTERVAL '1 month'
        """)
        month_users = cur.fetchone()[0]

        cur.execute("""
            SELECT COUNT(*)
            FROM users
            WHERE created_at >= CURRENT_DATE - INTERVAL '3 months'
        """)
        three_months_users = cur.fetchone()[0]

        cur.execute("""
            SELECT COUNT(*)
            FROM users
            WHERE created_at >= CURRENT_DATE - INTERVAL '6 months'
        """)
        six_months_users = cur.fetchone()[0]

        # Like va Match
        cur.execute("SELECT COUNT(*) FROM likes")
        total_likes = cur.fetchone()[0]

        cur.execute("""
            SELECT COUNT(*)
            FROM likes
            WHERE created_at >= CURRENT_DATE
        """)
        today_likes = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM matches")
        total_matches = cur.fetchone()[0]

        cur.execute("""
            SELECT COUNT(*)
            FROM matches
            WHERE created_at >= CURRENT_DATE
        """)
        today_matches = cur.fetchone()[0]

        # Referral
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

        "👥 FOYDALANUVCHILAR\n"
        f"├ Jami: {total_users}\n"
        f"├ 🟢 Aktiv: {active_users}\n"
        f"├ 🚫 Nofaol: {blocked_users}\n"
        f"├ 👑 Premium: {premium_users}\n"
        f"├ 🆕 Bugun: {today_users}\n"
        f"├ 📅 Oxirgi 3 kun: {three_days_users}\n"
        f"├ 📅 Oxirgi 7 kun: {week_users}\n"
        f"├ 📅 Oxirgi 15 kun: {fifteen_days_users}\n"
        f"├ 📅 Oxirgi 1 oy: {month_users}\n"
        f"├ 📅 Oxirgi 3 oy: {three_months_users}\n"
        f"└ 📅 Oxirgi 6 oy: {six_months_users}\n\n"

        "📈 FAOLLIK\n"
        f"├ ❤️ Jami Like: {total_likes}\n"
        f"├ ❤️ Bugungi Like: {today_likes}\n"
        f"├ 💞 Jami Match: {total_matches}\n"
        f"└ 💞 Bugungi Match: {today_matches}\n\n"

        "🎁 REFERRAL\n"
        f"└ Referral orqali kelganlar: {referral_users}"
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

        cur.execute(
            "UPDATE users SET is_active = FALSE, is_blocked = TRUE WHERE user_id = %s",
            (user_id,)
        )

        conn.commit()
        cur.close()
        conn.close()

        await update.message.reply_text(
            f"🚫 Foydalanuvchi bloklandi: {user_id}"
        )

    except:
        await update.message.reply_text(
            "❌ Format: /block USER_ID"
        )


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

        cur.execute(
            "UPDATE users SET is_active = TRUE, is_blocked = FALSE WHERE user_id = %s",
            (user_id,)
        )

        conn.commit()
        cur.close()
        conn.close()

        await update.message.reply_text(
            f"✅ Foydalanuvchi blokdan chiqarildi: {user_id}"
        )

    except:
        await update.message.reply_text(
            "❌ Format: /unblock USER_ID"
        )


async def delete_user(update, context):
    user = update.effective_user

    if user.id != ADMIN_ID:
        await update.message.reply_text("⛔ Siz admin emassiz!")
        return

    try:
        parts = update.message.text.split()
        user_id = int(parts[1])

        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute(
            "DELETE FROM users WHERE user_id = %s",
            (user_id,)
        )
        cur.execute(
            "DELETE FROM likes WHERE from_user = %s OR to_user = %s",
            (user_id, user_id)
        )
        cur.execute(
            "DELETE FROM matches WHERE user1 = %s OR user2 = %s",
            (user_id, user_id)
        )

        conn.commit()
        cur.close()
        conn.close()

        await update.message.reply_text(
            f"✅ Foydalanuvchi o'chirildi: {user_id}"
        )

    except:
        await update.message.reply_text(
            "❌ Format: /delete USER_ID"
        )


async def blocked_users(update, context):
    user = update.effective_user

    if user.id != ADMIN_ID:
        await update.message.reply_text("⛔ Siz admin emassiz!")
        return

    conn = get_db_connection()
    cur = conn.cursor()

    try:
        cur.execute(
            """
            SELECT user_id, first_name, username
            FROM users
            WHERE is_blocked = TRUE
            ORDER BY user_id DESC
            """
        )

        rows = cur.fetchall()

    finally:
        cur.close()
        conn.close()

    if not rows:
        await update.message.reply_text(
            "🚫 Bloklangan foydalanuvchilar yo'q."
        )
        return

    lines = [
        "🚫 BLOKLANGAN FOYDALANUVCHILAR\n"
    ]

    for i, row in enumerate(rows, 1):
        user_id, first_name, username = row

        name = first_name or "Noma'lum"
        username_text = f"@{username}" if username else "username yo'q"

        lines.append(
            f"{i}. 👤 {name}\n"
            f"   🆔 {user_id}\n"
            f"   📱 {username_text}\n"
        )

    lines.append(f"\n📊 Jami: {len(rows)} ta")

    await update.message.reply_text(
        "\n".join(lines)
    )


async def remove_premium(update, context):
    user = update.effective_user
    if user.id != ADMIN_ID:
        await update.message.reply_text("⛔ Siz admin emassiz!")
        return
    try:
        parts = update.message.text.split()
        user_id = int(parts[1])
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("UPDATE users SET premium_until = NULL WHERE user_id = %s", (user_id,))
        conn.commit()
        cur.close()
        conn.close()
        await update.message.reply_text(f"✅ Premium olib tashlandi: {user_id}")
    except:
        await update.message.reply_text("❌ Format: /unpremium USER_ID")

async def find_user(update, context):
    user = update.effective_user
    if user.id != ADMIN_ID:
        await update.message.reply_text("⛔ Siz admin emassiz!")
        return
    try:
        parts = update.message.text.split()
        query = parts[1]
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT user_id, first_name, username, age, city FROM users WHERE first_name ILIKE %s OR username ILIKE %s LIMIT 10", (f'%{query}%', f'%{query}%'))
        results = cur.fetchall()
        cur.close()
        conn.close()
        if not results:
            await update.message.reply_text("❌ Foydalanuvchi topilmadi.")
            return
        text = "🔍 QIDIRUV NATIJASI:\n\n"
        for r in results:
            text += f"• {r[1]} (@{r[2] or 'yoq'}) - {r[4]}\nID: {r[0]}\n\n"
        await update.message.reply_text(text)
    except:
        await update.message.reply_text("❌ Format: /finduser ISM")

async def approve_sl(update, context):
    user = update.effective_user
    if user.id != ADMIN_ID:
        await update.message.reply_text("⛔ Siz admin emassiz!")
        return
    try:
        parts = update.message.text.split()
        user_id = int(parts[1])
        amount = int(parts[2])
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("UPDATE users SET superlike_balance = COALESCE(superlike_balance, 0) + %s WHERE user_id = %s", (amount, user_id))
        conn.commit()
        cur.close()
        conn.close()
        await update.message.reply_text(f"✅ Superlike tasdiqlandi! {amount} ta")
        try:
            await context.bot.send_message(chat_id=user_id, text=f"🎉 {amount} ta Superlike hisobingizga qo'shildi!")
        except:
            pass
    except:
        await update.message.reply_text("❌ Format: /approvesl USER_ID MIQDOR")

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
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            AGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_age)],
            GENDER: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_gender)],
            CITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_city)],
            BIO: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_bio)],
            PHOTO: [
                MessageHandler(
                    filters.PHOTO | (filters.TEXT & ~filters.COMMAND),
                    get_photo
                )
            ],
        },
        fallbacks=[],
        allow_reentry=True,
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

    # New user onboarding: Welcome -> Profil yaratish -> Til
    app.add_handler(
        CallbackQueryHandler(
            create_profile,
            pattern="^create_profile$"
        )
    )

    app.add_handler(CommandHandler("admin", admin))
    app.add_handler(CommandHandler("givepremium", givepremium))
    app.add_handler(CommandHandler("removepremium", removepremium))
    app.add_handler(CommandHandler("blocked", blocked_users))

    app.add_handler(CommandHandler("checkpremium", checkpremium))
    app.add_handler(CommandHandler("premiumlist", premiumlist))
    app.add_handler(CommandHandler("premiumhistory", premiumhistory))
    app.add_handler(CommandHandler("premiumstats", premiumstats))
    app.add_handler(CommandHandler("approve", approve))
    app.add_handler(CommandHandler("broadcast", broadcast))
    app.add_handler(CommandHandler("find", find))
    app.add_handler(CommandHandler("profile", profile))
    app.add_handler(CommandHandler("matches", matches))
    app.add_handler(CommandHandler("settings", settings))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(
        MessageHandler(
            filters.PHOTO | filters.Document.ALL,
            handle_payment_check
        )
    )
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

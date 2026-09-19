import telebot
from telebot import types
import logging

import database


# ==========================================
# НАСТРОЙКИ
# ==========================================

TOKEN = "8797086782:AAFBI1rcPgBGen2eq_PuboytSNhMYasgJ2I"

# Telegram ID менеджера
MANAGER_ID = 1299734658


# ==========================================
# СОЗДАНИЕ БОТА
# ==========================================

bot = telebot.TeleBot(TOKEN)


# ==========================================
# БАЗА ДАННЫХ
# ==========================================

database.init_database()


# ==========================================
# ЛОГИ
# ==========================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger(__name__)


# ==========================================
# ЯЙЦА
# ==========================================

EGG_SHOP = {

    1: {
        "name": "🥚 Обычное яйцо",
        "price": 500
    },

    2: {
        "name": "🥚 Серебряное яйцо",
        "price": 600
    },

    3: {
        "name": "🥚 Золотое яйцо",
        "price": 700
    },

    4: {
        "name": "💎 Алмазное яйцо",
        "price": 800
    },

    5: {
        "name": "🔥 Огненное яйцо",
        "price": 900
    },

    6: {
        "name": "❄️ Ледяное яйцо",
        "price": 1000
    },

    7: {
        "name": "🌌 Космическое яйцо",
        "price": 1100
    },

    8: {
        "name": "👑 Королевское яйцо",
        "price": 1200
    },

    9: {
        "name": "⚡ Молниевое яйцо",
        "price": 1300
    },

    10: {
        "name": "🌑 Тёмное яйцо",
        "price": 1400
    }
}


# ==========================================
# ВРЕМЕННЫЕ ДАННЫЕ
# ==========================================

# Выбранные яйца для вывода
withdrawal_games = {}

# Пользователи, которые отправляют доказательства
waiting_for_proofs = {}

# Фотографии пользователей
proof_files = {}


# ==========================================
# ПОЛУЧИТЬ ЯЙЦА ПОЛЬЗОВАТЕЛЯ
# ==========================================

def get_user_egg_counts(user_id):

    eggs = database.get_player_eggs(
        user_id
    )

    egg_counts = {}

    for egg_id in eggs:

        if egg_id not in egg_counts:

            egg_counts[egg_id] = 0

        egg_counts[egg_id] += 1

    return egg_counts


# ==========================================
# START
# ==========================================

@bot.message_handler(commands=["start"])
def start(message):

    user_id = message.from_user.id

    database.create_player(
        user_id
    )

    withdrawal_games.pop(
        user_id,
        None
    )

    waiting_for_proofs.pop(
        user_id,
        None
    )

    proof_files.pop(
        user_id,
        None
    )

    logger.info(
        f"START | User {user_id}"
    )

    show_user_eggs(
        message
    )


# ==========================================
# ПОКАЗАТЬ ЯЙЦА
# ==========================================

def show_user_eggs(message):

    user_id = message.from_user.id

    egg_counts = get_user_egg_counts(
        user_id
    )


    # ======================================
    # НЕТ ЯИЦ
    # ======================================

    if not egg_counts:

        bot.send_message(
            message.chat.id,

            """🥚 ВЫВОД ЯИЦ

У тебя пока нет яиц. 🥲

Сначала получи яйца в основном
боте STEAL THE EGG."""
        )

        return


    # ======================================
    # ТЕКСТ
    # ======================================

    text = """🥚 ВЫВОД ЯИЦ

Твои яйца:

"""


    for egg_id, count in egg_counts.items():

        egg = EGG_SHOP.get(
            egg_id
        )

        if egg:

            text += (
                f"{egg['name']} × {count}\n"
            )


    text += """

━━━━━━━━━━━━━━━━━━

Выбери яйца, которые хочешь
вывести в Roblox.

Можно выбрать несколько яиц.

👇 Нажми на нужные яйца:"""


    # ======================================
    # КНОПКИ
    # ======================================

    keyboard = types.InlineKeyboardMarkup()


    for egg_id, count in egg_counts.items():

        egg = EGG_SHOP.get(
            egg_id
        )

        if not egg:
            continue

        keyboard.add(
            types.InlineKeyboardButton(
                f"{egg['name']} × {count}",
                callback_data=f"select_{egg_id}"
            )
        )


    keyboard.add(
        types.InlineKeyboardButton(
            "➡️ Продолжить",
            callback_data="continue_selection"
        )
    )


    bot.send_message(
        message.chat.id,
        text,
        reply_markup=keyboard
    )


# ==========================================
# ВЫБОР ЯЙЦА
# ==========================================

@bot.callback_query_handler(
    func=lambda call:
    call.data.startswith("select_")
)
def select_egg(call):

    user_id = call.from_user.id

    try:

        egg_id = int(
            call.data.split("_")[1]
        )

    except ValueError:

        bot.answer_callback_query(
            call.id,
            "❌ Ошибка."
        )

        return


    egg_counts = get_user_egg_counts(
        user_id
    )

    owned_count = egg_counts.get(
        egg_id,
        0
    )


    if owned_count == 0:

        bot.answer_callback_query(
            call.id,
            "❌ У тебя нет этого яйца."
        )

        return


    # ======================================
    # СОЗДАЁМ ВЫБОР
    # ======================================

    if user_id not in withdrawal_games:

        withdrawal_games[user_id] = {
            "selected": {}
        }


    selected = withdrawal_games[user_id][
        "selected"
    ]


    # ======================================
    # ВЫБРАТЬ / УБРАТЬ
    # ======================================

    if egg_id in selected:

        selected.pop(
            egg_id
        )

        bot.answer_callback_query(
            call.id,
            "❌ Яйцо убрано."
        )

    else:

        selected[egg_id] = owned_count

        bot.answer_callback_query(
            call.id,
            "✅ Яйцо выбрано."
        )


    # ======================================
    # КНОПКИ
    # ======================================

    keyboard = types.InlineKeyboardMarkup()


    for current_egg_id, count in egg_counts.items():

        egg = EGG_SHOP.get(
            current_egg_id
        )

        if not egg:
            continue


        if current_egg_id in selected:

            button_text = (
                f"✅ {egg['name']} × {count}"
            )

        else:

            button_text = (
                f"{egg['name']} × {count}"
            )


        keyboard.add(
            types.InlineKeyboardButton(
                button_text,
                callback_data=f"select_{current_egg_id}"
            )
        )


    keyboard.add(
        types.InlineKeyboardButton(
            "➡️ Продолжить",
            callback_data="continue_selection"
        )
    )


    # ======================================
    # ВЫБРАННЫЕ ЯЙЦА
    # ======================================

    selected_text = ""


    if selected:

        selected_text = (
            "\n\n🥚 Выбрано для вывода:\n"
        )


        for selected_id, selected_count in selected.items():

            egg = EGG_SHOP.get(
                selected_id
            )

            if egg:

                selected_text += (
                    f"✅ {egg['name']} × {selected_count}\n"
                )


    # ======================================
    # НОВЫЙ ТЕКСТ
    # ======================================

    new_text = """🥚 ВЫВОД ЯИЦ

Твои яйца:

"""


    for egg_id, count in egg_counts.items():

        egg = EGG_SHOP.get(
            egg_id
        )

        if egg:

            new_text += (
                f"{egg['name']} × {count}\n"
            )


    new_text += f"""

━━━━━━━━━━━━━━━━━━

Выбери яйца для вывода:{selected_text}

👇 После выбора нажми
«➡️ Продолжить»."""


    try:

        bot.edit_message_text(
            new_text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=keyboard
        )

    except Exception:

        logger.exception(
            f"EDIT ERROR | User {user_id}"
        )


# ==========================================
# ПРОДОЛЖИТЬ
# ==========================================

@bot.callback_query_handler(
    func=lambda call:
    call.data == "continue_selection"
)
def continue_selection(call):

    user_id = call.from_user.id

    if user_id not in withdrawal_games:

        bot.answer_callback_query(
            call.id,
            "❌ Выбери хотя бы одно яйцо."
        )

        return


    selected = withdrawal_games[user_id][
        "selected"
    ]


    if not selected:

        bot.answer_callback_query(
            call.id,
            "❌ Выбери хотя бы одно яйцо."
        )

        return


    bot.answer_callback_query(
        call.id
    )


    text = """🥚 ПРОВЕРКА ВЫБОРА

Ты выбрал:

"""


    total_eggs = 0


    for egg_id, count in selected.items():

        egg = EGG_SHOP.get(
            egg_id
        )

        if egg:

            text += (
                f"🥚 {egg['name']} × {count}\n"
            )

            total_eggs += count


    text += f"""

━━━━━━━━━━━━━━━━━━

🥚 Всего яиц:
{total_eggs}

Проверь выбор.

Если всё правильно,
нажми «✅ Подтвердить»."""


    keyboard = types.InlineKeyboardMarkup()


    keyboard.add(
        types.InlineKeyboardButton(
            "✅ Подтвердить",
            callback_data="confirm_eggs"
        )
    )


    keyboard.add(
        types.InlineKeyboardButton(
            "🔄 Выбрать заново",
            callback_data="restart_selection"
        )
    )


    bot.edit_message_text(
        text,
        call.message.chat.id,
        call.message.message_id,
        reply_markup=keyboard
    )


# ==========================================
# ВЫБРАТЬ ЗАНОВО
# ==========================================

@bot.callback_query_handler(
    func=lambda call:
    call.data == "restart_selection"
)
def restart_selection(call):

    user_id = call.from_user.id

    withdrawal_games.pop(
        user_id,
        None
    )

    bot.answer_callback_query(
        call.id
    )


    bot.delete_message(
        call.message.chat.id,
        call.message.message_id
    )


    show_user_eggs(
        call.message
    )


# ==========================================
# ПОДТВЕРЖДЕНИЕ ЯИЦ
# ==========================================

@bot.callback_query_handler(
    func=lambda call:
    call.data == "confirm_eggs"
)
def confirm_eggs(call):

    user_id = call.from_user.id

    if user_id not in withdrawal_games:

        bot.answer_callback_query(
            call.id,
            "❌ Заявка не найдена."
        )

        return


    selected = withdrawal_games[user_id][
        "selected"
    ]


    if not selected:

        bot.answer_callback_query(
            call.id,
            "❌ Яйца не выбраны."
        )

        return


    bot.answer_callback_query(
        call.id
    )


    # ======================================
    # ВКЛЮЧАЕМ ОТПРАВКУ ДОКАЗАТЕЛЬСТВ
    # ======================================

    waiting_for_proofs[user_id] = True

    proof_files[user_id] = []


    text = """📸 ДОКАЗАТЕЛЬСТВА

Выбор яиц сохранён! ✅

Теперь отправь скриншоты:

1️⃣ Подписка на TikTok

2️⃣ Видео про STEAL THE EGG

3️⃣ Более 1000 просмотров

📸 Можно отправить несколько
скриншотов.

После отправки всех скриншотов
нажми кнопку:

✅ ГОТОВО"""


    keyboard = types.InlineKeyboardMarkup()


    keyboard.add(
        types.InlineKeyboardButton(
            "❌ Отменить вывод",
            callback_data="cancel_withdrawal"
        )
    )


    bot.edit_message_text(
        text,
        call.message.chat.id,
        call.message.message_id,
        reply_markup=keyboard
    )


# ==========================================
# ОТМЕНА
# ==========================================

@bot.callback_query_handler(
    func=lambda call:
    call.data == "cancel_withdrawal"
)
def cancel_withdrawal(call):

    user_id = call.from_user.id

    withdrawal_games.pop(
        user_id,
        None
    )

    waiting_for_proofs.pop(
        user_id,
        None
    )

    proof_files.pop(
        user_id,
        None
    )


    bot.answer_callback_query(
        call.id
    )


    bot.send_message(
        call.message.chat.id,

        """❌ ВЫВОД ОТМЕНЁН

Заявка была отменена.

Чтобы начать заново,
нажми /start."""
    )


# ==========================================
# ПОЛУЧЕНИЕ ФОТО
# ==========================================

@bot.message_handler(
    content_types=["photo"]
)
def receive_photo(message):

    user_id = message.from_user.id


    # ======================================
    # ПРОВЕРКА
    # ======================================

    if user_id not in waiting_for_proofs:

        bot.send_message(
            message.chat.id,

            """❗ Сначала выбери яйца
для вывода через /start."""
        )

        return


    try:

        # Берём фото максимального качества
        photo = message.photo[-1]


        # ==================================
        # СОХРАНЯЕМ FILE ID
        # ==================================

        proof_files[user_id].append(
            photo.file_id
        )


        photo_number = len(
            proof_files[user_id]
        )


        # ==================================
        # КНОПКИ
        # ==================================

        keyboard = types.InlineKeyboardMarkup()


        keyboard.add(
            types.InlineKeyboardButton(
                "✅ ГОТОВО",
                callback_data="proofs_finished"
            )
        )


        keyboard.add(
            types.InlineKeyboardButton(
                "❌ Отменить вывод",
                callback_data="cancel_withdrawal"
            )
        )


        # ==================================
        # ОТВЕТ ПОЛЬЗОВАТЕЛЮ
        # ==================================

        bot.send_message(
            message.chat.id,

            f"""📸 СКРИНШОТ #{photo_number} ПОЛУЧЕН!

Скриншот сохранён. ✅

📸 Всего отправлено:
{photo_number}

Если есть ещё доказательства —
отправляй следующий скриншот.

Если это последний скриншот,
нажми кнопку «✅ ГОТОВО» ниже.""",

            reply_markup=keyboard
        )


        logger.info(
            f"PHOTO | User {user_id} | "
            f"Photo #{photo_number}"
        )


    except Exception:

        logger.exception(
            f"PHOTO ERROR | User {user_id}"
        )


        bot.send_message(
            message.chat.id,

            """❌ Не удалось сохранить
скриншот.

Попробуй отправить его ещё раз."""
        )


# ==========================================
# ГОТОВО
# ==========================================

@bot.callback_query_handler(
    func=lambda call:
    call.data == "proofs_finished"
)
def proofs_finished(call):

    user_id = call.from_user.id


    # ======================================
    # ПРОВЕРКА
    # ======================================

    if user_id not in waiting_for_proofs:

        bot.answer_callback_query(
            call.id,
            "❌ Активной заявки нет."
        )

        return


    photo_list = proof_files.get(
        user_id,
        []
    )


    photo_count = len(
        photo_list
    )


    if photo_count == 0:

        bot.answer_callback_query(
            call.id,
            "❌ Сначала отправь хотя бы одно фото."
        )

        return


    if user_id not in withdrawal_games:

        bot.answer_callback_query(
            call.id,
            "❌ Выбранные яйца не найдены."
        )

        return


    selected = withdrawal_games[user_id][
        "selected"
    ]


    bot.answer_callback_query(
        call.id,
        "✅ Заявка отправляется менеджеру!"
    )


    # ======================================
    # USERNAME
    # ======================================

    if call.from_user.username:

        username = (
            f"@{call.from_user.username}"
        )

    else:

        username = "отсутствует"


    # ======================================
    # СПИСОК ЯИЦ
    # ======================================

    eggs_text = ""

    total_eggs = 0


    for egg_id, count in selected.items():

        egg = EGG_SHOP.get(
            egg_id
        )

        if egg:

            eggs_text += (
                f"🥚 {egg['name']} × {count}\n"
            )

            total_eggs += count


    # ======================================
    # ТЕКСТ ЗАЯВКИ
    # ======================================

    manager_text = f"""📋 НОВАЯ ЗАЯВКА НА ВЫВОД

━━━━━━━━━━━━━━━━━━

👤 Пользователь:
{call.from_user.first_name}

🆔 Telegram ID:
{user_id}

🔗 Username:
{username}

━━━━━━━━━━━━━━━━━━

🥚 ЯЙЦА НА ВЫВОД:

{eggs_text}
🥚 Всего:
{total_eggs}

━━━━━━━━━━━━━━━━━━

📸 Скриншотов:
{photo_count}

━━━━━━━━━━━━━━━━━━

⏳ ЗАЯВКА ОЖИДАЕТ ПРОВЕРКИ

Проверь:

1️⃣ Подписку на TikTok
2️⃣ Видео про STEAL THE EGG
3️⃣ Более 1000 просмотров

📸 Фотографии отправлены выше.

👨‍💼 После проверки нажми
«✅ Одобрить заявку»."""


    # ======================================
    # ОТПРАВЛЯЕМ ФОТО МЕНЕДЖЕРУ
    # ======================================

    photos_sent = True


    for number, file_id in enumerate(
        photo_list,
        start=1
    ):

        try:

            bot.send_photo(
                MANAGER_ID,
                file_id,
                caption=f"""📸 ДОКАЗАТЕЛЬСТВО #{number}

👤 Пользователь:
{call.from_user.first_name}

🆔 Telegram ID:
{user_id}

🔗 Username:
{username}

📸 Скриншот #{number}"""
            )

        except Exception:

            photos_sent = False

            logger.exception(
                f"PHOTO SEND ERROR | "
                f"User {user_id} | "
                f"Photo #{number}"
            )


    # ======================================
    # ЕСЛИ ФОТО НЕ ОТПРАВИЛИСЬ
    # ======================================

    if not photos_sent:

        bot.send_message(
            call.message.chat.id,

            """❌ Не удалось отправить
все фотографии менеджеру.

Заявка не была завершена.

Попробуй нажать «✅ ГОТОВО»
ещё раз."""
        )

        bot.answer_callback_query(
            call.id,
            "❌ Ошибка отправки фото."
        )

        return


    # ======================================
    # КНОПКА ОДОБРЕНИЯ
    # ======================================

    manager_keyboard = types.InlineKeyboardMarkup()


    manager_keyboard.add(
        types.InlineKeyboardButton(
            "✅ Одобрить заявку",
            callback_data=f"approve_{user_id}"
        )
    )


    # ======================================
    # ОТПРАВЛЯЕМ ЗАЯВКУ МЕНЕДЖЕРУ
    # ======================================

    bot.send_message(
        MANAGER_ID,
        manager_text,
        reply_markup=manager_keyboard
    )


    # ======================================
    # ОТВЕТ ПОЛЬЗОВАТЕЛЮ
    # ======================================

    bot.send_message(
        call.message.chat.id,

        f"""✅ ЗАЯВКА ОТПРАВЛЕНА!

🥚 Яиц на вывод:
{total_eggs}

📸 Доказательств:
{photo_count}

━━━━━━━━━━━━━━━━━━

👨‍💼 Заявка отправлена
менеджеру на обработку.

⏳ Дождись проверки.

После проверки менеджер
свяжется с тобой.

🥚 STEAL THE EGG"""
    )


    # ======================================
    # ОЧИЩАЕМ ВРЕМЕННЫЕ ДАННЫЕ
    # ======================================

    waiting_for_proofs.pop(
        user_id,
        None
    )

    proof_files.pop(
        user_id,
        None
    )

    withdrawal_games.pop(
        user_id,
        None
    )


    logger.info(
        f"WITHDRAWAL | User {user_id} | "
        f"Eggs: {selected} | "
        f"Photos: {photo_count}"
    )


# ==========================================
# ОДОБРЕНИЕ ЗАЯВКИ МЕНЕДЖЕРОМ
# ==========================================

@bot.callback_query_handler(
    func=lambda call:
    call.data.startswith("approve_")
)
def approve_withdrawal(call):

    # ======================================
    # ПРОВЕРЯЕМ МЕНЕДЖЕРА
    # ======================================

    if call.from_user.id != MANAGER_ID:

        bot.answer_callback_query(
            call.id,
            "❌ У тебя нет доступа."
        )

        return


    # ======================================
    # ПОЛУЧАЕМ ID ПОЛЬЗОВАТЕЛЯ
    # ======================================

    try:

        user_id = int(
            call.data.split("_")[1]
        )

    except ValueError:

        bot.answer_callback_query(
            call.id,
            "❌ Ошибка ID пользователя."
        )

        return


    # ======================================
    # ОТПРАВЛЯЕМ СООБЩЕНИЕ ПОЛЬЗОВАТЕЛЮ
    # ======================================

    try:

        bot.send_message(
            user_id,

            """✅ ВАША ЗАЯВКА ОДОБРЕНА!

🥚 Ваша заявка на вывод яиц
была одобрена.

👨‍💼 С вами скоро свяжется менеджер.

Пожалуйста, ожидайте сообщения.

🥚 STEAL THE EGG"""
        )


        # ==================================
        # МЕНЕДЖЕРУ
        # ==================================

        bot.answer_callback_query(
            call.id,
            "✅ Заявка одобрена."
        )


        # ==================================
        # УБИРАЕМ КНОПКУ
        # ==================================

        try:

            bot.edit_message_reply_markup(
                call.message.chat.id,
                call.message.message_id,
                reply_markup=None
            )

        except Exception:

            logger.exception(
                f"BUTTON REMOVE ERROR | User {user_id}"
            )


        # ==================================
        # ДОБАВЛЯЕМ СТАТУС
        # ==================================

        try:

            bot.edit_message_text(
                call.message.text +
                "\n\n━━━━━━━━━━━━━━━━━━\n\n"
                "✅ ЗАЯВКА ОДОБРЕНА МЕНЕДЖЕРОМ",

                call.message.chat.id,
                call.message.message_id
            )

        except Exception:

            logger.exception(
                f"EDIT APPROVAL ERROR | User {user_id}"
            )


        logger.info(
            f"APPROVED | User {user_id} | "
            f"Manager {call.from_user.id}"
        )


    except Exception:

        logger.exception(
            f"APPROVE ERROR | User {user_id}"
        )


        bot.answer_callback_query(
            call.id,
            "❌ Не удалось отправить сообщение пользователю."
        )


# ==========================================
# ДРУГОЙ ТЕКСТ
# ==========================================

@bot.message_handler(
    content_types=["text"]
)
def other_text(message):

    bot.send_message(
        message.chat.id,

        """🥚 STEAL THE EGG

Для оформления вывода нажми:

/start

Там ты сможешь:

🥚 Посмотреть свои яйца
📤 Выбрать яйца для вывода
📸 Отправить доказательства"""
    )


# ==========================================
# ЗАПУСК
# ==========================================

logger.info(
    "================================"
)

logger.info(
    "🥚 STEAL THE EGG — WITHDRAW BOT"
)

logger.info(
    "🚀 BOT STARTED"
)

logger.info(
    "================================"
)


try:

    bot.infinity_polling(
        timeout=20,
        long_polling_timeout=20
    )

except Exception:

    logger.exception(
        "CRITICAL | Бот остановился"
    )
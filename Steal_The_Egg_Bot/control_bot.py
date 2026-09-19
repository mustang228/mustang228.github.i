import telebot
from telebot import types
import logging

import database


# ==========================================
# НАСТРОЙКИ
# ==========================================

TOKEN = "8607074626:AAF2vLhLmFWBKDNmSbEbu4XKwJpCk15aU-o"

# Telegram ID менеджера
MANAGER_ID = 1299734658

# Пароль для входа
CONTROL_PASSWORD = "12345"

# Сколько пользователей показывать на странице
USERS_PER_PAGE = 5


# ==========================================
# СОЗДАНИЕ БОТА
# ==========================================

bot = telebot.TeleBot(
    TOKEN
)


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

    1: "🥚 Обычное яйцо",

    2: "🥚 Серебряное яйцо",

    3: "🥚 Золотое яйцо",

    4: "💎 Алмазное яйцо",

    5: "🔥 Огненное яйцо",

    6: "❄️ Ледяное яйцо",

    7: "🌌 Космическое яйцо",

    8: "👑 Королевское яйцо",

    9: "⚡ Молниевое яйцо",

    10: "🌑 Тёмное яйцо"
}


# ==========================================
# ВРЕМЕННЫЕ ДАННЫЕ
# ==========================================

# Пользователи, которые вошли в панель
authorized_users = set()

# Пользователи, которые вводят пароль
waiting_for_password = set()

# Выбранный пользователь
selected_users = {}

# Выбранное яйцо
selected_eggs = {}


# ==========================================
# ПРОВЕРКА МЕНЕДЖЕРА
# ==========================================

def is_manager(user_id):

    return user_id == MANAGER_ID


# ==========================================
# ГЛАВНОЕ МЕНЮ
# ==========================================

def control_menu(chat_id):

    keyboard = types.InlineKeyboardMarkup()


    keyboard.add(
        types.InlineKeyboardButton(
            "👥 Пользователи",
            callback_data="users_0"
        )
    )


    keyboard.add(
        types.InlineKeyboardButton(
            "🔍 Найти пользователя",
            callback_data="find_user"
        )
    )


    keyboard.add(
        types.InlineKeyboardButton(
            "🚪 Выйти",
            callback_data="logout"
        )
    )


    bot.send_message(
        chat_id,

        """🛠 STEAL THE EGG
ПУЛЬТ УПРАВЛЕНИЯ

Добро пожаловать в панель
управления.

Выбери действие:""",

        reply_markup=keyboard
    )


# ==========================================
# START
# ==========================================

@bot.message_handler(
    commands=["start"]
)
def start(message):

    user_id = message.from_user.id


    # ======================================
    # ТОЛЬКО МЕНЕДЖЕР
    # ======================================

    if not is_manager(user_id):

        bot.send_message(
            message.chat.id,

            """❌ ДОСТУП ЗАПРЕЩЁН

У тебя нет доступа
к панели управления."""
        )

        return


    # Если уже авторизован
    if user_id in authorized_users:

        control_menu(
            message.chat.id
        )

        return


    # ======================================
    # ПРОСИМ ПАРОЛЬ
    # ======================================

    waiting_for_password.add(
        user_id
    )


    bot.send_message(
        message.chat.id,

        """🔐 ПУЛЬТ УПРАВЛЕНИЯ

Введите пароль для входа:

🔑 Пароль:"""
    )


# ==========================================
# ПРОВЕРКА ПАРОЛЯ
# ==========================================

@bot.message_handler(
    content_types=["text"]
)
def password_handler(message):

    user_id = message.from_user.id


    # ======================================
    # ПРОВЕРКА МЕНЕДЖЕРА
    # ======================================

    if not is_manager(user_id):

        bot.send_message(
            message.chat.id,

            "❌ У тебя нет доступа."
        )

        return


    # ======================================
    # ЕСЛИ ПОЛЬЗОВАТЕЛЬ НЕ ВВОДИТ ПАРОЛЬ
    # ======================================

    if user_id not in waiting_for_password:

        return


    # ======================================
    # ПРОВЕРКА
    # ======================================

    if message.text == CONTROL_PASSWORD:

        waiting_for_password.discard(
            user_id
        )

        authorized_users.add(
            user_id
        )


        bot.send_message(
            message.chat.id,

            """✅ ДОСТУП РАЗРЕШЁН

Вы успешно вошли
в пульт управления."""
        )


        control_menu(
            message.chat.id
        )


    else:

        bot.send_message(
            message.chat.id,

            """❌ НЕВЕРНЫЙ ПАРОЛЬ

Попробуйте ещё раз."""
        )


# ==========================================
# ПОЛЬЗОВАТЕЛИ
# ==========================================

@bot.callback_query_handler(
    func=lambda call:
    call.data.startswith("users_")
)
def users_page(call):

    user_id = call.from_user.id


    if not is_manager(user_id):

        bot.answer_callback_query(
            call.id,
            "❌ Нет доступа."
        )

        return


    if user_id not in authorized_users:

        bot.answer_callback_query(
            call.id,
            "❌ Сначала войдите."
        )

        return


    try:

        page = int(
            call.data.split("_")[1]
        )

    except ValueError:

        page = 0


    players = database.get_all_players()


    total_users = len(
        players
    )


    total_pages = (
        (total_users + USERS_PER_PAGE - 1)
        // USERS_PER_PAGE
    )


    if total_pages == 0:

        bot.answer_callback_query(
            call.id
        )


        bot.edit_message_text(
            """👥 ПОЛЬЗОВАТЕЛИ

Пока нет зарегистрированных
пользователей.""",

            call.message.chat.id,

            call.message.message_id
        )

        return


    if page < 0:

        page = 0


    if page >= total_pages:

        page = total_pages - 1


    start_index = (
        page * USERS_PER_PAGE
    )


    end_index = (
        start_index + USERS_PER_PAGE
    )


    current_players = players[
        start_index:end_index
    ]


    text = f"""👥 ПОЛЬЗОВАТЕЛИ

Страница {page + 1} из {total_pages}

Всего пользователей:
{total_users}

━━━━━━━━━━━━━━━━━━

"""


    keyboard = types.InlineKeyboardMarkup()


    for player in current_players:

        player_id = player[0]

        username = player[1]

        blocked = player[2]


        if username:

            username_text = (
                f"@{username}"
                if not username.startswith("@")
                else username
            )

        else:

            username_text = "без username"


        if blocked:

            status = "🚫"

        else:

            status = "🟢"


        button_text = (
            f"{status} {username_text} | {player_id}"
        )


        keyboard.add(
            types.InlineKeyboardButton(
                button_text,
                callback_data=f"profile_{player_id}"
            )
        )


    # ======================================
    # НАВИГАЦИЯ
    # ======================================

    navigation = []


    if page > 0:

        navigation.append(
            types.InlineKeyboardButton(
                "⬅️",
                callback_data=f"users_{page - 1}"
            )
        )


    if page < total_pages - 1:

        navigation.append(
            types.InlineKeyboardButton(
                "➡️",
                callback_data=f"users_{page + 1}"
            )
        )


    if navigation:

        keyboard.row(
            *navigation
        )


    keyboard.add(
        types.InlineKeyboardButton(
            "🏠 Главное меню",
            callback_data="control_home"
        )
    )


    bot.answer_callback_query(
        call.id
    )


    try:

        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=keyboard
        )

    except Exception:

        logger.exception(
            "USERS PAGE ERROR"
        )


# ==========================================
# ПРОФИЛЬ
# ==========================================

@bot.callback_query_handler(
    func=lambda call:
    call.data.startswith("profile_")
)
def profile(call):

    user_id = call.from_user.id


    if not is_manager(user_id):

        bot.answer_callback_query(
            call.id,
            "❌ Нет доступа."
        )

        return


    if user_id not in authorized_users:

        bot.answer_callback_query(
            call.id,
            "❌ Сначала войдите."
        )

        return


    try:

        player_id = int(
            call.data.split("_")[1]
        )

    except ValueError:

        bot.answer_callback_query(
            call.id,
            "❌ Ошибка."
        )

        return


    player = database.get_player(
        player_id
    )


    if player is None:

        bot.answer_callback_query(
            call.id,
            "❌ Пользователь не найден."
        )

        return


    db_user_id = player[0]

    username = player[1]

    blocked = player[2]

    tap_coins = player[3]

    egg_coins = player[4]


    if username:

        username_text = (
            f"@{username}"
            if not username.startswith("@")
            else username
        )

    else:

        username_text = "отсутствует"


    if blocked:

        status = "🚫 ЗАБЛОКИРОВАН"

    else:

        status = "🟢 АКТИВЕН"


    # ======================================
    # ЯЙЦА
    # ======================================

    eggs = database.get_player_eggs(
        player_id
    )


    egg_counts = {}


    for egg_id in eggs:

        egg_counts[egg_id] = (
            egg_counts.get(
                egg_id,
                0
            ) + 1
        )


    eggs_text = ""


    if egg_counts:

        for egg_id, count in egg_counts.items():

            egg_name = EGG_SHOP.get(
                egg_id,
                f"Яйцо #{egg_id}"
            )

            eggs_text += (
                f"{egg_name} × {count}\n"
            )

    else:

        eggs_text = "Нет яиц"


    text = f"""👤 ПРОФИЛЬ ПОЛЬЗОВАТЕЛЯ

━━━━━━━━━━━━━━━━━━

🆔 Telegram ID:
{db_user_id}

👤 Username:
{username_text}

📊 Статус:
{status}

━━━━━━━━━━━━━━━━━━

💰 Tap Coins:
{tap_coins}

🥚 Egg Coins:
{egg_coins}

━━━━━━━━━━━━━━━━━━

🥚 ЯЙЦА:

{eggs_text}"""


    keyboard = types.InlineKeyboardMarkup()


    # ======================================
    # БЛОКИРОВКА
    # ======================================

    if blocked:

        keyboard.add(
            types.InlineKeyboardButton(
                "🔓 Разблокировать",
                callback_data=f"unblock_{player_id}"
            )
        )

    else:

        keyboard.add(
            types.InlineKeyboardButton(
                "🚫 Заблокировать",
                callback_data=f"block_{player_id}"
            )
        )


    # ======================================
    # ДОБАВИТЬ ЯЙЦА
    # ======================================

    keyboard.add(
        types.InlineKeyboardButton(
            "🥚 Добавить яйца",
            callback_data=f"add_egg_{player_id}"
        )
    )


    # ======================================
    # ОТНЯТЬ ЯЙЦА
    # ======================================

    keyboard.add(
        types.InlineKeyboardButton(
            "🗑 Отнять яйца",
            callback_data=f"remove_egg_{player_id}"
        )
    )


    # ======================================
    # НАЗАД
    # ======================================

    keyboard.add(
        types.InlineKeyboardButton(
            "⬅️ Назад к пользователям",
            callback_data="users_0"
        )
    )


    bot.answer_callback_query(
        call.id
    )


    try:

        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=keyboard
        )

    except Exception:

        logger.exception(
            "PROFILE ERROR"
        )


# ==========================================
# ЗАБЛОКИРОВАТЬ
# ==========================================

@bot.callback_query_handler(
    func=lambda call:
    call.data.startswith("block_")
)
def block_user(call):

    user_id = call.from_user.id


    if not is_manager(user_id):

        bot.answer_callback_query(
            call.id,
            "❌ Нет доступа."
        )

        return


    try:

        target_id = int(
            call.data.split("_")[1]
        )

    except ValueError:

        bot.answer_callback_query(
            call.id,
            "❌ Ошибка."
        )

        return


    # Нельзя заблокировать самого менеджера
    if target_id == MANAGER_ID:

        bot.answer_callback_query(
            call.id,
            "❌ Нельзя заблокировать менеджера."
        )

        return


    database.block_player(
        target_id
    )


    bot.answer_callback_query(
        call.id,
        "🚫 Пользователь заблокирован."
    )


    # Обновляем профиль
    show_profile_after_action(
        call,
        target_id
    )


# ==========================================
# РАЗБЛОКИРОВАТЬ
# ==========================================

@bot.callback_query_handler(
    func=lambda call:
    call.data.startswith("unblock_")
)
def unblock_user(call):

    user_id = call.from_user.id


    if not is_manager(user_id):

        bot.answer_callback_query(
            call.id,
            "❌ Нет доступа."
        )

        return


    try:

        target_id = int(
            call.data.split("_")[1]
        )

    except ValueError:

        bot.answer_callback_query(
            call.id,
            "❌ Ошибка."
        )

        return


    database.unblock_player(
        target_id
    )


    bot.answer_callback_query(
        call.id,
        "🔓 Пользователь разблокирован."
    )


    show_profile_after_action(
        call,
        target_id
    )


# ==========================================
# ПОКАЗАТЬ ПРОФИЛЬ ПОСЛЕ ДЕЙСТВИЯ
# ==========================================

def show_profile_after_action(
    call,
    target_id
):

    player = database.get_player(
        target_id
    )


    if player is None:

        return


    db_user_id = player[0]

    username = player[1]

    blocked = player[2]

    tap_coins = player[3]

    egg_coins = player[4]


    if username:

        username_text = (
            f"@{username}"
            if not username.startswith("@")
            else username
        )

    else:

        username_text = "отсутствует"


    if blocked:

        status = "🚫 ЗАБЛОКИРОВАН"

    else:

        status = "🟢 АКТИВЕН"


    eggs = database.get_player_eggs(
        target_id
    )


    egg_counts = {}


    for egg_id in eggs:

        egg_counts[egg_id] = (
            egg_counts.get(
                egg_id,
                0
            ) + 1
        )


    eggs_text = ""


    if egg_counts:

        for egg_id, count in egg_counts.items():

            egg_name = EGG_SHOP.get(
                egg_id,
                f"Яйцо #{egg_id}"
            )

            eggs_text += (
                f"{egg_name} × {count}\n"
            )

    else:

        eggs_text = "Нет яиц"


    text = f"""👤 ПРОФИЛЬ ПОЛЬЗОВАТЕЛЯ

━━━━━━━━━━━━━━━━━━

🆔 Telegram ID:
{db_user_id}

👤 Username:
{username_text}

📊 Статус:
{status}

━━━━━━━━━━━━━━━━━━

💰 Tap Coins:
{tap_coins}

🥚 Egg Coins:
{egg_coins}

━━━━━━━━━━━━━━━━━━

🥚 ЯЙЦА:

{eggs_text}"""


    keyboard = types.InlineKeyboardMarkup()


    if blocked:

        keyboard.add(
            types.InlineKeyboardButton(
                "🔓 Разблокировать",
                callback_data=f"unblock_{target_id}"
            )
        )

    else:

        keyboard.add(
            types.InlineKeyboardButton(
                "🚫 Заблокировать",
                callback_data=f"block_{target_id}"
            )
        )


    keyboard.add(
        types.InlineKeyboardButton(
            "🥚 Добавить яйца",
            callback_data=f"add_egg_{target_id}"
        )
    )


    keyboard.add(
        types.InlineKeyboardButton(
            "🗑 Отнять яйца",
            callback_data=f"remove_egg_{target_id}"
        )
    )


    keyboard.add(
        types.InlineKeyboardButton(
            "⬅️ Назад к пользователям",
            callback_data="users_0"
        )
    )


    try:

        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=keyboard
        )

    except Exception:

        logger.exception(
            "PROFILE UPDATE ERROR"
        )


# ==========================================
# ДОБАВИТЬ ЯЙЦА
# ==========================================

@bot.callback_query_handler(
    func=lambda call:
    call.data.startswith("add_egg_")
)
def add_egg_menu(call):

    user_id = call.from_user.id


    if not is_manager(user_id):

        bot.answer_callback_query(
            call.id,
            "❌ Нет доступа."
        )

        return


    try:

        target_id = int(
            call.data.replace(
                "add_egg_",
                ""
            )
        )

    except ValueError:

        bot.answer_callback_query(
            call.id,
            "❌ Ошибка."
        )

        return


    selected_users[user_id] = target_id


    text = """🥚 ДОБАВЛЕНИЕ ЯЙЦА

Выбери какое яйцо
добавить пользователю:"""


    keyboard = types.InlineKeyboardMarkup()


    for egg_id, egg_name in EGG_SHOP.items():

        keyboard.add(
            types.InlineKeyboardButton(
                egg_name,
                callback_data=f"give_{egg_id}"
            )
        )


    keyboard.add(
        types.InlineKeyboardButton(
            "⬅️ Назад",
            callback_data=f"profile_{target_id}"
        )
    )


    bot.answer_callback_query(
        call.id
    )


    bot.edit_message_text(
        text,
        call.message.chat.id,
        call.message.message_id,
        reply_markup=keyboard
    )


# ==========================================
# ВЫБОР ЯЙЦА ДЛЯ ДОБАВЛЕНИЯ
# ==========================================

@bot.callback_query_handler(
    func=lambda call:
    call.data.startswith("give_")
)
def give_egg(call):

    user_id = call.from_user.id


    if not is_manager(user_id):

        bot.answer_callback_query(
            call.id,
            "❌ Нет доступа."
        )

        return


    if user_id not in selected_users:

        bot.answer_callback_query(
            call.id,
            "❌ Пользователь не выбран."
        )

        return


    target_id = selected_users[
        user_id
    ]


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


    selected_eggs[user_id] = {
        "user_id": target_id,
        "egg_id": egg_id,
        "action": "add"
    }


    text = f"""🥚 ДОБАВЛЕНИЕ ЯЙЦА

Пользователь:

🆔 {target_id}

Выбрано:

{EGG_SHOP.get(egg_id)}

Сколько яиц добавить?"""


    keyboard = types.InlineKeyboardMarkup()


    for amount in [1, 2, 5, 10, 25, 50]:

        keyboard.add(
            types.InlineKeyboardButton(
                f"+{amount}",
                callback_data=f"giveamount_{amount}"
            )
        )


    keyboard.add(
        types.InlineKeyboardButton(
            "⬅️ Назад",
            callback_data=f"profile_{target_id}"
        )
    )


    bot.answer_callback_query(
        call.id
    )


    bot.edit_message_text(
        text,
        call.message.chat.id,
        call.message.message_id,
        reply_markup=keyboard
    )


# ==========================================
# КОЛИЧЕСТВО ДОБАВЛЯЕМЫХ ЯИЦ
# ==========================================

@bot.callback_query_handler(
    func=lambda call:
    call.data.startswith("giveamount_")
)
def give_amount(call):

    user_id = call.from_user.id


    if not is_manager(user_id):

        bot.answer_callback_query(
            call.id,
            "❌ Нет доступа."
        )

        return


    if user_id not in selected_eggs:

        bot.answer_callback_query(
            call.id,
            "❌ Выбор не найден."
        )

        return


    try:

        amount = int(
            call.data.split("_")[1]
        )

    except ValueError:

        bot.answer_callback_query(
            call.id,
            "❌ Ошибка."
        )

        return


    data = selected_eggs[user_id]


    target_id = data["user_id"]

    egg_id = data["egg_id"]


    for _ in range(amount):

        database.add_egg(
            target_id,
            egg_id
        )


    selected_eggs.pop(
        user_id,
        None
    )

    selected_users.pop(
        user_id,
        None
    )


    bot.answer_callback_query(
        call.id,
        f"✅ Добавлено: {amount}"
    )


    bot.send_message(
        call.message.chat.id,

        f"""✅ ЯЙЦА ДОБАВЛЕНЫ

🆔 Пользователь:
{target_id}

🥚 Яйцо:
{EGG_SHOP.get(egg_id)}

➕ Добавлено:
{amount}"""
    )


    # Показываем профиль
    fake_call = call

    show_profile_after_action(
        fake_call,
        target_id
    )


# ==========================================
# ОТНЯТЬ ЯЙЦА
# ==========================================

@bot.callback_query_handler(
    func=lambda call:
    call.data.startswith("remove_egg_")
)
def remove_egg_menu(call):

    user_id = call.from_user.id


    if not is_manager(user_id):

        bot.answer_callback_query(
            call.id,
            "❌ Нет доступа."
        )

        return


    try:

        target_id = int(
            call.data.replace(
                "remove_egg_",
                ""
            )
        )

    except ValueError:

        bot.answer_callback_query(
            call.id,
            "❌ Ошибка."
        )

        return


    selected_users[user_id] = target_id


    text = """🗑 ОТНЯТИЕ ЯЙЦА

Выбери какое яйцо
отнять у пользователя:"""


    keyboard = types.InlineKeyboardMarkup()


    for egg_id, egg_name in EGG_SHOP.items():

        keyboard.add(
            types.InlineKeyboardButton(
                egg_name,
                callback_data=f"take_{egg_id}"
            )
        )


    keyboard.add(
        types.InlineKeyboardButton(
            "⬅️ Назад",
            callback_data=f"profile_{target_id}"
        )
    )


    bot.answer_callback_query(
        call.id
    )


    bot.edit_message_text(
        text,
        call.message.chat.id,
        call.message.message_id,
        reply_markup=keyboard
    )


# ==========================================
# ВЫБОР ЯЙЦА ДЛЯ УДАЛЕНИЯ
# ==========================================

@bot.callback_query_handler(
    func=lambda call:
    call.data.startswith("take_")
)
def take_egg(call):

    user_id = call.from_user.id


    if not is_manager(user_id):

        bot.answer_callback_query(
            call.id,
            "❌ Нет доступа."
        )

        return


    if user_id not in selected_users:

        bot.answer_callback_query(
            call.id,
            "❌ Пользователь не выбран."
        )

        return


    target_id = selected_users[
        user_id
    ]


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


    selected_eggs[user_id] = {
        "user_id": target_id,
        "egg_id": egg_id,
        "action": "remove"
    }


    text = f"""🗑 ОТНЯТИЕ ЯЙЦА

Пользователь:

🆔 {target_id}

Выбрано:

{EGG_SHOP.get(egg_id)}

Сколько яиц отнять?"""


    keyboard = types.InlineKeyboardMarkup()


    for amount in [1, 2, 5, 10, 25, 50]:

        keyboard.add(
            types.InlineKeyboardButton(
                f"-{amount}",
                callback_data=f"takeamount_{amount}"
            )
        )


    keyboard.add(
        types.InlineKeyboardButton(
            "⬅️ Назад",
            callback_data=f"profile_{target_id}"
        )
    )


    bot.answer_callback_query(
        call.id
    )


    bot.edit_message_text(
        text,
        call.message.chat.id,
        call.message.message_id,
        reply_markup=keyboard
    )


# ==========================================
# КОЛИЧЕСТВО УДАЛЯЕМЫХ ЯИЦ
# ==========================================

@bot.callback_query_handler(
    func=lambda call:
    call.data.startswith("takeamount_")
)
def take_amount(call):

    user_id = call.from_user.id


    if not is_manager(user_id):

        bot.answer_callback_query(
            call.id,
            "❌ Нет доступа."
        )

        return


    if user_id not in selected_eggs:

        bot.answer_callback_query(
            call.id,
            "❌ Выбор не найден."
        )

        return


    try:

        amount = int(
            call.data.split("_")[1]
        )

    except ValueError:

        bot.answer_callback_query(
            call.id,
            "❌ Ошибка."
        )

        return


    data = selected_eggs[user_id]


    target_id = data["user_id"]

    egg_id = data["egg_id"]


    removed = 0


    for _ in range(amount):

        success = database.remove_one_egg(
            target_id,
            egg_id
        )


        if success:

            removed += 1

        else:

            break


    selected_eggs.pop(
        user_id,
        None
    )

    selected_users.pop(
        user_id,
        None
    )


    bot.answer_callback_query(
        call.id,
        f"🗑 Удалено: {removed}"
    )


    bot.send_message(
        call.message.chat.id,

        f"""🗑 ЯЙЦА ОТНЯТЫ

🆔 Пользователь:
{target_id}

🥚 Яйцо:
{EGG_SHOP.get(egg_id)}

➖ Удалено:
{removed}"""
    )


    show_profile_after_action(
        call,
        target_id
    )


# ==========================================
# ГЛАВНОЕ МЕНЮ
# ==========================================

@bot.callback_query_handler(
    func=lambda call:
    call.data == "control_home"
)
def control_home(call):

    user_id = call.from_user.id


    if not is_manager(user_id):

        bot.answer_callback_query(
            call.id,
            "❌ Нет доступа."
        )

        return


    if user_id not in authorized_users:

        bot.answer_callback_query(
            call.id,
            "❌ Сначала войдите."
        )

        return


    bot.answer_callback_query(
        call.id
    )


    try:

        bot.edit_message_text(
            """🛠 STEAL THE EGG
ПУЛЬТ УПРАВЛЕНИЯ

Выбери действие:""",

            call.message.chat.id,
            call.message.message_id,
            reply_markup=get_control_keyboard()
        )

    except Exception:

        bot.send_message(
            call.message.chat.id,

            """🛠 STEAL THE EGG
ПУЛЬТ УПРАВЛЕНИЯ""",

            reply_markup=get_control_keyboard()
        )


# ==========================================
# КЛАВИАТУРА ПУЛЬТА
# ==========================================

def get_control_keyboard():

    keyboard = types.InlineKeyboardMarkup()


    keyboard.add(
        types.InlineKeyboardButton(
            "👥 Пользователи",
            callback_data="users_0"
        )
    )


    keyboard.add(
        types.InlineKeyboardButton(
            "🔍 Найти пользователя",
            callback_data="find_user"
        )
    )


    keyboard.add(
        types.InlineKeyboardButton(
            "🚪 Выйти",
            callback_data="logout"
        )
    )


    return keyboard


# ==========================================
# ПОИСК ПОЛЬЗОВАТЕЛЯ
# ==========================================

@bot.callback_query_handler(
    func=lambda call:
    call.data == "find_user"
)
def find_user(call):

    user_id = call.from_user.id


    if not is_manager(user_id):

        bot.answer_callback_query(
            call.id,
            "❌ Нет доступа."
        )

        return


    bot.answer_callback_query(
        call.id
    )


    bot.send_message(
        call.message.chat.id,

        """🔍 ПОИСК ПОЛЬЗОВАТЕЛЯ

Отправь Telegram ID пользователя.

Например:

123456789"""
    )


    # Запоминаем, что менеджер ищет пользователя
    waiting_for_password.add(
        f"search_{user_id}"
    )


# ==========================================
# ТЕКСТОВЫЙ ПОИСК
# ==========================================

@bot.message_handler(
    content_types=["text"]
)
def search_handler(message):

    user_id = message.from_user.id


    if not is_manager(user_id):

        return


    search_key = f"search_{user_id}"


    if search_key not in waiting_for_password:

        return


    waiting_for_password.discard(
        search_key
    )


    try:

        target_id = int(
            message.text.strip()
        )

    except ValueError:

        bot.send_message(
            message.chat.id,

            """❌ Неверный Telegram ID.

Нужно отправить только число."""
        )

        return


    player = database.get_player(
        target_id
    )


    if player is None:

        bot.send_message(
            message.chat.id,

            """❌ Пользователь не найден."""
        )

        return


    show_player_message(
        message.chat.id,
        target_id
    )


# ==========================================
# ПОКАЗАТЬ ПОЛЬЗОВАТЕЛЯ
# ==========================================

def show_player_message(
    chat_id,
    target_id
):

    player = database.get_player(
        target_id
    )


    if player is None:

        bot.send_message(
            chat_id,
            "❌ Пользователь не найден."
        )

        return


    user_id = player[0]

    username = player[1]

    blocked = player[2]

    tap_coins = player[3]

    egg_coins = player[4]


    if username:

        username_text = (
            f"@{username}"
            if not username.startswith("@")
            else username
        )

    else:

        username_text = "отсутствует"


    status = (
        "🚫 ЗАБЛОКИРОВАН"
        if blocked
        else "🟢 АКТИВЕН"
    )


    eggs = database.get_player_eggs(
        user_id
    )


    egg_counts = {}


    for egg_id in eggs:

        egg_counts[egg_id] = (
            egg_counts.get(
                egg_id,
                0
            ) + 1
        )


    eggs_text = ""


    if egg_counts:

        for egg_id, count in egg_counts.items():

            eggs_text += (
                f"{EGG_SHOP.get(egg_id)} × {count}\n"
            )

    else:

        eggs_text = "Нет яиц"


    text = f"""👤 ПРОФИЛЬ

━━━━━━━━━━━━━━━━━━

🆔 Telegram ID:
{user_id}

👤 Username:
{username_text}

📊 Статус:
{status}

━━━━━━━━━━━━━━━━━━

💰 Tap Coins:
{tap_coins}

🥚 Egg Coins:
{egg_coins}

━━━━━━━━━━━━━━━━━━

🥚 ЯЙЦА:

{eggs_text}"""


    keyboard = types.InlineKeyboardMarkup()


    if blocked:

        keyboard.add(
            types.InlineKeyboardButton(
                "🔓 Разблокировать",
                callback_data=f"unblock_{user_id}"
            )
        )

    else:

        keyboard.add(
            types.InlineKeyboardButton(
                "🚫 Заблокировать",
                callback_data=f"block_{user_id}"
            )
        )


    keyboard.add(
        types.InlineKeyboardButton(
            "🥚 Добавить яйца",
            callback_data=f"add_egg_{user_id}"
        )
    )


    keyboard.add(
        types.InlineKeyboardButton(
            "🗑 Отнять яйца",
            callback_data=f"remove_egg_{user_id}"
        )
    )


    keyboard.add(
        types.InlineKeyboardButton(
            "🏠 Главное меню",
            callback_data="control_home"
        )
    )


    bot.send_message(
        chat_id,
        text,
        reply_markup=keyboard
    )


# ==========================================
# ВЫХОД
# ==========================================

@bot.callback_query_handler(
    func=lambda call:
    call.data == "logout"
)
def logout(call):

    user_id = call.from_user.id


    if not is_manager(user_id):

        bot.answer_callback_query(
            call.id,
            "❌ Нет доступа."
        )

        return


    authorized_users.discard(
        user_id
    )

    waiting_for_password.discard(
        user_id
    )


    bot.answer_callback_query(
        call.id,
        "🚪 Вы вышли."
    )


    bot.edit_message_text(
        """🚪 ВЫХОД

Вы вышли из пульта управления.

Для повторного входа нажмите
/start."""
        ,
        call.message.chat.id,
        call.message.message_id
    )


# ==========================================
# ЗАПУСК
# ==========================================

logger.info(
    "================================"
)

logger.info(
    "🥚 STEAL THE EGG — CONTROL PANEL"
)

logger.info(
    "🚀 CONTROL BOT STARTED"
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
        "CRITICAL | CONTROL BOT STOPPED"
    )
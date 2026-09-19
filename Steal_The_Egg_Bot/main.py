import telebot
from telebot import types
import logging
import time
import random
from datetime import date

import database


# ============================================================
# НАСТРОЙКИ
# ============================================================

TOKEN = "8608670843:AAFtco-dfuQuR1v6XyMEllYHlHyMUTP-uTc"

TAP_DELAY = 0.7
GAME_DELAY = 2

TAP_COINS_FOR_EXCHANGE = 30
EGG_COINS_FROM_EXCHANGE = 10


# ============================================================
# БОТ
# ============================================================

bot = telebot.TeleBot(TOKEN)

database.init_database()


# ============================================================
# ВРЕМЕННЫЕ ДАННЫЕ
# ============================================================

last_tap = {}
last_game = {}
last_boss_attack = {}

guess_games = {}
math_games = {}
tic_games = {}


# ============================================================
# ЯЙЦА
# ============================================================

EGG_SHOP = {

    1: {
        "name": "🥚 Обычное яйцо",
        "price": 100,
        "rarity": "⚪ Обычное"
    },

    2: {
        "name": "🥚 Серебряное яйцо",
        "price": 600,
        "rarity": "🟢 Необычное"
    },

    3: {
        "name": "🥚 Золотое яйцо",
        "price": 700,
        "rarity": "🔵 Редкое"
    },

    4: {
        "name": "💎 Алмазное яйцо",
        "price": 800,
        "rarity": "🟣 Эпическое"
    },

    5: {
        "name": "🔥 Огненное яйцо",
        "price": 900,
        "rarity": "🟣 Эпическое"
    },

    6: {
        "name": "❄️ Ледяное яйцо",
        "price": 1000,
        "rarity": "🟡 Легендарное"
    },

    7: {
        "name": "🌌 Космическое яйцо",
        "price": 1100,
        "rarity": "🟡 Легендарное"
    },

    8: {
        "name": "👑 Королевское яйцо",
        "price": 1200,
        "rarity": "🔴 Мифическое"
    },

    9: {
        "name": "⚡ Молниевое яйцо",
        "price": 1300,
        "rarity": "🔴 Мифическое"
    },

    10: {
        "name": "🌑 Тёмное яйцо",
        "price": 1400,
        "rarity": "🔴 Мифическое"
    }
}


# ============================================================
# ПРЕДМЕТЫ
# ============================================================

ITEM_SHOP = {

    1: {
        "name": "⚡ Бустер тапов",
        "price": 150,
        "description": "+2 Tap Coins за тап на 10 минут"
    },

    2: {
        "name": "🥚 Бустер Egg Coins",
        "price": 250,
        "description": "+1 Egg Coin к наградам игр на 10 минут"
    },

    3: {
        "name": "🎁 XP Бустер",
        "price": 200,
        "description": "В 2 раза больше XP на 10 минут"
    }
}


active_items = {}


# ============================================================
# ДОСТИЖЕНИЯ
# ============================================================

ACHIEVEMENTS = {

    1: {
        "name": "👆 Первый тап",
        "description": "Сделать первый тап",
        "reward": 10
    },

    2: {
        "name": "💰 Богатей",
        "description": "Накопить 1000 Tap Coins",
        "reward": 25
    },

    3: {
        "name": "🥚 Коллекционер",
        "description": "Собрать 5 яиц",
        "reward": 50
    },

    4: {
        "name": "🥚 Яичный мастер",
        "description": "Собрать 10 разных яиц",
        "reward": 100
    },

    5: {
        "name": "🎮 Игрок",
        "description": "Сыграть 10 мини-игр",
        "reward": 50
    },

    6: {
        "name": "🔥 Серия",
        "description": "Получить серию 7 дней",
        "reward": 100
    },

    7: {
        "name": "⭐ Уровень 10",
        "description": "Достичь 10 уровня",
        "reward": 150
    },

    8: {
        "name": "👾 Охотник на боссов",
        "description": "Нанести 100 урона боссу",
        "reward": 100
    }
}


# ============================================================
# БОСС
# ============================================================

BOSS_MAX_HP = 10000
boss_hp = BOSS_MAX_HP


# ============================================================
# ЛОГИ
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger(__name__)


# ============================================================
# ИГРОК
# ============================================================

def create_player(user_id, username=""):

    database.ensure_player(
        user_id,
        username
    )


def prepare_user(message):

    user_id = message.from_user.id

    username = (
        message.from_user.username
        or ""
    )

    database.ensure_player(
        user_id,
        username
    )

    return user_id


# ============================================================
# ПРОВЕРКА БЛОКИРОВКИ
# ============================================================

def check_access(message):

    user_id = prepare_user(message)

    if database.is_blocked(user_id):

        bot.send_message(
            message.chat.id,
            "🚫 Твой аккаунт заблокирован."
        )

        return False

    return True


# ============================================================
# XP
# ============================================================

def give_xp(user_id, amount):

    before_xp, before_level = database.get_progress(
        user_id
    )

    database.add_xp(
        user_id,
        amount
    )

    after_xp, after_level = database.get_progress(
        user_id
    )

    if after_level > before_level:

        bot.send_message(
            user_id,

            f"""🎉 НОВЫЙ УРОВЕНЬ!

⭐ Ты достиг {after_level} уровня!

🎁 Продолжай играть и развиваться!"""
        )


# ============================================================
# ДОСТИЖЕНИЯ
# ============================================================

def check_achievements(user_id):

    unlocked = []

    tap_balance, egg_balance = database.get_balance(
        user_id
    )

    eggs = database.get_player_eggs(
        user_id
    )

    xp, level = database.get_progress(
        user_id
    )

    streak, last_login = database.get_login_info(
        user_id
    )

    # 1
    if (
        tap_balance >= 1
        and not database.has_achievement(
            user_id,
            1
        )
    ):

        unlocked.append(1)

    # 2
    if (
        tap_balance >= 1000
        and not database.has_achievement(
            user_id,
            2
        )
    ):

        unlocked.append(2)

    # 3
    if (
        len(eggs) >= 5
        and not database.has_achievement(
            user_id,
            3
        )
    ):

        unlocked.append(3)

    # 4
    different_eggs = len(
        set(eggs)
    )

    if (
        different_eggs >= 10
        and not database.has_achievement(
            user_id,
            4
        )
    ):

        unlocked.append(4)

    # 5
    taps, games, task_eggs = database.get_daily_tasks(
        user_id
    )

    if (
        games >= 10
        and not database.has_achievement(
            user_id,
            5
        )
    ):

        unlocked.append(5)

    # 6
    if (
        streak >= 7
        and not database.has_achievement(
            user_id,
            6
        )
    ):

        unlocked.append(6)

    # 7
    if (
        level >= 10
        and not database.has_achievement(
            user_id,
            7
        )
    ):

        unlocked.append(7)

    # 8
    boss_damage = database.get_boss_damage(
        user_id
    )

    if (
        boss_damage >= 100
        and not database.has_achievement(
            user_id,
            8
        )
    ):

        unlocked.append(8)

    # Выдача наград
    for achievement_id in unlocked:

        database.add_achievement(
            user_id,
            achievement_id
        )

        reward = ACHIEVEMENTS[
            achievement_id
        ]["reward"]

        database.add_egg_coins(
            user_id,
            reward
        )

        bot.send_message(
            user_id,

            f"""🏆 ДОСТИЖЕНИЕ ПОЛУЧЕНО!

{ACHIEVEMENTS[achievement_id]["name"]}

📜 {ACHIEVEMENTS[achievement_id]["description"]}

🎁 Награда:
+{reward} Egg Coins"""
        )


# ============================================================
# СЕРИЯ ВХОДОВ
# ============================================================

def process_login(message):

    user_id = message.from_user.id

    streak_before, last_login = database.get_login_info(
        user_id
    )

    streak = database.update_login(
        user_id
    )

    if last_login == date.today().isoformat():

        return

    reward = min(
        10 + streak * 5,
        100
    )

    database.add_egg_coins(
        user_id,
        reward
    )

    give_xp(
        user_id,
        10
    )

    bot.send_message(
        message.chat.id,

        f"""🔥 СЕРИЯ ВХОДОВ

🔥 Текущая серия:
{streak} дней

🎁 Награда за вход:
+{reward} Egg Coins

⭐ XP:
+10

Продолжай заходить каждый день!"""
    )

    check_achievements(
        user_id
    )


# ============================================================
# START
# ============================================================

@bot.message_handler(commands=["start"])
def start(message):

    if not check_access(message):
        return

    user_id = message.from_user.id

    logger.info(
        f"START | User {user_id}"
    )

    process_login(
        message
    )

    try:

        with open(
            "welcome_photo.png",
            "rb"
        ) as photo:

            bot.send_photo(
                message.chat.id,
                photo
            )

        keyboard = types.ReplyKeyboardMarkup(
            resize_keyboard=True
        )

        keyboard.add(
            types.KeyboardButton(
                "🥚 Играть"
            )
        )

        bot.send_message(
            message.chat.id,

            """🥚 ЙОУ! Добро пожаловать в STEAL THE EGG! 🚀

Готов залететь в мир яиц, коинов и мини-игр? 😎

👆 Тапай — получай Tap Coins!
🎮 Играй — получай Egg Coins!
🥚 Покупай крутые яйца!
🏆 Выполняй достижения!
👾 Сражайся с боссом!

🔥 Твоё приключение начинается прямо сейчас!

👇 Нажми «🥚 Играть»!""",

            reply_markup=keyboard
        )

    except Exception:

        logger.exception(
            "START ERROR"
        )


# ============================================================
# ГЛАВНЫЙ ОБРАБОТЧИК
# ============================================================

@bot.message_handler(
    content_types=["text"]
)
def buttons(message):

    if not check_access(message):
        return

    user_id = message.from_user.id
    text = message.text

    logger.info(
        f"MESSAGE | User {user_id} | {text}"
    )

    try:

        if text == "🥚 Играть":
            play(message)

        elif text == "👆 Тапать коины":
            tap_coins_menu(message)

        elif text == "👆 ТАПНИ ТУТ 👆":
            tapal(message)

        elif text == "Переведи в Egg Coins 💰":
            perevoda(message)

        elif text == "⬅️ Выйти в главное меню":
            exit_to_menu(message)

        elif text == "🔢 Угадать число":
            guess_number_start(message)

        elif text == "❌⭕ Крестики-нолики":
            tic_tac_toe_start(message)

        elif text == "🧠 Математика":
            mathematics_start(message)

        elif text == "🥚 Магазин яиц":
            egg_shop(message)

        elif text == "🎒 Мои яйца":
            my_eggs(message)

        elif text == "🥚 Вывод яиц":
            withdrawal_eggs(message)

        elif text == "🏆 Достижения":
            achievements_menu(message)

        elif text == "🏆 Таблица лидеров":
            leaderboard(message)

        elif text == "👤 Мой профиль":
            profile(message)

        elif text == "🎁 Ежедневный бонус":
            daily_bonus(message)

        elif text == "🎯 Ежедневные задания":
            daily_tasks(message)

        elif text == "👾 Босс":
            boss_menu(message)

        elif text == "🛒 Магазин предметов":
            item_shop(message)

        elif text.startswith(
            tuple(
                f"{i}."
                for i in range(1, 11)
            )
        ):
            buy_egg(message)

        elif text.startswith(
            tuple(
                f"🛒 {i}."
                for i in range(1, 4)
            )
        ):
            buy_item(message)

        elif user_id in guess_games:
            guess_number_answer(message)

        elif user_id in math_games:
            mathematics_answer(message)

        elif user_id in tic_games:
            tic_tac_toe_answer(message)

    except Exception:

        logger.exception(
            f"BUTTON ERROR | User {user_id}"
        )

        bot.send_message(
            message.chat.id,
            "❌ Произошла ошибка. Попробуй ещё раз."
        )


# ============================================================
# ГЛАВНОЕ МЕНЮ
# ============================================================

def play(message):

    user_id = message.from_user.id

    tap_balance, egg_balance = database.get_balance(
        user_id
    )

    eggs = database.get_player_eggs(
        user_id
    )

    xp, level = database.get_progress(
        user_id
    )

    streak, last_login = database.get_login_info(
        user_id
    )

    keyboard = types.ReplyKeyboardMarkup(
        resize_keyboard=True
    )

    keyboard.add(
        types.KeyboardButton("👆 Тапать коины"),
        types.KeyboardButton("🔢 Угадать число")
    )

    keyboard.add(
        types.KeyboardButton("❌⭕ Крестики-нолики"),
        types.KeyboardButton("🧠 Математика")
    )

    keyboard.add(
        types.KeyboardButton("🥚 Магазин яиц"),
        types.KeyboardButton("🎒 Мои яйца")
    )

    keyboard.add(
        types.KeyboardButton("👤 Мой профиль"),
        types.KeyboardButton("🏆 Достижения")
    )

    keyboard.add(
        types.KeyboardButton("🏆 Таблица лидеров"),
        types.KeyboardButton("🎯 Ежедневные задания")
    )

    keyboard.add(
        types.KeyboardButton("🎁 Ежедневный бонус"),
        types.KeyboardButton("👾 Босс")
    )

    keyboard.add(
        types.KeyboardButton("🛒 Магазин предметов")
    )

    keyboard.add(
        types.KeyboardButton("🥚 Вывод яиц")
    )

    bot.send_message(
        message.chat.id,

        f"""🥚 STEAL THE EGG 🚀

👆 Tap Coins: {tap_balance}
🥚 Egg Coins: {egg_balance}

🎒 Яиц: {len(eggs)}

⭐ Уровень: {level}
✨ XP: {xp}/{level * 100}

🔥 Серия: {streak} дней

Выбирай действие 👇""",

        reply_markup=keyboard
    )


# ============================================================
# ВЫХОД
# ============================================================

def exit_to_menu(message):

    user_id = message.from_user.id

    guess_games.pop(
        user_id,
        None
    )

    math_games.pop(
        user_id,
        None
    )

    tic_games.pop(
        user_id,
        None
    )

    play(message)


# ============================================================
# ТАПАЛКА
# ============================================================

def tap_coins_menu(message):

    user_id = message.from_user.id

    tap_balance, egg_balance = database.get_balance(
        user_id
    )

    keyboard = types.ReplyKeyboardMarkup(
        resize_keyboard=True
    )

    keyboard.add(
        types.KeyboardButton(
            "👆 ТАПНИ ТУТ 👆"
        )
    )

    keyboard.add(
        types.KeyboardButton(
            "Переведи в Egg Coins 💰"
        )
    )

    keyboard.add(
        types.KeyboardButton(
            "⬅️ Выйти в главное меню"
        )
    )

    bot.send_message(
        message.chat.id,

        f"""🔥 ТАПАЛКА

👆 Каждый тап даёт Tap Coins.

💰 Tap Coins:
{tap_balance}

🥚 Egg Coins:
{egg_balance}

👆 Обычный тап:
+1 Tap Coin

⏱️ Задержка:
0.7 сек

🔥 Используй бустеры из магазина предметов!""",

        reply_markup=keyboard
    )


def tapal(message):

    user_id = message.from_user.id

    current_time = time.monotonic()

    if user_id in last_tap:

        passed = (
            current_time
            - last_tap[user_id]
        )

        if passed < TAP_DELAY:
            return

    last_tap[user_id] = current_time

    amount = 1

    # Бустер тапов
    if user_id in active_items:

        if active_items[user_id].get(1, 0) > time.time():

            amount = 3

    database.add_tap_coins(
        user_id,
        amount
    )

    database.add_task_tap(
        user_id
    )

    give_xp(
        user_id,
        1
    )

    tap_balance, egg_balance = database.get_balance(
        user_id
    )

    bot.send_message(
        message.chat.id,

        f"""👆 +{amount} Tap Coin!

💰 Tap Coins:
{tap_balance}

🥚 Egg Coins:
{egg_balance}"""
    )

    check_achievements(
        user_id
    )


# ============================================================
# ОБМЕН
# ============================================================

def perevoda(message):

    user_id = message.from_user.id

    tap_balance, egg_balance = database.get_balance(
        user_id
    )

    if tap_balance < TAP_COINS_FOR_EXCHANGE:

        bot.send_message(
            message.chat.id,

            f"""❌ Недостаточно Tap Coins!

💰 У тебя:
{tap_balance}

🔒 Нужно:
{TAP_COINS_FOR_EXCHANGE}

🔄 30 Tap Coins = 10 Egg Coins"""
        )

        return

    converted = (
        tap_balance
        // TAP_COINS_FOR_EXCHANGE
    )

    received = (
        converted
        * EGG_COINS_FROM_EXCHANGE
    )

    spent = (
        converted
        * TAP_COINS_FOR_EXCHANGE
    )

    database.remove_tap_coins(
        user_id,
        spent
    )

    database.add_egg_coins(
        user_id,
        received
    )

    give_xp(
        user_id,
        5
    )

    tap_balance, egg_balance = database.get_balance(
        user_id
    )

    bot.send_message(
        message.chat.id,

        f"""🥚 ОБМЕН ВЫПОЛНЕН!

💰 Потрачено:
{spent} Tap Coins

🥚 Получено:
+{received} Egg Coins

💰 Осталось:
{tap_balance} Tap Coins

🥚 Egg Coins:
{egg_balance}"""
    )


# ============================================================
# УГАДАЙ ЧИСЛО
# ============================================================

def can_play_game(user_id):

    current_time = time.monotonic()

    if user_id in last_game:

        if (
            current_time
            - last_game[user_id]
            < GAME_DELAY
        ):

            return False

    last_game[user_id] = current_time

    return True


def guess_number_start(message):

    user_id = message.from_user.id

    if not can_play_game(user_id):

        bot.send_message(
            message.chat.id,
            "⏱️ Подожди немного!"
        )

        return

    number = random.randint(
        1,
        20
    )

    guess_games[user_id] = {
        "number": number,
        "attempts": 0
    }

    keyboard = types.ReplyKeyboardMarkup(
        resize_keyboard=True
    )

    keyboard.add(
        types.KeyboardButton(
            "⬅️ Выйти в главное меню"
        )
    )

    bot.send_message(
        message.chat.id,

        """🔢 УГАДАЙ ЧИСЛО

Я загадал число от 1 до 20.

🎯 У тебя 10 попыток.

🥚 Награда:

1-я → +5
2-я → +4
3-я → +3
4-я → +3
5-я → +2
6–10 → +1 Egg Coin

Пиши число 👇""",

        reply_markup=keyboard
    )


def guess_number_answer(message):

    user_id = message.from_user.id

    if message.text == "⬅️ Выйти в главное меню":

        guess_games.pop(
            user_id,
            None
        )

        play(message)

        return

    try:

        guess = int(
            message.text
        )

    except ValueError:

        bot.send_message(
            message.chat.id,
            "❌ Напиши число."
        )

        return

    if guess < 1 or guess > 20:

        bot.send_message(
            message.chat.id,
            "❌ Число от 1 до 20."
        )

        return

    game = guess_games[user_id]

    game["attempts"] += 1

    attempts = game["attempts"]

    number = game["number"]

    rewards = {
        1: 5,
        2: 4,
        3: 3,
        4: 3,
        5: 2,
        6: 1,
        7: 1,
        8: 1,
        9: 1,
        10: 1
    }

    if guess == number:

        reward = rewards[attempts]

        if (
            user_id in active_items
            and active_items[user_id].get(
                2,
                0
            ) > time.time()
        ):

            reward += 1

        database.add_egg_coins(
            user_id,
            reward
        )

        database.add_task_game(
            user_id
        )

        give_xp(
            user_id,
            10
        )

        guess_games.pop(
            user_id,
            None
        )

        _, egg_balance = database.get_balance(
            user_id
        )

        bot.send_message(
            message.chat.id,

            f"""🎉 ТЫ УГАДАЛ!

🔢 Число:
{number}

🎯 Попыток:
{attempts}

🥚 Награда:
+{reward} Egg Coins

🥚 Баланс:
{egg_balance}"""
        )

        check_achievements(
            user_id
        )

        play(message)

        return

    if attempts >= 10:

        guess_games.pop(
            user_id,
            None
        )

        database.add_task_game(
            user_id
        )

        bot.send_message(
            message.chat.id,

            f"""❌ ПОПЫТКИ ЗАКОНЧИЛИСЬ!

🔢 Было загадано:
{number}

🥚 Награда:
0 Egg Coins"""
        )

        play(message)

        return

    if guess < number:
        hint = "📈 Больше!"
    else:
        hint = "📉 Меньше!"

    bot.send_message(
        message.chat.id,

        f"""❌ Не угадал!

{hint}

🎯 Попытка:
{attempts}/10"""
    )


# ============================================================
# КРЕСТИКИ-НОЛИКИ
# ============================================================

def tic_tac_toe_start(message):

    user_id = message.from_user.id

    if not can_play_game(user_id):

        bot.send_message(
            message.chat.id,
            "⏱️ Подожди немного!"
        )

        return

    tic_games[user_id] = {
        "board": ["⬜"] * 9
    }

    send_tic_board(message)


def check_winner(board):

    combinations = [

        (0, 1, 2),
        (3, 4, 5),
        (6, 7, 8),

        (0, 3, 6),
        (1, 4, 7),
        (2, 5, 8),

        (0, 4, 8),
        (2, 4, 6)
    ]

    for a, b, c in combinations:

        if (
            board[a] != "⬜"
            and board[a] == board[b]
            and board[b] == board[c]
        ):

            return board[a]

    if "⬜" not in board:
        return "draw"

    return None


def send_tic_board(message):

    user_id = message.from_user.id

    board = tic_games[user_id]["board"]

    keyboard = types.ReplyKeyboardMarkup(
        resize_keyboard=True
    )

    for row in range(3):

        buttons_row = []

        for col in range(3):

            index = (
                row * 3
                + col
            )

            buttons_row.append(
                types.KeyboardButton(
                    f"{index + 1} {board[index]}"
                )
            )

        keyboard.row(
            *buttons_row
        )

    keyboard.add(
        types.KeyboardButton(
            "⬅️ Выйти в главное меню"
        )
    )

    bot.send_message(
        message.chat.id,

        """❌⭕ КРЕСТИКИ-НОЛИКИ

Ты играешь за ❌.

🥚 Победа: +5
🥚 Ничья: +2
🥚 Поражение: +0

Выбирай клетку:""",

        reply_markup=keyboard
    )


def tic_tac_toe_answer(message):

    user_id = message.from_user.id

    if message.text == "⬅️ Выйти в главное меню":

        tic_games.pop(
            user_id,
            None
        )

        play(message)

        return

    try:

        index = (
            int(message.text[0])
            - 1
        )

    except ValueError:

        bot.send_message(
            message.chat.id,
            "❌ Выбери клетку."
        )

        return

    if index < 0 or index > 8:
        return

    board = tic_games[user_id]["board"]

    if board[index] != "⬜":

        bot.send_message(
            message.chat.id,
            "❌ Клетка занята!"
        )

        return

    board[index] = "❌"

    winner = check_winner(board)

    if winner == "❌":

        database.add_egg_coins(
            user_id,
            5
        )

        database.add_task_game(
            user_id
        )

        give_xp(
            user_id,
            15
        )

        tic_games.pop(
            user_id,
            None
        )

        bot.send_message(
            message.chat.id,
            "🎉 ПОБЕДА!\n\n🥚 +5 Egg Coins"
        )

        check_achievements(
            user_id
        )

        play(message)

        return

    if winner == "draw":

        database.add_egg_coins(
            user_id,
            2
        )

        database.add_task_game(
            user_id
        )

        give_xp(
            user_id,
            10
        )

        tic_games.pop(
            user_id,
            None
        )

        bot.send_message(
            message.chat.id,
            "🤝 НИЧЬЯ!\n\n🥚 +2 Egg Coins"
        )

        play(message)

        return

    empty_cells = [
        i
        for i in range(9)
        if board[i] == "⬜"
    ]

    if empty_cells:

        computer_move = random.choice(
            empty_cells
        )

        board[computer_move] = "⭕"

    winner = check_winner(board)

    if winner == "⭕":

        database.add_task_game(
            user_id
        )

        tic_games.pop(
            user_id,
            None
        )

        bot.send_message(
            message.chat.id,
            "❌ Ты проиграл!\n\n🥚 +0 Egg Coins"
        )

        play(message)

        return

    if winner == "draw":

        database.add_egg_coins(
            user_id,
            2
        )

        database.add_task_game(
            user_id
        )

        tic_games.pop(
            user_id,
            None
        )

        bot.send_message(
            message.chat.id,
            "🤝 НИЧЬЯ!\n\n🥚 +2 Egg Coins"
        )

        play(message)

        return

    send_tic_board(message)


# ============================================================
# МАТЕМАТИКА
# ============================================================

def mathematics_start(message):

    user_id = message.from_user.id

    if not can_play_game(user_id):

        bot.send_message(
            message.chat.id,
            "⏱️ Подожди немного!"
        )

        return

    a = random.randint(
        5,
        30
    )

    b = random.randint(
        2,
        20
    )

    operation = random.choice(
        ["+", "-", "*"]
    )

    if operation == "+":
        answer = a + b

    elif operation == "-":
        answer = a - b

    else:
        answer = a * b

    math_games[user_id] = {
        "answer": answer
    }

    keyboard = types.ReplyKeyboardMarkup(
        resize_keyboard=True
    )

    keyboard.add(
        types.KeyboardButton(
            "⬅️ Выйти в главное меню"
        )
    )

    bot.send_message(
        message.chat.id,

        f"""🧠 МАТЕМАТИКА

🔢 {a} {operation} {b} = ?

🥚 Правильно:
+4 Egg Coins

Напиши ответ 👇""",

        reply_markup=keyboard
    )


def mathematics_answer(message):

    user_id = message.from_user.id

    if message.text == "⬅️ Выйти в главное меню":

        math_games.pop(
            user_id,
            None
        )

        play(message)

        return

    try:

        answer = int(
            message.text
        )

    except ValueError:

        bot.send_message(
            message.chat.id,
            "❌ Напиши число."
        )

        return

    correct = math_games[user_id]["answer"]

    math_games.pop(
        user_id,
        None
    )

    database.add_task_game(
        user_id
    )

    if answer == correct:

        reward = 4

        if (
            user_id in active_items
            and active_items[user_id].get(
                2,
                0
            ) > time.time()
        ):

            reward += 1

        database.add_egg_coins(
            user_id,
            reward
        )

        give_xp(
            user_id,
            10
        )

        bot.send_message(
            message.chat.id,

            f"""🎉 ПРАВИЛЬНО!

🥚 +{reward} Egg Coins"""
        )

    else:

        bot.send_message(
            message.chat.id,

            f"""❌ Неправильно!

Правильный ответ:
{correct}

🥚 +0 Egg Coins"""
        )

    check_achievements(
        user_id
    )

    play(message)


# ============================================================
# МАГАЗИН ЯИЦ
# ============================================================

def egg_shop(message):

    user_id = message.from_user.id

    _, egg_balance = database.get_balance(
        user_id
    )

    keyboard = types.ReplyKeyboardMarkup(
        resize_keyboard=True
    )

    for egg_id, egg in EGG_SHOP.items():

        keyboard.add(
            types.KeyboardButton(
                f"{egg_id}. "
                f"{egg['name']} — "
                f"{egg['price']} 🥚"
            )
        )

    keyboard.add(
        types.KeyboardButton(
            "⬅️ Выйти в главное меню"
        )
    )

    text = f"""🥚 МАГАЗИН ЯИЦ

🥚 Egg Coins:
{egg_balance}

"""

    for egg_id, egg in EGG_SHOP.items():

        text += (
            f"{egg_id}. "
            f"{egg['name']}\n"
            f"   {egg['rarity']}\n"
            f"   💰 {egg['price']} Egg Coins\n\n"
        )

    bot.send_message(
        message.chat.id,
        text,
        reply_markup=keyboard
    )


def buy_egg(message):

    user_id = message.from_user.id

    try:

        egg_id = int(
            message.text.split(".")[0]
        )

    except ValueError:

        return

    if egg_id not in EGG_SHOP:
        return

    egg = EGG_SHOP[egg_id]

    price = egg["price"]

    _, egg_balance = database.get_balance(
        user_id
    )

    if egg_balance < price:

        bot.send_message(
            message.chat.id,

            f"""❌ Недостаточно Egg Coins!

🥚 Цена:
{price}

💰 У тебя:
{egg_balance}

🔒 Не хватает:
{price - egg_balance}"""
        )

        return

    if not database.remove_egg_coins(
        user_id,
        price
    ):
        return

    database.add_egg(
        user_id,
        egg_id
    )

    database.add_task_egg(
        user_id
    )

    give_xp(
        user_id,
        15
    )

    _, egg_balance = database.get_balance(
        user_id
    )

    bot.send_message(
        message.chat.id,

        f"""🎉 ПОКУПКА!

{egg['name']}

✨ Редкость:
{egg['rarity']}

💰 Потрачено:
{price} Egg Coins

🥚 Осталось:
{egg_balance}

⭐ +15 XP"""
    )

    check_achievements(
        user_id
    )


# ============================================================
# МОИ ЯЙЦА
# ============================================================

def my_eggs(message):

    user_id = message.from_user.id

    eggs = database.get_player_eggs(
        user_id
    )

    keyboard = types.ReplyKeyboardMarkup(
        resize_keyboard=True
    )

    keyboard.add(
        types.KeyboardButton(
            "🥚 Магазин яиц"
        )
    )

    keyboard.add(
        types.KeyboardButton(
            "⬅️ Выйти в главное меню"
        )
    )

    if not eggs:

        bot.send_message(
            message.chat.id,

            """🎒 МОИ ЯЙЦА

У тебя пока нет яиц.

🥚 Загляни в магазин!""",

            reply_markup=keyboard
        )

        return

    counts = {}

    for egg_id in eggs:

        counts[egg_id] = (
            counts.get(
                egg_id,
                0
            ) + 1
        )

    text = """🎒 МОИ ЯЙЦА

"""

    for egg_id, count in counts.items():

        egg = EGG_SHOP[egg_id]

        text += (
            f"{egg['name']} × {count}\n"
            f"   {egg['rarity']}\n\n"
        )

    text += f"""
🥚 Всего:
{len(eggs)}
"""

    bot.send_message(
        message.chat.id,
        text,
        reply_markup=keyboard
    )


# ============================================================
# ПРОФИЛЬ
# ============================================================

def profile(message):

    user_id = message.from_user.id

    tap_balance, egg_balance = database.get_balance(
        user_id
    )

    xp, level = database.get_progress(
        user_id
    )

    streak, _ = database.get_login_info(
        user_id
    )

    eggs = database.get_player_eggs(
        user_id
    )

    achievements = database.get_achievements(
        user_id
    )

    bot.send_message(
        message.chat.id,

        f"""👤 МОЙ ПРОФИЛЬ

🆔 ID:
{user_id}

👤 Username:
@{message.from_user.username
   if message.from_user.username
   else "без username"}

━━━━━━━━━━━━━━

👆 Tap Coins:
{tap_balance}

🥚 Egg Coins:
{egg_balance}

🎒 Яиц:
{len(eggs)}

🏆 Достижений:
{len(achievements)}/{len(ACHIEVEMENTS)}

━━━━━━━━━━━━━━

⭐ Уровень:
{level}

✨ XP:
{xp}/{level * 100}

🔥 Серия:
{streak} дней"""
    )


# ============================================================
# ДОСТИЖЕНИЯ
# ============================================================

def achievements_menu(message):

    user_id = message.from_user.id

    unlocked = database.get_achievements(
        user_id
    )

    text = """🏆 ДОСТИЖЕНИЯ

"""

    for achievement_id, achievement in ACHIEVEMENTS.items():

        if achievement_id in unlocked:

            icon = "✅"

        else:

            icon = "🔒"

        text += (
            f"{icon} "
            f"{achievement['name']}\n"
            f"   {achievement['description']}\n"
            f"   🎁 {achievement['reward']} Egg Coins\n\n"
        )

    text += (
        f"Получено: "
        f"{len(unlocked)}/{len(ACHIEVEMENTS)}"
    )

    bot.send_message(
        message.chat.id,
        text
    )


# ============================================================
# ТАБЛИЦА ЛИДЕРОВ
# ============================================================

def leaderboard(message):

    players = database.get_top_players(
        10
    )

    text = """🏆 ТАБЛИЦА ЛИДЕРОВ

"""

    if not players:

        text += "Пока нет игроков."

    else:

        for index, player in enumerate(
            players,
            start=1
        ):

            user_id = player[0]
            username = player[1]
            egg_coins = player[2]
            level = player[4]

            if username:

                name = f"@{username}"

            else:

                name = f"ID {user_id}"

            text += (
                f"{index}. {name}\n"
                f"   🥚 {egg_coins} Egg Coins\n"
                f"   ⭐ Уровень {level}\n\n"
            )

    bot.send_message(
        message.chat.id,
        text
    )


# ============================================================
# ЕЖЕДНЕВНЫЙ БОНУС
# ============================================================

def daily_bonus(message):

    user_id = message.from_user.id

    today = date.today().isoformat()

    last_bonus = database.get_daily_bonus_date(
        user_id
    )

    if last_bonus == today:

        bot.send_message(
            message.chat.id,

            """🎁 ЕЖЕДНЕВНЫЙ БОНУС

Ты уже забрал сегодняшний бонус!

⏰ Возвращайся завтра."""
        )

        return

    streak, _ = database.get_login_info(
        user_id
    )

    reward = min(
        20 + streak * 5,
        100
    )

    database.add_egg_coins(
        user_id,
        reward
    )

    database.set_daily_bonus_date(
        user_id
    )

    give_xp(
        user_id,
        20
    )

    bot.send_message(
        message.chat.id,

        f"""🎁 ЕЖЕДНЕВНЫЙ БОНУС

🥚 Ты получил:
+{reward} Egg Coins

⭐ XP:
+20

🔥 Твоя серия:
{streak} дней

Возвращайся завтра!"""
    )


# ============================================================
# ЕЖЕДНЕВНЫЕ ЗАДАНИЯ
# ============================================================

def daily_tasks(message):

    user_id = message.from_user.id

    taps, games, eggs = database.get_daily_tasks(
        user_id
    )

    tap_done = min(
        taps,
        100
    )

    game_done = min(
        games,
        3
    )

    egg_done = min(
        eggs,
        1
    )

    text = f"""🎯 ЕЖЕДНЕВНЫЕ ЗАДАНИЯ

👆 Сделать 100 тапов
{'✅' if taps >= 100 else '🔄'}
{tap_done}/100

🎮 Сыграть 3 игры
{'✅' if games >= 3 else '🔄'}
{game_done}/3

🥚 Купить 1 яйцо
{'✅' if eggs >= 1 else '🔄'}
{egg_done}/1

━━━━━━━━━━━━━━

🎁 Награды:

👆 100 тапов → +25 Egg Coins
🎮 3 игры → +30 Egg Coins
🥚 1 яйцо → +40 Egg Coins
"""

    bot.send_message(
        message.chat.id,
        text
    )


# ============================================================
# БОСС
# ============================================================

def boss_menu(message):

    user_id = message.from_user.id

    damage = database.get_boss_damage(
        user_id
    )

    keyboard = types.InlineKeyboardMarkup()

    keyboard.add(
        types.InlineKeyboardButton(
            "⚔️ Атаковать босса",
            callback_data="boss_attack"
        )
    )

    keyboard.add(
        types.InlineKeyboardButton(
            "🔄 Обновить",
            callback_data="boss_refresh"
        )
    )

    bot.send_message(
        message.chat.id,

        f"""👾 EGG BOSS

🌑 Тёмный Хранитель

❤️ HP:
{boss_hp}/{BOSS_MAX_HP}

⚔️ Твой урон:
{damage}

🎁 За участие:
+XP

🏆 Если босс будет побеждён,
участники получат Egg Coins!

👇 Атакуй босса:""",

        reply_markup=keyboard
    )


@bot.callback_query_handler(
    func=lambda call:
    call.data in [
        "boss_attack",
        "boss_refresh"
    ]
)
def boss_callback(call):

    global boss_hp

    user_id = call.from_user.id

    if database.is_blocked(user_id):

        bot.answer_callback_query(
            call.id,
            "🚫 Ты заблокирован."
        )

        return

    if call.data == "boss_refresh":

        bot.answer_callback_query(
            call.id
        )

        boss_menu(
            call.message
        )

        return

    current_time = time.monotonic()

    if user_id in last_boss_attack:

        if (
            current_time
            - last_boss_attack[user_id]
            < 0.7
        ):

            bot.answer_callback_query(
                call.id,
                "⏱️ Подожди немного!"
            )

            return

    last_boss_attack[user_id] = current_time

    if boss_hp <= 0:

        bot.answer_callback_query(
            call.id,
            "👾 Босс уже побеждён!"
        )

        return

    damage = random.randint(
        5,
        15
    )

    boss_hp -= damage

    database.add_boss_damage(
        user_id,
        damage
    )

    give_xp(
        user_id,
        2
    )

    bot.answer_callback_query(
        call.id,
        f"⚔️ -{damage} HP!"
    )

    if boss_hp <= 0:

        boss_hp = BOSS_MAX_HP

        database.add_egg_coins(
            user_id,
            100
        )

        bot.send_message(
            call.message.chat.id,

            """🎉 БОСС ПОБЕЖДЁН!

👾 Тёмный Хранитель повержен!

🥚 Твоя награда:
+100 Egg Coins

🔥 Новый босс появился!"""
        )

        check_achievements(
            user_id
        )

        return

    bot.edit_message_text(
        f"""👾 EGG BOSS

🌑 Тёмный Хранитель

❤️ HP:
{boss_hp}/{BOSS_MAX_HP}

⚔️ Твой урон:
{database.get_boss_damage(user_id)}

Продолжай атаковать!""",

        call.message.chat.id,
        call.message.message_id,

        reply_markup=types.InlineKeyboardMarkup()
    )

    keyboard = types.InlineKeyboardMarkup()

    keyboard.add(
        types.InlineKeyboardButton(
            "⚔️ Атаковать босса",
            callback_data="boss_attack"
        )
    )

    keyboard.add(
        types.InlineKeyboardButton(
            "🔄 Обновить",
            callback_data="boss_refresh"
        )
    )

    try:

        bot.edit_message_reply_markup(
            call.message.chat.id,
            call.message.message_id,
            reply_markup=keyboard
        )

    except Exception:
        pass


# ============================================================
# МАГАЗИН ПРЕДМЕТОВ
# ============================================================

def item_shop(message):

    user_id = message.from_user.id

    _, egg_balance = database.get_balance(
        user_id
    )

    keyboard = types.ReplyKeyboardMarkup(
        resize_keyboard=True
    )

    for item_id, item in ITEM_SHOP.items():

        keyboard.add(
            types.KeyboardButton(
                f"🛒 {item_id}. "
                f"{item['name']} — "
                f"{item['price']} 🥚"
            )
        )

    keyboard.add(
        types.KeyboardButton(
            "⬅️ Выйти в главное меню"
        )
    )

    text = f"""🛒 МАГАЗИН ПРЕДМЕТОВ

🥚 Egg Coins:
{egg_balance}

"""

    for item_id, item in ITEM_SHOP.items():

        count = database.get_item_count(
            user_id,
            item_id
        )

        text += (
            f"{item_id}. {item['name']}\n"
            f"💰 Цена: {item['price']}\n"
            f"📦 У тебя: {count}\n"
            f"💡 {item['description']}\n\n"
        )

    bot.send_message(
        message.chat.id,
        text,
        reply_markup=keyboard
    )


def buy_item(message):

    user_id = message.from_user.id

    try:

        item_id = int(
            message.text.split(".")[0]
            .replace("🛒 ", "")
        )

    except ValueError:

        return

    if item_id not in ITEM_SHOP:
        return

    item = ITEM_SHOP[item_id]

    if not database.remove_egg_coins(
        user_id,
        item["price"]
    ):

        bot.send_message(
            message.chat.id,
            "❌ Недостаточно Egg Coins!"
        )

        return

    database.add_item(
        user_id,
        item_id
    )

    give_xp(
        user_id,
        10
    )

    bot.send_message(
        message.chat.id,

        f"""🛒 ПОКУПКА УСПЕШНА!

{item['name']}

💡 {item['description']}

📦 Предмет добавлен
в твой инвентарь."""
    )


# ============================================================
# ВЫВОД
# ============================================================

def withdrawal_eggs(message):

    keyboard = types.InlineKeyboardMarkup()

    keyboard.add(
        types.InlineKeyboardButton(
            "🥚 Перейти к боту вывода",
            url="https://t.me/stealtheegg_vyvod_bot"
        )
    )

    keyboard.add(
        types.InlineKeyboardButton(
            "⬅️ Главное меню",
            callback_data="withdrawal_exit"
        )
    )

    bot.send_message(
        message.chat.id,

        """🥚 ВЫВОД ЯИЦ

Для вывода перейди
в специального бота.

👉 @stealtheegg_vyvod_bot

Там ты получишь инструкции
по оформлению заявки.""",

        reply_markup=keyboard
    )


@bot.callback_query_handler(
    func=lambda call:
    call.data == "withdrawal_exit"
)
def withdrawal_exit(call):

    bot.answer_callback_query(
        call.id
    )

    play(
        call.message
    )


# ============================================================
# ЗАПУСК
# ============================================================

logger.info(
    "================================"
)

logger.info(
    "🥚 STEAL THE EGG"
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
        "CRITICAL | BOT STOPPED"
    )
import database

USER_ID = 1385580268  # <-- сюда свой Telegram ID


database.init_database()
database.create_player(USER_ID)


for egg_id in range(1, 11):
    database.add_egg(USER_ID, egg_id)


print("✅ Все 10 яиц добавлены!")
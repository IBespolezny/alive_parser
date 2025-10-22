README — Работа с базой данных PostgreSQL для Motorland Parser
===============================================================

1️⃣ Установка PostgreSQL:
------------------------
1. Скачай PostgreSQL с https://www.postgresql.org/download/
2. Установи и запомни пароль пользователя postgres
3. Создай БД:
   psql -U postgres
   CREATE DATABASE motorland;
   \q

4. Проверь подключение:
   psql -U postgres -d motorland

5. При необходимости измени логин/пароль в config.py

---------------------------------------------------------------

2️⃣ Работа db.py:
-----------------
Модуль db.py управляет таблицей catalog_items:

- create_table() — создаёт таблицу, если не существует
- upsert_item(item_data) — вставляет или обновляет товар
- deactivate_old_items(active_skus) — помечает неактуальные товары
- get_pending_details(limit) — возвращает товары для парсинга деталей
- update_detail_info(sku, new_data) — сохраняет детальные данные
- compute_hash(item_data) — создаёт MD5-хэш для контроля изменений

Поля таблицы:
-------------
id, sku, title, car_model, price, link, image,
hash, is_active, last_seen, detail_status, extra_data (JSONB)

detail_status: 
 - 'pending' — ждёт детального парсинга
 - 'parsed' — детальная страница обработана
 - 'error' — ошибка при парсинге

---------------------------------------------------------------

3️⃣ Пример работы:
------------------
1. Подключи db.py, config.py, html_parser.py, html_fetcher.py
2. Выполни db_test.py:
   python db_test.py

3. Он:
   - загружает HTML каталога
   - парсит карточки
   - сохраняет их в PostgreSQL
   - выводит в консоль, что добавлено/обновлено

---------------------------------------------------------------

4️⃣ Структура проекта:
----------------------

motorland-parserV2/
│
├── functional_scripts/
│   ├── db.py
│   ├── db_test.py
│   ├── html_fetcher.py
│   ├── html_parser.py
│   ├── session_snapshot.py
│   ├── config.py
│   └── README_DB.txt
│
└── session_snapshot.json

---------------------------------------------------------------

5️⃣ Советы:
-----------
- Всегда вызывай deactivate_old_items после полного прохода каталога.
- Для детальных страниц используй get_pending_details().
- extra_data (JSONB) хранит динамические параметры (Год, КПП и т.п.).
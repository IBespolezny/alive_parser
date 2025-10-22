import os
# config.py
# Конфигурация подключения к PostgreSQL и параметры проекта
DB_CONFIG = {
    "host": os.getenv("PG_HOST"),
    "port": 5432,
    "user": os.getenv("POSTGRES_USER"),
    "password": os.getenv("POSTGRES_PASSWORD"),
    "dbname": os.getenv("POSTGRES_DB"),
}

# DB_CONFIG = {
#     "db_name": "parser_db",
#     "user": "parser_user",
#     "password": "parser_pass",  # 🔒 замени на свой пароль
#     "host": "localhost",
#     "port": "5432",
# }

# Путь к snapshot сессии и другим служебным данным
SESSION_SNAPSHOT_PATH = "session_snapshot.json"

# Общие настройки проекта
DETAIL_WORKER_CONCURRENCY = 5
DETAIL_BATCH_SIZE = 50
DETAIL_POLL_INTERVAL = 2.0
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
CATALOG_BASE_URL = "https://motorland.by/minsk-auto-parts/"
DEACTIVATE_AFTER_PASSES = 2
FETCH_TIMEOUT = 20
CONCURRENCY = 5

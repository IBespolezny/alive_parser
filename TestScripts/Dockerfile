FROM python:3.11-slim

# Системные зависимости для psycopg2 и lxml
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Устанавливаем зависимости Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем проект
COPY functional_scripts ./functional_scripts

# Основной скрипт запускается при старте контейнера
CMD ["python", "functional_scripts/runner.py"]
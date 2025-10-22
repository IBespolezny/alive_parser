# export_to_csv_fixed.py
import csv
import json
import psycopg2
from fastapi import FastAPI, Response
from fastapi.responses import FileResponse
import io
from functional_scripts.config import DB_CONFIG

app = FastAPI()
OUTPUT_FILE = "catalog_export.csv"

def get_data_from_db():
    """Функция для получения данных из БД"""
    # Подключение к БД
    conn = psycopg2.connect(
        dbname=DB_CONFIG["dbname"],
        user=DB_CONFIG["user"],
        password=DB_CONFIG["password"],
        host=DB_CONFIG["host"],
        port=DB_CONFIG["port"]
    )
    cursor = conn.cursor()
    
    # Берём все записи
    cursor.execute("""
        SELECT sku, title, car_model, price, link, image, hash, is_active, last_seen, detail_status, extra_data
        FROM catalog_items
        WHERE is_active=TRUE;
    """)
    rows = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return rows

def generate_csv_content():
    """Генерирует содержимое CSV файла"""
    rows = get_data_from_db()
    
    # Основные поля
    main_fields = ["sku", "title", "car_model", "price", "link", "image", "hash", "is_active", "last_seen", "detail_status"]
    
    # Собираем все ключи из extra_data
    extra_keys = set()
    extra_data_list = []
    for row in rows:
        extra = row[10] or {}
        if isinstance(extra, str):
            extra = json.loads(extra)
        extra_data_list.append(extra)
        extra_keys.update(extra.keys())
    
    # Полный список колонок CSV
    all_fields = main_fields + sorted(extra_keys)
    
    # Создаём CSV в памяти
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=all_fields)
    writer.writeheader()
    
    for row, extra in zip(rows, extra_data_list):
        # Заполняем основные поля
        row_dict = dict(zip(main_fields, row[:10]))
        
        # Заполняем отдельные столбцы для extra_data
        for key in extra_keys:
            row_dict[key] = extra.get(key)
        
        writer.writerow(row_dict)
    
    return output.getvalue()

@app.get("/export-csv")
async def export_to_csv():
    """Эндпоинт для экспорта CSV"""
    csv_content = generate_csv_content()
    
    # Возвращаем CSV как файл для скачивания
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=catalog_export.csv"}
    )

@app.get("/export-csv-file")
async def export_to_csv_file():
    """Альтернативный вариант - возврат файла с диска"""
    # Сначала создаем файл на диске
    rows = get_data_from_db()
    
    # Основные поля
    main_fields = ["sku", "title", "car_model", "price", "link", "image", "hash", "is_active", "last_seen", "detail_status"]
    
    # Собираем все ключи из extra_data
    extra_keys = set()
    extra_data_list = []
    for row in rows:
        extra = row[10] or {}
        if isinstance(extra, str):
            extra = json.loads(extra)
        extra_data_list.append(extra)
        extra_keys.update(extra.keys())
    
    # Полный список колонок CSV
    all_fields = main_fields + sorted(extra_keys)
    
    # Создаём CSV файл
    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=all_fields)
        writer.writeheader()
        
        for row, extra in zip(rows, extra_data_list):
            # Заполняем основные поля
            row_dict = dict(zip(main_fields, row[:10]))
            
            # Заполняем отдельные столбцы для extra_data
            for key in extra_keys:
                row_dict[key] = extra.get(key)
            
            writer.writerow(row_dict)
    
    print(f"[INFO] Экспорт завершен, файл: {OUTPUT_FILE}")
    
    # Возвращаем файл
    return FileResponse(
        path=OUTPUT_FILE,
        filename="catalog_export.csv",
        media_type="text/csv"
    )

# Сохраняем оригинальную функцию для запуска из командной строки
def export_to_csv_original():
    """Оригинальная функция для создания CSV файла"""
    rows = get_data_from_db()
    
    # Основные поля
    main_fields = ["sku", "title", "car_model", "price", "link", "image", "hash", "is_active", "last_seen", "detail_status"]
    
    # Собираем все ключи из extra_data
    extra_keys = set()
    extra_data_list = []
    for row in rows:
        extra = row[10] or {}
        if isinstance(extra, str):
            extra = json.loads(extra)
        extra_data_list.append(extra)
        extra_keys.update(extra.keys())
    
    # Полный список колонок CSV
    all_fields = main_fields + sorted(extra_keys)
    
    # Создаём CSV
    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=all_fields)
        writer.writeheader()
        
        for row, extra in zip(rows, extra_data_list):
            # Заполняем основные поля
            row_dict = dict(zip(main_fields, row[:10]))
            
            # Заполняем отдельные столбцы для extra_data
            for key in extra_keys:
                row_dict[key] = extra.get(key)
            
            writer.writerow(row_dict)
    
    print(f"[INFO] Экспорт завершен, файл: {OUTPUT_FILE}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
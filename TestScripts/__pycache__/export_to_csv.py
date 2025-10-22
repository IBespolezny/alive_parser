# export_to_csv_fixed.py
import csv
import json
import psycopg2
from config import DB_CONFIG

OUTPUT_FILE = "catalog_export.csv"

def export_to_csv():
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
    
    cursor.close()
    conn.close()


if __name__ == "__main__":
    export_to_csv()
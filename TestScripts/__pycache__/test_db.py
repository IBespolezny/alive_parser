# db_test.py
import asyncio
import json
from pathlib import Path

from html_fetcher import HTMLFetcher
from html_parser import parse_catalog_page
from session_snapshot import load_snapshot
from db import Database
from config import DB_CONFIG, SESSION_SNAPSHOT_PATH

import aiohttp

async def main():
    # === 1. Загружаем headers и cookies ===
    headers, cookies, _ = load_snapshot(SESSION_SNAPSHOT_PATH)

    # === 2. Инициализация БД ===
    db = Database(**DB_CONFIG)

    # === 3. Загружаем HTML первой страницы каталога ===
    async with aiohttp.ClientSession(headers=headers, cookies=cookies) as session:
        fetcher = HTMLFetcher(session)
        html = await fetcher.fetch_catalog_page(9)

    # === 4. Парсим страницу ===
    items, all_keys = parse_catalog_page(html)
    print(f"Найдено товаров: {len(items)}")

    # === 5. Сохраняем в БД ===
    active_skus = []
    for item in items:
        sku = item.get("sku")
        active_skus.append(sku)
        extra_data = {
            k: v for k, v in item.items()
            if k not in ("title", "car_model", "price", "link", "sku", "image")
        }
        db.upsert_item({
            "sku": sku,
            "title": item.get("title"),
            "car_model": item.get("car_model"),
            "price": item.get("price"),
            "link": item.get("link"),
            "image": item.get("image"),
            "extra_data": extra_data
        })

    # === 6. Деактивируем пропавшие товары ===
    db.deactivate_old_items(active_skus)

    print("✅ Импорт каталога завершён успешно.")

if __name__ == "__main__":
    asyncio.run(main())

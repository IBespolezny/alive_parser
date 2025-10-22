"""
Парсер каталога — холст для поэтапной разработки
Исправлено: детальный парсер теперь не запускается до полного обхода каталога.
Добавлен флаг TEST_MAX_PAGES для тестирования с ограничением страниц.
Добавлена логика semi_off и запись в БД во время обхода.
Добавлено автоматическое логирование последней спаршенной страницы.
"""

import time
import logging
import asyncio
import aiohttp
from typing import Optional, List
from pathlib import Path
from config import (
    DB_CONFIG,
    SESSION_SNAPSHOT_PATH,
    DETAIL_WORKER_CONCURRENCY,
    DETAIL_BATCH_SIZE,
    DETAIL_POLL_INTERVAL,
    USER_AGENT,
    CATALOG_BASE_URL,
)
from header_generator import generate_headers
from html_fetcher import HTMLFetcher
from html_parser import parse_catalog_page, get_total_pages
from db import Database
import sys
# --------------------------- Логирование ---------------------------
logger = logging.getLogger("catalog_parser")
logging.basicConfig(
        stream=sys.stdout,  # вывод в stdout
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s"
    )

def setup_logging(level: str = "INFO"):
    lvl = getattr(logging, level.upper(), logging.INFO)
    logging.basicConfig(level=lvl, format="%(asctime)s [%(levelname)s] %(message)s")

# --------------------------- Флаг тестирования ---------------------------
TEST_MAX_PAGES = 0  # Для теста можно ограничить обход каталога до 10 страниц
LAST_PAGE_FILE = Path("last_page.txt")

# --------------------------- Класс обхода каталога ---------------------------
class CatalogWalker:
    def __init__(self):
        self._pass_count = 0
        self.db = Database(**DB_CONFIG)

    def _read_last_page(self) -> int:
        if LAST_PAGE_FILE.exists():
            try:
                return int(LAST_PAGE_FILE.read_text())
            except Exception:
                return 1
        return 1

    def _write_last_page(self, page: int):
        LAST_PAGE_FILE.write_text(str(page))

    def _remove_last_page_file(self):
        if LAST_PAGE_FILE.exists():
            LAST_PAGE_FILE.unlink()

    async def _check_total_pages(self, fetcher: HTMLFetcher) -> int:
        html = await fetcher.fetch(CATALOG_BASE_URL)
        if not html:
            logger.warning("Не удалось получить главную страницу каталога для проверки страниц")
            return 0
        total = get_total_pages(html)
        logger.info(f"Обнаружено страниц в каталоге: {total}")

        with self.db.conn.cursor() as cur:
            cur.execute("UPDATE catalog_items SET detail_status='semi_off' WHERE is_active=TRUE;")
        logger.info("Все активные детали помечены как semi_off")

        return total

    async def _fetch_pages(self, fetcher: HTMLFetcher, start_page: int = 1, end_page: int = 2) -> List[str]:
        pages = []
        for i in range(start_page, end_page + 1):
            url = f"{CATALOG_BASE_URL}?pg={i}" if i > 1 else CATALOG_BASE_URL
            html = await fetcher.fetch(url)
            if html:
                pages.append(html)
                logger.info(f"Fetched catalog page {i}")

                # Парсим страницу и сохраняем прямо в БД
                items, all_keys = parse_catalog_page(html)
                for item in items:
                    sku = item.get("sku")
                    if not sku:
                        continue
                    extra_data = {k: v for k, v in item.items() if k not in ("title", "car_model", "price", "link", "sku", "image")}

                    # upsert с проверкой hash
                    self.db.upsert_item({
                        "sku": sku,
                        "title": item.get("title"),
                        "car_model": item.get("car_model"),
                        "price": item.get("price"),
                        "link": item.get("link"),
                        "image": item.get("image"),
                        "extra_data": extra_data,
                    })

                    # Убираем semi_off у найденных
                    with self.db.conn.cursor() as cur:
                        cur.execute("UPDATE catalog_items SET detail_status='pending' WHERE sku=%s AND detail_status='semi_off';", (sku,))

                # Логируем последнюю спаршенную страницу
                self._write_last_page(i)

            else:
                logger.warning(f"Failed to fetch catalog page {i}")

            await asyncio.sleep(0.3)
        return pages

    async def start_pass_async(self):
        self._pass_count += 1
        logger.info(f"Starting catalog pass #{self._pass_count}")
        async with aiohttp.ClientSession(headers=generate_headers()) as session:
            fetcher = HTMLFetcher(session)
            total_pages = await self._check_total_pages(fetcher)
            if total_pages < 3000:
                logger.warning(f"Количество страниц ({total_pages}) меньше 3000 — переход к детальному парсингу позже.")
                
                return None

            start_page = self._read_last_page()
            max_pages = TEST_MAX_PAGES if TEST_MAX_PAGES else total_pages
            end_page = min(start_page + max_pages - 1, total_pages)

            pages = await self._fetch_pages(fetcher, start_page, end_page)

            # Деактивируем детали, которые остались semi_off
            with self.db.conn.cursor() as cur:
                cur.execute("UPDATE catalog_items SET is_active=FALSE WHERE detail_status='semi_off';")
            logger.info("Детали, которые не были найдены, деактивированы (is_active=FALSE)")

            # Если достигли последней страницы, удаляем файл
            if end_page >= max_pages:
                self._remove_last_page_file()

        return pages

    def start_pass(self):
        return asyncio.run(self.start_pass_async())

    def count_passes(self):
        return self._pass_count

    def close(self):
        logger.info("CatalogWalker closed")

# --------------------------- Основной цикл ---------------------------

def main_loop():
    setup_logging("INFO")
    logger.info("Starting main loop")
    catalog = CatalogWalker()

    try:
        pages = catalog.start_pass()
        if not pages:
            logger.info("Каталог слишком короткий или не удалось пройти — детальный парсинг не запускаем.")
        else:
            logger.info(f"Каталог успешно пройден ({len(pages)} страниц). Все semi_off переведены в inActive, last_page.txt удалён.")
        logger.info("Работа завершена.")
    except KeyboardInterrupt:
        logger.info("KeyboardInterrupt — завершение работы")
    except Exception as e:
        logger.exception("Unexpected error in main loop: %s", e)
    finally:
        catalog.close()
        logger.info("Main loop exited")

if __name__ == "__main__":
    main_loop()

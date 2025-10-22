import aiohttp
import asyncio
import logging
import sys
from html_fetcher import HTMLFetcher
from html_parser import parse_detail_page
from config import DB_CONFIG, DETAIL_WORKER_CONCURRENCY, DETAIL_POLL_INTERVAL, DETAIL_BATCH_SIZE
from db import Database

logger = logging.getLogger(__name__)
logging.basicConfig(
    stream=sys.stdout,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

class DetailWorker:
    def __init__(self):
        self.db = Database(**DB_CONFIG)
        self.sem = asyncio.Semaphore(DETAIL_WORKER_CONCURRENCY)
        self.running = True

    def mark_batch_in_progress(self, limit: int):
        """Отмечает batch задач как in_progress, используя колонку status."""
        with self.db.conn.cursor() as cur:
            cur.execute("""
                UPDATE catalog_items
                SET status = 'in_progress'
                WHERE id IN (
                    SELECT id FROM catalog_items
                    WHERE status = 'pending' AND is_active = TRUE
                    LIMIT %s
                    FOR UPDATE SKIP LOCKED
                )
                RETURNING sku, link;
            """, (limit,))
            rows = cur.fetchall()
        return rows

    def reset_status(self, sku: str, status: str = "pending"):
        """Сбрасывает статус конкретной записи."""
        with self.db.conn.cursor() as cur:
            cur.execute("UPDATE catalog_items SET status = %s WHERE sku = %s;", (status, sku))
        self.db.conn.commit()

    def update_detail_info(self, sku: str, parsed: dict):
        """Обновляет detail-информацию и ставит status='parsed'."""
        with self.db.conn.cursor() as cur:
            cur.execute("SELECT extra_data FROM catalog_items WHERE sku = %s;", (sku,))
            row = cur.fetchone()
            existing_extra = row[0] if row and row[0] else {}
            merged_extra = existing_extra.copy()
            merged_extra.update(parsed.get("extra_data", {}))

            cur.execute("""
                UPDATE catalog_items
                SET extra_data = %s, status = 'parsed', last_seen = NOW()
                WHERE sku = %s;
            """, (json.dumps(merged_extra), sku))
        self.db.conn.commit()

    async def run(self):
        """Основной цикл работы воркера."""
        async with aiohttp.ClientSession() as session:
            fetcher = HTMLFetcher(session)
            while self.running:
                tasks = self.mark_batch_in_progress(DETAIL_BATCH_SIZE)
                if not tasks:
                    logger.info("Нет задач для парсинга. Ожидание...")
                    await asyncio.sleep(DETAIL_POLL_INTERVAL)
                    break

                logger.info(f"Найдено {len(tasks)} задач на обработку.")
                await asyncio.gather(*(self.process_one(fetcher, sku, url) for sku, url in tasks))

    async def process_one(self, fetcher: HTMLFetcher, sku: str, url: str):
        async with self.sem:
            try:
                html = await fetcher.fetch_detail_page(url)
                if not html:
                    logger.warning(f"[{sku}] Не удалось загрузить страницу, возвращаем в очередь")
                    self.reset_status(sku, "pending")
                    return

                parsed = parse_detail_page(html)
                self.update_detail_info(sku, parsed)
                logger.info(f"[{sku}] Успешно обновлено (parsed)")

            except Exception as e:
                logger.exception(f"[{sku}] Ошибка парсинга: {e}")
                self.reset_status(sku, "pending")


if __name__ == "__main__":
    import json

    async def main():
        worker = DetailWorker()
        await worker.run()

    asyncio.run(main())

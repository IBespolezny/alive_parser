import os
import psycopg2
from psycopg2.extras import Json
import hashlib
from datetime import datetime

class Database:
    def __init__(self, dbname, user, password, host=os.getenv("PG_HOST"), port=os.getenv("PG_PORT")):
        self.conn = psycopg2.connect(
            dbname=dbname,
            user=user,
            password=password,
            host=host,
            port=port
        )
        self.conn.autocommit = True
        self.create_table()

    def create_table(self):
        with self.conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS catalog_items (
                    id SERIAL PRIMARY KEY,
                    sku TEXT UNIQUE,
                    title TEXT,
                    car_model TEXT,
                    price TEXT,
                    link TEXT,
                    image TEXT,
                    hash CHAR(32),
                    is_active BOOLEAN DEFAULT TRUE,
                    last_seen TIMESTAMP,
                    detail_status TEXT DEFAULT 'pending',
                    extra_data JSONB
                );
            """)

    def compute_hash(self, item_data: dict) -> str:
        """Создаёт MD5-хэш по основным полям и характеристикам."""
        hash_source = (
            (item_data.get("sku") or "") +
            (item_data.get("title") or "") +
            (item_data.get("car_model") or "") +
            (item_data.get("price") or "") +
            (item_data.get("image") or "") +
            (item_data.get("link") or "") +
            str(item_data.get("extra_data") or "")
        )
        return hashlib.md5(hash_source.encode("utf-8")).hexdigest()

    def upsert_item(self, item_data: dict):
        """Добавляет или обновляет товар без дублирования."""
        sku = item_data.get("sku")
        if not sku:
            return

        item_hash = self.compute_hash(item_data)
        item_data["hash"] = item_hash
        now = datetime.utcnow()

        with self.conn.cursor() as cur:
            # Проверяем, есть ли товар
            cur.execute("SELECT hash FROM catalog_items WHERE sku = %s;", (sku,))
            result = cur.fetchone()

            if result is None:
                # Новый товар
                cur.execute("""
                    INSERT INTO catalog_items (sku, title, car_model, price, link, image, hash, last_seen, extra_data)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    sku,
                    item_data.get("title"),
                    item_data.get("car_model"),
                    item_data.get("price"),
                    item_data.get("link"),
                    item_data.get("image"),
                    item_hash,
                    now,
                    Json(item_data.get("extra_data", {}))
                ))
            else:
                old_hash = result[0]
                if old_hash != item_hash:
                    # Обновляем, если изменилось
                    cur.execute("""
                        UPDATE catalog_items
                        SET title=%s, car_model=%s, price=%s, link=%s, image=%s,
                            hash=%s, last_seen=%s, is_active=TRUE, extra_data=%s
                        WHERE sku=%s
                    """, (
                        item_data.get("title"),
                        item_data.get("car_model"),
                        item_data.get("price"),
                        item_data.get("link"),
                        item_data.get("image"),
                        item_hash,
                        now,
                        Json(item_data.get("extra_data", {})),
                        sku
                    ))
                else:
                    # Просто обновляем время и активность
                    cur.execute("""
                        UPDATE catalog_items SET last_seen=%s, is_active=TRUE WHERE sku=%s
                    """, (now, sku))

    def deactivate_old_items(self, active_skus: list[str]):
        """Деактивирует товары, которых нет в текущем каталоге."""
        with self.conn.cursor() as cur:
            cur.execute("""
                UPDATE catalog_items
                SET is_active=FALSE
                WHERE sku NOT IN %s;
            """, (tuple(active_skus),))

    def get_pending_details(self, limit=50):
        """Возвращает товары, для которых нужно парсить детальную страницу."""
        with self.conn.cursor() as cur:
            cur.execute("""
                SELECT sku, link FROM catalog_items
                WHERE detail_status='pending' AND is_active=TRUE
                LIMIT %s;
            """, (limit,))
            return cur.fetchall()

    def update_detail_info(self, sku, new_data: dict):
        """Обновляет товар после парсинга детальной страницы."""
        item_hash = self.compute_hash(new_data)
        now = datetime.utcnow()
        with self.conn.cursor() as cur:
            cur.execute("""
                UPDATE catalog_items
                SET extra_data=%s, hash=%s, detail_status='parsed', last_seen=%s
                WHERE sku=%s;
            """, (Json(new_data.get("extra_data", {})), item_hash, now, sku))

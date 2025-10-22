import os
import psycopg2
import hashlib
import json
from datetime import datetime, timedelta
from psycopg2.extras import Json, RealDictCursor
from typing import List, Tuple, Optional, Dict, Any

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

    
    def mark_batch_in_progress(self, limit=50) -> list[tuple[str, str]]:
        """
        Берёт batch задач со статусом 'pending' и помечает их как 'in_progress',
        чтобы несколько воркеров не брали одну и ту же запись.
        """
        with self.conn.cursor() as cur:
            cur.execute("""
                UPDATE catalog_items
                SET detail_status='in_progress'
                WHERE id IN (
                    SELECT id FROM catalog_items
                    WHERE detail_status='pending' AND is_active=TRUE
                    LIMIT %s
                    FOR UPDATE SKIP LOCKED
                )
                RETURNING sku, link;
            """, (limit,))
            return cur.fetchall()
    
    def update_detail_info(self, sku, new_data: dict):
        """
        Обновляет запись товара после парсинга детальной страницы.
        Если extra_data уже есть, дописывает новые ключи и значения.
        """
        with self.conn.cursor() as cur:
            # Получаем старое extra_data
            cur.execute("SELECT extra_data FROM catalog_items WHERE sku=%s;", (sku,))
            row = cur.fetchone()
            existing_extra = row[0] if row and row[0] else {}

            # Объединяем старые и новые данные
            merged_extra = existing_extra.copy()
            merged_extra.update(new_data.get("extra_data", {}))

            # Пересчёт hash по всем данным (можно добавить поля из основного item, если нужно)
            # В этом примере хэш только для extra_data
            import hashlib
            new_hash = hashlib.md5(json.dumps(merged_extra, sort_keys=True).encode("utf-8")).hexdigest()

            # Обновляем запись
            cur.execute("""
                UPDATE catalog_items
                SET extra_data=%s, hash=%s, detail_status='parsed', last_seen=NOW()
                WHERE sku=%s;
            """, (Json(merged_extra), new_hash, sku))

        def create_table(self):
            """Создаёт основную таблицу и производит простую миграцию колонок (если нужно)."""
            with self.conn.cursor() as cur:
                # основная таблица (как у тебя)
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
                        last_seen_pass INTEGER DEFAULT 0,
                        created_at TIMESTAMP DEFAULT now(),
                        detail_status TEXT DEFAULT 'pending',
                        attempts INTEGER DEFAULT 0,
                        extra_data JSONB
                    );
                """)
                # таблица для архива (если хочешь хранить удалённые записи)
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS catalog_items_archive (
                        id BIGSERIAL PRIMARY KEY,
                        archived_at TIMESTAMP DEFAULT now(),
                        data JSONB
                    );
                """)
                # таблица meta для хранения метаданных (pages_count, current_pass и т.д.)
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS meta (
                        key TEXT PRIMARY KEY,
                        value JSONB,
                        updated_at TIMESTAMP DEFAULT now()
                    );
                """)
            # оставляем autocommit=True как у тебя

    # -----------------------------
    # Meta helpers
    # -----------------------------
    def get_meta(self, key: str, default: Optional[Any] = None) -> Any:
        """Возвращает разобранное JSON-значение meta по ключу."""
        with self.conn.cursor() as cur:
            cur.execute("SELECT value FROM meta WHERE key = %s;", (key,))
            row = cur.fetchone()
            if not row:
                return default
            return row[0]

    def set_meta(self, key: str, value: Any) -> None:
        """Записывает/обновляет meta (значение сохраняется как JSONB)."""
        with self.conn.cursor() as cur:
            cur.execute("""
                INSERT INTO meta (key, value, updated_at)
                VALUES (%s, %s, now())
                ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value, updated_at = now();
            """, (key, Json(value)))

    # -----------------------------
    # Upsert with pass tracking
    # -----------------------------
    def upsert_item(self, item_data: dict, last_seen_pass: Optional[int] = None):
        """
        Добавляет или обновляет товар.
        Если передан last_seen_pass (int) — ставит last_seen_pass = value.
        При создании нового товара detail_status остаётся 'pending' (чтобы его распарсили детально).
        """
        sku = item_data.get("sku")
        if not sku:
            return

        item_hash = self.compute_hash(item_data)
        now = datetime.utcnow()
        last_seen_pass_val = last_seen_pass if last_seen_pass is not None else 0

        with self.conn.cursor() as cur:
            cur.execute("SELECT hash, extra_data FROM catalog_items WHERE sku = %s;", (sku,))
            result = cur.fetchone()

            if result is None:
                # Новый товар — создаём
                cur.execute("""
                    INSERT INTO catalog_items
                        (sku, title, car_model, price, link, image, hash, last_seen, last_seen_pass, is_active, extra_data)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, TRUE, %s)
                    ON CONFLICT (sku) DO NOTHING
                """, (
                    sku,
                    item_data.get("title"),
                    item_data.get("car_model"),
                    item_data.get("price"),
                    item_data.get("link"),
                    item_data.get("image"),
                    item_hash,
                    now,
                    last_seen_pass_val,
                    Json(item_data.get("extra_data", {}))
                ))
            else:
                old_hash, old_extra = result[0], result[1] or {}
                # Если хэш изменился — обновляем поля и объединяем extra_data (не теряем старые)
                if old_hash != item_hash:
                    # объединим extra_data: старое + новое (new overrides old)
                    merged_extra = {}
                    try:
                        merged_extra = old_extra.copy()
                    except Exception:
                        merged_extra = old_extra if isinstance(old_extra, dict) else {}
                    merged_extra.update(item_data.get("extra_data", {}))

                    cur.execute("""
                        UPDATE catalog_items
                        SET title=%s, car_model=%s, price=%s, link=%s, image=%s,
                            hash=%s, last_seen=%s, last_seen_pass=%s, is_active=TRUE, extra_data=%s
                        WHERE sku=%s
                    """, (
                        item_data.get("title"),
                        item_data.get("car_model"),
                        item_data.get("price"),
                        item_data.get("link"),
                        item_data.get("image"),
                        item_hash,
                        now,
                        last_seen_pass_val,
                        Json(merged_extra),
                        sku
                    ))
                else:
                    # Хэш не изменился — обновляем только время и pass (если передан)
                    cur.execute("""
                        UPDATE catalog_items
                        SET last_seen=%s, last_seen_pass=%s, is_active=TRUE
                        WHERE sku=%s
                    """, (now, last_seen_pass_val, sku))

    # -----------------------------
    # Deactivate/archive helpers (двухпроходная логика)
    # -----------------------------
    def deactivate_items_not_seen_since_pass(self, threshold_pass: int, archive: bool = True) -> int:
        """
        Деактивирует (или архивирует+удаляет) товары, у которых last_seen_pass <= threshold_pass.
        Если archive=True — переносим записи в catalog_items_archive (JSON) и затем удаляем.
        Возвращает число деактивированных/архивированных записей.
        """
        with self.conn.cursor() as cur:
            if archive:
                # Переносим в архив (сохраняем полные данные)
                cur.execute("""
                    INSERT INTO catalog_items_archive (data)
                    SELECT to_jsonb(ci)
                    FROM catalog_items ci
                    WHERE last_seen_pass <= %s;
                """, (threshold_pass,))
                # Удалим из основной таблицы (если хочешь деактивировать без удаления, можно UPDATE)
                cur.execute("DELETE FROM catalog_items WHERE last_seen_pass <= %s RETURNING 1;", (threshold_pass,))
                deleted = cur.rowcount
                return deleted
            else:
                # Просто деактивируем (оставляем в таблице, что важно для CSV-запросов)
                cur.execute("""
                    UPDATE catalog_items
                    SET is_active = FALSE
                    WHERE last_seen_pass <= %s
                    RETURNING sku;
                """, (threshold_pass,))
                rows = cur.fetchall()
                return len(rows)

    # -----------------------------
    # Counters / query helpers
    # -----------------------------
    def count_pending_details(self) -> int:
        with self.conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM catalog_items WHERE detail_status='pending' AND is_active=TRUE;")
            return cur.fetchone()[0]

    def get_pending_details(self, limit=50):
        """Возвращает товары, для которых нужно парсить детальную страницу (без изменения статуса)."""
        with self.conn.cursor() as cur:
            cur.execute("""
                SELECT sku, link FROM catalog_items
                WHERE detail_status='pending' AND is_active=TRUE
                LIMIT %s;
            """, (limit,))
            return cur.fetchall()

    # mark_batch_in_progress у тебя уже есть и корректен (оставь его)
    # reset_status у тебя уже есть (reset_status(sku, status='pending')) — оставь

    # -----------------------------
    # In-progress timeout handling
    # -----------------------------
    def reset_in_progress_older_than(self, seconds: int = 600) -> int:
        """
        Возвращает в pending все задачи со статусом 'in_progress', у которых last_seen старше now() - seconds.
        Увеличивает attempts.
        Возвращает число сброшенных задач.
        """
        cutoff = datetime.utcnow() - timedelta(seconds=seconds)
        with self.conn.cursor() as cur:
            cur.execute("""
                UPDATE catalog_items
                SET detail_status='pending', attempts = attempts + 1
                WHERE detail_status='in_progress' AND last_seen < %s
                RETURNING sku;
            """, (cutoff,))
            rows = cur.fetchall()
            return len(rows)

    # -----------------------------
    # Archive single item (utility)
    # -----------------------------
    def archive_item(self, sku: str) -> bool:
        """
        Переносит запись в архивную таблицу catalog_items_archive (JSON) и удаляет из основной таблицы.
        Возвращает True если удалено.
        """
        with self.conn.cursor() as cur:
            cur.execute("SELECT to_jsonb(ci) FROM catalog_items ci WHERE sku=%s;", (sku,))
            row = cur.fetchone()
            if not row:
                return False
            cur.execute("INSERT INTO catalog_items_archive (data) VALUES (%s);", (row[0],))
            cur.execute("DELETE FROM catalog_items WHERE sku=%s;", (sku,))
            return True

    # -----------------------------
    # Utility: fetch one item by sku (RealDict)
    # -----------------------------
    def get_item(self, sku: str) -> Optional[Dict[str, Any]]:
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM catalog_items WHERE sku=%s;", (sku,))
            row = cur.fetchone()
            return dict(row) if row else None

    # -----------------------------
    # Ensure columns helper (optionally)
    # -----------------------------
    def ensure_columns(self):
        """
        (Опционально) Проверяет/добавляет колонки в таблице, если запускаешь на старой схеме.
        Можно вызывать при инициализации.
        """
        with self.conn.cursor() as cur:
            # Добавим last_seen_pass и attempts, если нет
            cur.execute("ALTER TABLE catalog_items ADD COLUMN IF NOT EXISTS last_seen_pass INTEGER DEFAULT 0;")
            cur.execute("ALTER TABLE catalog_items ADD COLUMN IF NOT EXISTS attempts INTEGER DEFAULT 0;")
            cur.execute("ALTER TABLE catalog_items ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT now();")
    def ensure_meta_table(self):
        with self.conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS meta (
                    key TEXT PRIMARY KEY,
                    value JSONB,
                    updated_at TIMESTAMP DEFAULT now()
                );
            """)
    def reset_status(self, sku: str, status: str = "pending"):
        """Сбрасывает статус товара (например, при ошибке парсинга)"""
        cur = self.conn.cursor()
        cur.execute("UPDATE details SET status = %s WHERE sku = %s", (status, sku))
        self.conn.commit()
        
        
# session_snapshot.py
import json
import time
from typing import Dict, Tuple, Optional

def save_snapshot(
    headers: Dict[str, str],
    cookies: Dict[str, str],
    path: str = "session_snapshot.json",
    note: Optional[str] = None
) -> None:
    """
    Сохраняет snapshot сессии в JSON файл.
    
    :param headers: словарь заголовков
    :param cookies: словарь cookies
    :param path: путь к файлу
    :param note: произвольная заметка
    """
    payload = {
        "headers": headers,
        "cookies": cookies,
        "meta": {
            "fetched_at": time.time(),
            "note": note or "",
        }
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    print(f"[session_snapshot] Saved snapshot to {path}")


def load_snapshot(path: str = "session_snapshot.json") -> Tuple[Dict[str, str], Dict[str, str], Dict]:
    """
    Загружает snapshot сессии из JSON файла.
    
    :param path: путь к файлу
    :return: headers, cookies, meta
    """
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    headers = data.get("headers", {})
    cookies = data.get("cookies", {})
    meta = data.get("meta", {})
    print(f"[session_snapshot] Loaded snapshot from {path}")
    return headers, cookies, meta


# Пример использования:
# save_snapshot(headers_dict, cookies_dict, note="initial fetch")
# headers, cookies, meta = load_snapshot()
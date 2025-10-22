import random
import re

# Разнообразный набор валидных User-Agent строк (десктоп, мобайл, планшет, разные браузеры)
USER_AGENTS = [
    # Chrome (Windows)
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.6098.94 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/121.0.6169.47 Safari/537.36",
    # Edge (Chromium)
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 Edg/121.0.0.0",
    # Firefox
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0",
    # Safari (macOS)
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/605.1.15 "
    "(KHTML, like Gecko) Version/17.0 Safari/605.1.15",
    # Mobile Safari
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 "
    "(KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
    # Chrome on Android
    "Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/121.0.0.0 Mobile Safari/537.36",
    # Opera
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 OPR/86.0.4363.70",
]

ACCEPT_LANG = [
    "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
    "ru,en-US;q=0.9,en;q=0.8",
    "ru-RU,ru;q=0.9",
]

ACCEPT = [
    "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "*/*",
]

REFERERS = [
    "https://www.google.com/",
    "https://yandex.by/",
    "https://motorland.by/",
    "https://www.bing.com/",
]

ACCEPT_ENCODING = [
    "gzip, deflate, br",
    "gzip, deflate",
]


def _bump_version_component(comp_str: str, jitter: int = 3) -> str:
    """Небольшой случайный сдвиг версий в числовых компонентах."""
    parts = comp_str.split(".")
    new_parts = []
    for p in parts:
        if p.isdigit():
            new_parts.append(str(max(0, int(p) + random.randint(-jitter, jitter))))
        else:
            new_parts.append(p)
    return ".".join(new_parts)


def random_user_agent() -> str:
    """Возвращает слегка рандомизированный User-Agent."""
    ua = random.choice(USER_AGENTS)
    ua = re.sub(r"\d+\.\d+(?:\.\d+)*", lambda m: _bump_version_component(m.group(0), jitter=4), ua)
    return ua


def generate_headers() -> dict:
    """Создаёт валидный и разнообразный набор HTTP-заголовков."""
    return {
        "User-Agent": random_user_agent(),
        "Accept": random.choice(ACCEPT),
        "Accept-Language": random.choice(ACCEPT_LANG),
        "Accept-Encoding": random.choice(ACCEPT_ENCODING),
        "Referer": random.choice(REFERERS),
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "DNT": str(random.choice([0, 1])),
        "Sec-Fetch-Dest": random.choice(["document", "empty"]),
        "Sec-Fetch-Mode": random.choice(["navigate", "cors"]),
        "Sec-Fetch-Site": random.choice(["none", "same-origin", "cross-site"]),
        "Cache-Control": random.choice(["max-age=0", "no-cache"]),
    }


if __name__ == "__main__":
    for _ in range(5):
        print(generate_headers(), end="\n\n")

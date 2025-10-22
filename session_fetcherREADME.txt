session_fetcher.py — быстрый сбор headers и cookies
Назначение

Асинхронная и синхронная утилита для получения HTTP headers и cookies:

Парсит curl-команду из DevTools.

Делает GET-запрос через aiohttp для обычных сайтов.

Использует Playwright для сайтов, где cookies устанавливаются через JS.

Позволяет использовать синхронно через обёртку.

Функции
1. obtain_headers_and_cookies (async)
headers, cookies = await obtain_headers_and_cookies(curl=None, url=None, force_browser=False, timeout=30)


Параметры:

curl — строка curl из DevTools. Если передан, возвращает headers и cookies без сети.

url — URL сайта для GET-запроса (если curl=None).

force_browser — True → всегда использовать Playwright (JS cookies).

timeout — таймаут для aiohttp GET.

Возвращает:
(headers: dict, cookies: dict)

Поведение:

Если curl передан → парсим и возвращаем.

Иначе:

Пробуем aiohttp GET.

Если cookies пустые → fallback Playwright.

2. obtain_headers_and_cookies_sync (sync)
headers, cookies = obtain_headers_and_cookies_sync(curl=None, url=None, force_browser=False, timeout=30)


Синхронная обёртка для obtain_headers_and_cookies.

Примеры использования

Из curl DevTools

headers, cookies = obtain_headers_and_cookies_sync(curl=my_curl_string)


С aiohttp (быстро)

headers, cookies = obtain_headers_and_cookies_sync(url="https://motorland.by/auto-parts/")


С Playwright (JS cookies)

headers, cookies = obtain_headers_and_cookies_sync(url="https://motorland.by/auto-parts/", force_browser=True)

Особенности

Cookies можно сохранять и использовать повторно, пока не протухнут.

Headers автоматически подставляются, но Cookie из curl/response всегда корректно разбираются.

Playwright нужен только для сайтов с JS-set cookies.

Можно использовать как sync и async в зависимости от задачи.
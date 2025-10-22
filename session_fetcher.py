# session_fetcher.py
import re
import asyncio
from typing import Optional, Tuple, Dict

# aiohttp is required for normal async HTTP fetching
import aiohttp

# Playwright is optional: used only if force_browser=True or as fallback.
# We import it lazily inside the function to avoid hard dependency unless requested.


def _parse_curl(curl_cmd: str) -> Tuple[Dict[str, str], Dict[str, str]]:
    """
    Простая разборка curl-команды: извлекает заголовки (-H) и Cookie: ...
    Возвращает (headers_dict, cookies_dict).
    Не пытается обработать все возможные варианты curl, но покрывает типичный DevTools output.
    """
    headers: Dict[str, str] = {}
    cookies: Dict[str, str] = {}

    # find all -H 'Header: value' or -H "Header: value"
    h_matches = re.findall(r"-H\s+('|\")([^'\"]+?):\s*([^'\"]+?)\1", curl_cmd)
    for _, name, value in h_matches:
        name = name.strip()
        value = value.strip()
        if name.lower() == "cookie":
            # split cookie string into pairs
            for part in value.split(";"):
                if "=" in part:
                    k, v = part.split("=", 1)
                    cookies[k.strip()] = v.strip()
        else:
            headers[name] = value

    # Also try to extract URL-specified headers lines without -H (edge cases)
    # (not necessary usually)

    return headers, cookies


async def _fetch_via_aiohttp(url: str, headers: Optional[Dict[str, str]], timeout: int = 30) -> Tuple[Dict[str, str], Dict[str, str]]:
    """
    Делает GET через aiohttp и возвращает (used_headers, cookies_dict_from_response).
    used_headers — то что мы подали (или дефолтный UA).
    """
    # default headers if not provided
    default_headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36",
        "Accept": "*/*",
        "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
    }
    used_headers = dict(default_headers)
    if headers:
        # prefer explicit headers from caller (don't overwrite cookies header here)
        for k, v in headers.items():
            if k.lower() == "cookie":
                # we won't add Cookie header to used_headers (we will read cookies from response)
                continue
            used_headers[k] = v

    cookies_out: Dict[str, str] = {}
    timeout_obj = aiohttp.ClientTimeout(total=timeout)
    async with aiohttp.ClientSession(headers=used_headers, timeout=timeout_obj) as sess:
        async with sess.get(url) as resp:
            # read to ensure cookies set (some sites set cookies on resource load)
            await resp.text()  # we don't return HTML here, only cookies/headers
            # resp.cookies is a dict of Morsel
            for name, morsel in resp.cookies.items():
                cookies_out[name] = morsel.value

            # Also some sites return Set-Cookie headers multiple times; ensure we captured them
            # used_headers we return as the set sent
            return used_headers, cookies_out


async def _fetch_via_playwright(url: str, headers: Optional[Dict[str, str]] = None, wait: int = 2) -> Tuple[Dict[str, str], Dict[str, str]]:
    """
    Fallback using Playwright to capture cookies that are set via JS.
    Returns (headers_used, cookies_dict).
    Requires 'playwright' package and browser installed (playwright install).
    """
    try:
        from playwright.async_api import async_playwright
    except Exception as e:
        raise RuntimeError("Playwright is not available. Install with 'pip install playwright' and run 'playwright install'") from e

    # Minimal headers to pass into page.set_extra_http_headers.
    default_headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36",
    }
    headers_used = dict(default_headers)
    if headers:
        for k, v in headers.items():
            if k.lower() != "cookie":
                headers_used[k] = v

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(user_agent=headers_used.get("User-Agent"))
        # set extra headers (Playwright will send them on navigation)
        await context.set_extra_http_headers({k: v for k, v in headers_used.items() if k.lower() != "user-agent"})
        page = await context.new_page()
        try:
            await page.goto(url, wait_until="networkidle", timeout=30000)
            # small wait to allow client-side scripts set cookies
            if wait:
                await asyncio.sleep(wait)
            cookies_list = await context.cookies()
            cookies_out: Dict[str, str] = {c["name"]: c["value"] for c in cookies_list}
            await browser.close()
            return headers_used, cookies_out
        except Exception:
            await browser.close()
            raise


async def obtain_headers_and_cookies(
    *,
    curl: Optional[str] = None,
    url: Optional[str] = None,
    force_browser: bool = False,
    timeout: int = 30
) -> Tuple[Dict[str, str], Dict[str, str]]:
    """
    Основная функция (async) — возвращает (headers_dict, cookies_dict).

    Параметры:
    - curl: необязательная строка с curl (например, из DevTools). Если передана — парсим её и возвращаем.
    - url: если curl не передан, укажи url, с которого нужно получить cookies/headers (aiohttp + fallback playwright).
    - force_browser: если True — сразу используем Playwright (полезно когда cookies устанавливаются через JS).
    - timeout: таймаут для aiohttp.

    Поведение:
    - Если curl передан: парсим и возвращаем headers+cookies (no network).
    - Иначе (curl не передан):
        - если force_browser: используем playwright (требует установки).
        - иначе: сначала пробуем aiohttp GET; если получили cookies — возвращаем их;
                  если cookies пустые и сайт может ставить их через JS — пытаемся Playwright.
    """
    if curl:
        headers, cookies = _parse_curl(curl)
        return headers, cookies

    if not url:
        raise ValueError("Either curl or url must be provided")

    if force_browser:
        return await _fetch_via_playwright(url, headers=None)

    # try aiohttp first
    try:
        used_headers, cookies_out = await _fetch_via_aiohttp(url, headers=None, timeout=timeout)
    except Exception as e:
        # if aiohttp failed for some reason, try playwright as fallback
        try:
            return await _fetch_via_playwright(url, headers=None)
        except Exception:
            raise RuntimeError(f"Both aiohttp and Playwright fetch failed: {e}") from e

    # if we got cookies via aiohttp, return them
    if cookies_out:
        return used_headers, cookies_out

    # otherwise try playwright fallback (JS-set cookies)
    try:
        return await _fetch_via_playwright(url, headers=used_headers)
    except Exception:
        # no cookies and playwright failed — return whatever we have (headers, empty cookies)
        return used_headers, cookies_out


# Simple synchronous helper to run the async function from sync code
def obtain_headers_and_cookies_sync(*, curl: Optional[str] = None, url: Optional[str] = None, force_browser: bool = False, timeout: int = 30):
    return asyncio.run(obtain_headers_and_cookies(curl=curl, url=url, force_browser=force_browser, timeout=timeout))


# ---------------------------
# Example usage (not executed here):
#
# 1) If you have curl string:
# headers, cookies = obtain_headers_and_cookies_sync(curl=my_curl_string)
#
# 2) If you want to fetch from URL using aiohttp (fast):
# headers, cookies = obtain_headers_and_cookies_sync(url="https://motorland.by/auto-parts/")
#
# 3) Force Playwright (if cookies are set by JS):
# headers, cookies = obtain_headers_and_cookies_sync(url="https://motorland.by/auto-parts/", force_browser=True)
#
# Save headers/cookies to your config and reuse until they expire.
# ---------------------------

# main_test_snapshot.py
import asyncio
from session_fetcher import obtain_headers_and_cookies_sync
from session_snapshot import save_snapshot, load_snapshot
import requests
import aiohttp

TEST_URL = "https://motorland.by/auto-parts/"

# -----------------------
# 1) Получаем headers + cookies
# -----------------------
def get_session():
    headers, cookies = obtain_headers_and_cookies_sync(url=TEST_URL)
    return headers, cookies

# -----------------------
# 2) Синхронная проверка через requests
# -----------------------
def check_with_requests(url, headers, cookies):
    print("=== requests check ===")
    resp = requests.get(url, headers=headers, cookies=cookies, timeout=30)
    print("requests status:", resp.status_code)
    print("len(html):", len(resp.text))
    print("html snippet:", resp.text[:500].replace("\n", " "))
    with open('responseRequests.html', 'w', encoding='utf-8') as f:
        f.write(resp.text)
    return resp

# -----------------------
# 3) Асинхронная проверка через aiohttp
# -----------------------
async def check_with_aiohttp(url, headers, cookies):
    print("\n=== aiohttp check ===")
    timeout = aiohttp.ClientTimeout(total=30)
    async with aiohttp.ClientSession(headers=headers, cookies=cookies, timeout=timeout) as sess:
        async with sess.get(url) as resp:
            html = await resp.text()
            print("aiohttp status:", resp.status)
            print("len(html):", len(html))
            print("html snippet:", html[:500].replace("\n", " "))
            with open('responseAiohttp.html', 'w', encoding='utf-8') as f:
                f.write(html)
            return resp.status, html

# -----------------------
# Main
# -----------------------
def main():
    # Получаем сессию
    headers, cookies = get_session()
    print("Obtained headers keys:", list(headers.keys())[:10])
    print("Obtained cookies keys:", list(cookies.keys())[:20])

    # -----------------------
    # Сохраняем snapshot
    # -----------------------
    save_snapshot(headers, cookies, note="Initial fetch")

    # -----------------------
    # Загружаем snapshot и проверяем
    # -----------------------
    loaded_headers, loaded_cookies, meta = load_snapshot()
    print("Loaded snapshot fetched at:", meta.get("fetched_at"))
    assert headers == loaded_headers, "Headers mismatch!"
    assert cookies == loaded_cookies, "Cookies mismatch!"
    print("Snapshot load check passed ✅")

    # -----------------------
    # Проверка сайта
    # -----------------------
    try:
        check_with_requests(TEST_URL, headers, cookies)
    except Exception as e:
        print("requests check failed:", e)

    try:
        asyncio.run(check_with_aiohttp(TEST_URL, headers, cookies))
    except Exception as e:
        print("aiohttp check failed:", e)

if __name__ == "__main__":
    main()
import asyncio
import aiohttp
import os
from header_generator import random_user_agent
from html_fetcher import HTMLFetcher


async def main():
    base_url = "https://motorland.by/minsk-auto-parts/?pg={page}"

    # 📁 Папка для сохранения HTML
    out_dir = os.path.join(os.path.dirname(__file__), "responses2")
    os.makedirs(out_dir, exist_ok=True)

    # Создаём стартовую сессию
    headers = {"User-Agent": random_user_agent()}
    async with aiohttp.ClientSession(headers=headers) as session:
        fetcher = HTMLFetcher(session)

        # Пробегаемся по страницам 1–100
        for i in range(5000, 7000):
            ua = random_user_agent()
            session.headers.update({"User-Agent": ua})
            url = base_url.format(page=i)

            try:
                html = await fetcher.fetch(url)
                if html:
                    filename = os.path.join(out_dir, f"page_{i:03d}.html")
                    with open(filename, "w", encoding="utf-8") as f:
                        f.write(html)

                    print(f"[{i}] ✅ OK — saved {os.path.basename(filename)}")
                    print(f"     URL: {url}")
                    print(f"     UA:  {ua}")
                else:
                    print(f"[{i}] ❌ FAIL (empty response) — {url}")
            except Exception as e:
                print(f"[{i}] ⚠️ Error fetching {url}: {e}")

            await asyncio.sleep(0.3)  # задержка между запросами

    print("\n✅ Тест завершён. Все результаты сохранены в 'responses/'")


if __name__ == "__main__":
    asyncio.run(main())

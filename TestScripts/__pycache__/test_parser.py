import asyncio
from html_fetcher import HTMLFetcher
from session_snapshot import load_snapshot
from html_parser import parse_catalog_page  # наша новая функция

async def main():
    # Загружаем cookies и headers
    headers, cookies, _ = load_snapshot("session_snapshot.json")

    import aiohttp
    async with aiohttp.ClientSession(headers=headers, cookies=cookies) as session:
        fetcher = HTMLFetcher(session)

        # Получаем HTML страницы каталога
        html = await fetcher.fetch_catalog_page(1)

        # Передаем HTML в нашу функцию парсинга
        items, all_keys = parse_catalog_page(html)

        print("=== Найденные товары ===")
        for item in items:
            print(item)
        
        print("\n=== Все ключи характеристик ===")
        print(all_keys)

if __name__ == "__main__":
    asyncio.run(main())
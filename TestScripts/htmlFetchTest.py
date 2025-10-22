import asyncio
import aiohttp
from session_snapshot import load_snapshot
from html_fetcher import HTMLFetcher

async def main():
    # Загружаем snapshot корректно
    headers, cookies, meta = load_snapshot("session_snapshot.json")

    # Создаем сессию с заголовками и cookies
    async with aiohttp.ClientSession(headers=headers, cookies=cookies) as session:
        fetcher = HTMLFetcher(session)

        # Пример получения страницы каталога
        html_catalog = await fetcher.fetch_catalog_page(1)
        if html_catalog:
            with open('html_catalog.html', 'w', encoding='utf-8') as file:
                file.write(html_catalog)
            print("✅ Каталог сохранен в html_catalog.html")

        # Пример ссылки на деталь
        detail_url = "https://motorland.by/engines/opel/astra/j-2010-2017/1-6-litra/dizel/cdti/b16dtl/sku-20637378/"

        html_detail = await fetcher.fetch_detail_page(detail_url)
        if html_detail:
            with open('html_detail.html', 'w', encoding='utf-8') as file:
                file.write(html_detail)
            print("✅ Деталь сохранена в html_detail.html")

if __name__ == "__main__":
    asyncio.run(main())

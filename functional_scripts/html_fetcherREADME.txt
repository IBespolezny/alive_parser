import asyncio
import aiohttp
from html_fetcher import HTMLFetcher

async def main():
    async with aiohttp.ClientSession() as session:
        fetcher = HTMLFetcher(session)

        # Загрузка каталога (страница 1)
        html_catalog = await fetcher.fetch_catalog_page(1)
        if html_catalog:
            print("Каталог успешно загружен!")

        # Загрузка конкретной детали по ссылке
        url = "https://motorland.by/engines/opel/astra/j-2010-2017/1-6-litra/dizel/cdti/b16dtl/sku-20637378/"
        html_detail = await fetcher.fetch_detail_page(url)
        if html_detail:
            print("Страница детали успешно загружена!")

asyncio.run(main())
🔍 Методы
Метод	Описание	Аргументы
fetch(url, retries=3, delay=1.0)	Загружает HTML-страницу по URL с повторными попытками при ошибках.	url — адрес страницы, retries — кол-во попыток, delay — пауза между ними
fetch_catalog_page(page_num=1)	Загружает страницу каталога (?pg=N). Если page_num=1, берёт первую страницу без параметра.	page_num — номер страницы
fetch_detail_page(url)	Загружает страницу конкретной детали по полной ссылке.	url — ссылка на деталь

🧠 Примечания
Логирование выполняется через модуль logging.

Поддерживает автоматическую обработку ошибок aiohttp.ClientError.

Возвращает str с HTML-текстом при успехе или None при неудаче.

Рекомендуется использовать совместно с асинхронными парсерами (например, BeautifulSoup или lxml в асинхронном режиме).
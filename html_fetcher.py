# html_fetcher.py
import asyncio
import aiohttp
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class HTMLFetcher:
    def __init__(self, session: aiohttp.ClientSession):
        self.session = session

    async def fetch(self, url: str, retries: int = 3, delay: float = 1.0) -> Optional[str]:
        """Асинхронно получает HTML страницу с повторными попытками."""
        for attempt in range(retries):
            try:
                async with self.session.get(url) as resp:
                    if resp.status == 200:
                        text = await resp.text()
                        logger.debug(f"Fetched {url} ({len(text)} bytes)")
                        return text
                    else:
                        logger.warning(f"Non-200 ({resp.status}) for {url}")
            except aiohttp.ClientError as e:
                logger.warning(f"Network error for {url}: {e}")
            await asyncio.sleep(delay)
        logger.error(f"Failed to fetch after {retries} attempts: {url}")
        return None

    async def fetch_catalog_page(self, page_num: int = 1) -> Optional[str]:
        url = f"https://motorland.by/auto-parts/?pg={page_num}" if page_num > 1 else "https://motorland.by/auto-parts/"
        return await self.fetch(url)

    async def fetch_detail_page(self, url: str) -> Optional[str]:
        """Получает страницу конкретной детали по полной ссылке."""
        return await self.fetch(url)

import asyncio
import aiohttp
import time
import logging
from parser import HTMLParser

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("crawler")

class AsyncCrawler:
    def __init__(self, max_concurrent: int = 10):
        self.max_concurrent = max_concurrent
        self._semaphore = asyncio.Semaphore(max_concurrent)
        self._session = None
        self.parser = HTMLParser() 

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=30, connect=10)
            connector = aiohttp.TCPConnector(limit=self.max_concurrent)
            self._session = aiohttp.ClientSession(timeout=timeout, connector=connector)
        return self._session

    async def fetch_url(self, url: str) -> str:
        session = await self._get_session()
        async with self._semaphore:
            logger.info(f"Start: {url}")
            try:
                async with session.get(url) as response:
                    response.raise_for_status()
                    text = await response.text()
                    logger.info(f"Done: {url} ({response.status}, {len(text)} bytes)")
                    return text
            except aiohttp.ClientResponseError as e:
                logger.warning(f"HTTP {e.status} for {url}")
                return ""
            except asyncio.TimeoutError:
                logger.warning(f"Timeout for {url}")
                return ""
            except aiohttp.ClientError as e:
                logger.warning(f"Network error for {url}: {e}")
                return ""

    async def fetch_urls(self, urls: list[str]) -> dict[str, str]:
        tasks = [self.fetch_url(url) for url in urls]
        results = await asyncio.gather(*tasks)
        return dict(zip(urls, results))

    async def fetch_urls_sequential(self, urls: list[str]) -> dict[str, str]:
        results = {}
        for url in urls:
            results[url] = await self.fetch_url(url)
        return results

    async def close(self) -> None:
        if self._session and not self._session.closed:
            await self._session.close()

    async def fetch_and_parse(self, url: str) -> dict:
        html = await self.fetch_url(url)
        if not html:
            return {"url": url, "error": "не удалось загрузить"}
        return self.parser.parse_html(html, url)
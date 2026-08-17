import asyncio
import aiohttp
import logging
from parser import HTMLParser
from crawler_queue import CrawlerQueue
from filters import URLFilter, normalize_url
from semaphore_manager import SemaphoreManager

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("crawler")

class AsyncCrawler:
    def __init__(self, max_concurrent: int = 10, max_depth: int = 2):
        self.max_concurrent = max_concurrent
        self.max_depth = max_depth
        self._semaphore_manager = SemaphoreManager(
            global_limit=max_concurrent,
            per_domain_limit=3,
        )
        self._session = None
        self.parser = HTMLParser() 

        self.visited_urls = set()       # что уже видели (без дубликатов)
        self.failed_urls = {}           # {url: ошибка}
        self.processed_urls = {} 

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=30, connect=10)
            connector = aiohttp.TCPConnector(limit=self.max_concurrent)
            self._session = aiohttp.ClientSession(timeout=timeout, connector=connector)
        return self._session

    async def fetch_url(self, url: str) -> str:
        session = await self._get_session()
        async with self._semaphore_manager.acquire(url):
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
        return await self.parser.parse_html(html, url)

    async def crawl(self, start_urls: list[str], max_pages: int = 100,
                    same_domain_only: bool = False) -> dict:
        from urllib.parse import urlparse

        queue = CrawlerQueue()
        base_domain = urlparse(start_urls[0]).netloc
        url_filter = URLFilter(same_domain_only=same_domain_only,
                               base_domain=base_domain)

        for url in start_urls:
            queue.add_url(url, depth=0)

        import time
        start_time = time.perf_counter()
        page_count = 0

        while True:
            if len(self.processed_urls) >= max_pages:
                break

            item = await queue.get_next()
            if item is None:
                break

            url = item["url"]
            depth = item["depth"]
            url = normalize_url(url) 

            if url in self.visited_urls:
                continue
            self.visited_urls.add(url)

            result = await self.fetch_and_parse(url)

            if result.get("error"):
                self.failed_urls[url] = result["error"]
                queue.mark_failed(url, result["error"])
                continue

            self.processed_urls[url] = result
            queue.mark_processed(url)

            page_count += 1
            elapsed = time.perf_counter() - start_time
            speed = page_count / elapsed if elapsed > 0 else 0
            stats = queue.get_stats()
            logger.info(
                f"Прогресс: обработано={page_count} | "
                f"в очереди={stats['in_queue']} | "
                f"ошибок={len(self.failed_urls)} | "
                f"скорость={speed:.1f} стр/сек"
            )

            if depth < self.max_depth:
                for link in result.get("links", []):
                    link = normalize_url(link)  
                    if link not in self.visited_urls and url_filter.is_allowed(link):
                        queue.add_url(link, depth=depth + 1)

        return self.processed_urls
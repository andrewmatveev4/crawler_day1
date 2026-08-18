import asyncio
import aiohttp
import logging
from parser import HTMLParser
from crawler_queue import CrawlerQueue
from filters import URLFilter, normalize_url
from semaphore_manager import SemaphoreManager
from rate_limiter import RateLimiter
from urllib.parse import urlparse
from robots import RobotsParser
import time
from errors import classify_http_status, TransientError, PermanentError, NetworkError
from retry_strategy import RetryStrategy

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("crawler")

class AsyncCrawler:
    def __init__(self, max_concurrent: int = 10, max_depth: int = 2,
                 requests_per_second: float = 1.0, min_delay: float = 0.0,
                 jitter: float = 0.0, respect_robots: bool = True,
                 user_agent: str = "MyBot/1.0", max_retries_on_error: int = 3, backoff_factor: float = 2.0):
        self.max_concurrent = max_concurrent
        self.max_depth = max_depth
        self.user_agent = user_agent
        self.respect_robots = respect_robots
        self._semaphore_manager = SemaphoreManager(
            global_limit=max_concurrent,
            per_domain_limit=3,
        )
        self._rate_limiter = RateLimiter(
            requests_per_second=requests_per_second,
            per_domain=True,
            min_delay=min_delay,
            jitter=jitter,
        )
        self.retry_strategy = RetryStrategy(
            max_retries=max_retries_on_error,
            backoff_factor=backoff_factor,
        )
        self._robots = RobotsParser()
        self._session = None
        self.parser = HTMLParser()

        self.visited_urls = set()
        self.failed_urls = {}
        self.processed_urls = {}
        self.blocked_by_robots = []
        self.request_times = []

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=30, connect=10)
            connector = aiohttp.TCPConnector(limit=self.max_concurrent)
            self._session = aiohttp.ClientSession(timeout=timeout, connector=connector)
        return self._session

    async def fetch_url(self, url: str) -> str:
        session = await self._get_session()
        domain = urlparse(url).netloc

        async with self._semaphore_manager.acquire(url):
            await self._rate_limiter.acquire(domain)
            self.request_times.append(time.monotonic())
            logger.info(f"Start: {url}")
            try:
                async with session.get(url) as response:
                    response.raise_for_status()
                    text = await response.text()
                    logger.info(f"Done: {url} ({response.status}, {len(text)} bytes)")
                    return text
            except aiohttp.ClientResponseError as e:
                error_class = classify_http_status(e.status)
                logger.warning(f"HTTP {e.status} for {url} → {error_class.__name__}")
                raise error_class(f"HTTP {e.status}: {url}")
            except asyncio.TimeoutError:
                logger.warning(f"Timeout for {url} → TransientError")
                raise TransientError(f"Timeout: {url}")
            except aiohttp.ClientError as e:
                logger.warning(f"Network error for {url} → NetworkError")
                raise NetworkError(f"Network: {url}: {e}")

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
        try:
            html = await self.retry_strategy.execute_with_retry(self.fetch_url, url)
        except Exception as e:
            logger.warning(f"Не удалось загрузить {url}: {type(e).__name__}")
            return {"url": url, "error": f"{type(e).__name__}: {e}"}

        if not html:
            return {"url": url, "error": "пустой ответ"}
        return await self.parser.parse_html(html, url)

    async def _is_allowed_by_robots(self, url: str) -> bool:
        if not self.respect_robots:
            return True
        return await self._robots.can_fetch(url, user_agent=self.user_agent)

    async def _apply_crawl_delay(self, url: str):
        if not self.respect_robots:
            return
        delay = await self._robots.get_crawl_delay(url, user_agent=self.user_agent)
        if delay > 0:
            self._rate_limiter.bump_min_delay(delay)
            logger.info(f"Crawl-delay={delay}s применён из robots.txt для {url}")
    
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

            if not await self._is_allowed_by_robots(url):
                self.blocked_by_robots.append(url)
                logger.warning(f"robots.txt запретил: {url}")
                continue
            await self._apply_crawl_delay(url)
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

    def get_avg_delay(self) -> float:
        if len(self.request_times) < 2:
            return 0.0
        times = sorted(self.request_times)
        gaps = [times[i] - times[i - 1] for i in range(1, len(times))]
        return sum(gaps) / len(gaps)

    
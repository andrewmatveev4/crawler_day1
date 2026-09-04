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
from errors import ParseError
from datetime import datetime
from advanced_crawler import AdvancedCrawler


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
                 user_agent: str = "MyBot/1.0", max_retries_on_error: int = 3, backoff_factor: float = 2.0, storage=None):
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
        self.error_records = []
        self.processed_urls = {}
        self.blocked_by_robots = []
        self.request_times = []
        self.storage = storage
        self._response_meta = {}
        self.start_time = None
        self.end_time = None
        self._meta_lock = asyncio.Lock()

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=30, connect=10)
            connector = aiohttp.TCPConnector(limit=self.max_concurrent)
            self._session = aiohttp.ClientSession(timeout=timeout, connector=connector)
        return self._session

    def _timeout_for_attempt(self, attempt: int, base_timeout: int = 30) -> aiohttp.ClientTimeout:
        total = base_timeout + attempt * 5
        return aiohttp.ClientTimeout(total=total, connect=10, sock_read=total)

    async def fetch_url(self, url: str, attempt: int = 0) -> str:
        if not await self._is_allowed_by_robots(url):
            self.blocked_by_robots.append(url)
            logger.warning(f"robots.txt запретил: {url}")
            return ""
        await self._apply_crawl_delay(url)

        domain = urlparse(url).netloc
        session = await self._get_session()
        timeout = self._timeout_for_attempt(attempt)

        async with self._semaphore_manager.acquire(url):
            await self._rate_limiter.acquire(domain)
            self.request_times.append(time.monotonic())
            logger.info(f"Start: {url}")
            try:
                headers = {"User-Agent": self.user_agent}
                async with session.get(url, headers=headers, timeout=timeout) as response:
                    status = response.status
                    content_type = response.headers.get("Content-Type", "")
                    async with self._meta_lock:
                        self._response_meta[url] = (status, content_type)
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
        tasks = [
            self.retry_strategy.execute_with_retry(self.fetch_url, url, pass_attempt=True)
            for url in urls
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        output = {}
        for url, result in zip(urls, results):
            if isinstance(result, Exception):
                logger.warning(f"Ошибка для {url}: {type(result).__name__}")
                output[url] = ""
            else:
                output[url] = result
        return output

    async def fetch_urls_sequential(self, urls: list[str]) -> dict[str, str]:
        results = {}
        for url in urls:
            results[url] = await self.fetch_url(url)
        return results
    
    async def close(self) -> None:
        if self._session and not self._session.closed:
            await self._session.close()
        if self.storage is not None:
            await self.storage.close()

    async def fetch_and_parse(self, url: str) -> dict:
        try:
            html = await self.retry_strategy.execute_with_retry(self.fetch_url, url, pass_attempt=True)
        except Exception as e:
            logger.warning(f"Не удалось загрузить {url}: {type(e).__name__}")
            self.error_records.append({
                "url": url,
                "error_type": type(e).__name__,
                "message": str(e),
            })
            return {"url": url, "error": f"{type(e).__name__}: {e}"}

        if not html:
            return {"url": url, "error": "пустой ответ"}

        try:
            return await self.parser.parse_html(html, url)
        except ParseError as e:
            logger.warning(f"Не удалось распарсить {url}: {type(e).__name__}")
            self.error_records.append({
                "url": url,
                "error_type": type(e).__name__,
                "message": str(e),
            })
            return {"url": url, "error": f"{type(e).__name__}: {e}"}

    async def _is_allowed_by_robots(self, url: str) -> bool:
        if not self.respect_robots:
            return True
        session = await self._get_session()
        return await self._robots.can_fetch(url, user_agent=self.user_agent, session=session)

    async def _apply_crawl_delay(self, url: str):
        if not self.respect_robots:
            return
        session = await self._get_session()
        delay = await self._robots.get_crawl_delay(url, user_agent=self.user_agent, session=session)
        if delay > 0:
            domain = urlparse(url).netloc
            self._rate_limiter.set_domain_delay(domain, delay)
            logger.info(f"Crawl-delay={delay}s применён из robots.txt для {url}")
    
    async def crawl(self, start_urls: list[str], max_pages: int = 100,
                    same_domain_only: bool = False,
                    exclude_patterns: list = None,
                    include_patterns: list = None) -> dict:
        self.queue = CrawlerQueue()
        base_domains = [urlparse(u).netloc for u in start_urls]
        url_filter = URLFilter(
            same_domain_only=same_domain_only,
            base_domains=base_domains,
            exclude_patterns=exclude_patterns,
            include_patterns=include_patterns,
        )

        for url in start_urls:
            if url_filter.is_allowed(url):
                await self.queue.add_url(url, depth=0)
            else:
                logger.info(f"Стартовый URL отфильтрован: {url}")

        self.start_time = time.perf_counter()

        while len(self.visited_urls) < max_pages:
            remaining = max_pages - len(self.visited_urls)
            batch_limit = min(self.max_concurrent, remaining)

            batch = []
            while len(batch) < batch_limit:
                item = await self.queue.get_next_item()
                if item is None:
                    break
                batch.append(item)

            if not batch:
                break

            tasks = [
                self._process_one(item["url"], item["depth"], url_filter)
                for item in batch
            ]
            results = await asyncio.gather(*tasks)

            for new_links in results:
                for link, depth in new_links:
                    await self.queue.add_url(link, depth=depth)

            elapsed = time.perf_counter() - self.start_time
            speed = len(self.processed_urls) / elapsed if elapsed > 0 else 0
            done = len(self.visited_urls)
            percent = (done / max_pages * 100) if max_pages > 0 else 0
            remaining_pages = max(0, max_pages - done)
            eta = remaining_pages / speed if speed > 0 else 0
            logger.info(
                f"Прогресс: {done}/{max_pages} ({percent:.0f}%) | "
                f"ошибок={len(self.failed_urls)} | "
                f"скорость={speed:.1f} стр/сек | "
                f"ETA={eta:.0f}s"
            )

        self.end_time = time.perf_counter()
        return self.processed_urls
    
    async def _process_one(self, url: str, depth: int, url_filter) -> list:
        normalized = normalize_url(url)
        if normalized in self.visited_urls:
            return []
        self.visited_urls.add(normalized)

        result = await self.fetch_and_parse(url)   # загрузка/резолв — по оригиналу

        if url in self.blocked_by_robots:
            return []

        if result.get("error"):
            self.failed_urls[normalized] = result["error"]
            await self.queue.mark_failed(normalized, result["error"])
            return []

        self.processed_urls[normalized] = result
        await self.queue.mark_processed(normalized)

        if self.storage is not None:
            status, content_type = self._response_meta.get(url, (None, ""))
            record = {
                "url": normalized,
                "title": result.get("title", ""),
                "text": result.get("text", ""),
                "links": result.get("links", []),
                "metadata": result.get("metadata", {}),
                "crawled_at": datetime.now().isoformat(),
                "status_code": status,
                "content_type": content_type,
            }
            try:
                await self._save_with_retry(record)
            except Exception as e:
                logger.warning(f"Не удалось сохранить {normalized} после повторов: {type(e).__name__}: {e}")

        new_links = []
        if depth < self.max_depth:
            for link in result.get("links", []):
                link = normalize_url(link)
                if link not in self.visited_urls and url_filter.is_allowed(link):
                    new_links.append((link, depth + 1))
        return new_links
    
    def get_avg_delay(self) -> float:
        if len(self.request_times) < 2:
            return 0.0
        times = sorted(self.request_times)
        gaps = [times[i] - times[i - 1] for i in range(1, len(times))]
        return sum(gaps) / len(gaps)

    def get_error_stats(self) -> dict:
        return {
            "failed_urls_count": len(self.failed_urls),
            "retry_stats": self.retry_strategy.stats,
            "errors_by_type": self.retry_strategy.errors_by_type,
            "error_records": self.error_records,
            "blocked_by_robots": len(self.blocked_by_robots),
            "avg_retry_time": self.retry_strategy.avg_retry_time(),
        }

    async def _save_with_retry(self, record: dict) -> None:
        async def _attempt(rec):
            try:
                await self.storage.save(rec)
            except Exception as e:
                raise TransientError(f"Ошибка сохранения: {e}")

        await self.retry_strategy.execute_with_retry(_attempt, record)
    
if __name__ == "__main__":
    from cli import parse_args, build_settings, run_crawler
    import asyncio

    args = parse_args()
    settings = build_settings(args)
    asyncio.run(run_crawler(settings))

    
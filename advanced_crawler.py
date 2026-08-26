from crawler import AsyncCrawler
from stats import CrawlerStats
from storage import JSONStorage, CSVStorage, SQLiteStorage
from logging_setup import setup_logging
from sitemap import SitemapParser
import logging
logger = logging.getLogger("crawler")


class AdvancedCrawler:
    def __init__(self, settings: dict):
        self.settings = settings
        self.crawler = None
        self.stats = None

    @classmethod
    def from_config(cls, config_path: str):
        import json
        with open(config_path, encoding="utf-8") as f:
            settings = json.load(f)
        return cls(settings)

    def _make_storage(self):
        output = self.settings.get("output", "results.json")
        fmt = self.settings.get("format", "json")

        if fmt == "json":
            return JSONStorage(output)
        elif fmt == "csv":
            return CSVStorage(output)
        elif fmt == "sqlite":
            return SQLiteStorage(output)
        else:
            return JSONStorage(output)

    async def crawl(self, start_urls: list = None):
        storage = self._make_storage()
        self.crawler = AsyncCrawler(
            max_concurrent=self.settings.get("max_concurrent", 10),
            max_depth=self.settings.get("max_depth", 2),
            requests_per_second=self.settings.get("rate_limit", 1.0),
            min_delay=self.settings.get("min_delay", 0.0),
            jitter=self.settings.get("jitter", 0.0),
            respect_robots=self.settings.get("respect_robots", False),
            user_agent=self.settings.get("user_agent", "MyBot/1.0"),
            storage=storage,
        )

        if start_urls is not None:
            urls = start_urls
        else:
            urls = await self._get_start_urls()

        await self.crawler.crawl(
            start_urls=urls,
            max_pages=self.settings.get("max_pages", 100),
            same_domain_only=self.settings.get("same_domain_only", False),
            exclude_patterns=self.settings.get("exclude_patterns"),
            include_patterns=self.settings.get("include_patterns"),
        )

        self.stats = CrawlerStats(self.crawler)
        return self.stats

    def get_stats(self):
        return self.stats

    def export_to_json(self, filename: str) -> None:
        self.stats.export_to_json(filename)

    def export_to_html_report(self, filename: str) -> None:
        self.stats.export_to_html_report(filename)

    async def close(self) -> None:
        if self.crawler is not None:
            await self.crawler.close()

    async def _get_start_urls(self) -> list:
        sitemap_url = self.settings.get("sitemap")
        if sitemap_url:
            parser = SitemapParser(user_agent=self.settings.get("user_agent", "MyBot/1.0"))
            urls = await parser.fetch_sitemap(sitemap_url)
            logger.info(f"Из sitemap получено {len(urls)} url")
            return urls
        return self.settings.get("urls", [])
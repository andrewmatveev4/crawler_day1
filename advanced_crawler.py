from crawler import AsyncCrawler
from stats import CrawlerStats
from storage import JSONStorage, CSVStorage, SQLiteStorage
from logging_setup import setup_logging


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

    async def run(self):
        setup_logging(self.settings.get("log_file", "crawler.log"))
        storage = self._make_storage()

        self.crawler = AsyncCrawler(
            max_concurrent=self.settings.get("max_concurrent", 10),
            max_depth=self.settings.get("max_depth", 2),
            requests_per_second=self.settings.get("rate_limit", 1.0),
            respect_robots=self.settings.get("respect_robots", False),
            storage=storage,
        )

        await self.crawler.crawl(
            start_urls=self.settings["urls"],
            max_pages=self.settings.get("max_pages", 100),
        )

        self.stats = CrawlerStats(self.crawler)
        await self.crawler.close()
        return self.stats
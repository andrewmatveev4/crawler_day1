import asyncio
from crawler import AsyncCrawler
from storage import DataStorage


class FlakyStorage(DataStorage):
    """Падает первые 2 раза на каждом save, потом успевает."""
    def __init__(self):
        self.saved = []
        self.attempts = 0

    async def save(self, data):
        self.attempts += 1
        if self.attempts % 3 != 0:   # падает 2 раза из 3
            raise IOError(f"притворяюсь, что диск занят (попытка {self.attempts})")
        self.saved.append(data)

    async def close(self):
        pass


async def main():
    storage = FlakyStorage()
    crawler = AsyncCrawler(
        max_concurrent=1, max_depth=0, respect_robots=False,
        max_retries_on_error=3, storage=storage,
    )
    await crawler.crawl(
        start_urls=["https://books.toscrape.com/"],
        max_pages=1,
    )
    await crawler.close()

    print("\n" + "=" * 40)
    print(f"Всего попыток save: {storage.attempts}")
    print(f"Реально сохранено:  {len(storage.saved)} (ждём 1 — ретраи спасли запись)")


if __name__ == "__main__":
    asyncio.run(main())
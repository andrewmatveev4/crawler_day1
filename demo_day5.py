import asyncio
import logging
from crawler import AsyncCrawler

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s", datefmt="%H:%M:%S")


async def main():
    crawler = AsyncCrawler(
        max_concurrent=3,
        max_depth=1,
        requests_per_second=2.0,
        respect_robots=True,
        user_agent="MyBot/1.0",
        max_retries_on_error=3,
        backoff_factor=2.0,
    )

    start_urls = [
        "https://www.google.com/",
        "https://www.google.com/nonexistent-page-xyz-404",  # 404 → PermanentError, НЕ повторяем
    ]

    results = await crawler.crawl(start_urls=start_urls, max_pages=5)
    await crawler.close()

    print("\n" + "=" * 50)
    print("СТАТИСТИКА ДНЯ 5")
    print("=" * 50)
    print(f"Обработано:  {len(results)}")
    print(f"Ошибок:      {len(crawler.failed_urls)}")
    for url, err in crawler.failed_urls.items():
        print(f"   ❌ {url}")
        print(f"      {err}")


asyncio.run(main())
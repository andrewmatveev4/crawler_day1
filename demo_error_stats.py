import asyncio
import json
from crawler import AsyncCrawler


async def main():
    crawler = AsyncCrawler(
        max_concurrent=3,
        max_depth=0,
        respect_robots=False,
        max_retries_on_error=3,
    )

    start_urls = [
        "https://books.toscrape.com/",                       # живой
        "https://books.toscrape.com/nonexistent-404-page",   # 404 → Permanent
        "https://httpstat.us/503",                           # 503 → Transient, будет ретраиться
    ]

    await crawler.crawl(start_urls=start_urls, max_pages=10)
    await crawler.close()

    print("\n" + "=" * 45)
    print("СТАТИСТИКА ОШИБОК")
    print("=" * 45)
    print(json.dumps(crawler.get_error_stats(), indent=2, ensure_ascii=False))


asyncio.run(main())
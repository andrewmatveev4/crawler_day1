import asyncio
import json
from crawler import AsyncCrawler


async def main():
    crawler = AsyncCrawler(
        max_concurrent=3,
        max_depth=0,
        respect_robots=False,
        max_retries_on_error=2,
    )

    start_urls = [
        "https://books.toscrape.com/",                       # живой
        "https://books.toscrape.com/nonexistent-404-page",   # 404 → PermanentError
        "https://books.toscrape.com/another-missing-xyz",    # ещё 404
    ]

    await crawler.crawl(start_urls=start_urls, max_pages=10)
    await crawler.close()

    print("\n" + "=" * 45)
    print("СТАТИСТИКА ОШИБОК")
    print("=" * 45)
    stats = crawler.get_error_stats()
    print(json.dumps(stats, indent=2, ensure_ascii=False))


asyncio.run(main())
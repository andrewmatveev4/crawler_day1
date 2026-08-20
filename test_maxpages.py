import asyncio
from crawler import AsyncCrawler


async def main():
    crawler = AsyncCrawler(max_concurrent=10, max_depth=0, respect_robots=False, requests_per_second=20.0)

    # 10 стартовых URL, но max_pages=5 — должно обработаться РОВНО 5
    start_urls = [f"https://books.toscrape.com/catalogue/page-{i}.html" for i in range(1, 11)]

    results = await crawler.crawl(start_urls=start_urls, max_pages=5)
    await crawler.close()

    print(f"\nСтартовых URL: {len(start_urls)}")
    print(f"max_pages: 5")
    print(f"Обработано: {len(results)}  {'✅ лимит соблюдён' if len(results) <= 5 else '❌ перебор!'}")


asyncio.run(main())
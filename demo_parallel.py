import asyncio
from crawler import AsyncCrawler


async def main():
    crawler = AsyncCrawler(max_concurrent=3, max_depth=1, respect_robots=False, requests_per_second=10.0)
    results = await crawler.crawl(
        start_urls=["https://books.toscrape.com/"],
        max_pages=8,
        same_domain_only=True,
    )
    await crawler.close()
    print(f"\nОбработано: {len(results)} страниц")


asyncio.run(main())
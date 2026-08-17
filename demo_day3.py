import asyncio
from crawler import AsyncCrawler


async def main():
    crawler = AsyncCrawler(max_concurrent=5, max_depth=2)

    results = await crawler.crawl(
        start_urls=["https://www.python.org"],
        max_pages=15,
        same_domain_only=True,
    )

    await crawler.close()

    print("\n" + "=" * 50)
    print(f"Обработано страниц: {len(results)}")
    print(f"Ошибок: {len(crawler.failed_urls)}")
    print(f"Всего посещено (visited): {len(crawler.visited_urls)}")
    print("\nОбработанные URL:")
    for url in results:
        print(f"  {url}")


asyncio.run(main())
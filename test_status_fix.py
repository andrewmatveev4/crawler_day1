import asyncio
from crawler import AsyncCrawler
from stats import CrawlerStats


async def main():
    crawler = AsyncCrawler(max_concurrent=3, max_depth=0, respect_robots=False)

    start_urls = [
        "https://books.toscrape.com/",                          # 200
        "https://books.toscrape.com/nonexistent-404-page-xyz",  # 404
        "https://httpstat.us/500",                              # 500
    ]
    await crawler.crawl(start_urls=start_urls, max_pages=5)
    await crawler.close()

    stats = CrawlerStats(crawler)
    print("\n" + "=" * 40)
    print(f"Статус-коды: {stats.status_distribution()}")
    print(f"Успешно: {stats.successful()} | Ошибок: {stats.failed()}")


if __name__ == "__main__":
    asyncio.run(main())
import asyncio
from crawler import AsyncCrawler


async def main():
    crawler = AsyncCrawler(max_concurrent=5, max_depth=1, respect_robots=False)

    # ДВА стартовых домена
    start_urls = [
        "https://books.toscrape.com/",
        "https://quotes.toscrape.com/",
    ]
    await crawler.crawl(
        start_urls=start_urls,
        max_pages=10,
        same_domain_only=True,   # только свои домены
    )
    await crawler.close()

    # смотрим, с каких доменов реально собрали страницы
    from urllib.parse import urlparse
    domains = {}
    for url in crawler.processed_urls:
        d = urlparse(url).netloc
        domains[d] = domains.get(d, 0) + 1

    print("\n" + "=" * 40)
    print(f"Обработано: {len(crawler.processed_urls)}")
    print(f"По доменам: {domains}")


if __name__ == "__main__":
    asyncio.run(main())
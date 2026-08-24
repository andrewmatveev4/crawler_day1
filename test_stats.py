import asyncio
from crawler import AsyncCrawler
from stats import CrawlerStats


async def main():
    crawler = AsyncCrawler(
        max_concurrent=5,
        max_depth=1,
        respect_robots=False,
        requests_per_second=10.0,
    )
    await crawler.crawl(
        start_urls=["https://books.toscrape.com/"],
        max_pages=8,
        same_domain_only=True,
    )
    await crawler.close()

    stats = CrawlerStats(crawler)

    print("\n" + "=" * 40)
    print("СТАТИСТИКА")
    print("=" * 40)
    print(f"Всего страниц:      {stats.total_pages()}")
    print(f"Успешно:            {stats.successful()}")
    print(f"Ошибок:             {stats.failed()}")
    print(f"Время работы:       {stats.elapsed_time():.2f}s")
    print(f"Средняя скорость:   {stats.avg_speed():.2f} стр/сек")
    print(f"Статус-коды:        {stats.status_distribution()}")
    print(f"Топ доменов:        {stats.top_domains()}")


if __name__ == "__main__":
    asyncio.run(main())
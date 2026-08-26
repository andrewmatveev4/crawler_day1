import asyncio
from advanced_crawler import AdvancedCrawler


async def main():
    crawler = AdvancedCrawler.from_config("config_sitemap.json")
    await crawler.crawl()
    stats = crawler.get_stats()

    print("\n" + "=" * 40)
    print(f"Обработано из sitemap: {stats.total_pages()}")
    print(f"Успешно: {stats.successful()} | Ошибок: {stats.failed()}")
    print(f"Топ доменов: {stats.top_domains()}")

    await crawler.close()


if __name__ == "__main__":
    asyncio.run(main())
import asyncio
from advanced_crawler import AdvancedCrawler


async def main():
    crawler = AdvancedCrawler.from_config("config.json")
    await crawler.crawl()
    stats = crawler.get_stats()

    # способ 1 — как словарь (из ТЗ-примера)
    print(f"stats['total_pages'] = {stats['total_pages']}")
    # способ 2 — как объект (наши демки)
    print(f"stats.total_pages() = {stats.total_pages()}")

    await crawler.close()


if __name__ == "__main__":
    asyncio.run(main())
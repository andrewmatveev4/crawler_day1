import asyncio
from advanced_crawler import AdvancedCrawler


async def main():
    crawler = AdvancedCrawler.from_config("config.json")

    await crawler.crawl()
    stats = crawler.get_stats()

    print("\n" + "=" * 40)
    print("РЕЗУЛЬТАТ (через AdvancedCrawler)")
    print("=" * 40)
    print(f"Всего страниц:    {stats.total_pages()}")
    print(f"Успешно:          {stats.successful()}")
    print(f"Ошибок:           {stats.failed()}")
    print(f"Время работы:     {stats.elapsed_time():.2f}s")
    print(f"Средняя скорость: {stats.avg_speed():.2f} стр/сек")
    print(f"Статус-коды:      {stats.status_distribution()}")
    print(f"Топ доменов:      {stats.top_domains()}")

    crawler.export_to_json("report.json")
    crawler.export_to_html_report("report.html")
    print("\nОтчёты сохранены: report.json, report.html")

    await crawler.close()


if __name__ == "__main__":
    asyncio.run(main())
import argparse
import json
import asyncio
from advanced_crawler import AdvancedCrawler


def load_config(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)
    
def parse_args():
    parser = argparse.ArgumentParser(description="Асинхронный веб-краулер")

    parser.add_argument("--urls", nargs="+", help="Стартовые URL")
    parser.add_argument("--max-pages", type=int, help="Макс. страниц")
    parser.add_argument("--max-depth", type=int, help="Макс. глубина")
    parser.add_argument("--output", help="Файл результата")
    parser.add_argument("--rate-limit", type=float, help="Запросов/сек")
    parser.add_argument("--respect-robots", action="store_true", help="Соблюдать robots.txt")
    parser.add_argument("--config", help="Путь к JSON конфигу")
    parser.add_argument("--report", help="Файл для отчёта статистики")

    return parser.parse_args()

def build_settings(args) -> dict:
    settings = {
        "urls": None,
        "max_pages": 100,
        "max_depth": 2,
        "output": "results.json",
        "rate_limit": 1.0,
        "respect_robots": False,
    }

    # конфиг перебивает дефолты
    if args.config:
        settings.update(load_config(args.config))

    # флаги перебивают всё — но только реально переданные (не None)
    if args.urls is not None:
        settings["urls"] = args.urls
    if args.max_pages is not None:
        settings["max_pages"] = args.max_pages
    if args.max_depth is not None:
        settings["max_depth"] = args.max_depth
    if args.output is not None:
        settings["output"] = args.output
    if args.rate_limit is not None:
        settings["rate_limit"] = args.rate_limit
    if args.respect_robots:
        settings["respect_robots"] = True
    if args.report is not None:
        settings["report"] = args.report

    return settings


async def run_crawler(settings):
    crawler = AdvancedCrawler(settings)
    try:
        await crawler.crawl()
    except ValueError as e:
        print(f"Ошибка: {e}")
        return
    stats = crawler.get_stats()

    print(f"\nОбработано: {stats.total_pages()} | успешно: {stats.successful()} | ошибок: {stats.failed()}")
    print(f"Статус-коды: {stats.status_distribution()}")

    report = settings.get("report")
    if report:
        if report.endswith(".html"):
            crawler.export_to_html_report(report)
        else:
            crawler.export_to_json(report)
        print(f"Отчёт сохранён: {report}")

    output = settings.get("output", "results.json")
    print(f"Страницы сохранены: {output}")

    await crawler.close()


if __name__ == "__main__":
    args = parse_args()
    settings = build_settings(args)
    asyncio.run(run_crawler(settings))
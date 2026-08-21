import asyncio
import os
from crawler import AsyncCrawler
from storage import JSONStorage, CSVStorage, SQLiteStorage


async def crawl_into(storage, label):
    crawler = AsyncCrawler(
        max_concurrent=5,
        max_depth=1,
        respect_robots=False,
        requests_per_second=10.0,
        storage=storage,
    )
    await crawler.crawl(
        start_urls=["https://books.toscrape.com/"],
        max_pages=8,
        same_domain_only=True,
    )
    await crawler.close()
    print(f"  [{label}] краул завершён, данные сохранены")


async def main():
    # чистим старые файлы, чтоб append не копил с прошлых прогонов
    for f in ["day6_all.jsonl", "day6_all.csv", "day6_all.db"]:
        if os.path.exists(f):
            os.remove(f)

    print("=== Краулим в 3 формата ===")

    # JSON
    await crawl_into(JSONStorage("day6_all.jsonl"), "JSON")

    # CSV
    await crawl_into(CSVStorage("day6_all.csv"), "CSV")

    # SQLite (тут нужен init_db до краула)
    sqlite_storage = SQLiteStorage("day6_all.db")
    await sqlite_storage.init_db()
    await crawl_into(sqlite_storage, "SQLite")

    # читаем обратно, показываем что везде легло
    print("\n=== Проверка сохранённого ===")

    with open("day6_all.jsonl", encoding="utf-8") as f:
        json_lines = f.readlines()
    print(f"JSON:   {len(json_lines)} строк в day6_all.jsonl")

    with open("day6_all.csv", encoding="utf-8") as f:
        csv_lines = f.readlines()
    print(f"CSV:    {len(csv_lines)} строк в day6_all.csv (вкл. заголовок)")

    import aiosqlite
    db = await aiosqlite.connect("day6_all.db")
    async with db.execute("SELECT COUNT(*) FROM pages") as cur:
        (count,) = await cur.fetchone()
    await db.close()
    print(f"SQLite: {count} строк в таблице pages")


if __name__ == "__main__":
    asyncio.run(main())
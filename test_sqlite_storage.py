import asyncio
import os
from storage import SQLiteStorage


async def main():
    path = "test_crawler.db"
    if os.path.exists(path):
        os.remove(path)

    storage = SQLiteStorage(path)
    await storage.init_db()
    await storage.init_db()   # второй раз — проверяем IF NOT EXISTS, не должно упасть

    await storage.save({"url": "http://a.com", "title": "Привет", "crawled_at": "2026-08-21"})
    await storage.save({"url": "http://b.com", "title": "О'Брайен, тест", "crawled_at": "2026-08-21"})
    await storage.close()

    # читаем обратно из базы напрямую
    import aiosqlite
    db = await aiosqlite.connect(path)
    async with db.execute("SELECT id, url, title, crawled_at FROM pages") as cursor:
        rows = await cursor.fetchall()
    await db.close()

    print("=== строки в базе ===")
    for row in rows:
        print(row)
    print(f"=== всего строк: {len(rows)} (ждём 2) ===")


if __name__ == "__main__":
    asyncio.run(main())
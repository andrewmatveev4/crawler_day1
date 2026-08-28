import asyncio
import os
from storage import SQLiteStorage


async def main():
    path = "test_concurrent.db"
    if os.path.exists(path):
        os.remove(path)

    storage = SQLiteStorage(path, batch_size=5)

    # 50 параллельных save — максимальная нагрузка на гонку
    tasks = [
        storage.save({
            "url": f"http://test.com/{i}",
            "title": f"Страница {i}",
            "crawled_at": "2026-08-28",
            "status_code": 200,
            "content_type": "text/html",
        })
        for i in range(50)
    ]
    await asyncio.gather(*tasks)   # все 50 разом
    await storage.close()          # флаш хвоста

    # считаем, сколько реально в базе
    import aiosqlite
    db = await aiosqlite.connect(path)
    async with db.execute("SELECT COUNT(*) FROM pages") as cur:
        (total,) = await cur.fetchone()
    async with db.execute("SELECT COUNT(DISTINCT url) FROM pages") as cur:
        (unique,) = await cur.fetchone()
    await db.close()

    print("\n" + "=" * 40)
    print(f"Записано всего:    {total} (ждём 50)")
    print(f"Уникальных url:    {unique} (ждём 50)")
    print(f"Дублей:            {total - unique} (ждём 0)")


if __name__ == "__main__":
    asyncio.run(main())
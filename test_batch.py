import asyncio
import os
from storage import SQLiteStorage


async def main():
    path = "test_batch.db"
    if os.path.exists(path):
        os.remove(path)

    # batch_size=5, а запишем 8 → 5 уйдут авто-сливом, 3 останутся на flush в close
    storage = SQLiteStorage(path, batch_size=5)
    await storage.init_db()

    for i in range(8):
        await storage.save({
            "url": f"http://test.com/{i}",
            "title": f"Страница {i}",
            "crawled_at": "2026-08-21",
        })

    # ДО close проверим, сколько реально в базе — должно быть 5 (первая пачка),
    # а 3 ещё висят в буфере
    import aiosqlite
    db = await aiosqlite.connect(path)
    async with db.execute("SELECT COUNT(*) FROM pages") as cur:
        (before_close,) = await cur.fetchone()
    await db.close()
    print(f"До close(): в базе {before_close} (ждём 5 — первая пачка слита, 3 в буфере)")

    await storage.close()   # тут flush хвоста

    db = await aiosqlite.connect(path)
    async with db.execute("SELECT COUNT(*) FROM pages") as cur:
        (after_close,) = await cur.fetchone()
    await db.close()
    print(f"После close(): в базе {after_close} (ждём 8 — хвост дослит)")


if __name__ == "__main__":
    asyncio.run(main())
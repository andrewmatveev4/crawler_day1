import asyncio
import os
import json
from storage import SQLiteStorage


async def main():
    path = "test_full.db"
    if os.path.exists(path):
        os.remove(path)   # старая таблица помешает — сносим

    storage = SQLiteStorage(path)
    # НЕ зовём init_db вручную — проверяем заодно авто-инициализацию (пункт 3)

    await storage.save({
        "url": "http://a.com",
        "title": "Тест",
        "text": "текст страницы",
        "links": ["http://a.com/1", "http://a.com/2"],
        "metadata": {"description": "опис", "keywords": "ключи"},
        "crawled_at": "2026-08-24",
        "status_code": 200,
        "content_type": "text/html; charset=utf-8",
    })
    await storage.close()

    # читаем обратно
    import aiosqlite
    db = await aiosqlite.connect(path)
    async with db.execute(
        "SELECT url, title, text, links, metadata, crawled_at, status_code, content_type FROM pages"
    ) as cur:
        row = await cur.fetchone()
    await db.close()

    print("=== строка из базы ===")
    print(f"url:          {row[0]}")
    print(f"title:        {row[1]}")
    print(f"text:         {row[2]}")
    print(f"links (raw):  {row[3]}")
    print(f"metadata(raw):{row[4]}")
    print(f"crawled_at:   {row[5]}")
    print(f"status_code:  {row[6]}")
    print(f"content_type: {row[7]}")

    # распаковка обратно списка и словаря
    links = json.loads(row[3])
    metadata = json.loads(row[4])
    print("\n=== распаковка json ===")
    print(f"links[0]:     {links[0]}  (тип {type(links).__name__})")
    print(f"metadata key: {metadata['description']}  (тип {type(metadata).__name__})")


if __name__ == "__main__":
    asyncio.run(main())
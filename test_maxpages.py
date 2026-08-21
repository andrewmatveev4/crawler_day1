import asyncio
import os
from storage import JSONStorage



async def main():
    path = "test_output.jsonl"
    # чистим перед тестом, чтоб не мешались старые записи (append копит!)
    if os.path.exists(path):
        os.remove(path)

    storage = JSONStorage(path)

    await storage.save({"url": "http://a.com", "title": "Привет мир"})
    await storage.save({"url": "http://b.com", "title": "Второй"})
    await storage.close()

    print("=== содержимое файла ===")
    with open(path, encoding="utf-8") as f:
        content = f.read()
    print(content)

    lines = content.strip().split("\n")
    print(f"=== строк записано: {len(lines)} (ждём 2) ===")


if __name__ == "__main__":
    asyncio.run(main())



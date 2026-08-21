import asyncio
import os
from storage import CSVStorage


async def main():
    path = "test_output.csv"
    if os.path.exists(path):
        os.remove(path)

    storage = CSVStorage(path)

    # вторая запись — с ЗАПЯТОЙ внутри значения, спецсимвол
    await storage.save({"url": "http://a.com", "title": "Привет"})
    await storage.save({"url": "http://b.com", "title": "Книги, скидки, всё"})
    await storage.close()

    print("=== содержимое файла ===")
    with open(path, encoding="utf-8") as f:
        content = f.read()
    print(content)

    lines = content.strip().split("\n")
    print(f"=== всего строк: {len(lines)} (ждём 3: заголовок + 2 данных) ===")


if __name__ == "__main__":
    asyncio.run(main())
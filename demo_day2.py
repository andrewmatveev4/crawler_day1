import asyncio
from crawler import AsyncCrawler
import time


async def main():
    crawler = AsyncCrawler(max_concurrent=5)
    urls = [
        "https://example.com",
        "https://www.python.org",
        "https://www.github.com",
    ]

    start = time.perf_counter()
    tasks = [crawler.fetch_and_parse(url) for url in urls]
    results = await asyncio.gather(*tasks)
    elapsed = time.perf_counter() - start   

    await crawler.close()

    # красивый вывод статистики по каждой странице
    for r in results:
        print("\n" + "=" * 50)
        print(f"URL:      {r.get('url')}")
        print(f"Title:    {r.get('metadata', {}).get('title', '—')}")
        print(f"Ссылок:   {len(r.get('links', []))}")
        print(f"Картинок: {len(r.get('images', []))}")
        print(f"Текст:    {len(r.get('text', ''))} символов")
    print("\n" + "=" * 50)
    print(f"Всего страниц: {len(results)}")
    print(f"Время:         {elapsed:.2f} сек")


asyncio.run(main())
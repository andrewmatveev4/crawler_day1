import asyncio
from crawler import AsyncCrawler


async def main():
    crawler = AsyncCrawler(respect_robots=True, user_agent="MyBot/1.0")

    # /search запрещён в robots.txt гугла — зовём fetch_url НАПРЯМУЮ, минуя crawl
    print("=== прямой fetch_url на запрещённый /search ===")
    result = await crawler.fetch_url("https://www.google.com/search?q=test")
    print(f"результат: {'пусто (заблокирован)' if result == '' else 'загрузился (ПЛОХО!)'}")
    print(f"в blocked_by_robots: {crawler.blocked_by_robots}")

    await crawler.close()


asyncio.run(main())
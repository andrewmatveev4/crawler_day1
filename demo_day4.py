import asyncio
from crawler import AsyncCrawler


async def demo_crawl_with_robots():
    print("=" * 55)
    print("ДЕМО 1: обход с rate limiting + соблюдением robots.txt")
    print("=" * 55)

    crawler = AsyncCrawler(
        max_concurrent=3,
        max_depth=0,                 # только стартовые URL, без ухода вглубь
        requests_per_second=2.0,
        min_delay=0.3,
        jitter=0.2,
        respect_robots=True,
        user_agent="MyBot/1.0",
    )

    start_urls = [
        "https://www.google.com/",              # разрешён
        "https://www.google.com/search?q=test", # robots.txt запретит (/search под Disallow)
        "https://www.google.com/robots.txt",    # сам robots, разрешён
    ]
    results = await crawler.crawl(start_urls=start_urls, max_pages=20)
    await crawler.close()

    print("\n" + "-" * 55)
    print("СТАТИСТИКА")
    print("-" * 55)
    print(f"Обработано страниц:        {len(results)}")
    print(f"Ошибок:                    {len(crawler.failed_urls)}")
    print(f"Заблокировано robots.txt:  {len(crawler.blocked_by_robots)}")
    print(f"Средняя задержка:          {crawler.get_avg_delay():.2f}s")
    print(f"Всего запросов:            {len(crawler.request_times)}")
    if crawler.blocked_by_robots:
        print("\nЗаблокированные robots.txt URL:")
        for u in crawler.blocked_by_robots:
            print(f"   🚫 {u}")



async def demo_rate_limit_domains():
    import time
    from rate_limiter import RateLimiter

    print("\n" + "=" * 55)
    print("ДЕМО 2: rate limiting — один домен vs разные домены")
    print("=" * 55)

    # 4 запроса на ОДИН домен: должны выстроиться в очередь
    rl = RateLimiter(requests_per_second=2.0)
    start = time.monotonic()
    await asyncio.gather(*[rl.acquire("site-a.com") for _ in range(4)])
    one_domain = time.monotonic() - start
    print(f"4 запроса на ОДИН домен:     {one_domain:.2f}s  (ждут друг друга)")

    # по 1 запросу на 4 РАЗНЫХ домена: должны пройти сразу
    rl = RateLimiter(requests_per_second=2.0)
    start = time.monotonic()
    await asyncio.gather(
        rl.acquire("site-a.com"),
        rl.acquire("site-b.com"),
        rl.acquire("site-c.com"),
        rl.acquire("site-d.com"),
    )
    diff_domains = time.monotonic() - start
    print(f"4 запроса на РАЗНЫЕ домены:  {diff_domains:.2f}s  (независимы)")


async def main():
    await demo_crawl_with_robots()
    await demo_rate_limit_domains()


asyncio.run(main())
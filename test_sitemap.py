import asyncio
from sitemap import SitemapParser


async def main():
    parser = SitemapParser()

    # обычный или индексный — у большинства крупных есть
    print("=== gov.uk ===")
    urls = await parser.fetch_sitemap("https://www.gov.uk/sitemap.xml")
    print(f"Найдено url: {len(urls)}")
    for u in urls[:5]:
        print(f"  {u}")

    print("\n=== w3.org ===")
    urls2 = await parser.fetch_sitemap("https://www.w3.org/sitemap.xml")
    print(f"Найдено url: {len(urls2)}")
    for u in urls2[:5]:
        print(f"  {u}")

if __name__ == "__main__":
    asyncio.run(main())
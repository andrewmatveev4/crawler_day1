import asyncio
from parser import HTMLParser


async def main():
    parser = HTMLParser()

    # нормальный html — всё должно извлечься
    html = """
    <html>
      <head><title>Тестовая страница</title></head>
      <body>
        <h1>Заголовок</h1>
        <p>Немного текста тут.</p>
        <a href="https://example.com/page">ссылка</a>
      </body>
    </html>
    """
    result = await parser.parse_html(html, "http://test.local")

    print("\n" + "=" * 40)
    print(f"title:  {result['title']}")
    print(f"text:   {result['text'][:50]}...")
    print(f"links:  {result['links']}")
    print(f"error:  {result.get('error', 'НЕТ ошибки — частичный/полный результат вернулся')}")


if __name__ == "__main__":
    asyncio.run(main())
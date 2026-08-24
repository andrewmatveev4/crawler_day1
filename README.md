# Async Web Crawler

Асинхронный веб-краулер на Python (asyncio + aiohttp). Параллельный обход, соблюдение robots.txt, rate limiting, повторы при ошибках, сохранение в несколько форматов, статистика и отчёты.

## Возможности

- Асинхронный параллельный обход (батчи + семафоры)
- Соблюдение robots.txt и crawl-delay
- Rate limiting по доменам с jitter
- Автоповторы при временных ошибках (экспоненциальный backoff, растущие таймауты)
- Сохранение данных: JSON, CSV, SQLite (batch-вставки, индексы)
- Поддержка sitemap.xml (обычные и индексные, рекурсивно)
- Статистика и HTML/JSON отчёты
- CLI и конфигурация через JSON
- Логирование в файл с ротацией + консоль

## Установка

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install aiohttp aiofiles aiosqlite beautifulsoup4 lxml
```

## Быстрый старт

### Через CLI

```bash
python cli.py --urls https://example.com --max-pages 50 --max-depth 2
```

### Через конфиг

```bash
python cli.py --config config.json
```

### Программно

```python
import asyncio
from advanced_crawler import AdvancedCrawler


async def main():
    crawler = AdvancedCrawler.from_config("config.json")
    stats = await crawler.run()
    print(f"Обработано: {stats.total_pages()}")
    stats.export_to_html_report("report.html")


asyncio.run(main())
```

## Конфигурация (config.json)

```json
{
    "urls": ["https://books.toscrape.com/"],
    "max_pages": 10,
    "max_depth": 1,
    "rate_limit": 2.0,
    "respect_robots": false,
    "format": "json",
    "output": "results.json"
}
```

Приоритет настроек: значения по умолчанию < конфиг-файл < флаги командной строки.

## Параметры CLI

| Флаг | Описание |
|------|----------|
| `--urls` | Стартовые URL (один или несколько) |
| `--max-pages` | Максимум страниц |
| `--max-depth` | Максимальная глубина обхода |
| `--rate-limit` | Запросов в секунду |
| `--respect-robots` | Соблюдать robots.txt |
| `--output` | Файл для результатов |
| `--config` | Путь к JSON-конфигу |

## Компоненты

- **`crawler.py`** — `AsyncCrawler`, ядро обхода
- **`advanced_crawler.py`** — `AdvancedCrawler`, дирижёр (конфиг + краулер + статистика + экспорт)
- **`storage.py`** — хранилища (`JSONStorage`, `CSVStorage`, `SQLiteStorage`) на общем контракте `DataStorage`
- **`stats.py`** — `CrawlerStats`, метрики и отчёты
- **`sitemap.py`** — `SitemapParser`, разбор sitemap.xml
- **`retry_strategy.py`** — повторы при ошибках
- **`rate_limiter.py`**, **`robots.py`**, **`semaphore_manager.py`** — вежливость и параллелизм
- **`parser.py`** — извлечение данных из HTML
- **`cli.py`** — командный интерфейс
- **`logging_setup.py`** — настройка логирования

## Форматы хранения

- **JSON** (JSON Lines) — по объекту на строку
- **CSV** — с заголовками и экранированием
- **SQLite** — таблица `pages`, batch-вставки, индекс по url

## Статистика

`CrawlerStats` собирает: всего страниц, успешные/неудачные, среднюю скорость, распределение по статус-кодам, топ доменов, время работы. Экспорт: `export_to_json()`, `export_to_html_report()`.
from urllib.parse import urlparse
from collections import Counter


class CrawlerStats:
    def __init__(self, crawler):
        self.crawler = crawler

    def total_pages(self) -> int:
        return len(self.crawler.visited_urls)

    def successful(self) -> int:
        return len(self.crawler.processed_urls)

    def failed(self) -> int:
        return len(self.crawler.failed_urls)

    def status_distribution(self) -> dict:
        statuses = [
            meta[0]
            for meta in self.crawler._response_meta.values()
        ]
        return dict(Counter(statuses))

    def top_domains(self, n: int = 5) -> list:
        domains = [
            urlparse(url).netloc
            for url in self.crawler.processed_urls
        ]
        return Counter(domains).most_common(n)

    def elapsed_time(self) -> float:
        if self.crawler.start_time is None or self.crawler.end_time is None:
            return 0.0
        return self.crawler.end_time - self.crawler.start_time

    def avg_speed(self) -> float:
        elapsed = self.elapsed_time()
        if elapsed <= 0:
            return 0.0
        return self.successful() / elapsed

    def to_dict(self) -> dict:
        return {
            "total_pages": self.total_pages(),
            "successful": self.successful(),
            "failed": self.failed(),
            "elapsed_time": round(self.elapsed_time(), 2),
            "avg_speed": round(self.avg_speed(), 2),
            "status_distribution": self.status_distribution(),
            "top_domains": self.top_domains(),
        }

    def export_to_json(self, filename: str) -> None:
        import json
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)

    def export_to_html_report(self, filename: str) -> None:
        data = self.to_dict()

        status_rows = "".join(
            f"<tr><td>{code}</td><td>{count}</td></tr>"
            for code, count in data["status_distribution"].items()
        )
        domain_rows = "".join(
            f"<tr><td>{domain}</td><td>{count}</td></tr>"
            for domain, count in data["top_domains"]
        )

        html = f"""<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="utf-8">
    <title>Отчёт краулера</title>
    <style>
        body {{ font-family: sans-serif; margin: 40px; }}
        table {{ border-collapse: collapse; margin: 10px 0; }}
        td, th {{ border: 1px solid #ccc; padding: 6px 12px; }}
        h1 {{ color: #333; }}
    </style>
</head>
<body>
    <h1>Отчёт краулера</h1>
    <p>Всего страниц: <b>{data['total_pages']}</b></p>
    <p>Успешно: <b>{data['successful']}</b> | Ошибок: <b>{data['failed']}</b></p>
    <p>Время работы: <b>{data['elapsed_time']}s</b> | Скорость: <b>{data['avg_speed']} стр/сек</b></p>

    <h2>Статус-коды</h2>
    <table><tr><th>Код</th><th>Кол-во</th></tr>{status_rows}</table>

    <h2>Топ доменов</h2>
    <table><tr><th>Домен</th><th>Страниц</th></tr>{domain_rows}</table>
</body>
</html>"""

        with open(filename, "w", encoding="utf-8") as f:
            f.write(html)
from urllib.parse import urlparse, urlunparse

class URLFilter:
    def __init__(self, same_domain_only=False, base_domain="",
                 exclude_patterns=None, include_patterns=None):
        self.same_domain_only = same_domain_only
        self.base_domain = base_domain
        self.exclude_patterns = exclude_patterns or []
        self.include_patterns = include_patterns or []

    def is_allowed(self, url: str) -> bool:
        # 1. фильтр по домену
        if self.same_domain_only:
            domain = urlparse(url).netloc
            if domain != self.base_domain:
                return False

        # 2. исключающие паттерны
        for pattern in self.exclude_patterns:
            if pattern in url:
                return False

        # 3. включающие паттерны (если заданы — url обязан содержать хотя бы один)
        if self.include_patterns:
            if not any(pattern in url for pattern in self.include_patterns):
                return False

        return True

def normalize_url(url: str) -> str:
    parsed = urlparse(url)
    # собираем url заново БЕЗ фрагмента (#...) и БЕЗ хвостового слэша в пути
    path = parsed.path.rstrip("/")
    normalized = urlunparse((
        parsed.scheme,
        parsed.netloc,
        path,
        parsed.params,
        parsed.query,
        "",              # fragment — обнуляем (#... выкидываем)
    ))
    return normalized


if __name__ == "__main__":
    f = URLFilter(same_domain_only=True, base_domain="example.com",
                  exclude_patterns=[".pdf", "/admin"])

    print(f.is_allowed("https://example.com/page1"))      # True  — свой домен, чистый
    print(f.is_allowed("https://google.com/page"))        # False — чужой домен
    print(f.is_allowed("https://example.com/file.pdf"))   # False — .pdf запрещён
    print(f.is_allowed("https://example.com/admin/panel")) # False — /admin запрещён
    print(normalize_url("https://www.python.org"))       # https://www.python.org
    print(normalize_url("https://www.python.org/"))      # https://www.python.org
    print(normalize_url("https://www.python.org#top"))   # https://www.python.org
    print(normalize_url("https://www.python.org/about/")) # https://www.python.org/about
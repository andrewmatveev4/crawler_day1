class CrawlerError(Exception):
    """Базовая ошибка краулера — родитель для всех остальных."""
    pass


class TransientError(CrawlerError):
    """Временная ошибка (таймаут, 503, 429) — можно повторить."""
    pass


class PermanentError(CrawlerError):
    """Постоянная ошибка (404, 403, 401) — повторять бессмысленно."""
    pass


class NetworkError(CrawlerError):
    """Сетевая ошибка (connection refused, DNS) — можно повторить."""
    pass


class ParseError(CrawlerError):
    """Ошибка парсинга HTML."""
    pass

def classify_http_status(status: int) -> type:
    """Смотрит на HTTP-статус, возвращает КЛАСС нашей ошибки (не объект, а класс)."""
    if status in (429, 500, 502, 503, 504):
        return TransientError      # временные — сервер перегружен/моргнул, повторим
    if status in (404, 403, 401, 400):
        return PermanentError      # постоянные — нет смысла долбить
    return PermanentError          # всё остальное по умолчанию считаем постоянным
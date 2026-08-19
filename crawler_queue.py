class CrawlerQueue:
    def __init__(self):
        self._queue = []          # список url, ждущих обработки
        self._processed = []      # успешно обработанные
        self._failed = {}         # неудачные: {url: причина}

    def add_url(self, url: str, priority: int = 0, depth: int = 0):
        self._queue.append({"url": url, "priority": priority, "depth": depth})

    async def get_next_item(self):
        if not self._queue:
            return None
        best = max(self._queue, key=lambda item: item["priority"])
        self._queue.remove(best)
        return best

    async def get_next(self) -> str | None:
        item = await self.get_next_item()
        if item is None:
            return None
        return item["url"]

    def mark_processed(self, url: str):
        self._processed.append(url)

    def mark_failed(self, url: str, error: str):
        self._failed[url] = error

    def get_stats(self) -> dict:
        return {
            "in_queue": len(self._queue),
            "processed": len(self._processed),
            "failed": len(self._failed),
        }

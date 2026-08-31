import asyncio

class CrawlerQueue:
    def __init__(self):
        self._queue = []
        self._processed = []
        self._failed = {}
        self._lock = asyncio.Lock()

    async def add_url(self, url: str, priority: int = 0, depth: int = 0):
        async with self._lock:
            self._queue.append({"url": url, "priority": priority, "depth": depth})

    async def get_next_item(self):
        async with self._lock:
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

    async def mark_processed(self, url: str):
        async with self._lock:
            self._processed.append(url)

    async def mark_failed(self, url: str, error: str):
        async with self._lock:
            self._failed[url] = error

    def get_stats(self) -> dict:
        return {
            "in_queue": len(self._queue),
            "processed": len(self._processed),
            "failed": len(self._failed),
        }

import asyncio
from urllib.parse import urlparse


class SemaphoreManager:
    def __init__(self, global_limit: int = 10, per_domain_limit: int = 3):
        self.global_semaphore = asyncio.Semaphore(global_limit)
        self.per_domain_limit = per_domain_limit
        self._domain_semaphores = {}       # {домен: свой семафор}
        self.active_tasks = 0              # счётчик активных запросов

    def _get_domain_semaphore(self, url: str) -> asyncio.Semaphore:
        domain = urlparse(url).netloc
        if domain not in self._domain_semaphores:
            self._domain_semaphores[domain] = asyncio.Semaphore(self.per_domain_limit)
        return self._domain_semaphores[domain]

    def acquire(self, url: str):
        return _DualSemaphore(self.global_semaphore,
                              self._get_domain_semaphore(url),
                              self)

class _DualSemaphore:
    def __init__(self, global_sem, domain_sem, manager):
        self.global_sem = global_sem
        self.domain_sem = domain_sem
        self.manager = manager

    async def __aenter__(self):
        await self.global_sem.acquire()
        await self.domain_sem.acquire()
        self.manager.active_tasks += 1

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.manager.active_tasks -= 1
        self.domain_sem.release()
        self.global_sem.release()

if __name__ == "__main__":
    import asyncio

    async def worker(manager, url, n):
        async with manager.acquire(url):
            print(f"[{n}] захватил {urlparse(url).netloc}, активных: {manager.active_tasks}")
            await asyncio.sleep(1)
        print(f"[{n}] освободил")

    async def test():
        manager = SemaphoreManager(global_limit=10, per_domain_limit=2)
        # 5 запросов к ОДНОМУ домену, лимит на домен = 2
        tasks = [worker(manager, "https://example.com/page", i) for i in range(5)]
        await asyncio.gather(*tasks)

    asyncio.run(test())
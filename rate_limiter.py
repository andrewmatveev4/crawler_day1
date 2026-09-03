import time
import asyncio
import random


class RateLimiter:
    def __init__(self, requests_per_second: float = 1.0, per_domain: bool = True, min_delay: float = 0.0, jitter: float = 0.0,):
        self.interval = 1.0 / requests_per_second
        self.per_domain = per_domain
        self.min_delay = min_delay
        self.jitter = jitter
        self.next_free: dict[str, float] = {}
        self.domain_delay: dict[str, float] = {}
        self.lock = asyncio.Lock()

    async def acquire(self, domain: str = None):
        key = domain if self.per_domain else "__global__"

        async with self.lock:
            now = time.monotonic()
            domain_delay = self.domain_delay.get(key, 0.0)
            step = max(self.interval, self.min_delay, domain_delay)
            slot = max(now, self.next_free.get(key, 0.0))
            if self.jitter > 0:
                slot += random.uniform(0, self.jitter)
            self.next_free[key] = slot + step

        wait = slot - now

        if wait > 0:
            await asyncio.sleep(wait)

    def set_domain_delay(self, domain: str, value: float):
        current = self.domain_delay.get(domain, 0.0)
        if value > current:
            self.domain_delay[domain] = value


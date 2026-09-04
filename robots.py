import asyncio
import aiohttp
import logging
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

logger = logging.getLogger("crawler")


class RobotsParser:
    def __init__(self):
        self._cache: dict[str, RobotFileParser] = {}
        self._locks: dict[str, asyncio.Lock] = {}
        self._locks_guard = asyncio.Lock()

    async def _fetch_text(self, robots_url: str, headers: dict, session) -> str | None:
        # если сессия передана — используем её (общий пул краулера),
        # иначе создаём свою (fallback для автономного использования)
        if session is not None:
            async with session.get(robots_url, headers=headers) as response:
                if response.status == 200:
                    return await response.text()
                return None
        else:
            timeout = aiohttp.ClientTimeout(total=10)
            async with aiohttp.ClientSession(timeout=timeout) as own:
                async with own.get(robots_url, headers=headers) as response:
                    if response.status == 200:
                        return await response.text()
                    return None

    async def fetch_robots(self, base_url: str, user_agent: str = "*", session=None) -> RobotFileParser:
        domain = urlparse(base_url).netloc

        if domain in self._cache:
            return self._cache[domain]

        async with self._locks_guard:
            if domain not in self._locks:
                self._locks[domain] = asyncio.Lock()
            domain_lock = self._locks[domain]

        async with domain_lock:
            if domain in self._cache:
                return self._cache[domain]

            robots_url = f"{urlparse(base_url).scheme}://{domain}/robots.txt"
            rp = RobotFileParser()
            headers = {"User-Agent": user_agent}
            try:
                text = await self._fetch_text(robots_url, headers, session)
                if text is not None:
                    rp.parse(text.splitlines())
                    logger.info(f"robots.txt загружен: {robots_url}")
                else:
                    rp.parse([])
                    logger.info(f"robots.txt недоступен: {robots_url}, разрешаем всё")
            except Exception as e:
                rp.parse([])
                logger.warning(f"robots.txt ошибка для {domain}: {e}, разрешаем всё")

            self._cache[domain] = rp
            return rp

    async def can_fetch(self, url: str, user_agent: str = "*", session=None) -> bool:
        rp = await self.fetch_robots(url, user_agent=user_agent, session=session)
        return rp.can_fetch(user_agent, url)

    async def get_crawl_delay(self, url: str, user_agent: str = "*", session=None) -> float:
        rp = await self.fetch_robots(url, user_agent=user_agent, session=session)
        delay = rp.crawl_delay(user_agent)
        return float(delay) if delay is not None else 0.0
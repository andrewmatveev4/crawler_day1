import asyncio
import logging
from errors import TransientError, NetworkError

logger = logging.getLogger("crawler")


class RetryStrategy:
    def __init__(self, max_retries: int = 3, backoff_factor: float = 2.0, retry_on: list = None):
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self.retry_on = tuple(retry_on) if retry_on else (TransientError, NetworkError)

    async def execute_with_retry(self, coro, *args, **kwargs):
        for attempt in range(self.max_retries):
            try:
                return await coro(*args, **kwargs)
            except Exception as e:
                should_retry = isinstance(e, self.retry_on)

                if not should_retry:
                    logger.warning(f"Не повторяем ({type(e).__name__}) — постоянная ошибка")
                    raise

                if attempt < self.max_retries - 1:
                    delay = self.backoff_factor ** attempt
                    logger.warning(
                        f"Попытка {attempt + 1}/{self.max_retries} ({type(e).__name__}), жду {delay:.1f}s"
                    )
                    await asyncio.sleep(delay)
                else:
                    logger.warning(f"Все {self.max_retries} попыток исчерпаны ({type(e).__name__})")
                    raise
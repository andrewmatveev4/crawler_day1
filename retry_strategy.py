import asyncio
import logging
from errors import TransientError, NetworkError

logger = logging.getLogger("crawler")


class RetryStrategy:
    def __init__(self, max_retries: int = 3, backoff_factor: float = 2.0, retry_on: list = None):
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self.retry_on = tuple(retry_on) if retry_on else (TransientError, NetworkError)
        self.stats = {
            "retried": 0,
            "succeeded_after_retry": 0,
            "gave_up": 0,
            "not_retried": 0,
        }
        self.errors_by_type = {}       # {"TransientError": 3, "PermanentError": 1}
        self.permanent_errors = []     # список сообщений постоянных ошибок

    async def execute_with_retry(self, coro, *args, **kwargs):
        for attempt in range(self.max_retries):
            try:
                result = await coro(*args, **kwargs)
                if attempt > 0:
                    self.stats["succeeded_after_retry"] += 1
                    logger.info(f"Успех после {attempt} повтор(ов)")
                return result
            except Exception as e:
                should_retry = isinstance(e, self.retry_on)

                if not should_retry:
                    self.stats["not_retried"] += 1
                    self.errors_by_type[type(e).__name__] = self.errors_by_type.get(type(e).__name__, 0) + 1
                    self.permanent_errors.append(str(e))
                    logger.warning(f"Не повторяем ({type(e).__name__}) — постоянная ошибка")
                    raise

                if attempt < self.max_retries - 1:
                    self.stats["retried"] += 1
                    delay = self.backoff_factor ** attempt
                    logger.warning(
                        f"Попытка {attempt + 1}/{self.max_retries} ({type(e).__name__}), жду {delay:.1f}s"
                    )
                    await asyncio.sleep(delay)
                else:
                    self.stats["gave_up"] += 1
                    self.errors_by_type[type(e).__name__] = self.errors_by_type.get(type(e).__name__, 0) + 1
                    logger.warning(f"Все {self.max_retries} попыток исчерпаны ({type(e).__name__})")
                    raise
import asyncio
import logging
from retry_strategy import RetryStrategy
from errors import TransientError

logging.basicConfig(level=logging.INFO, format="%(message)s")

counter = {"n": 0}


async def flaky(url, timeout=10):
    counter["n"] += 1
    if counter["n"] < 3:
        raise TransientError(f"облом {counter['n']} на {url} (timeout={timeout})")
    return f"успех на попытке {counter['n']}"


async def always_fails(name):
    raise TransientError(f"{name} всегда падает")


async def main():
    rs = RetryStrategy(max_retries=3, backoff_factor=2.0)

    print("=== flaky: падает 2 раза, потом успех ===")
    result = await rs.execute_with_retry(flaky, "http://test.com", timeout=30)
    print(f"РЕЗУЛЬТАТ: {result}\n")

    print("=== always_fails: временная, но падает всегда → исчерпает попытки ===")
    try:
        await rs.execute_with_retry(always_fails, "Бомба")
    except Exception as e:
        print(f"долетело наверх: {type(e).__name__}\n")

    print("=== СТАТИСТИКА СТРАТЕГИИ ===")
    for key, val in rs.stats.items():
        print(f"  {key}: {val}")


asyncio.run(main())
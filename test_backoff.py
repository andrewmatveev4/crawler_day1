import asyncio
import logging
from retry_strategy import RetryStrategy
from errors import TransientError, PermanentError

logging.basicConfig(level=logging.INFO, format="%(message)s")


async def temporary_problem(url):
    raise TransientError(f"503 на {url}")      # временная — должны повторять


async def permanent_problem(url):
    raise PermanentError(f"404 на {url}")      # постоянная — НЕ должны повторять


async def main():
    rs = RetryStrategy(max_retries=3, backoff_factor=2.0)

    print("=== TransientError (503): ожидаем 3 попытки ===")
    try:
        await rs.execute_with_retry(temporary_problem, "http://a.com")
    except TransientError as e:
        print(f"сдались после повторов: {e}\n")

    print("=== PermanentError (404): ожидаем МГНОВЕННУЮ сдачу, без повторов ===")
    try:
        await rs.execute_with_retry(permanent_problem, "http://b.com")
    except PermanentError as e:
        print(f"сразу сдались, не повторяя: {e}")


asyncio.run(main())
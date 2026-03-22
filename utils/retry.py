import asyncio
import httpx
from typing import TypeVar, Callable, Awaitable

T = TypeVar("T")

RETRYABLE_EXCEPTIONS = (
    httpx.TimeoutException,
    httpx.ConnectError,
    httpx.RemoteProtocolError,
)

RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}


async def retry_async(
    func: Callable[..., Awaitable[T]],
    *args,
    max_retries: int = 3,
    base_delay: float = 1.0,
    **kwargs,
) -> T:
    """Execute an async function with exponential backoff retry.

    Retries on transient HTTP errors (429, 5xx) and connection issues.
    """
    last_exception = None
    for attempt in range(max_retries + 1):
        try:
            return await func(*args, **kwargs)
        except RETRYABLE_EXCEPTIONS as e:
            last_exception = e
            if attempt < max_retries:
                delay = base_delay * (2 ** attempt)
                await asyncio.sleep(delay)
        except httpx.HTTPStatusError as e:
            last_exception = e
            if e.response.status_code in RETRYABLE_STATUS_CODES and attempt < max_retries:
                delay = base_delay * (2 ** attempt)
                await asyncio.sleep(delay)
            else:
                raise
    raise last_exception

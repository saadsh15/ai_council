import httpx
from typing import List
import asyncio

async def validate_source(url: str) -> bool:
    """Check if a source URL is valid and accessible."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.head(url)
            return response.status_code == 200
    except (httpx.HTTPError, httpx.TimeoutException):
        return False

async def validate_sources(urls: List[str]) -> List[bool]:
    """Validate multiple source URLs in parallel."""
    tasks = [validate_source(url) for url in urls]
    return await asyncio.gather(*tasks)

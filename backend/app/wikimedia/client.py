import asyncio
from collections.abc import Awaitable, Callable

import httpx

from app.settings import settings

RETRY_STATUSES = {429, 500, 502, 503, 504}
MAX_RETRY_AFTER = 10.0


class WikimediaError(Exception):
    pass


def user_agent() -> str:
    return f"timeline-prototype/0.1 ({settings.wikimedia_contact})"


class WikimediaClient:
    def __init__(
        self,
        transport: httpx.AsyncBaseTransport | None = None,
        sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
    ) -> None:
        self._http = httpx.AsyncClient(
            headers={"User-Agent": user_agent()},
            timeout=settings.wikimedia_timeout,
            transport=transport,
        )
        self._sleep = sleep

    async def close(self) -> None:
        await self._http.aclose()

    async def get_json(self, url: str, params: dict) -> dict:
        host = httpx.URL(url).host
        failure = ""
        delay = 0.0
        for attempt in range(settings.wikimedia_max_retries + 1):
            if attempt:
                await self._sleep(delay)
            delay = float(2**attempt)
            try:
                response = await self._http.get(url, params=params)
            except httpx.TimeoutException:
                failure = "timed out"
                continue
            except httpx.TransportError:
                failure = "could not be reached"
                continue
            if response.status_code in RETRY_STATUSES:
                failure = f"returned HTTP {response.status_code}"
                delay = retry_after(response, delay)
                continue
            if response.status_code == 403:
                raise WikimediaError(
                    f"{host} refused the request; set TIMELINE_WIKIMEDIA_CONTACT "
                    "to a URL or email address."
                )
            if response.is_error:
                raise WikimediaError(f"{host} returned HTTP {response.status_code}.")
            try:
                data = response.json()
            except ValueError:
                raise WikimediaError(f"{host} returned an invalid response.") from None
            if isinstance(data, dict) and "error" in data:
                raise WikimediaError(f"{host} error: {data['error'].get('info', 'unknown')}")
            return data
        raise WikimediaError(f"{host} {failure}.")


def retry_after(response: httpx.Response, default: float) -> float:
    try:
        return min(float(response.headers["Retry-After"]), MAX_RETRY_AFTER)
    except (KeyError, ValueError):
        return default

import httpx
import pytest

from app.settings import settings
from app.wikimedia.client import WikimediaClient, WikimediaError

pytestmark = pytest.mark.anyio

URL = "https://www.wikidata.org/w/api.php"


def client_with(responses: list) -> tuple[WikimediaClient, list[httpx.Request], list[float]]:
    requests: list[httpx.Request] = []
    sleeps: list[float] = []
    remaining = iter(responses)

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        response = next(remaining)
        if isinstance(response, Exception):
            raise response
        return response

    async def sleep(seconds: float) -> None:
        sleeps.append(seconds)

    return WikimediaClient(httpx.MockTransport(handler), sleep), requests, sleeps


async def test_returns_json_and_sends_user_agent():
    client, requests, sleeps = client_with([httpx.Response(200, json={"ok": True})])

    assert await client.get_json(URL, {"action": "query"}) == {"ok": True}

    assert settings.wikimedia_contact in requests[0].headers["User-Agent"]
    assert requests[0].url.params["action"] == "query"
    assert sleeps == []


async def test_throttling_waits_for_retry_after():
    client, requests, sleeps = client_with(
        [httpx.Response(429, headers={"Retry-After": "3"}), httpx.Response(200, json={})]
    )

    assert await client.get_json(URL, {}) == {}

    assert len(requests) == 2
    assert sleeps == [3.0]


async def test_retry_after_is_capped():
    client, _, sleeps = client_with(
        [httpx.Response(429, headers={"Retry-After": "600"}), httpx.Response(200, json={})]
    )

    await client.get_json(URL, {})

    assert sleeps == [10.0]


async def test_server_errors_and_timeouts_are_retried_with_backoff():
    client, requests, sleeps = client_with(
        [httpx.Response(503), httpx.ReadTimeout("slow"), httpx.Response(200, json={})]
    )

    assert await client.get_json(URL, {}) == {}

    assert len(requests) == 3
    assert sleeps == [1.0, 2.0]


async def test_gives_up_after_retry_limit():
    client, requests, _ = client_with([httpx.Response(503)] * 5)

    with pytest.raises(WikimediaError, match="HTTP 503"):
        await client.get_json(URL, {})

    assert len(requests) == settings.wikimedia_max_retries + 1


async def test_timeout_is_reported():
    client, _, _ = client_with([httpx.ConnectTimeout("slow")] * 5)

    with pytest.raises(WikimediaError, match="timed out"):
        await client.get_json(URL, {})


async def test_client_error_is_not_retried():
    client, requests, _ = client_with([httpx.Response(400)])

    with pytest.raises(WikimediaError, match="HTTP 400"):
        await client.get_json(URL, {})

    assert len(requests) == 1


async def test_refused_request_points_to_contact_setting():
    client, _, _ = client_with([httpx.Response(403)])

    with pytest.raises(WikimediaError, match="TIMELINE_WIKIMEDIA_CONTACT"):
        await client.get_json(URL, {})


async def test_invalid_json_is_an_error():
    client, _, _ = client_with([httpx.Response(200, text="<html>")])

    with pytest.raises(WikimediaError, match="invalid response"):
        await client.get_json(URL, {})


async def test_api_error_body_is_an_error():
    client, _, _ = client_with([httpx.Response(200, json={"error": {"info": "bad ids"}})])

    with pytest.raises(WikimediaError, match="bad ids"):
        await client.get_json(URL, {})

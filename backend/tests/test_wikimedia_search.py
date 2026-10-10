import json
from datetime import date
from pathlib import Path

import httpx
import pytest

from app.wikimedia.client import WikimediaClient, WikimediaError
from app.wikimedia.search import discover_events, search_entities, search_wikipedia

pytestmark = pytest.mark.anyio

FIXTURES = Path(__file__).parent / "fixtures" / "wikimedia"


def recorded(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def sparql_result(*qids: str) -> dict:
    bindings = [{"item": {"value": f"http://www.wikidata.org/entity/{qid}"}} for qid in qids]
    return {"results": {"bindings": bindings}}


def fake_wikimedia(sparql: dict | None = None) -> tuple[WikimediaClient, list[httpx.Request]]:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if request.url.host == "query.wikidata.org":
            return httpx.Response(200, json=sparql)
        if request.url.host.endswith("wikipedia.org"):
            return httpx.Response(200, json=recorded("wikipedia_search.json"))
        action = request.url.params["action"]
        return httpx.Response(200, json=recorded(f"{action}.json"))

    return WikimediaClient(httpx.MockTransport(handler)), requests


def params(requests: list[httpx.Request], index: int) -> httpx.QueryParams:
    return requests[index].url.params


async def test_search_entities_fetches_found_entities():
    client, requests = fake_wikimedia()

    events, rejected = await search_entities(client, "Battle of Waterloo", 2)

    assert [event.title for event in events] == ["Battle of Waterloo"]
    assert rejected == 0
    assert params(requests, 0)["search"] == "Battle of Waterloo"
    assert params(requests, 0)["limit"] == "2"
    assert params(requests, 1)["ids"] == "Q48314|Q17539747"


async def test_search_limit_is_capped():
    client, requests = fake_wikimedia()

    await search_entities(client, "Battle of Waterloo", 500)

    assert params(requests, 0)["limit"] == "50"


async def test_search_wikipedia_resolves_pages_to_entities():
    client, requests = fake_wikimedia()

    events, _ = await search_wikipedia(client, "Battle of Waterloo", 3)

    assert requests[0].url.host == "en.wikipedia.org"
    assert params(requests, 0)["gsrsearch"] == "Battle of Waterloo"
    assert params(requests, 1)["ids"] == "Q48314|Q25194739|Q7100624"
    assert [event.wikidata_id for event in events] == ["Q48314"]


async def test_wikipedia_pages_without_entity_are_dropped():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"query": {"pages": [{"title": "No item", "index": 1}]}})

    client = WikimediaClient(httpx.MockTransport(handler))

    assert await search_wikipedia(client, "anything", 3) == ([], 0)


@pytest.mark.parametrize("language", ["en.evil.example", "EN", "", "e/n"])
async def test_invalid_language_is_refused(language):
    client, requests = fake_wikimedia()

    with pytest.raises(WikimediaError, match="language"):
        await search_wikipedia(client, "anything", 3, language)

    assert requests == []


async def test_discover_builds_query_from_validated_values():
    client, requests = fake_wikimedia(sparql_result("Q48314"))

    events, _ = await discover_events(
        client,
        date(1815, 1, 1),
        date(1815, 12, 31),
        20,
        event_type="battle",
        place="Q31",
        participant="Q142",
    )

    query = params(requests, 0)["query"]
    assert '"1815-01-01T00:00:00Z"' in query
    assert '"1815-12-31T23:59:59Z"' in query
    assert "wdt:P31/wdt:P279* wd:Q178561" in query
    assert "wdt:P17|wdt:P276 wd:Q31" in query
    assert "wdt:P710 wd:Q142" in query
    assert query.endswith("LIMIT 20")
    assert [event.title for event in events] == ["Battle of Waterloo"]


async def test_discover_without_filters_has_only_the_date_range():
    client, requests = fake_wikimedia(sparql_result())

    assert await discover_events(client, date(1815, 1, 1), date(1815, 12, 31), 20) == ([], 0)

    query = params(requests, 0)["query"]
    assert "wd:" not in query
    assert len(requests) == 1


async def test_discover_resolves_place_name_to_entity():
    client, requests = fake_wikimedia(sparql_result())

    await discover_events(client, date(1815, 1, 1), date(1815, 12, 31), 20, place="Waterloo")

    assert params(requests, 0)["search"] == "Waterloo"
    assert "wdt:P17|wdt:P276 wd:Q48314" in params(requests, 1)["query"]


async def test_discover_fails_when_name_is_not_found():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"search": []})

    client = WikimediaClient(httpx.MockTransport(handler))

    with pytest.raises(WikimediaError, match="No Wikidata entity"):
        await discover_events(client, date(1815, 1, 1), date(1815, 12, 31), 20, place="Nowhere")


async def test_discover_refuses_unknown_event_type():
    client, requests = fake_wikimedia(sparql_result())

    with pytest.raises(WikimediaError, match="Unknown event type"):
        await discover_events(
            client, date(1815, 1, 1), date(1815, 12, 31), 20, event_type="wd:Q1 } #"
        )

    assert requests == []


async def test_discover_drops_events_outside_the_range():
    client, _ = fake_wikimedia(sparql_result("Q517"))

    events, _ = await discover_events(client, date(1769, 1, 1), date(1769, 12, 31), 20)

    assert [event.title for event in events] == ["Napoleon (born)"]

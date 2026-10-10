import re
from datetime import date

from app.events import EventCandidate
from app.wikimedia.client import WikimediaClient, WikimediaError
from app.wikimedia.normalize import events_from_entity

WIKIDATA_API = "https://www.wikidata.org/w/api.php"
SPARQL_ENDPOINT = "https://query.wikidata.org/sparql"
MAX_LIMIT = 50
QID_PATTERN = re.compile(r"^Q\d+$")
LANGUAGE_PATTERN = re.compile(r"^[a-z]{2,3}(-[a-z]+)*$")

EVENT_TYPES = {
    "battle": "Q178561",
    "war": "Q198",
    "siege": "Q188055",
    "treaty": "Q131569",
    "peace treaty": "Q625298",
    "revolution": "Q10931",
    "rebellion": "Q124734",
    "coup": "Q45382",
    "massacre": "Q3199915",
    "election": "Q40231",
    "coronation": "Q209715",
    "earthquake": "Q7944",
    "volcanic eruption": "Q7692360",
}

Found = tuple[list[EventCandidate], int]


async def search_entities(
    client: WikimediaClient, query: str, limit: int, language: str = "en"
) -> Found:
    qids = await entity_ids(client, query, limit, check_language(language))
    return await events_for(client, qids, language)


async def search_wikipedia(
    client: WikimediaClient, query: str, limit: int, language: str = "en"
) -> Found:
    data = await client.get_json(
        f"https://{check_language(language)}.wikipedia.org/w/api.php",
        {
            "action": "query",
            "generator": "search",
            "gsrsearch": query,
            "gsrlimit": clamp(limit),
            "gsrnamespace": 0,
            "prop": "pageprops",
            "ppprop": "wikibase_item",
            "format": "json",
            "formatversion": 2,
        },
    )
    pages = sorted(data.get("query", {}).get("pages", []), key=lambda page: page.get("index", 0))
    qids = [page["pageprops"]["wikibase_item"] for page in pages if "pageprops" in page]
    return await events_for(client, qids, language)


async def discover_events(
    client: WikimediaClient,
    start_date: date,
    end_date: date,
    limit: int,
    event_type: str | None = None,
    place: str | None = None,
    participant: str | None = None,
) -> Found:
    if event_type is not None and event_type not in EVENT_TYPES:
        raise WikimediaError(
            f"Unknown event type '{event_type}'. Allowed: {', '.join(EVENT_TYPES)}."
        )
    query = discovery_query(
        start_date,
        end_date,
        clamp(limit),
        EVENT_TYPES.get(event_type),
        await resolve(client, place),
        await resolve(client, participant),
    )
    data = await client.get_json(SPARQL_ENDPOINT, {"query": query, "format": "json"})
    qids = [
        row["item"]["value"].rsplit("/", 1)[-1]
        for row in data.get("results", {}).get("bindings", [])
    ]
    candidates, rejected = await events_for(client, qids, "en")
    in_range = [c for c in candidates if start_date <= c.date <= end_date]
    return in_range, rejected


def discovery_query(
    start_date: date,
    end_date: date,
    limit: int,
    type_id: str | None,
    place_id: str | None,
    participant_id: str | None,
) -> str:
    filters = ""
    if type_id:
        filters += f"  ?item wdt:P31/wdt:P279* wd:{type_id} .\n"
    if place_id:
        filters += f"  ?item wdt:P17|wdt:P276 wd:{place_id} .\n"
    if participant_id:
        filters += f"  ?item wdt:P710 wd:{participant_id} .\n"
    return (
        "SELECT DISTINCT ?item WHERE {\n"
        "  ?item p:P585|p:P580 ?statement .\n"
        "  ?statement psv:P585|psv:P580 ?value .\n"
        "  ?value wikibase:timePrecision 11 ; wikibase:timeValue ?date .\n"
        f'  FILTER(?date >= "{start_date.isoformat()}T00:00:00Z"^^xsd:dateTime'
        f' && ?date <= "{end_date.isoformat()}T23:59:59Z"^^xsd:dateTime)\n'
        f"{filters}"
        f"}} LIMIT {limit}"
    )


async def resolve(client: WikimediaClient, name: str | None) -> str | None:
    if name is None or QID_PATTERN.match(name):
        return name
    qids = await entity_ids(client, name, 1, "en")
    if not qids:
        raise WikimediaError(f"No Wikidata entity found for '{name}'.")
    return qids[0]


async def entity_ids(client: WikimediaClient, query: str, limit: int, language: str) -> list[str]:
    data = await client.get_json(
        WIKIDATA_API,
        {
            "action": "wbsearchentities",
            "search": query,
            "language": language,
            "limit": clamp(limit),
            "format": "json",
        },
    )
    return [item["id"] for item in data.get("search", [])]


async def events_for(client: WikimediaClient, qids: list[str], language: str) -> Found:
    if not qids:
        return [], 0
    data = await client.get_json(
        WIKIDATA_API,
        {
            "action": "wbgetentities",
            "ids": "|".join(qids),
            "props": "labels|descriptions|claims|sitelinks/urls",
            "languages": language,
            "languagefallback": 1,
            "sitefilter": f"{language.replace('-', '_')}wiki",
            "format": "json",
        },
    )
    candidates: list[EventCandidate] = []
    rejected = 0
    for qid in qids:
        found, skipped = events_from_entity(data.get("entities", {}).get(qid, {}), language)
        candidates += found
        rejected += skipped
    return candidates, rejected


def check_language(language: str) -> str:
    if not LANGUAGE_PATTERN.match(language):
        raise WikimediaError(f"Invalid language code '{language}'.")
    return language


def clamp(limit: int) -> int:
    return max(1, min(limit, MAX_LIMIT))

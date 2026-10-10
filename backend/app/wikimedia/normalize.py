import re

from pydantic import ValidationError

from app.events import EventCandidate

DATE_PROPERTIES = {
    "P569": "born",
    "P570": "died",
    "P571": "founded",
    "P576": "dissolved",
    "P577": "released",
    "P580": "start",
    "P582": "end",
    "P585": "",
}
DAY_PRECISION = 11
TIME_PATTERN = re.compile(r"^\+(\d{4})-(\d{2})-(\d{2})T")


def events_from_entity(entity: dict, language: str) -> tuple[list[EventCandidate], int]:
    label = text(entity.get("labels"), language)
    if not label:
        return [], 0
    description = text(entity.get("descriptions"), language)
    sitelink = (entity.get("sitelinks") or {}).get(f"{language.replace('-', '_')}wiki", {})
    candidates: list[EventCandidate] = []
    rejected = 0
    for date_property, suffix in DATE_PROPERTIES.items():
        for statement in (entity.get("claims") or {}).get(date_property, []):
            try:
                candidates.append(
                    EventCandidate(
                        wikidata_id=entity["id"],
                        source_statement_id=statement.get("id"),
                        date_property=date_property,
                        title=f"{label} ({suffix})" if suffix else label,
                        date=exact_day(statement),
                        description=description,
                        wikipedia_url=sitelink.get("url"),
                    )
                )
            except (ValueError, ValidationError):
                rejected += 1
    return candidates, rejected


def text(values: dict | None, language: str) -> str:
    values = values or {}
    return (values.get(language) or values.get("en") or {}).get("value", "")


def exact_day(statement: dict) -> str:
    if statement.get("rank") == "deprecated":
        raise ValueError("deprecated statement")
    snak = statement.get("mainsnak", {})
    if snak.get("snaktype") != "value":
        raise ValueError("no value")
    value = snak["datavalue"]["value"]
    match = TIME_PATTERN.match(value["time"])
    if value.get("precision") != DAY_PRECISION or not match:
        raise ValueError("not an exact CE day")
    return "-".join(match.groups())

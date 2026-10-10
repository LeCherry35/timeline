import json
from datetime import date
from pathlib import Path

import pytest

from app.wikimedia.normalize import events_from_entity

FIXTURES = Path(__file__).parent / "fixtures" / "wikimedia"


def recorded_entity(qid: str) -> dict:
    data = json.loads((FIXTURES / "wbgetentities.json").read_text(encoding="utf-8"))
    return data["entities"][qid]


def statement(time: str = "+1815-06-18T00:00:00Z", precision: int = 11, **overrides) -> dict:
    mainsnak = {
        "snaktype": "value",
        "datavalue": {"value": {"time": time, "precision": precision}},
    }
    return {"id": "Q1$a", "rank": "normal", "mainsnak": mainsnak} | overrides


def entity(**claims) -> dict:
    return {"id": "Q1", "labels": {"en": {"value": "Thing"}}, "claims": claims}


def test_recorded_event_is_normalized():
    [event], rejected = events_from_entity(recorded_entity("Q48314"), "en")

    assert rejected == 0
    assert event.wikidata_id == "Q48314"
    assert event.source_statement_id == "Q48314$bacee479-457c-e1dd-9285-3685e0d86514"
    assert event.date_property == "P585"
    assert event.title == "Battle of Waterloo"
    assert event.date == date(1815, 6, 18)
    assert event.description == "1815 battle during the War of the Seventh Coalition"
    assert event.wikipedia_url == "https://en.wikipedia.org/wiki/Battle_of_Waterloo"


def test_recorded_person_gives_dated_titles_and_rejects_year_precision():
    events, rejected = events_from_entity(recorded_entity("Q517"), "en")

    assert [(event.title, event.date) for event in events] == [
        ("Napoleon (born)", date(1769, 8, 15)),
        ("Napoleon (died)", date(1821, 5, 5)),
    ]
    assert rejected == 2


@pytest.mark.parametrize(
    "bad",
    [
        statement(precision=9),
        statement(precision=10),
        statement(time="-0044-03-15T00:00:00Z"),
        statement(time="+0000-01-01T00:00:00Z"),
        statement(time="+1815-02-30T00:00:00Z"),
        statement(rank="deprecated"),
        statement(mainsnak={"snaktype": "somevalue"}),
        statement(mainsnak={"snaktype": "novalue"}),
    ],
)
def test_statement_without_exact_day_is_rejected(bad):
    assert events_from_entity(entity(P585=[bad]), "en") == ([], 1)


def test_other_properties_are_ignored():
    assert events_from_entity(entity(P1619=[statement()]), "en") == ([], 0)


def test_entity_without_label_is_skipped():
    unlabeled = entity(P585=[statement()]) | {"labels": {}}

    assert events_from_entity(unlabeled, "en") == ([], 0)


def test_missing_description_and_sitelink_are_optional():
    [event], _ = events_from_entity(entity(P585=[statement()]), "en")

    assert event.description == ""
    assert event.wikipedia_url is None


def test_requested_language_is_used():
    localized = entity(P585=[statement()]) | {
        "labels": {"de": {"value": "Ding"}, "en": {"value": "Thing"}},
        "sitelinks": {"dewiki": {"url": "https://de.wikipedia.org/wiki/Ding"}},
    }

    [event], _ = events_from_entity(localized, "de")

    assert event.title == "Ding"
    assert event.wikipedia_url == "https://de.wikipedia.org/wiki/Ding"

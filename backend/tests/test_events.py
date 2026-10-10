from datetime import date

import pytest
from pydantic import ValidationError

from app.events import EventCandidate, EventStore


def candidate(**overrides) -> EventCandidate:
    fields = {
        "wikidata_id": "Q48314",
        "source_statement_id": "Q48314$1",
        "date_property": "P585",
        "title": "Battle of Waterloo",
        "date": "1815-06-18",
    }
    return EventCandidate(**(fields | overrides))


@pytest.mark.parametrize(
    "overrides",
    [
        {"wikidata_id": "48314"},
        {"date_property": "585"},
        {"title": ""},
        {"date": "1815"},
        {"date": "1815-06"},
        {"date": "1815-02-30"},
    ],
)
def test_invalid_candidate_is_rejected(overrides):
    with pytest.raises(ValidationError):
        candidate(**overrides)


def test_add_stores_event_with_id():
    store = EventStore(max_events=10)

    result = store.add([candidate()])

    assert result.added == 1
    assert result.warnings == []
    [event] = store.list()
    assert event.id
    assert event.date == date(1815, 6, 18)
    assert event.title == "Battle of Waterloo"


def test_list_is_ordered_by_date():
    store = EventStore(max_events=10)

    store.add(
        [
            candidate(source_statement_id="b", title="Later", date="1900-01-01"),
            candidate(source_statement_id="a", title="Earlier", date="1800-01-01"),
        ]
    )

    assert [event.title for event in store.list()] == ["Earlier", "Later"]


def test_same_statement_id_is_duplicate():
    store = EventStore(max_events=10)
    store.add([candidate()])

    result = store.add([candidate(title="Waterloo", date="1815-06-19")])

    assert (result.added, result.duplicates) == (0, 1)
    assert len(store.list()) == 1


def test_duplicates_within_one_batch_are_detected():
    store = EventStore(max_events=10)

    result = store.add([candidate(), candidate()])

    assert (result.added, result.duplicates) == (1, 1)


def test_fallback_key_applies_without_statement_id():
    store = EventStore(max_events=10)
    store.add([candidate(source_statement_id=None)])

    result = store.add(
        [
            candidate(source_statement_id=None, title="Other title"),
            candidate(source_statement_id=None, date_property="P580", title="Start"),
            candidate(source_statement_id=None, date="1815-06-19", title="Next day"),
        ]
    )

    assert (result.added, result.duplicates) == (2, 1)


def test_same_date_events_are_retained():
    store = EventStore(max_events=10)
    store.add([candidate()])

    result = store.add(
        [candidate(wikidata_id="Q1", source_statement_id="Q1$1", title="Another event")]
    )

    assert (result.added, result.ambiguous) == (1, 0)
    assert result.warnings == []


def test_equal_normalized_titles_on_same_date_warn():
    store = EventStore(max_events=10)
    store.add([candidate()])

    result = store.add(
        [
            candidate(
                wikidata_id="Q1", source_statement_id="Q1$1", title="  battle of  WATERLOO "
            )
        ]
    )

    assert (result.added, result.ambiguous) == (1, 1)
    assert len(result.warnings) == 1
    assert len(store.list()) == 2


def test_equal_titles_on_different_dates_do_not_warn():
    store = EventStore(max_events=10)
    store.add([candidate()])

    result = store.add(
        [candidate(wikidata_id="Q1", source_statement_id="Q1$1", date="1815-06-19")]
    )

    assert (result.added, result.ambiguous) == (1, 0)


def test_limit_rejects_new_events_but_still_counts_duplicates():
    store = EventStore(max_events=2)

    result = store.add(
        [candidate(source_statement_id=str(n), title=f"Event {n}") for n in range(3)]
        + [candidate(source_statement_id="0", title="Event 0")]
    )

    assert (result.added, result.rejected, result.duplicates) == (2, 1, 1)
    assert len(result.warnings) == 1
    assert len(store.list()) == 2


def test_clear_empties_store():
    store = EventStore(max_events=10)
    store.add([candidate()])

    store.clear()

    assert store.list() == []

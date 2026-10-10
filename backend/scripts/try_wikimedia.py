"""Run one live Wikimedia search and print the events it would produce.

From backend/:  uv run python -m scripts.try_wikimedia

Edit the variables below, then run.

SEARCH      which search to run:
              "entities"   name lookup on Wikidata         uses QUERY, LIMIT, LANGUAGE
              "wikipedia"  full-text search on Wikipedia   uses QUERY, LIMIT, LANGUAGE
              "discover"   events in a date range          uses START_DATE, END_DATE, LIMIT,
                                                           EVENT_TYPE, PLACE, PARTICIPANT

QUERY       text to search for            "Battle of Waterloo", "Napoleon", "French Revolution"
            "wikipedia" also takes search operators   'incategory:"Depeche Mode albums"'
LIMIT       max Wikidata entities, 1-50   10
LANGUAGE    Wikipedia language code       "en", "de", "fr"

START_DATE  first day, YYYY-MM-DD         "1815-01-01"
END_DATE    last day, YYYY-MM-DD          "1815-12-31"
EVENT_TYPE  None, or one of: battle, war, siege, treaty, peace treaty, revolution, rebellion,
            coup, massacre, election, coronation, earthquake, volcanic eruption
PLACE       None, a name or a QID         "Japan", "Q17"
PARTICIPANT None, a name or a QID         "France", "Q142"
"""

import asyncio
import sys
from datetime import date

from app.wikimedia.client import WikimediaClient, WikimediaError
from app.wikimedia.search import discover_events, search_entities, search_wikipedia

SEARCH = "wikipedia"

QUERY = 'incategory:"Depeche Mode albums"'
LIMIT = 50
LANGUAGE = "en"

START_DATE = "1815-01-01"
END_DATE = "1815-12-31"
EVENT_TYPE = "battle"
PLACE = None
PARTICIPANT = None


FIELD_NOTES = {
    "wikidata_id": "Wikidata entity the event comes from",
    "source_statement_id": "the exact Wikidata statement holding the date",
    "date_property": "which kind of date: P569 birth, P570 death, P571 inception, "
    "P576 dissolution, P577 release, P580 start, P582 end, P585 point in time",
    "title": "entity name, plus (born)/(start)/... unless the date is a point in time",
    "date": "exact day",
    "description": "short Wikidata description",
    "wikipedia_url": "article in the requested language, or None",
}


async def main() -> None:
    client = WikimediaClient()
    try:
        if SEARCH == "entities":
            print(f"search_entities(query={QUERY!r}, limit={LIMIT}, language={LANGUAGE!r})")
            events, rejected = await search_entities(client, QUERY, LIMIT, LANGUAGE)
        elif SEARCH == "wikipedia":
            print(f"search_wikipedia(query={QUERY!r}, limit={LIMIT}, language={LANGUAGE!r})")
            events, rejected = await search_wikipedia(client, QUERY, LIMIT, LANGUAGE)
        else:
            print(
                f"discover_events(start_date={START_DATE!r}, end_date={END_DATE!r}, "
                f"limit={LIMIT}, event_type={EVENT_TYPE!r}, place={PLACE!r}, "
                f"participant={PARTICIPANT!r})"
            )
            events, rejected = await discover_events(
                client,
                date.fromisoformat(START_DATE),
                date.fromisoformat(END_DATE),
                LIMIT,
                EVENT_TYPE,
                PLACE,
                PARTICIPANT,
            )
    except WikimediaError as error:
        print(f"\nraised WikimediaError: {error}")
        return
    finally:
        await client.close()

    print("\nreturns two values: (events, rejected)")
    print(f"\nevents = list of {len(events)} EventCandidate, each one point on the timeline")
    for number, event in enumerate(sorted(events, key=lambda event: event.date), 1):
        print(f"\n  event {number}")
        for field, value in event.model_dump().items():
            print(f"    {field:<20} {value}")
    print(f"\nrejected = {rejected}")
    print("  date statements found on the same entities but skipped,")
    print("  because they are not an exact day (year only, BCE, unknown, deprecated)")
    print("\nfields")
    for field, note in FIELD_NOTES.items():
        print(f"  {field:<20} {note}")


sys.stdout.reconfigure(encoding="utf-8")
asyncio.run(main())

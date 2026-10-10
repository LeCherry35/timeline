from collections.abc import Iterable
from datetime import date
from uuid import uuid4

from pydantic import BaseModel, Field


class EventCandidate(BaseModel):
    wikidata_id: str = Field(pattern=r"^Q\d+$")
    source_statement_id: str | None = Field(default=None, min_length=1)
    date_property: str = Field(pattern=r"^P\d+$")
    title: str = Field(min_length=1)
    date: date
    description: str = ""
    wikipedia_url: str | None = None


class Event(EventCandidate):
    id: str


class AddResult(BaseModel):
    added: int = 0
    duplicates: int = 0
    ambiguous: int = 0
    rejected: int = 0
    warnings: list[str] = []


def dedup_key(event: EventCandidate) -> tuple:
    if event.source_statement_id:
        return ("statement", event.source_statement_id)
    return ("entity", event.wikidata_id, event.date_property, event.date)


def normalize_title(title: str) -> str:
    return " ".join(title.casefold().split())


class EventStore:
    def __init__(self, max_events: int) -> None:
        self.max_events = max_events
        self._events: dict[tuple, Event] = {}

    def list(self) -> list[Event]:
        return sorted(self._events.values(), key=lambda event: event.date)

    def clear(self) -> None:
        self._events.clear()

    def add(self, candidates: Iterable[EventCandidate]) -> AddResult:
        result = AddResult()
        same_day_titles = {
            (event.date, normalize_title(event.title)) for event in self._events.values()
        }
        for candidate in candidates:
            key = dedup_key(candidate)
            if key in self._events:
                result.duplicates += 1
                continue
            if len(self._events) >= self.max_events:
                result.rejected += 1
                continue
            day_title = (candidate.date, normalize_title(candidate.title))
            if day_title in same_day_titles:
                result.ambiguous += 1
                result.warnings.append(
                    f"Possible duplicate kept: '{candidate.title}' on {candidate.date} "
                    f"({candidate.wikidata_id})."
                )
            same_day_titles.add(day_title)
            self._events[key] = Event(id=uuid4().hex, **candidate.model_dump())
            result.added += 1
        if result.rejected:
            result.warnings.append(
                f"Event limit of {self.max_events} reached; {result.rejected} not added."
            )
        return result

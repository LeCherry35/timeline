from collections.abc import Iterable
from datetime import date
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field


class EventCandidate(BaseModel):
    wikidata_id: str = Field(pattern=r"^Q\d+$")
    source_statement_id: str | None = Field(default=None, min_length=1)
    date_property: str = Field(pattern=r"^P\d+$")
    title: str = Field(min_length=1)
    date: date
    description: str = ""
    wikipedia_url: str | None = None


class Event(EventCandidate):
    model_config = ConfigDict(frozen=True)

    id: str


class AddResult(BaseModel):
    added: int = 0
    duplicates: int = 0
    ambiguous: int = 0
    rejected: int = 0
    warnings: list[str] = []


def fallback_key(event: EventCandidate) -> tuple:
    return (event.wikidata_id, event.date_property, event.date)


def normalize_title(title: str) -> str:
    return " ".join(title.casefold().split())


class EventStore:
    def __init__(self, max_events: int) -> None:
        self.max_events = max_events
        self._events: list[Event] = []
        self._statement_ids: set[str] = set()
        self._fallback_keys: set[tuple] = set()

    def list(self) -> list[Event]:
        return sorted(self._events, key=lambda event: event.date)

    def clear(self) -> None:
        self._events.clear()
        self._statement_ids.clear()
        self._fallback_keys.clear()

    def add(self, candidates: Iterable[EventCandidate]) -> AddResult:
        result = AddResult()
        same_day_titles = {
            (event.date, normalize_title(event.title)) for event in self._events
        }
        for candidate in candidates:
            key = fallback_key(candidate)
            statement_id = candidate.source_statement_id
            if key in self._fallback_keys or statement_id in self._statement_ids:
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
            self._events.append(Event(id=uuid4().hex, **candidate.model_dump()))
            self._fallback_keys.add(key)
            if statement_id:
                self._statement_ids.add(statement_id)
            result.added += 1
        if result.rejected:
            result.warnings.append(
                f"Event limit of {self.max_events} reached; {result.rejected} not added."
            )
        return result

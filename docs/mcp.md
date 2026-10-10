# MCP

The Python backend exposes MCP tools to isolated Claude Code and OpenCode containers. The selected harness and model are configured through environment variables.

Search tools add valid results directly. The agent chooses the search strategy and query but does not review individual results in the prototype.

## Search tools

### `search_wikidata_entities_and_add_events`

Finds named Wikidata entities, fetches their structured date statements, and adds events.

Input:

```text
query
limit
language?
```

Use for named people, places, organizations, and events. Entity search is name lookup, not broad historical research.

### `discover_wikidata_events_and_add`

Discovers events through backend-controlled SPARQL templates and adds them.

Input:

```text
start_date
end_date
event_type?
place?
participant?
limit
```

Use for structured requests such as battles in a period or events involving a country. The backend does not accept unrestricted SPARQL. Public SPARQL failures are returned as warnings.

`event_type` is one of: battle, war, siege, treaty, peace treaty, revolution, rebellion, coup, massacre, election, coronation, earthquake, volcanic eruption. `place` and `participant` take a name or a Wikidata QID; a name resolves to the top entity search result. Discovery matches point-in-time and start-time dates inside the range. A query without filters over a long range can time out.

### `search_wikipedia_and_add_events`

Runs Wikipedia full-text search, resolves pages to Wikidata entities, obtains structured dates from Wikidata, and adds events.

Input:

```text
query
limit
language?
```

Use for broad text topics that entity search cannot resolve. Dates are not extracted from Wikipedia prose.

## State tools

### `get_events`

Returns the complete current event list so the agent can discuss it. Pagination is unnecessary for the prototype limit of about 100 events.

## Search result handling

Each search tool fetches structured Wikidata statements, accepts only exact-day dates, normalizes results, deduplicates them, updates state, and returns counts and warnings.

`limit` counts Wikidata entities, at most 50. One entity can produce several events, such as a start and an end.

Deduplication is deterministic. Events are duplicates when their source statement IDs match, or when their Wikidata ID, date property, and date match. Other same-date events are retained; equal normalized titles are reported as ambiguous. Cross-entity semantic and LLM-based deduplication are deferred.

## Boundaries

Agents decide which tool to call but never modify state directly. The backend owns Wikimedia access, validation, deterministic deduplication, and state changes.

The prototype does not expose separate add, edit, remove, clear, importance, database, shell, unrestricted SPARQL, or generic HTTP tools.

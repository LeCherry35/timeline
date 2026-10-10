# Architecture

```text
Claude Code or OpenCode container
              │ MCP
              ▼
        Python backend
        ├── MCP server
        ├── Wikimedia integration
        ├── deterministic deduplicator
        ├── in-memory event store
        ├── REST API
        └── SSE event stream
              │
              ▼
         React timeline
```

The backend owns Wikimedia access and timeline state. Agent containers do not access state, application files, or Wikimedia directly.

MCP tools and the browser API use the same timeline service. State changes are sent to the browser through Server-Sent Events.

## Search flow

1. The agent selects entity search, structured discovery, or Wikipedia full-text search.
2. The backend resolves results to Wikidata entities and retrieves structured date statements.
3. Results without an exact-day date are rejected.
4. Deterministic deduplication compares source statement IDs, with Wikidata ID, date property, and date as the fallback key.
5. Valid new events are stored and broadcast to the browser.
6. The tool returns counts and warnings; the agent does not review individual results.

Same-date events are only deduplication candidates. Ambiguous candidates are retained because the prototype has no semantic or LLM-based deduplication.

## Browser API

- `GET /api/events` returns the initial event list.
- `GET /api/events/stream` sends state changes.
- `GET /api/health` reports backend health.

## Event

```text
id
wikidata_id
source_statement_id
date_property
title
date
description
wikipedia_url
```

`date` is an exact day in `YYYY-MM-DD` format. `source_statement_id` and `date_property` identify its originating Wikidata statement for deterministic deduplication. Importance and imprecise historical dates are deferred.

The in-memory store is scoped to the current agent session and is discarded when that session ends or the backend restarts.

The vis-timeline data adapter stays separate from the event model so the renderer can later be replaced with Canvas or WebGL.

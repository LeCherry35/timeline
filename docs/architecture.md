# Architecture

```text
Claude Code or OpenCode container
        ▲ chat      │ MCP
        │           ▼
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
4. Deterministic deduplication compares source statement IDs and the key of Wikidata ID, date property, and date; a match on either is a duplicate.
5. Valid new events are stored and broadcast to the browser.
6. The tool returns counts and warnings; the agent does not review individual results.

Same-date events are only deduplication candidates. Ambiguous candidates are retained because the prototype has no semantic or LLM-based deduplication.

## Browser API

- `GET /api/events` returns the initial event list.
- `GET /api/events/stream` sends state changes.
- `GET /api/health` reports backend health.
- `POST /api/chat` sends `{ "message": string }` to the agent and returns `{ "reply": string }`.

## Chat transport

The browser talks only to the backend. The backend forwards each message to the agent container over HTTP on the compose network and returns the whole reply; timeline changes reach the browser through the event stream.

The backend owns the single agent session: it creates one on the first message and reuses it. A backend restart starts a new session.

For OpenCode the backend calls `opencode serve`:

- `GET /global/health`
- `POST /session`
- `POST /session/:id/message` with `{ "parts": [{ "type": "text", "text": string }] }`; the reply is the concatenated text parts of the response.

## Harness runtime contract

A harness container:

- serves its chat API on port `4096`, reachable only on the compose network;
- is configured by `AGENT_HARNESS` (selects `agent/<name>/`), `AGENT_MODEL` (`provider/model`), and that provider's API key variable, so the provider is switched through `.env` alone;
- reaches application capabilities only through the backend MCP server at `http://backend:8000/mcp`.

Adding a harness requires `agent/<name>/` and a backend adapter; the browser API does not change.

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

`date` is an exact day in `YYYY-MM-DD` format. `source_statement_id` and `date_property` identify its originating Wikidata statement for deterministic deduplication; `source_statement_id`, `description`, and `wikipedia_url` are optional. Importance and imprecise historical dates are deferred.

Adding events returns `added`, `duplicates`, `ambiguous`, `rejected`, and `warnings`. Ambiguous events are also counted as added. Events over the limit (`TIMELINE_MAX_EVENTS`, default 100) are rejected.

The in-memory store is scoped to the current agent session and is discarded when that session ends or the backend restarts.

The vis-timeline data adapter stays separate from the event model so the renderer can later be replaced with Canvas or WebGL.

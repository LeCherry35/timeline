# Prototype implementation plan

The repository currently contains documentation only. Implement the prototype in the following order.

## 1. Runtime foundation

- [ ] Define the browser-to-agent chat transport and initial harness runtime contract.
- [ ] Scaffold the Python backend with FastAPI, settings, tests, and dependency management.
- [ ] Scaffold the React/Vite frontend with TypeScript and Vitest.
- [ ] Add local container configuration for the backend, frontend, and one agent harness.

## 2. Event domain

- [ ] Implement the event model, including Wikidata entity and source statement IDs.
- [ ] Implement the in-memory event store and approximately 100-event limit.
- [ ] Implement deterministic deduplication by source statement, with entity, date property, and date as the fallback key.
- [ ] Retain other same-date events and warn on equal normalized titles.
- [ ] Test validation, insertion, limits, and deduplication.

## 3. Wikimedia integration

- [ ] Implement a shared Wikimedia HTTP client with a descriptive user agent, timeouts, throttling handling, and bounded retries.
- [ ] Implement Wikidata entity search and structured statement retrieval.
- [ ] Implement event discovery with allowlisted SPARQL templates and filters.
- [ ] Implement Wikipedia full-text search and Wikidata QID resolution.
- [ ] Normalize exact-day dates, titles, descriptions, sitelinks, and source statement IDs.
- [ ] Test clients with recorded or mocked Wikimedia responses.

## 4. Timeline service and MCP

- [ ] Implement one timeline service shared by MCP and browser APIs.
- [ ] Implement `search_wikidata_entities_and_add_events`.
- [ ] Implement `discover_wikidata_events_and_add`.
- [ ] Implement `search_wikipedia_and_add_events`.
- [ ] Implement `get_events`.
- [ ] Return added, rejected, duplicate, and ambiguous counts with warnings.
- [ ] Add MCP integration tests covering search-to-state flows.

## 5. Browser API

- [ ] Implement health and initial event-list endpoints.
- [ ] Implement SSE snapshots or state-change events with reconnect handling.
- [ ] Connect the browser-to-agent chat transport selected in step 1.
- [ ] Test REST, SSE, and chat boundaries.

## 6. Frontend

- [ ] Implement the chat interface and connection status.
- [ ] Implement event state loading and SSE synchronization.
- [ ] Implement the vis-timeline adapter and renderer.
- [ ] Show event details on hover and open Wikipedia on click.
- [ ] Display backend and search warnings without requiring result review.
- [ ] Add component and state synchronization tests.

## 7. Agent runtime

- [ ] Configure one harness and model through environment variables.
- [ ] Restrict the agent container to the MCP tools and required chat transport.
- [ ] Add instructions for selecting among entity, structured, and full-text search.
- [ ] Verify that the agent can search for and discuss events.
- [ ] Add the second harness only after the end-to-end flow works.

## 8. End-to-end verification

- [ ] Start the complete local stack from one documented command.
- [ ] Verify named-entity, period/type, and broad-topic searches.
- [ ] Verify duplicate imports, ambiguous same-date events, session reset, and SSE updates.
- [ ] Verify Wikimedia timeout, throttling, malformed-data, and SPARQL failure behavior.
- [ ] Run backend tests, frontend tests, type checks, and production builds.

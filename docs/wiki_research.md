# Wikimedia data research

## Recommended approach

Use **Wikidata** as the primary source for structured historical facts and dates. Use **Wikipedia** for readable descriptions and article content.

### Wikidata

Wikidata contains people, countries, events, places, relationships, and structured dates. Every entity has a stable ID such as `Q42`, which should be stored instead of relying on names.

Useful APIs:

- Entity search: `https://www.wikidata.org/w/api.php?action=wbsearchentities&search=Napoleon&language=en&format=json`
- Entity JSON: `https://www.wikidata.org/wiki/Special:EntityData/Q517.json`
- Wikibase REST API: `https://www.wikidata.org/w/rest.php/wikibase/v1/entities/items/Q517`
- SPARQL queries: `https://query.wikidata.org/sparql`

Common date properties:

- `P569` — date of birth
- `P570` — date of death
- `P571` — inception
- `P576` — dissolution
- `P580` — start time
- `P582` — end time
- `P585` — point in time
- `P1319` — earliest possible date
- `P1326` — latest possible date

Historical dates must retain their precision and calendar. A value represented as `1500-01-01` may mean only “the year 1500,” not January 1. The application should support approximate dates, ranges, BCE dates, conflicting statements, Julian/Gregorian calendars, and year- or century-only precision.

Use SPARQL for background discovery, such as finding all battles in a period or all rulers of a country. Do not depend on the public SPARQL service for synchronous user requests because it can be slow, throttled, or temporarily unavailable.

### Wikipedia

After identifying an entity through Wikidata, follow its Wikipedia sitelink to obtain narrative content.

Useful APIs:

- MediaWiki REST API: `https://en.wikipedia.org/w/rest.php/v1/page/Napoleon_Bonaparte/html`
- MediaWiki Action API: `https://en.wikipedia.org/w/api.php`

The REST API provides page content and HTML. The Action API supports search, extracts, categories, links, and revision metadata. Avoid extracting dates from prose or infobox HTML when a structured Wikidata statement exists.

## Search strategies

- Wikidata entity search resolves named subjects but does not answer broad historical questions.
- Backend-controlled SPARQL templates discover events by period, type, place, or participant. The public service may be slow, throttled, or unavailable.
- Wikipedia full-text search finds topical pages. Results must be resolved to Wikidata entities; dates are not extracted from prose.

## Prototype import flow

1. Select entity search, structured discovery, or Wikipedia full-text search.
2. Resolve results to Wikidata QIDs.
3. Fetch structured statements and exact-day dates.
4. Normalize events while preserving source statement identity.
5. Deduplicate on matching source statement IDs or on matching entity, date property, and date.
6. Retain other same-date events and warn when their normalized titles match.
7. Follow Wikipedia sitelinks for readable descriptions.
8. Add valid events directly; the agent does not review individual results.

Semantic deduplication, imprecise dates, caching, and asynchronous discovery are deferred.

For millions of records, use the weekly Wikidata JSON dumps instead of making individual API requests.

## Licensing and API requirements

- Wikidata structured data is available under CC0.
- Wikipedia text generally uses CC BY-SA 4.0 and requires attribution and license compliance.
- Wikimedia Commons files may each have different licenses.
- Send a descriptive `User-Agent` containing the application name and contact information.
- Cache responses and respect rate limits, `429`, `Retry-After`, and service-lag responses.
- Keep references because community-maintained facts can be incomplete or conflicting.

## Official documentation

- [Wikidata data access](https://www.wikidata.org/wiki/Wikidata:Data_access/en)
- [Wikidata dates](https://www.wikidata.org/wiki/Help:Dates)
- [Wikidata REST API](https://www.wikidata.org/wiki/Wikidata:REST_API)
- [MediaWiki REST API](https://www.mediawiki.org/wiki/API:REST_API)
- [MediaWiki Action API](https://www.mediawiki.org/wiki/API:Action_API/en)
- [Wikimedia API usage guidelines](https://foundation.wikimedia.org/wiki/Policy:Wikimedia_Foundation_API_Usage_Guidelines/en)

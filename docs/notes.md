# Deferred

- Support BCE dates. The event model uses Python `date`, which starts at year 1, so earlier dates fail validation.
- Convert Julian-calendar dates. Dates are kept as Wikidata states them and the calendar model is ignored.
- Use Wikipedia article extracts as descriptions. Events carry the short Wikidata description.
- Read dates from statement qualifiers, such as the start of a held position.
- Add event removal and list-clearing tools after the agent can reliably select events. The prototype only fills the list; starting a new agent session creates an empty list.

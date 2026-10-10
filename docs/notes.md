# Deferred

- Support BCE dates. The event model uses Python `date`, which starts at year 1, so earlier dates fail validation.
- Add event removal and list-clearing tools after the agent can reliably select events. The prototype only fills the list; starting a new agent session creates an empty list.

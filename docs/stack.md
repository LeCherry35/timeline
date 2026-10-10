# Stack

## Frontend

- React with TypeScript
- Vite
- vis-timeline
- Plain CSS or CSS Modules
- Native `fetch` and `EventSource`
- Vitest

Use vis-timeline for the prototype. Keep it behind a renderer component and consider migration to Canvas or WebGL as soon as event volume or historical range requires it.

## Backend

- Python
- FastAPI
- Pydantic
- httpx
- pydantic-settings
- uv
- pytest

The MVP uses in-memory state. It has no database, authentication, task queue, or Redis.

## AI

- Claude Code and OpenCode as interchangeable agent harnesses
- Agent and model selected through environment variables
- Agents run in isolated containers and access application capabilities through MCP

## Runtime

The MVP runs locally as a React frontend, Python backend, and one selected agent container.

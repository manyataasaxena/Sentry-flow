# SentryFlow

## Project Overview

SentryFlow is an agent-orchestration control plane with a React dashboard and a FastAPI backend. It provides a LangGraph-based run pipeline, tool execution adapters, verification and guardrails, and a deterministic adversarial regression suite. The default LLM implementation is a deterministic mock.

## Architecture

The backend follows a hexagonal structure: API and database adapters call inward to agent orchestration, core services, and schema contracts. The React/Vite client calls the versioned API.

```text
┌──────────────────────────────────┐
│ React 19 + Vite dashboard        │
│ Overview · Runs · Tools · System │
│ Evals                            │
└────────────────┬─────────────────┘
                 │ HTTP / WebSocket
┌────────────────▼─────────────────┐
│ FastAPI API adapters              │
│ runs · tools · evals · system     │
└────────────────┬─────────────────┘
                 │
┌────────────────▼─────────────────┐
│ Agent application                 │
│ intake → planner → approval gate  │
│ → worker → finalize → verifier    │
└────────┬───────────────────┬─────┘
         │                   │
┌────────▼─────────┐  ┌──────▼────────────┐
│ Core / schemas   │  │ Adapters          │
│ config, contracts│  │ PostgreSQL, Redis │
│ guardrails       │  │ mock tool runtime │
└──────────────────┘  └───────────────────┘
```

## Features

- Operations dashboard with overview, run history and details, tool registry, circuit-breaker status, and Evals views.
- FastAPI endpoints for runs, tools, evaluation reports, system status, audit, and WebSocket run events.
- LangGraph run pipeline with intake classification, planning, approval gate, worker, verifier, and final-answer stages.
- Calculator, database-backed knowledge-base lookup, and deterministic/mock implementations for web search, HTTP fetch, and webhook execution.
- Deterministic intake and output checks for prompt attacks, SSRF targets, PII, and API-key patterns.
- PostgreSQL persistence and checkpoint integration, plus Redis connectivity.
- A 36-case, self-authored adversarial regression suite with API reporting and a dashboard view.

## Tech Stack

- **Backend:** Python 3.12+, FastAPI, Pydantic v2, LangGraph, SQLAlchemy, Psycopg, Redis client, PyYAML.
- **Frontend:** React 19, TypeScript, Vite, Tailwind CSS, shadcn/ui, Lucide.
- **Data services:** PostgreSQL 16 and Redis 7.
- **Observability:** Langfuse integration surface; tracing is currently log-only.
- **Containers:** Docker, Docker Compose, nginx.

## Installation

### Local development

Prerequisites: Python 3.12 or newer, Node.js, pnpm, PostgreSQL, and Redis.

1. Copy `.env.example` to `.env` and adjust the service URLs if needed. The example uses the Compose-mapped PostgreSQL port `5433` and Redis port `6379`.
2. Install the backend package and development tools:

   ```bash
   python -m pip install -e "backend[dev]"
   ```

3. Start the backend from the repository root:

   ```bash
   PYTHONPATH=backend uvicorn app.main:app --reload
   ```

4. In another terminal, install and start the frontend:

   ```bash
   pnpm install --frozen-lockfile
   pnpm dev
   ```

   The frontend API base defaults to `http://127.0.0.1:8000/api/v1`. Set `VITE_API_URL` before the Vite build or in the frontend environment to override it.

### Docker Compose

Copy `.env.example` to `.env` if you want to customize build-time `VITE_API_URL`, then build and start the stack:

```bash
docker compose up --build
```

The dashboard is served at `http://localhost:8080`, the API at `http://localhost:8000`, PostgreSQL is exposed on host port `5433`, and Redis on `6379`. PostgreSQL data is stored in the named `postgres_data` volume. Compose waits for PostgreSQL and Redis health checks before starting the backend.

## Screenshots

<!-- Screenshot placeholder: add a dashboard screenshot here. -->

![Dashboard screenshot placeholder](docs/screenshots/dashboard-placeholder.png)

<!-- Screenshot placeholder: add an Evals screenshot here. -->

![Evals screenshot placeholder](docs/screenshots/evals-placeholder.png)

## Testing

Run these from the repository root:

```bash
ruff check backend/app backend/tests
mypy --strict --config-file backend/pyproject.toml backend/app
pytest backend/tests
```

## Known Limitations

- Runs are stored in memory and lost on restart.
- `approval_gate` auto-approves (no human pause yet).
- LLM is a deterministic `FakeLLM` (real providers not wired).
- Langfuse tracing is log-only.
- The adversarial suite is 36 self-authored cases (regression tests, not real-world accuracy).

## Future Work

- Add durable run and evaluation-report storage.
- Add an explicit human approval and resume flow.
- Wire real LLM providers and production-grade tracing.
- Expand the adversarial corpus using reviewed, representative attack data.
- Add end-to-end deployment and service-level health monitoring.

## License

MIT. See [LICENSE](LICENSE) for the license text.

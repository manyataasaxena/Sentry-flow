# SentryFlow — Standing Rules for the AI Agent

You are the Lead Systems Architect and Senior AI Systems Engineer for SentryFlow, a
production-grade multi-agent platform (LangGraph Planner-Worker-Verifier, FastAPI, Next.js / Vite React,
Redis, PostgreSQL, Langfuse). Follow a modular Hexagonal Architecture.

## Non-negotiable rules
1. All backend logic lives in `backend/app/` following the documented structure. Never create files outside it.
   Entry point is `backend/app/main.py`.
2. Python 3.12. Every function has full type hints. All data structures are Pydantic v2 models
   (frozen, extra="forbid"). No raw dicts or Any in signatures.
3. Async first: all API handlers, DB/Redis/HTTP/LLM calls, and agent nodes are async.
4. Every agent node, tool execution, and LLM call is decorated with Langfuse `@observe(name=...)`.
5. Every external call goes through `resilient_call()` (typed try/except + circuit breaker +
   retry on transient errors only + fallback). No bare `except`.
6. All LLM output is enforced with Instructor `response_model=<PydanticModel>`. Never parse free text.
7. Dependencies point inward: schemas ← core ← agents; adapters (db, llm gateway, tool providers)
   implement `core/ports.py` Protocols. `agents/` never imports `db/`, `api/`, or vendor SDKs.
8. Config only via `core/config.py` Settings. Never read `os.environ` elsewhere. Never log secrets.
9. LangGraph uses `AsyncPostgresSaver` (psycopg pool with autocommit=True, prepare_threshold=0,
   row_factory=dict_row; call `setup()` once in FastAPI lifespan). `thread_id == run_id`.
10. The whole system must run with `MOCK_LLM=true` (FakeLLM) and zero API keys.
11. Frontend: React 19 / TypeScript strict, Tailwind CSS, shadcn/ui, React Flow (@xyflow/react),
    Framer Motion / Lucide, TanStack Query. API types match OpenAPI schema.
12. Work strictly phase by phase. After each phase, list files created and how to verify,
    then wait for approval before continuing.

## Change-control rules (apply to every edit after the initial build)
13. Before editing, declare scope: files you WILL touch, files you will NOT touch, and their zone.
14. Frozen contracts (`schemas/*`, `core/ports.py`, `api.gen.ts`) are additive-only. Security-critical
    files (`guardrails.py`, `verifier.py`, `resilience.py`, `circuit_breaker.py`, `tests/adversarial/*`)
    are never weakened. If a change needs one of these, STOP and ask.
15. Prefer adding a new file behind an existing port (new tool, new adapter, new feature folder)
    over modifying existing files. One concern per change; no drive-by refactors, renames, or upgrades.
16. Never edit a test or lower a threshold to make it pass. Never hand-edit generated files.
17. Prompts live only in `agents/prompts/*.md` with versioned filenames.
18. Frontend: routes are thin; logic lives in `features/<name>/` and `components/`;
    colors/radii come from tokens; only API and WS clients touch the network.
19. After every change, verify types and tests, paste the results, and maintain clean commits.

## Tech Stack & UI Conventions
- You are building a React + TypeScript application with Tailwind CSS and shadcn/ui.
- Put pages in src/pages/ and components in src/components/.
- The main page is src/pages/Index.tsx.
- Keep routes in src/App.tsx.

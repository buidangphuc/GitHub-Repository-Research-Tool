# Implementation Plan: GitHub Repository Research Tool

**Branch**: `[001-github-repo-research]` | **Date**: 2026-04-18 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-github-repo-research/spec.md`

## Summary

Build a compact event-driven repository research demo inside the existing
FastAPI codebase. FastAPI will act as the API gateway and UI host: it accepts a
repository URL, generates a `job_id`, enqueues a Celery task through Redis, and
returns immediately so the browser can render a dashboard shell and begin short
polling. Redis will serve both as Celery broker and short-lived job-state
cache. Celery workers will run in a separate container but reuse the same
Python codebase, pulling tasks from Redis to call GitHub GraphQL, run a fast
LLM model, and persist final results to the primary database. Docker Compose
will bundle the app, worker, Redis, and database into one demo-ready startup
flow.

## Existing Asset Review

- `main.py` and `core/registrar.py`: extend application registration without
  creating a second FastAPI app or a separate frontend runtime.
- `app/router.py`: extend the router aggregation to include research endpoints
  while preserving the current feature-based layout.
- `app/task/celery.py`, `app/task/conf.py`, `app/task/service/task_service.py`,
  `app/task/celery_task/base.py`, and `app/task/celery_task/tasks.py`: reuse
  the current Celery bootstrap and task infrastructure instead of creating a
  second worker framework.
- `database/redis.py`: reuse the existing async Redis client for both job-state
  cache access and broker-adjacent state flows.
- `docker-compose.yaml` and `docker-compose.local.yaml`: simplify and adapt the
  existing compose assets to run app, worker, Redis, and a demo database in one
  command.
- `core/conf.py`: extend settings for Redis-backed job state, GraphQL token,
  polling interval, AI provider controls, and database mode.
- `common/exception/exception_handler.py`, `common/response/response_schema.py`,
  `middleware/request_id_middleware.py`, and `common/log.py`: reuse existing
  API error handling, request correlation, and structured logging.
- New files are justified inside `app/research/`, `app/task/celery_task/`, and
  `tests/research/` because no current namespace owns repository research jobs,
  stored research results, or polling-specific view composition.

## Technical Context

**Language/Version**: Python 3.10+  
**Primary Dependencies**: FastAPI, Celery, Redis, SQLAlchemy, Jinja2, Pydantic
v2, httpx, GitHub GraphQL over HTTP POST, OpenAI-compatible fast LLM client  
**Storage**: Redis for broker and job-state cache; PostgreSQL as the default
Docker Compose demo database; SQLite as an optional local non-container
fallback  
**Testing**: pytest, pytest-asyncio, FastAPI route tests, Celery task tests,
state-transition tests, mocked GraphQL and LLM provider tests  
**Target Platform**: Docker Compose deployment with app, worker, Redis, and DB
containers; macOS or Linux local development  
**Project Type**: Feature-based FastAPI monolith with event-driven background
execution  
**Performance Goals**: accept valid jobs within 1 second, render warm-cache
instant overview data within 500 milliseconds when available, and reach a
terminal state within 30 seconds for typical demo repositories  
**Constraints**: keep GitHub and LLM I/O asynchronous where possible; use
Redis as the only broker; use short polling at a default 2-second interval;
validate all cross-stage payloads with Pydantic; expose research APIs in
Swagger UI; reuse the existing task infrastructure before introducing any new
orchestration layer  
**Scale/Scope**: one repository per job, demo-focused worker scale, one primary
database, and no WebSocket or SSE channel in v1

## Constitution Check

*GATE: Passed before Phase 0 research. Re-check after Phase 1 design.*

### Initial Gate Review

- **Existing Assets First**: PASS. The plan extends the current FastAPI router,
  Celery app, Redis utility, and Docker Compose assets rather than creating a
  parallel queue or deployment stack.
- **Reusable Service Architecture**: PASS. The design separates gateway,
  GraphQL ingestion, AI analysis, persistence, job-state handling, and UI view
  composition into focused services.
- **Integration-First Data Contracts**: PASS. Input, job-state, GraphQL,
  processing, AI, persistence, and UI payloads are validated by Pydantic before
  crossing subsystem boundaries.
- **Scalability by Design**: PASS. Gateway and worker roles are separated,
  Redis centralizes short-lived state, and Celery workers can be scaled later
  without rewriting the UI or request contract.
- **Pattern Discipline and Low Coupling**: PASS. Existing task primitives are
  reused, and background execution is introduced only where it directly reduces
  UX blocking and coupling.
- **Operational Reliability and Observability**: PASS. State transitions are
  explicit across submission, queueing, running, completion, failure, caching,
  and persistence, with request-id-linked logs.

### Post-Design Re-Check

- PASS. The design stays inside the current repository structure, reuses task
  infrastructure, and keeps worker, gateway, and UI concerns separated while
  remaining demo-friendly.

## Project Structure

### Documentation (this feature)

```text
specs/001-github-repo-research/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── research-web.openapi.yaml
└── tasks.md
```

### Source Code (repository root)

```text
app/
├── router.py
├── admin/
├── task/
│   ├── api/
│   ├── celery.py
│   ├── celery_task/
│   │   ├── base.py
│   │   └── research_jobs.py
│   └── service/
└── research/
    ├── __init__.py
    ├── api/
    │   ├── __init__.py
    │   ├── router.py
    │   └── v1/
    │       ├── __init__.py
    │       └── research.py
    ├── schema/
    │   ├── job.py
    │   ├── github.py
    │   ├── report.py
    │   └── status.py
    ├── model/
    │   ├── research_job.py
    │   └── research_result.py
    ├── crud/
    │   ├── crud_research_job.py
    │   └── crud_research_result.py
    ├── service/
    │   ├── research_gateway_service.py
    │   ├── research_status_service.py
    │   ├── github_graphql_service.py
    │   ├── ai_analysis_service.py
    │   └── research_result_service.py
    └── templates/
        └── research/
            └── index.html

core/
├── conf.py
└── registrar.py

database/
├── db.py
└── redis.py

docker-compose.yaml

tests/
└── research/
    ├── test_research_page.py
    ├── test_research_api.py
    ├── test_research_status_service.py
    ├── test_github_graphql_service.py
    ├── test_ai_analysis_service.py
    └── test_research_jobs.py
```

**Structure Decision**: Keep the feature inside the current FastAPI monolith.
Place HTTP and view orchestration in `app/research/`, reuse the existing
`app/task/celery_task/` package for background execution, and introduce
research-specific model and CRUD modules only where final result storage is
required. Reuse `database/redis.py` for job-state cache access and keep Docker
Compose as the main demo bootstrap path.

## Delivery Outline

1. Extend configuration, routing, and Compose setup so the app, worker, Redis,
   and demo database can run together with one startup flow.
2. Build strict Pydantic schemas for job submission, job status, GraphQL
   payloads, processing context, AI output, stored results, and UI view state.
3. Implement FastAPI research endpoints for page rendering, job submission, and
   status polling with Swagger-visible JSON contracts.
4. Implement Redis-backed job state management and connect submission flow to
   the existing Celery app using Redis as broker.
5. Implement a research-specific Celery task under the current task package to
   perform GraphQL ingestion, AI analysis, and result persistence.
6. Implement GitHub GraphQL and AI services optimized for fast demo execution,
   including bounded README and structure handling.
7. Implement result persistence using PostgreSQL in Compose mode with a clear
   SQLite fallback path for local non-container runs.
8. Render the Jinja2 dashboard with instant metrics, AI skeletons, and
  short-polling upgrades from `pending` or `processing` to `completed` or
   `failed`.
9. Add route, worker, state-transition, and failure-path tests covering job
   acceptance, polling, provider errors, worker failure, and stored result
   retrieval.

## Complexity Tracking

No constitution exceptions or complexity waivers are required for this plan.

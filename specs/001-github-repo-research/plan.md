# Implementation Plan: [FEATURE]

**Branch**: `001-github-repo-research` | **Date**: 2026-04-19 | **Spec**: [specs/001-github-repo-research/spec.md](specs/001-github-repo-research/spec.md)
**Input**: Feature specification from `/specs/001-github-repo-research/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/plan-template.md` for the execution workflow.

## Summary

[Describe the user-facing capability, the integration paths it touches, the
shared services or contracts it extends, which existing repository assets it
reuses first, and how the change reduces duplication while improving
integratability, reliability, or scale.]

## Existing Asset Review

[List the existing files, directories, scripts, and operational assets reviewed
for reuse. Explain which ones will be extended and justify each new file,
directory, or workflow that must be introduced.]

## Technical Context

<!--
  ACTION REQUIRED: Replace the content in this section with the technical details
  for the project. The structure here is presented in advisory capacity to guide
  the iteration process.
-->

**Language/Version**: Python 3.12+  
**Primary Dependencies**: FastAPI, Pydantic v2, SQLAlchemy, Redis, aiobotocore, boto3, httpx, pytest  
**Queue Transport**: SQS-compatible — ElasticMQ (`softwaremill/elasticmq-native`) in local/Compose, AWS SQS in production  
**Storage**: PostgreSQL (Compose) / SQLite (local fallback) for persistence; Redis for job-state cache and AI-result caching  
**Testing**: pytest, pytest-asyncio, API tests, contract tests, and regression checks for reused modules; moto for in-process SQS unit tests  
**Target Platform**: Server-side Python service on macOS/Linux with Docker Compose  
**Project Type**: Feature-based FastAPI backend service  
**Performance Goals**: Keep latency predictable while allowing more traffic, deeper workflows, and new integrations without rewriting core flows  
**Constraints**: Extend existing `app/`, `common/`, `core/`, `database/`, `middleware/`, `socketio/`, `utils/`, and `scripts/` assets before creating new modules; keep I/O async where it already is; forbid duplicate business logic; Celery is removed — all queue and worker logic must go through the `IMessageQueue` port and the async SQS polling worker  
**Scale/Scope**: Prefer localized changes inside existing feature packages and shared infrastructure; any new top-level package requires explicit justification

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Existing Assets First**: Does the plan list the current files,
  directories, scripts, and infrastructure it will extend, and justify every
  new module or workflow it introduces?
- **Reusable Service Architecture**: Does the design extend shared services,
  adapters, or abstractions instead of introducing duplicated function logic?
- **Integration-First Data Contracts**: Do all external payloads enter through
  adapters and map once into canonical internal contracts?
- **Scalability by Design**: Are statelessness, async I/O, concurrency limits,
  and isolation of expensive work explicitly addressed?
- **Pattern Discipline and Low Coupling**: Are chosen patterns justified by
  reduced duplication or coupling rather than ceremony?
- **Operational Reliability and Observability**: Are failure points explicit
  across fetch, validate, map, orchestrate, analyze, and render stages?

## Project Structure

### Documentation (this feature)

```text
specs/001-github-repo-research/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)
<!--
  ACTION REQUIRED: Replace the placeholder tree below with the concrete layout
  for this feature. Delete unused options and expand the chosen structure with
  real paths (e.g., apps/admin, packages/something). The delivered plan must
  not include Option labels.
-->

```text
app/
├── router.py
├── admin/
│   ├── api/v1/
│   ├── crud/
│   ├── model/
│   ├── schema/
│   └── service/
├── research/                        # feature package (new)
│   ├── api/v1/                      # FastAPI routes: POST /research, GET /research/{job_id}
│   ├── crud/                        # DB access for ResearchJobRecord + FinalResearchReport
│   ├── model/                       # SQLAlchemy ORM models
│   ├── schema/                      # Pydantic contracts (all boundary types)
│   ├── service/                     # Orchestration + AI analysis services
│   ├── ports/                       # IMessageQueue, IStateCache, IGitHubClient, ILLMClient
│   ├── adapters/                    # SQS adapter (aiobotocore), Redis adapter, GitHub adapter, LLM adapter
│   └── worker/
│       └── sqs_worker.py            # Async long-poll loop: receive → validate → pipeline → delete/DLQ
└── task/                            # Existing task package (unchanged)

common/
core/
database/
middleware/
socketio/
utils/
scripts/
tests/
  └── research/                      # Unit + integration tests (mock SQS via moto or ElasticMQ)
```

**Structure Decision**: Use the repository's existing FastAPI layout. The `app/research/` package is introduced as a new feature package because no existing package owns GitHub-research or LLM-inference responsibilities. The `app/task/` package is **not** extended because its Celery task-runner model is replaced by the explicit SQS polling worker (`app/research/worker/sqs_worker.py`). Queue, cache, GitHub API, and LLM interactions are all hidden behind port interfaces in `app/research/ports/` with adapter implementations in `app/research/adapters/`. Shared response envelopes, JWT middleware, and core configuration are reused without modification.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., New abstraction layer] | [current need] | [why extending the existing shared service was insufficient] |
| [e.g., Queue/cache boundary] | [specific scaling problem] | [why inline synchronous orchestration was insufficient] |

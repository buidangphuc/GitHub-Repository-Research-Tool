# Tasks: AI-Native GitHub Repository Research Tool

**Input**: Design documents from `/specs/001-github-repo-research/`
**Prerequisites**: plan.md ✅ | spec.md ✅ | research.md ✅ | data-model.md ✅ | contracts/research-web.openapi.yaml ✅ | quickstart.md ✅

**Queue Transport**: SQS / ElasticMQ (Celery removed — all background work via async SQS polling worker)  
**Architecture**: Ports and Adapters — domain logic never imports infrastructure libraries directly

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project structure, environment, and Docker Compose initialization

- [X] T001 Review existing assets (`app/`, `common/`, `core/`, `database/`, `middleware/`, `utils/`, `scripts/`) and record extension points per `specs/001-github-repo-research/plan.md` asset review
- [X] T002 Create `app/research/` feature package skeleton: `__init__.py` in `api/v1/`, `crud/`, `model/`, `schema/`, `service/`, `ports/`, `adapters/`, `worker/` per plan.md project structure tree
- [X] T003 [P] Add `aiobotocore`, `boto3`, `moto[sqs]`, `jinja2`, `httpx` to `requirements.txt` (remove `celery` entry if present)
- [X] T004 [P] Add `elasticmq` service (`softwaremill/elasticmq-native`, port `9324`) to `docker-compose.yaml`; keep existing Redis and PostgreSQL services unchanged
- [X] T005 [P] Add `SQS_ENDPOINT_URL`, `SQS_QUEUE_URL`, `SQS_DLQ_URL`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `GITHUB_TOKEN`, `OPENAI_API_KEY` (optional) to `core/conf.py` settings and `.env.example`
- [X] T006 [P] Add `research-worker` service to `docker-compose.yaml` running `python -m app.research.worker.sqs_worker`; share the app image, pass the same env vars

**Checkpoint**: `docker compose up` starts FastAPI, ElasticMQ, Redis, PostgreSQL, and the research-worker container

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Port interfaces, adapters, Pydantic contracts, DB models, and SQS worker skeleton — MUST complete before any user story

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T007 Define port interfaces `IMessageQueue`, `IStateCache`, `IGitHubClient`, `ILLMClient` as abstract base classes in `app/research/ports/__init__.py`; document method signatures and error contracts for each
- [X] T008 [P] Define all Pydantic v2 boundary schemas in `app/research/schema/`: `ResearchRequest`, `JobAcceptedResponse`, `PollingStatusResponse`, `ParsedRepoTarget`, `InstantMetadata`, `ResearchJobMessage`, `StructuredAIResponse`, `ResearchReport`, `ResearchJobStateSnapshot` — mapped 1:1 to `contracts/research-web.openapi.yaml` and `data-model.md`
- [X] T009 [P] Implement SQLAlchemy ORM models `ResearchJobRecord` and `FinalResearchReportRecord` in `app/research/model/research.py`; add Alembic migration in `alembic/versions/` for both tables
- [X] T010 [P] Implement `SQSMessageQueueAdapter` in `app/research/adapters/sqs_adapter.py` using `aiobotocore`; implements `IMessageQueue.send()`, `receive()`, `delete()`, `change_visibility()`; reads `SQS_ENDPOINT_URL` and `SQS_QUEUE_URL` from settings
- [X] T011 [P] Implement `RedisStateCacheAdapter` in `app/research/adapters/redis_adapter.py` using the existing `database/redis.py` client; implements `IStateCache.set_state()`, `get_state()`, `delete_state()`; serialises snapshots as JSON
- [X] T012 Add queue and DLQ provisioning to `app/research/adapters/sqs_adapter.py`: on startup create `research-jobs` queue and `research-jobs-dlq` if absent; set `VisibilityTimeout=120` and `maxReceiveCount=3` DLQ policy
- [X] T013 [P] Implement CRUD helpers in `app/research/crud/crud_research.py`: `create_job_record()`, `update_job_status()`, `save_final_report()`, `get_job_by_id()` — all use async SQLAlchemy session
- [X] T014 Implement async SQS polling worker skeleton in `app/research/worker/sqs_worker.py`: `async def run_worker()` long-polls the queue, deserialises each body into `ResearchJobMessage`, dispatches to `execute_research_pipeline()`, deletes message on success, abandons to DLQ after `max_attempts` exceeded; runnable via `python -m app.research.worker.sqs_worker`
- [X] T015 [P] Wire dependency injection in `app/research/dependencies.py`: resolve `IMessageQueue → SQSMessageQueueAdapter`, `IStateCache → RedisStateCacheAdapter` from settings; expose FastAPI `Depends()` callables
- [X] T016 [P] Implement adapter conformance tests in `tests/research/test_adapter_conformance.py` using `moto[sqs]` for in-process SQS mocking; assert each adapter satisfies its port contract
- [X] T017 [P] Extend structured logging in `common/log.py` to include `request_id`, `job_id`, `stage`, `latency_ms`, `failure_reason` fields; extend `middleware/request_id_middleware.py` if needed

**Checkpoint**: Ports, adapters, schemas, DB models, and worker loop in place; adapter tests pass with moto mock

---

## Phase 3: User Story 1 — AI-Assisted Repository Semantic Overview (Priority: P1) 🎯 MVP

**Goal**: User submits a valid public GitHub repository URL, immediately receives a `job_id` with `pending` status, and within 30 seconds receives a complete report combining deterministic GitHub facts and AI-generated semantic summary.

**Independent Test**: Submit `https://github.com/tiangolo/fastapi` via `POST /api/v1/research/jobs`; verify `202` + `job_id`; poll `GET /api/v1/research/jobs/{job_id}` until `completed`; assert `deterministic_data` and `ai_insights` are both non-null and structurally valid per `StructuredAIResponse`.

### Implementation for User Story 1

- [X] T018 [P] [US1] Implement `GitHubGraphQLAdapter` in `app/research/adapters/github_adapter.py` implementing `IGitHubClient`; executes a single GraphQL v4 query for `name`, `description`, `stargazerCount`, `forkCount`, `primaryLanguage`, `pushedAt`, top-level tree (≤100 entries), and README blob; maps to `InstantMetadata` and `RepositoryRawContext`
- [X] T019 [P] [US1] Implement URL validation and `ParsedRepoTarget` extraction in `app/research/service/url_validator.py`; rejects malformed, gist, org-profile, and branch-tree URLs; raises `HTTPException(400)` with RFC 7807 `application/problem+json` body via `common/exception/errors.py`
- [X] T020 [US1] Implement `ResearchOrchestrationService.submit()` in `app/research/service/orchestration.py`: validate URL → parse target → generate UUID `job_id` → persist `ResearchJobRecord(status=pending)` via CRUD → write pending state to Redis via `IStateCache` → enqueue `ResearchJobMessage` via `IMessageQueue`; return `JobAcceptedResponse`
- [X] T021 [P] [US1] Implement `POST /api/v1/research/jobs` in `app/research/api/v1/research_router.py`; call `ResearchOrchestrationService.submit()`; return `202 JobAcceptedResponse`; register in `app/research/api/v1/__init__.py` and `app/router.py`
- [X] T022 [P] [US1] Implement context sanitization and token-budget truncation in `app/research/service/context_sanitizer.py`: strip `node_modules`, `.git`, binary/image paths; truncate README and manifest to `MAX_CONTEXT_TOKENS` (default 32 000) by character estimation; record each truncation as a `PartialAnalysisWarning`; return `LLMPromptPayload`
- [X] T023 [P] [US1] Implement `LLMAdapter` in `app/research/adapters/llm_adapter.py` implementing `ILLMClient`; construct a system prompt treating repository content as untrusted data and requesting structured JSON; call configured provider (OpenAI-compatible or Gemini); parse and validate response against `StructuredAIResponse`; raise `LLMUnavailableError` on timeout, parse failure, or content-policy block
- [X] T024 [US1] Implement `execute_research_pipeline()` in `app/research/service/pipeline.py`: Redis state → `processing` → GitHub fetch via `IGitHubClient` → update `instant_data` in Redis → sanitize context → LLM call via `ILLMClient` → validate `StructuredAIResponse` → persist `FinalResearchReport` via CRUD → Redis state → `completed`; update `progress_msg` at each milestone
- [X] T025 [P] [US1] Implement `GET /api/v1/research/jobs/{job_id}` in `app/research/api/v1/research_router.py`; load state from Redis via `IStateCache`; attach full `ResearchReport` from DB when `completed`; return `PollingStatusResponse`; return `404 Problem` for unknown `job_id`
- [X] T026 [P] [US1] Implement Jinja2 dashboard `GET /research` in `app/research/api/v1/research_router.py`; serve `app/research/templates/research.html` with form that submits to `POST /api/v1/research/jobs` and polls every 2 s; progressively render skeleton → instant metadata → full AI report
- [X] T027 [US1] Implement AI-result cache in `ResearchOrchestrationService`: check Redis for cached `StructuredAIResponse` keyed by `{owner}/{repo}@{commit_sha}` before enqueuing; build `FinalResearchReport` immediately on cache hit; persist AI result after successful LLM call with configurable TTL

**Checkpoint**: Full US1 flow works end-to-end — submit → poll → `completed` report with deterministic facts and AI insights

---

## Phase 4: User Story 2 — Automated Health And Architecture Inference (Priority: P2)

**Goal**: Report classifies technologies into meaningful groups (frontend, backend, database, infrastructure, tooling) and provides evidence-backed health and architecture assessments.

**Independent Test**: Submit a repository with recognizable manifests; verify `tech_stack` entries grouped into labelled categories; verify `risk_level` is `Low/Medium/High` with a cited evidence signal; verify `architecture` is non-null.

### Implementation for User Story 2

- [ ] T028 [P] [US2] Extend `GitHubGraphQLAdapter` to fetch manifest contents (`package.json`, `requirements.txt`, `go.mod`, `Cargo.toml`, `pom.xml`, `build.gradle`, up to 5 files ≤8 KB each) within the same single GraphQL query; map into a `ManifestHints` sub-model on `RepositoryRawContext`
- [ ] T029 [P] [US2] Extend `context_sanitizer.py` to extract contributor activity signals (`pushedAt`, open-issue count, last-commit age) and add them to `LLMPromptPayload.health_signals`
- [ ] T030 [US2] Extend LLM system prompt in `LLMAdapter` with tech-stack categorization instructions (frontend / backend / database / infrastructure / tooling) and health-signal interpretation guidelines; add `tech_categories: dict[str, list[str]]` and `health_evidence: list[str]` to `StructuredAIResponse` schema and `contracts/research-web.openapi.yaml`
- [ ] T031 [P] [US2] Extend `ResearchReport` Pydantic schema and `FinalResearchReportRecord` ORM model with `tech_categories` and `health_evidence` fields; add a new Alembic migration in `alembic/versions/`
- [ ] T032 [US2] Implement Markdown report renderer in `app/research/service/report_renderer.py`: sections — **Repository Overview**, **Tech Stack** (grouped), **Architecture**, **Health Assessment** (evidence-backed), **Risk Level** with cited signal, **AI Confidence**, **Limitations**; call from `execute_research_pipeline()` and store `markdown_report` field on `FinalResearchReport`
- [ ] T033 [P] [US2] Extend `research.html` Jinja2 template to render `tech_categories` table and `health_evidence` list from the completed `ResearchReport`

**Checkpoint**: US1 and US2 both work independently; health and tech-stack sections are categorized in completed reports

---

## Phase 5: User Story 3 — Graceful AI Degradation And Trust Boundaries (Priority: P3)

**Goal**: System degrades gracefully under AI failures, oversized context, prompt injection, and unknown job IDs — always returning a deterministic outcome.

**Independent Test**: Simulate LLM timeout, JSON parse error, oversized README (>100 KB), prompt injection in README, and unknown `job_id`; verify each returns a deterministic outcome with the correct status, warning, or error rather than an unhandled exception.

### Implementation for User Story 3

- [ ] T034 [P] [US3] Enforce token-budget hard limit in `context_sanitizer.py`: apply progressive truncation (README first → manifest snippets → file-tree leaves) if payload exceeds `MAX_CONTEXT_TOKENS` after soft truncation; record each event as a `PartialAnalysisWarning`; surface warnings in `PollingStatusResponse.progress_msg` and `ResearchReport`
- [ ] T035 [P] [US3] Add prompt-injection sanitization in `context_sanitizer.py`: wrap all repository-derived text in `<repository_content>` XML delimiters; strip or escape role-switching sequences (e.g. `ignore previous instructions`); log sanitization events with `request_id` via `common/log.py`
- [X] T036 [US3] Implement AI-fallback path in `execute_research_pipeline()`: catch `LLMUnavailableError`, `asyncio.TimeoutError`, `ValidationError`, and `ContentPolicyError`; build a deterministic-only `FinalResearchReport` with `ai_fallback=True` and `ai_fallback_reason`; persist and transition job to `completed` (not `failed`) so the user still receives usable output
- [X] T037 [P] [US3] Implement DLQ drain handler in `app/research/worker/sqs_worker.py`: when `attempt` exceeds `max_attempts`, call `update_job_status(failed)` on DB and write a failed state snapshot to Redis with the last error message before abandoning the message; no message should be silently lost
- [X] T038 [P] [US3] Verify `GET /api/v1/research/jobs/{job_id}` returns `404 Problem` (RFC 7807, `type: /problems/job-not-found`) when `job_id` is absent from both Redis and DB; ensure response body conforms to the `Problem` schema in `contracts/research-web.openapi.yaml`
- [ ] T039 [P] [US3] Extend `common/exception/exception_handler.py` to catch unhandled pipeline exceptions during the polling endpoint and return a `500 Problem` JSON body with `request_id` and `trace_id` rather than an HTML error page
- [ ] T040 [US3] Extend `tests/research/test_adapter_conformance.py` with failure-path assertions: mock `IMessageQueue` via moto; assert `LLMUnavailableError`, truncation warnings, DLQ abandonment, and unknown-job 404 each produce the expected deterministic outcome without unhandled exceptions

**Checkpoint**: All three user stories work independently; system never hangs or crashes on AI failure, oversized context, or unknown job IDs

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Observability, structured logging, performance guards, and quickstart validation

- [X] T041 [P] Add structured JSON logging (`request_id`, `job_id`, `stage`, `latency_ms`) to each pipeline stage in `execute_research_pipeline()` via `common/log.py`; log GitHub fetch latency, LLM latency, total pipeline latency, truncation events, and fallback activations
- [ ] T042 [P] Expose `GET /metrics` (Prometheus text format) in `middleware/metrics.py`; track `research_jobs_submitted_total`, `research_jobs_completed_total`, `research_jobs_failed_total`, `llm_latency_seconds` histogram, `github_fetch_latency_seconds` histogram; register in `app/router.py`
- [ ] T043 [P] Add rate-limiting middleware to `POST /api/v1/research/jobs`; configure via `RATE_LIMIT_REQUESTS` and `RATE_LIMIT_WINDOW_SECONDS` env vars; return `429 Problem` on breach
- [ ] T044 Update `specs/001-github-repo-research/quickstart.md`: replace all Celery references with ElasticMQ/SQS worker references; update Docker Compose service list; document `SQS_ENDPOINT_URL`; align smoke-test steps with `research-worker` container
- [ ] T045 [P] Validate all five quickstart smoke-test scenarios manually: submit valid repo → poll to completed; warm-cache second submit; missing AI key → fallback report; invalid URL rejection; worker failure → `failed` state
- [ ] T046 [P] Add performance SLO tests in `tests/research/test_performance_slo.py`: assert p95 deterministic metadata available ≤2 s and full AI-enriched result ≤30 s under simulated normal load
- [ ] T047 [P] Add contract artifact validation tests in `tests/research/test_contract_artifacts.py`: assert all Pydantic schemas in `app/research/schema/` satisfy the shapes defined in `contracts/research-web.openapi.yaml`
- [ ] T048 [P] Run `ruff`, `black`, and `mypy` across `app/research/`, `common/`, and `tests/research/`; fix all lint and type errors

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 — **BLOCKS all user stories**
- **US1 (Phase 3)**: Depends on Phase 2 — MVP increment, deliver first
- **US2 (Phase 4)**: Depends on Phase 2 — can start after Phase 2, may run in parallel with US1 if staffed
- **US3 (Phase 5)**: Depends on Phase 2 — best started after US1 end-to-end flow exists
- **Polish (Phase 6)**: Depends on all desired user stories being complete

### User Story Dependencies

- **US1 (P1)**: No dependency on US2 or US3 — fully independent MVP
- **US2 (P2)**: Extends US1's `StructuredAIResponse` and `LLMAdapter`; independently testable with separate repositories
- **US3 (P3)**: Wraps the pipeline from US1; testable with mocked pipeline stages

### Parallel Opportunities

**Phase 1**: T003, T004, T005, T006 run in parallel after T002  
**Phase 2**: T008, T009, T010, T011, T013, T015, T016, T017 run in parallel after T007; T012 after T010; T014 after T007 + T008  
**Phase 3 (US1)**: T018, T019, T022, T023 run in parallel after T015; T021 after T019 + T020; T025 + T026 after T024  
**Phase 4 (US2)**: T028, T029, T033 run in parallel after Phase 2; T031 after T030; T032 after T031  
**Phase 5 (US3)**: T034, T035, T037, T038, T039 run in parallel after Phase 2; T040 after T036 + T037  
**Phase 6**: T041, T042, T043, T045, T046, T047, T048 run in parallel after story phases complete

### Implementation Strategy

- **MVP scope**: Phases 1–3 (T001–T027) — fully functional research tool with SQS-backed async pipeline
- **Increment 2**: Phase 4 (US2) — richer health and tech-stack analysis
- **Increment 3**: Phase 5 (US3) — production-grade resilience and trust boundaries
- **Increment 4**: Phase 6 — observability, metrics, and operational readiness

---

## Summary

| Phase | Tasks | Stories | Parallelizable |
|-------|-------|---------|----------------|
| Phase 1: Setup | T001–T006 | — | T003–T006 |
| Phase 2: Foundational | T007–T017 | — | T008–T011, T013, T015, T016, T017 |
| Phase 3: US1 (P1) MVP | T018–T027 | US1 | T018, T019, T022, T023, T025, T026 |
| Phase 4: US2 (P2) | T028–T033 | US2 | T028, T029, T031, T033 |
| Phase 5: US3 (P3) | T034–T040 | US3 | T034, T035, T037, T038, T039 |
| Phase 6: Polish | T041–T048 | — | T041–T043, T045–T048 |
| **Total** | **48 tasks** | **3 stories** | **~30 parallelizable** |

**Suggested MVP**: Phases 1 + 2 + 3 (T001–T027)

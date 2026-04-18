# Tasks: AI-Native GitHub Repository Research Tool

**Input**: Design documents from `/specs/001-github-repo-research/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, quickstart.md

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Initialize feature skeleton and runtime wiring using existing FastAPI, Celery, Redis, and Compose assets.

- [ ] T001 Review reusable extension points and capture final touchpoints in specs/001-github-repo-research/plan.md
- [ ] T002 Create research feature package skeleton in app/research/__init__.py, app/research/api/__init__.py, app/research/api/router.py, and app/research/api/v1/__init__.py
- [ ] T003 [P] Create research schema files in app/research/schema/job.py, app/research/schema/status.py, app/research/schema/github.py, and app/research/schema/report.py
- [ ] T004 [P] Create research service placeholders in app/research/service/research_gateway_service.py, app/research/service/research_status_service.py, app/research/service/github_graphql_service.py, app/research/service/ai_analysis_service.py, and app/research/service/research_result_service.py
- [ ] T005 [P] Create research persistence skeleton in app/research/model/research_job.py, app/research/model/research_result.py, app/research/crud/crud_research_job.py, and app/research/crud/crud_research_result.py
- [ ] T006 [P] Create research page template in app/research/templates/research/index.html
- [ ] T007 Wire research router into aggregator in app/router.py and app/research/api/router.py
- [ ] T008 Extend runtime settings for GitHub token, AI provider, polling interval, and token budget in core/conf.py
- [ ] T009 Align Compose runtime for app, worker, Redis, and PostgreSQL demo flow in docker-compose.yaml and docker-compose.local.yaml

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Build shared contracts, adapters, and state orchestration required by all user stories.

**⚠️ CRITICAL**: No user story work starts before this phase is complete.

- [ ] T010 Implement strict URL normalization and repository target parser in app/research/service/research_gateway_service.py
- [ ] T011 [P] Define canonical Pydantic contracts for request, accepted response, polling snapshot, and final report in app/research/schema/job.py, app/research/schema/status.py, and app/research/schema/report.py
- [ ] T012 [P] Define internal contracts for parsed target, deterministic metadata, and structured AI payload in app/research/schema/github.py and app/research/schema/report.py
- [ ] T013 Define port interfaces for queue, cache, database, GitHub, and LLM boundaries in app/research/ports/queue_port.py, app/research/ports/cache_port.py, app/research/ports/repository_port.py, app/research/ports/github_port.py, and app/research/ports/llm_port.py
- [ ] T014 [P] Implement adapter wiring through dependency injection for queue, cache, database, GitHub, and LLM implementations in app/research/adapters/queue/, app/research/adapters/cache/, app/research/adapters/repository/, app/research/adapters/github/, app/research/adapters/llm/, app/research/dependencies.py, and core/registrar.py
- [ ] T015 [P] Add adapter conformance tests to verify every adapter implementation satisfies its boundary contract in tests/research/test_adapter_conformance.py
- [ ] T016 Implement deterministic error mapping for invalid URL, missing job, provider error, worker failure, and persistence failure in common/exception/errors.py and common/exception/exception_handler.py
- [ ] T017 [P] Add structured logging fields for request_id, job_id, stage, boundary, latency_ms, and failure_reason in common/log.py and middleware/request_id_middleware.py

**Checkpoint**: Foundation complete. User stories can proceed in priority order or parallel.

---

## Phase 3: User Story 1 - AI-Assisted Repository Semantic Overview (Priority: P1) 🎯 MVP

**Goal**: Accept repository URL, enqueue background job, return immediate acceptance, and deliver deterministic + AI-enriched overview via polling.

**Independent Test**: Submit a valid public repository URL and verify immediate `job_id` response, progressing status snapshots, and final report that separates deterministic facts from AI insights.

### Tests for User Story 1

- [ ] T018 [P] [US1] Add route test for research page render in tests/research/test_research_page.py
- [ ] T019 [P] [US1] Add API test for job submission accepted contract in tests/research/test_research_api.py
- [ ] T020 [P] [US1] Add polling status transition test for pending to processing to completed in tests/research/test_research_status_service.py
- [ ] T021 [P] [US1] Add Celery job orchestration test for enqueue and execution handoff in tests/research/test_research_jobs.py

### Implementation for User Story 1

- [ ] T022 [US1] Implement POST /api/v1/research/jobs and GET /api/v1/research/jobs/{job_id} endpoints in app/research/api/v1/research.py
- [ ] T023 [US1] Implement GET /research dashboard endpoint and view model assembly in app/research/api/v1/research.py and app/research/templates/research/index.html
- [ ] T024 [US1] Implement submission orchestration (validate URL, create job_id, persist pending state, enqueue worker) in app/research/service/research_gateway_service.py
- [ ] T025 [US1] Implement Redis-backed status snapshot retrieval and response shaping in app/research/service/research_status_service.py and database/redis.py
- [ ] T026 [US1] Implement research worker flow entrypoint with state updates in app/task/celery_task/research_jobs.py
- [ ] T027 [US1] Register research API routes in app/research/api/router.py and app/router.py

**Checkpoint**: US1 is independently functional and demoable.

---

## Phase 4: User Story 2 - Automated Health And Architecture Inference (Priority: P2)

**Goal**: Convert GitHub evidence into categorized tech stack, architecture inference, and health risk observations grounded in repository data.

**Independent Test**: Analyze repositories with known manifests and activity patterns, then verify categorized stack, architecture summary, and health signals with evidence-backed output.

### Tests for User Story 2

- [ ] T028 [P] [US2] Add GitHub GraphQL ingestion and mapping tests in tests/research/test_github_graphql_service.py
- [ ] T029 [P] [US2] Add AI structured output validation tests in tests/research/test_ai_analysis_service.py
- [ ] T030 [P] [US2] Add integration test for deterministic plus AI merged final report in tests/research/test_research_api.py

### Implementation for User Story 2

- [ ] T031 [US2] Implement GitHub GraphQL fetch and deterministic context extraction in app/research/service/github_graphql_service.py
- [ ] T032 [US2] Implement AI inference service with structured output contract enforcement in app/research/service/ai_analysis_service.py
- [ ] T033 [US2] Implement cache reuse by repository freshness marker in app/research/service/research_result_service.py and database/redis.py
- [ ] T034 [US2] Implement persistence entities and CRUD for completed reports in app/research/model/research_job.py, app/research/model/research_result.py, app/research/crud/crud_research_job.py, and app/research/crud/crud_research_result.py
- [ ] T035 [US2] Implement structured Markdown report generation as the primary human-readable artifact while preserving machine-readable JSON contracts in app/research/service/research_result_service.py, app/research/service/report_render_service.py, and app/research/schema/report.py
- [ ] T036 [US2] Persist completed report and update completed state in app/task/celery_task/research_jobs.py

**Checkpoint**: US2 independently delivers actionable project insights.

---

## Phase 5: User Story 3 - Graceful AI Degradation And Trust Boundaries (Priority: P3)

**Goal**: Keep deterministic report useful when AI fails, enforce trust boundaries, and return deterministic error outcomes for missing jobs and provider failures.

**Independent Test**: Simulate oversized payloads, prompt injection text, AI timeout/parse failures, and unknown job_id polling while confirming deterministic fallback behavior.

### Tests for User Story 3

- [ ] T037 [P] [US3] Add truncation and partial-analysis warning tests in tests/research/test_ai_analysis_service.py
- [ ] T038 [P] [US3] Add AI failure fallback tests (timeout, parse error, policy block) in tests/research/test_research_jobs.py
- [ ] T039 [P] [US3] Add missing job_id deterministic not-found tests in tests/research/test_research_api.py

### Implementation for User Story 3

- [ ] T040 [US3] Implement README/tree sanitization and deterministic token-budget truncation in app/research/service/ai_analysis_service.py
- [ ] T041 [US3] Implement prompt injection safeguards for untrusted repository text in app/research/service/ai_analysis_service.py
- [ ] T042 [US3] Implement deterministic fallback report shaping when AI is unavailable in app/research/service/research_result_service.py and app/research/schema/report.py
- [ ] T043 [US3] Implement failure-state transitions and user-safe polling messages in app/research/service/research_status_service.py and app/task/celery_task/research_jobs.py
- [ ] T044 [US3] Implement deterministic not-found handling for unknown job_id in app/research/api/v1/research.py and common/exception/errors.py

**Checkpoint**: US3 independently guarantees trust boundaries and graceful degradation.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final hardening across all user stories.

- [ ] T045 [P] Update API docs and examples for research endpoints in README.md
- [ ] T046 Validate quickstart scenarios against implemented flows in specs/001-github-repo-research/quickstart.md
- [ ] T047 [P] Add stage-level observability assertions for queue/cache/db/GitHub/LLM boundaries, including latency and error metrics in tests/research/test_research_status_service.py
- [ ] T048 Remove duplicate logic and consolidate shared mapping helpers in app/research/service/research_gateway_service.py and app/research/service/research_result_service.py
- [ ] T049 Run and stabilize full research test suite in tests/research/test_research_page.py, tests/research/test_research_api.py, tests/research/test_research_status_service.py, tests/research/test_github_graphql_service.py, tests/research/test_ai_analysis_service.py, and tests/research/test_research_jobs.py
- [ ] T050 [P] Add contract artifact validation tests for specs/001-github-repo-research/contracts/research-web.openapi.yaml against app/research/schema/job.py, app/research/schema/status.py, and app/research/schema/report.py in tests/research/test_contract_artifacts.py
- [ ] T051 [P] Add performance validation for unified SLO targets (p95 deterministic metadata <=2s and full result <=30s) in tests/research/test_performance_slo.py and tests/research/test_research_jobs.py

---

## Dependencies & Execution Order

### Phase Dependencies

- Setup (Phase 1): no dependencies, starts immediately.
- Foundational (Phase 2): depends on Setup completion and blocks all user stories.
- User Stories (Phases 3-5): all depend on Foundational completion.
- Polish (Phase 6): depends on completion of target user stories.

### User Story Dependencies

- US1 (P1): starts after Foundational and defines MVP baseline.
- US2 (P2): starts after Foundational; integrates with US1 outputs but remains independently testable.
- US3 (P3): starts after Foundational; hardens failure and trust behavior independently.

### Within Each User Story

- Tests are written first and should fail before implementation.
- Schemas/contracts precede service orchestration changes.
- Service logic precedes endpoint wiring and report rendering.
- Story checkpoint must pass before moving to next priority in sequential delivery.

## Parallel Opportunities

- Setup parallel tasks: T003, T004, T005, T006.
- Foundational parallel tasks: T011, T012, T014, T015, T017.
- US1 parallel tests: T018, T019, T020, T021.
- US2 parallel tests: T028, T029, T030.
- US3 parallel tests: T037, T038, T039.
- Polish parallel tasks: T047, T050, T051.
- Cross-team story parallelism: US2 and US3 can run concurrently after Foundational if capacity allows.

## Parallel Example: User Story 1

```bash
# Parallel test execution for US1
pytest tests/research/test_research_page.py tests/research/test_research_api.py tests/research/test_research_status_service.py tests/research/test_research_jobs.py

# Parallel implementation split for US1
# Dev A: app/research/api/v1/research.py + app/research/api/router.py
# Dev B: app/research/service/research_gateway_service.py + app/research/service/research_status_service.py
# Dev C: app/task/celery_task/research_jobs.py + app/research/templates/research/index.html
```

## Implementation Strategy

### MVP First (US1 only)

1. Complete Phase 1 (Setup).
2. Complete Phase 2 (Foundational).
3. Complete Phase 3 (US1).
4. Validate independent US1 acceptance criteria and demo.

### Incremental Delivery

1. Setup + Foundational to establish reusable contracts and adapters.
2. Deliver US1 as MVP.
3. Add US2 for richer inference and persistence.
4. Add US3 for graceful degradation and trust boundaries.
5. Run Polish phase for docs, observability, and final regression.

### Team Parallel Strategy

1. Team completes Setup + Foundational together.
2. After checkpoint, split across US1/US2/US3 ownership.
3. Merge by story checkpoints and finalize with Polish tasks.

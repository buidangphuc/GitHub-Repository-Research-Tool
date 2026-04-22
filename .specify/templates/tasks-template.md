---

description: "Task list template for feature implementation"
---

# Tasks: [FEATURE NAME]

**Input**: Design documents from `/specs/[###-feature-name]/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests remain OPTIONAL unless
the feature specification requires them, but adapter integrity, canonical
contract mapping, duplicate-logic prevention, scalability boundaries, and
observability tasks are NEVER optional for this project.

**Reuse Audit**: Tasks MUST start from the assets already reviewed in spec.md
and plan.md. When a new file, directory, or workflow is required, include the
justification directly in the task description.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Feature modules**: `app/<feature>/api/v1/`, `app/<feature>/service/`, `app/<feature>/schema/`, `app/<feature>/model/`, `app/<feature>/crud/`
- **Shared backend infrastructure**: `common/`, `core/`, `database/`, `middleware/`, `socketio/`, `utils/`
- **Operational assets**: `scripts/`, `alembic/`, `Dockerfile`, `docker-compose*.yaml`
- Paths shown below assume this repository layout - adjust only when plan.md justifies a different location

<!-- 
  ============================================================================
  IMPORTANT: The tasks below are SAMPLE TASKS for illustration purposes only.
  
  The /speckit.tasks command MUST replace these with actual tasks based on:
  - User stories from spec.md (with their priorities P1, P2, P3...)
  - Feature requirements from plan.md
  - Entities from data-model.md
  - Endpoints from contracts/
  
  Tasks MUST be organized by user story so each story can be:
  - Implemented independently
  - Tested independently
  - Delivered as an MVP increment
  
  DO NOT keep these sample tasks in the generated tasks.md file.
  ============================================================================
-->

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Review reusable assets in app/, common/, core/, database/, middleware/, socketio/, utils/, scripts/, and infra files; record the planned extension points
- [ ] T002 Extend the existing FastAPI feature structure per implementation plan without creating an unnecessary top-level package
- [ ] T003 [P] Configure linting, formatting, and architecture guardrails against duplicated logic and unjustified new modules

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

Examples of foundational tasks (adjust based on your project):

- [ ] T004 Define or extend boundary schemas and canonical contracts in app/*/schema/, app/*/model/, and common/
- [ ] T005 [P] Implement reusable CRUD, adapter, or integration utilities in app/*/crud/, database/, or shared provider clients
- [ ] T006 [P] Setup API routing, dependency wiring, and request validation in app/router.py and app/*/api/
- [ ] T007 Create orchestration or background flows for fetch -> validate -> map -> analyze -> render in app/*/service/, middleware/, or app/task/celery_task/
- [ ] T008 Build shared mapping, context, and domain services in common/, utils/, core/, and existing feature services
- [ ] T009 Setup structured logging, error taxonomy, concurrency limits, auth, and configuration management in common/, common/security/, middleware/, and core/

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - [Title] (Priority: P1) 🎯 MVP

**Goal**: [Brief description of what this story delivers]

**Independent Test**: [How to verify this story works on its own]

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T010 [P] [US1] Contract test for adapter behavior or canonical contract mapping in tests/contract/test_[name].py
- [ ] T011 [P] [US1] Integration test for the end-to-end flow in tests/integration/test_[name].py

### Implementation for User Story 1

- [ ] T012 [P] [US1] Add or extend schemas and models in app/[feature]/schema/[file].py or app/[feature]/model/[file].py
- [ ] T013 [P] [US1] Extend CRUD, adapter, or mapping logic in app/[feature]/crud/[file].py, database/[file].py, or an existing provider helper
- [ ] T014 [US1] Extend shared domain service or orchestration flow in app/[feature]/service/[file].py, middleware/[file].py, or app/task/celery_task/[file].py
- [ ] T015 [US1] Implement endpoint or router entry point in app/[feature]/api/v1/[file].py and register it through app/router.py
- [ ] T016 [US1] Add observability, deterministic errors, and scale guards without duplicating existing logic
- [ ] T017 [US1] Render output through shared response, schema, or serialization components in common/response/[file].py, common/schema.py, or the existing feature package

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - [Title] (Priority: P2)

**Goal**: [Brief description of what this story delivers]

**Independent Test**: [How to verify this story works on its own]

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T018 [P] [US2] Contract test for adapter extension, canonical contract behavior, or endpoint behavior in tests/contract/test_[name].py
- [ ] T019 [P] [US2] Integration test for the user journey in tests/integration/test_[name].py

### Implementation for User Story 2

- [ ] T020 [P] [US2] Extend schemas, models, or mapping rules in app/[feature]/schema/[entity].py, app/[feature]/model/[entity].py, or common/
- [ ] T021 [US2] Extend shared service or orchestration logic in app/[feature]/service/[file].py, middleware/[file].py, or app/task/service/[file].py
- [ ] T022 [US2] Implement API or pipeline integration in app/[feature]/api/v1/[file].py or app/router.py
- [ ] T023 [US2] Integrate with existing CRUD, contracts, shared services, middleware, and response helpers as needed

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - [Title] (Priority: P3)

**Goal**: [Brief description of what this story delivers]

**Independent Test**: [How to verify this story works on its own]

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T024 [P] [US3] Contract test for error handling, observability, or report output in tests/contract/test_[name].py
- [ ] T025 [P] [US3] Integration test for the user journey in tests/integration/test_[name].py

### Implementation for User Story 3

- [ ] T026 [P] [US3] Extend schemas, transforms, or response sections in app/[feature]/schema/[entity].py, app/[feature]/model/[entity].py, common/response/[file].py, or utils/[file].py
- [ ] T027 [US3] Implement service or orchestration logic in app/[feature]/service/[file].py, middleware/[file].py, or app/task/celery_task/[file].py
- [ ] T028 [US3] Implement endpoint or reporting behavior in app/[feature]/api/v1/[file].py, common/response/[file].py, or another justified existing location

**Checkpoint**: All user stories should now be independently functional

---

[Add more user story phases as needed, following the same pattern]

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] TXXX [P] Documentation updates in docs/
- [ ] TXXX Remove duplicate logic and consolidate abstractions where overlap emerged
- [ ] TXXX Performance and concurrency optimization across all stories
- [ ] TXXX [P] Additional unit tests (if requested) in tests/unit/
- [ ] TXXX Validate rate-limit handling, schema drift behavior, backpressure, and explicit failure observability
- [ ] TXXX Run quickstart.md validation

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - May integrate with US1 but should be independently testable
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - May integrate with US1/US2 but should be independently testable

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Contracts and adapters before orchestration or report rendering
- Extend shared services before creating new abstractions
- Core implementation before integration
- No source-specific parsing outside adapters
- Failure behavior, observability, and Markdown output before story sign-off
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for [endpoint] in tests/contract/test_[name].py"
Task: "Integration test for [user journey] in tests/integration/test_[name].py"

# Launch all models for User Story 1 together:
Task: "Create or extend [Entity1] schema in app/[feature]/schema/[entity1].py"
Task: "Create or extend [Entity2] model in app/[feature]/model/[entity2].py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1
   - Developer B: User Story 2
   - Developer C: User Story 3
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing when tests are included
- Always include tasks for adapter integrity, canonical contract reuse, duplicate-logic prevention, and observability
- Record manual Git steps separately when needed; do not assume hook-driven commits
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, duplicated function logic, and source-specific parsing outside adapters

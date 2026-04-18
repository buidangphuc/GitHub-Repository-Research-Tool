# Implementation Plan: [FEATURE]

**Branch**: `[###-feature-name]` | **Date**: [DATE] | **Spec**: [link]
**Input**: Feature specification from `/specs/[###-feature-name]/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/plan-template.md` for the execution workflow.

## Summary

[Describe the user-facing capability, the integration paths it touches, the
shared services or contracts it extends, and how the change reduces
duplication while improving integratability, reliability, or scale.]

## Technical Context

<!--
  ACTION REQUIRED: Replace the content in this section with the technical details
  for the project. The structure here is presented in advisory capacity to guide
  the iteration process.
-->

**Language/Version**: Python 3.11+  
**Primary Dependencies**: FastAPI, Pydantic, httpx, provider SDKs, pytest  
**Storage**: N/A for MVP unless a feature explicitly introduces persistence  
**Testing**: pytest, pytest-asyncio, contract tests for adapters and canonical contracts  
**Target Platform**: Server-side Python service on macOS/Linux  
**Project Type**: Async integration and report orchestration service  
**Performance Goals**: Keep latency predictable while allowing new providers, higher traffic, and deeper analysis without rewriting core flows  
**Constraints**: Respect GitHub rate limits, keep services stateless where practical, forbid source-specific parsing outside adapters, and avoid duplicate business logic  
**Scale/Scope**: Public GitHub repositories only; single-repository analysis per request in the MVP, with future growth handled through adapters and canonical contracts

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

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
specs/[###-feature]/
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
src/
├── api/
├── adapters/
├── contracts/
├── domain/
├── orchestration/
├── reporting/
├── services/
└── shared/

tests/
├── architecture/
├── contract/
├── integration/
└── unit/
```

**Structure Decision**: Use a layered async backend service. Place HTTP
boundaries in `src/api/`, provider-specific integrations in `src/adapters/`,
canonical internal contracts in `src/contracts/`, core business rules in
`src/domain/`, flow composition in `src/orchestration/`, reusable operational
and support services in `src/services/`, report formatting in `src/reporting/`,
and shared utilities in `src/shared/`. No source-specific parsing may escape
the adapter layer, and no shared business behavior may be reimplemented in
parallel modules.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., New abstraction layer] | [current need] | [why extending the existing shared service was insufficient] |
| [e.g., Queue/cache boundary] | [specific scaling problem] | [why inline synchronous orchestration was insufficient] |

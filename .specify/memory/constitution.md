<!--
Sync Impact Report
Version change: 2.0.0 -> 2.1.0
Modified principles:
- I. Reusable Service Architecture -> I. Reusable Service Architecture and Existing Assets First
Added sections:
- Existing Assets and Reuse Targets
Removed sections:
- None
Templates requiring updates:
- ✅ updated .specify/templates/plan-template.md
- ✅ updated .specify/templates/spec-template.md
- ✅ updated .specify/templates/tasks-template.md
- ✅ no .specify/templates/commands/*.md files were present to update
Runtime/config aligned:
- ✅ updated .specify/extensions.yml
Follow-up TODOs:
- None
-->

# GitInsight: GitHub Repository Research Tool Constitution

## Mission Statement

GitInsight exists to transform raw repository data into actionable technical
intelligence through a healthy, reusable, and scalable architecture. The MVP
MUST accept a public GitHub repository URL, integrate authoritative repository
data into stable internal models, and produce a structured Markdown report that
remains maintainable as data sources, traffic volume, and analytical depth grow.
The system MUST evolve by extending the FastAPI platform assets already present
in this repository before introducing new modules, new tooling, or parallel
workflows.

## Core Principles

### I. Reusable Service Architecture and Existing Assets First

The system MUST be organized around reusable services, adapters, and domain
flows instead of feature-specific utility sprawl. Every change MUST begin with a
review of the assets already present in the repository, and work that fits an
existing responsibility MUST extend that asset instead of creating a parallel
module. Logic that appears in more than one workflow MUST be extracted into
shared modules with clear ownership; copy-paste reuse is non-compliant. New
functions, packages, or wrappers are allowed only when the specification or
plan records why existing assets cannot absorb the behavior without harming
cohesion, dependency boundaries, or readability.

Rationale: Scalability in codebase size depends on reducing duplication,
preserving cohesion, and making change happen in one place.

### II. Integration-First Data Contracts

Data integration is the primary engineering problem and MUST drive the system
design. Every external source MUST enter the system through explicit adapters
and be normalized into canonical internal models before downstream use. GitHub
API responses, repository-derived inputs, and future provider integrations MUST
be validated with Pydantic schemas at the boundary, mapped once into internal
contracts, and consumed from those contracts only. Source-specific parsing MUST
NOT leak into business services, prompt builders, or report renderers.

Rationale: A stable integration layer is the prerequisite for adding new data
sources, changing providers, and avoiding rewrite pressure across the system.

### III. Scalability by Design

The MVP MUST be scalable in execution model, dependency boundaries, and change
cost. Services MUST remain stateless where practical, I/O MUST be asynchronous,
and expensive work MUST be isolated behind explicit orchestration boundaries so
it can later be parallelized, queued, cached, or distributed without rewriting
core business logic. GitHub API access and report generation MUST be designed
for concurrency control, backpressure, and bounded resource usage from the
start.

Rationale: Healthy scalability is achieved by design constraints early, not by
late-stage optimization after the architecture hardens.

### IV. Pattern Discipline and Low Coupling

Design patterns MUST be used to reduce coupling, centralize behavior, and make
extension predictable; they MUST NOT be introduced as ceremony. Adapter,
Strategy, Factory, Facade, and pipeline-style orchestration are preferred when
they eliminate repeated branching logic or isolate vendor-specific behavior.
Any pattern that increases indirection without reducing duplication,
integration complexity, or scaling risk MUST be rejected.

Rationale: The goal is a healthy architecture, not a pattern catalog. Patterns
are justified only when they lower maintenance cost and support growth.

### V. Operational Reliability and Observability

Every integration path and core service MUST expose predictable error handling,
structured logging, and observable failure states. Rate limiting, partial data,
schema mismatches, and provider degradation MUST be surfaced explicitly. The
system MUST be designed so operators can identify where a failure occurred:
boundary fetch, contract validation, mapping, orchestration, AI analysis, or
report rendering.

Rationale: A scalable system that cannot be diagnosed is not healthy in
production.

## Core Functional Scope

### MVP Boundaries

- Input validation for public GitHub repository URLs
- Repository metadata extraction and normalization from the GitHub REST API
- README and file-tree collection through reusable integration flows
- Canonical internal models shared by analysis and reporting components
- AI-generated architectural observations and actionable recommendations
- Structured Markdown report generation for human review

### Out of Scope

- Private repository support or authenticated repository access
- Deep code security auditing or formal vulnerability assessment
- Full source-code indexing across entire repositories
- Commit-history analytics, contributor behavior scoring, or trend dashboards
- Multi-repository benchmarking or portfolio comparison
- Autonomous code modification, pull request generation, or execution workflows
- New scaffolding, helper packages, or tooling that duplicate existing
  repository assets without a documented exception

## Technical Pillars

### Backend

FastAPI is the required backend framework for request handling and orchestration.
Service design MUST remain asynchronous end-to-end for network-bound workflows,
stateless where practical, and organized into clear layers: API boundary,
integration adapters, domain services, orchestration, and output rendering.
Feature work MUST extend the repository's existing application surface before a
new top-level package is introduced.

### Data Layer

Pydantic is the required schema layer for external data contracts, internal
normalization, and internal data contracts. All boundary objects MUST be typed,
validated, versionable, and serializable without ad hoc parsing. Canonical
models MUST be reused across services instead of redefining equivalent schemas
per feature.

### AI Engine

AI is a downstream consumer of integrated data, not the architectural center of
the system. Gemini 1.5 Pro and Gemini 1.5 Flash are approved model tiers for
the MVP, but model routing MUST consume canonical normalized inputs and MUST
remain replaceable behind a provider abstraction.

### API Strategy

GitHub integration MUST use the REST API with robust error handling for rate
limiting, missing resources, and partial responses. Retry, backoff, caching,
and failure messaging MUST preserve user trust and avoid ambiguous system
states. Future data sources MUST follow the same adapter and contract rules as
GitHub so integration scale does not create architectural drift.

## Existing Assets and Reuse Targets

### Application Surface

API, service, schema, model, and CRUD work MUST first review `app/router.py`
and the feature packages under `app/admin/` and `app/task/`. When a change fits
an existing feature namespace, that namespace MUST be extended instead of
creating a sibling router tree, duplicate service layer, or parallel package.

### Shared Cross-Cutting Assets

Cross-cutting concerns MUST first reuse `common/`, `common/security/`, `core/`,
`database/`, `middleware/`, `socketio/`, and `utils/`. New shared helpers,
middleware, or support packages are allowed only when these directories cannot
absorb the behavior without mixing responsibilities or creating tighter
coupling.

### Operations and Delivery

Migrations, startup, formatting, export, and environment workflows MUST first
reuse `alembic/`, `scripts/`, `Dockerfile`, `docker-compose.yaml`,
`docker-compose.local.yaml`, `requirements.txt`, `pyproject.toml`, and
`mypy.ini` before new operational tooling is added.

### Git Workflow Control

Git repository initialization, branching, and commits are user-controlled
operational actions. Speckit, agents, and local project configuration MUST NOT
assume hook-driven Git initialization, feature-branch creation, or auto-commit.
They MAY provide manual guidance only when the user explicitly requests it.

## AI Strategy & Prompt Engineering

### Role-Based Prompting

The primary analysis prompt MAY frame the model as a Senior AI Solution
Architect and Product Manager, but prompt design MUST remain secondary to clean
data contracts and deterministic orchestration. Prompts MUST consume normalized
internal models rather than raw provider payloads.

### Context Management

Large READMEs, extensive directory trees, and oversized metadata payloads MUST
be filtered before inference. Context assembly MUST prioritize high-signal
artifacts, remove duplication, and enforce deterministic truncation rules so
the model receives the most relevant evidence within the available context
window. Context building logic MUST be centralized so the same truncation,
ranking, and deduplication rules are not reimplemented across features.

### Output Grounding

Prompt payloads MUST only contain validated data. When evidence is thin,
conflicting, or absent, the model MUST state the limitation instead of filling
gaps with speculation. Output formatting MUST be separated from data fetching
and inference so report rendering can evolve without rewriting integration or
analysis flows.

## Definition of Success

- Reuse-first: Every accepted change MUST name the existing asset it extends or
  justify why a new module, package, or script is necessary.
- Integratable: Adding a new data source MUST require a localized adapter and
  mapping change, not a rewrite of business services or report logic.
- Scalable: The runtime model MUST support increased traffic, more integrations,
  and deeper analysis through composition, concurrency control, and isolation
  of expensive work.
- Reliable: Failure modes MUST be observable and deterministic across fetch,
  validation, mapping, orchestration, inference, and rendering.

## Governance

This constitution supersedes informal project practices for GitInsight. Every
specification, plan, and task list MUST include a constitution check covering
reuse of existing services, integrity of integration contracts, scalability of
the execution model, appropriateness of chosen patterns, operational
observability, and the existing repository assets reviewed before new files are
introduced. Any exception MUST be documented with rationale and reviewed before
implementation proceeds.

Every specification, plan, and task list MUST record the existing files,
directories, scripts, and operational assets reviewed for reuse. If a new
top-level directory, shared helper, or workflow is introduced, the change MUST
state why the current assets were insufficient. Convenience alone is not a
sufficient justification.

Git workflow automation is user-controlled. `.specify/extensions.yml` MUST keep
Git hooks disabled unless the user explicitly asks to re-enable repository
initialization, branch creation, or auto-commit behavior for a specific phase.

Amendments require a written rationale, a summary of impacted artifacts, and an
update to all affected templates or guidance files in the same change set.
Versioning follows semantic rules: MAJOR for incompatible principle changes or
scope reversals, MINOR for new principles or materially expanded governance,
and PATCH for clarifications that do not alter project obligations.

Compliance review occurs at specification approval, implementation planning,
and pre-merge review. Work that violates this constitution without an approved
exception is non-compliant and MUST be revised before acceptance. Any pull
request that introduces duplicated function logic, source-specific parsing
outside integration adapters, new cross-cutting behavior without a shared
abstraction, or unnecessary new modules despite suitable existing assets MUST be
treated as a design defect.

**Version**: 2.1.0 | **Ratified**: 2026-04-18 | **Last Amended**: 2026-04-18

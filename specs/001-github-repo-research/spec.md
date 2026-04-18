# Feature Specification: AI-Native GitHub Repository Research Tool

**Feature Branch**: `[001-github-repo-research]`  
**Created**: 2026-04-18  
**Status**: Draft  
**Input**: User description: "Build a small application that accepts a public GitHub repository URL and produces a clear, structured report covering repository overview, project insights, activity and health, with thoughtful UX, robust edge-case handling, and AI-enhanced insights where useful."

## Existing Asset Review *(mandatory)*

- Reviewed `app/router.py`, `app/admin/`, `common/response/`, `core/conf.py`, `database/redis.py`, `middleware/`, and `README.md` for reuse opportunities.
- Extend first: reuse the current FastAPI router aggregation, shared response envelopes, configuration system, Redis integration, and middleware chain before adding new orchestration or transport layers.
- AI-specific extension: introduce `app/ai/` to manage prompt templates, prompt sanitization, LLM clients, and response parsing, plus `app/schemas/` for cross-feature Pydantic contracts used by structured AI outputs.
- Justification: repository research is a hybrid pipeline from GitHub data extraction to context cleaning to LLM inference to normalized reporting. The MVP does not need a separate microservice, but it does need isolated AI orchestration so LLM concerns do not leak into repository-fetching services or transport adapters.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - AI-Assisted Repository Semantic Overview (Priority: P1)

As a user evaluating an unfamiliar public GitHub repository, I want to submit its URL and quickly receive a structured report that combines deterministic repository facts with AI-generated semantic summaries so I can understand the repository's purpose and likely architecture without manually reading the entire README and file tree.

This journey starts with validated repository input, returns a `job_id` and immediate deterministic metadata when possible, sanitizes and truncates README and tree evidence for the AI stage, and requires the LLM to return JSON that conforms to the internal insight contract.

**Why this priority**: This is the main user value. Without a reliable semantic overview grounded in repository evidence, the tool is only a thin GitHub metadata wrapper.

**Independent Test**: Can be fully tested by submitting a valid public repository URL and verifying that the system returns immediate accepted feedback plus a final report where deterministic facts and AI summaries are both present and clearly separated.

**Acceptance Scenarios**:

1. **Given** a valid public repository URL, **When** research starts, **Then** the system returns an accepted response with a `job_id`, persists initial job state, and exposes deterministic metadata as soon as it is available.
2. **Given** a valid public repository with README and file tree evidence, **When** the AI stage completes, **Then** the system returns a structured JSON insight payload that accurately summarizes repository purpose and architecture without inventing features that are absent from the evidence.
3. **Given** a repository whose metadata or prior AI result is already cached for the same repository state, **When** research starts, **Then** the system reuses cached data and reduces unnecessary reprocessing or LLM cost.

---

### User Story 2 - Automated Health And Architecture Inference (Priority: P2)

As a user deciding whether a repository is adoptable, I want the system to analyze dependency manifests, contributor activity, and file structure so I receive a clear assessment of tech stack, maintenance posture, and notable risks rather than a raw list of repository files and package names.

This journey combines deterministic GitHub evidence with AI inference, uses prompt instructions or few-shot examples to classify technologies into meaningful buckets, and preserves a clear distinction between factual observations and reasoned conclusions.

**Why this priority**: Project evaluation depends on turning noisy repository evidence into actionable categories and risk signals, not just surfacing raw API fields.

**Independent Test**: Can be fully tested by analyzing repositories with recognizable manifest files and contribution history, then validating that the report classifies frontend, backend, database, and operational technologies into sensible groups and explains major health signals.

**Acceptance Scenarios**:

1. **Given** a repository with complex dependency manifests, **When** it is analyzed, **Then** the report groups technologies into meaningful categories such as frontend, backend, database, infrastructure, or developer tooling instead of only echoing raw dependency names.
2. **Given** a repository with sparse recent activity or stale maintenance signals, **When** the health section is generated, **Then** the report flags the evidence-backed risk level and cites the factual signal that triggered the inference.
3. **Given** a repository with multiple architecture clues across README and file tree, **When** architecture inference runs, **Then** the report distinguishes direct evidence from probable interpretation.

---

### User Story 3 - Graceful AI Degradation And Trust Boundaries (Priority: P3)

As a user relying on the report, I want hard facts and AI insights to remain clearly separated and I want the system to degrade gracefully when AI inference fails, times out, or receives oversized or adversarial context so I can still trust the output and continue using the application.

This journey enforces prompt sanitization, deterministic truncation, partial-analysis warnings, explicit failure states, and an API-only fallback report when the AI stage is unavailable or unsafe to trust.

**Why this priority**: AI failures are inevitable. Trust depends on making failures visible and keeping the deterministic part of the system useful even when inference is unavailable.

**Independent Test**: Can be fully tested by simulating oversized repositories, prompt injection attempts in README content, LLM timeouts, JSON parse errors, and unknown `job_id` requests while confirming that the user receives deterministic outcomes instead of a broken dashboard.

**Acceptance Scenarios**:

1. **Given** an oversized repository whose README and file tree exceed the configured token budget, **When** research runs, **Then** the system deterministically truncates the prompt payload, records a partial-analysis warning, and continues without crashing the AI stage.
2. **Given** an LLM timeout, rate limit, content-policy block, or JSON parse failure, **When** research runs, **Then** the system returns the deterministic GitHub-backed report and labels AI insight sections as temporarily unavailable.
3. **Given** a prompt injection attempt embedded in repository content, **When** the LLM prompt is constructed, **Then** the system treats repository text as untrusted data, preserves its factual content, and does not allow the injected instructions to override system behavior.
4. **Given** a non-existent `job_id`, **When** the client polls for status, **Then** the system returns a deterministic not-found outcome rather than hanging or misreporting progress.

### Edge Cases

- Malformed URLs, organization profile URLs, gist URLs, issue URLs, or branch or tree URLs that do not resolve to a repository root
- Repositories that are renamed, transferred, archived, deleted, or made private while a research job is in flight
- Repository READMEs or file trees large enough to overflow the AI context window
- Prompt injection content inside README, documentation, or manifest files that attempts to override system instructions
- AI hallucination risk when README text is vague, outdated, or marketing-heavy
- GitHub GraphQL rate limits, provider outages, or LLM quota exhaustion during active jobs
- Worker crash, queue interruption, or Redis state loss after a job has already been accepted
- Jobs that complete inference but fail while persisting final results
- Polling requests for expired, missing, or already cleaned-up job state keys
- Repositories without README, manifest files, or meaningful top-level structure
- Large monorepos where only a high-signal subset of structure can be summarized within the evidence budget

## Scope Boundaries *(mandatory)*

### In Scope

- One-repository-at-a-time research initiated from a public GitHub repository URL
- Hybrid pipeline: GitHub GraphQL extraction, context sanitization, deterministic truncation, and LLM inference
- AI-assisted semantic summarization, tech stack classification, health and risk assessment, and structured report composition
- Strict structured AI outputs that conform to internal Pydantic contracts
- FastAPI submission and status endpoints with OpenAPI visibility
- Progressive UX with an immediate accepted response, deterministic metadata as early as possible, and short polling for final insight delivery
- Default deployment using Celery workers, Redis-backed queue or state handling, and stored results suitable for demo use
- Reuse of the current `app/`, `common/`, `core/`, `database/`, `middleware/`, and existing task-processing assets before introducing new modules

### Out of Scope

- Private repository access, authenticated cloning, or per-user GitHub token management
- Full RAG that clones or embeds entire repositories into a vector database
- Static code analysis, deep vulnerability scanning, or semantic indexing of every source file
- Fine-tuning or self-hosting custom foundation models for the MVP
- WebSocket-first real-time push channels when short polling satisfies the MVP UX
- Multi-repository comparison, recommendation, or portfolio dashboards in v1
- Account management, billing, quota administration, or organization-level tenancy

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST accept a GitHub repository URL and reject malformed, unsupported, or non-repository URLs before any background job or LLM work is started.
- **FR-002**: System MUST return an accepted response with a `job_id`, persist initial job state, and avoid blocking on full report generation.
- **FR-003**: System MUST expose a status endpoint that returns at least `pending`, `processing`, `completed`, or `failed` states plus the latest update timestamp and any partial report snapshot that is safe to show.
- **FR-004**: System MUST fetch deterministic repository evidence from GitHub GraphQL before invoking any LLM resources so invalid requests and upstream rate-limit failures do not spend AI budget.
- **FR-005**: System MUST filter or suppress noisy or unsafe context sources such as generated trees, binary or image entries, `node_modules`, `.git`, vendored artifacts, and other low-signal paths before constructing the LLM prompt.
- **FR-006**: System MUST deterministically truncate README, file tree, and manifest-derived context to stay within the configured AI token budget.
- **FR-007**: System MUST treat repository text as untrusted input and apply prompt-construction safeguards so repository content cannot override system instructions.
- **FR-008**: The LLM integration MUST request structured output and reject or repair non-conforming responses until they match the internal `StructuredAIResponse` contract or the AI stage is marked unavailable.
- **FR-009**: System MUST clearly separate deterministic facts from AI-generated insights in both API responses and the rendered report.
- **FR-011**: System MUST preserve an API-only fallback report when AI generation fails because of timeout, rate limit, content filtering, malformed JSON, or provider unavailability.
- **FR-012**: System MUST cache AI responses for the same repository state, such as owner, name, and commit hash or equivalent freshness marker, to avoid repeated inference cost.
- **FR-013**: System MUST validate all inter-stage payloads between GitHub extraction, sanitization, queue transport, AI inference, cache, database, and UI using strict Pydantic contracts before storing or returning them.
- **FR-014**: System MUST store completed research results in a primary persistence layer so final reports can be reloaded after background processing finishes.
- **FR-015**: System MUST provide deterministic failure outcomes for invalid input, missing jobs, queue or worker failures, GitHub provider errors, AI provider errors, and persistence failures.
- **FR-016**: System MUST expose the JSON research endpoints through FastAPI-generated OpenAPI or Swagger UI for demo visibility.
- **FR-017**: The default development and demo deployment MUST integrate with the existing task-processing stack, while queue, cache, database, and LLM providers are accessed through replaceable adapter interfaces rather than hard-coded business logic.

### Non-Functional Requirements

- **NFR-001**: For 95% of sampled valid requests under normal demo conditions, deterministic metadata MUST be available within 2 seconds and full AI-enriched results MUST be available within 15 seconds using progressive delivery.
- **NFR-002**: The maximum payload sent to the LLM MUST be capped at the configured budget, such as 32,000 tokens, and larger payloads MUST be truncated deterministically.
- **NFR-003**: If the AI stage fails for timeout, JSON parse error, content policy, or provider outage reasons, the system MUST return the deterministic report without a critical application error.
- **NFR-004**: Repeated analysis requests for the same repository state SHOULD reuse cached AI output or previously persisted results to control cost and reduce latency.
- **NFR-005**: The system MUST emit logs and metrics that make failures observable at the GitHub fetch, sanitization, queue, AI inference, response validation, persistence, and rendering stages.
- **NFR-006**: The report and status experience MUST remain readable on common laptop and mobile viewport widths, and the default short-polling cadence MUST be configurable with a 2-second default.
- **NFR-007**: The core application logic MUST NOT be tightly coupled to specific infrastructure choices such as Redis, SQS, PostgreSQL, or a single LLM provider. All external services, including databases, message queues, caches, and LLM APIs, MUST be abstracted using a Ports and Adapters pattern, and runtime implementations MUST be resolved through dependency injection and environment-based configuration.

### Key Entities *(include if feature involves data)*

- **RepositoryResearchInput**: The normalized representation of a submitted public GitHub repository URL and client options.
- **ResearchJobRecord**: The lifecycle record containing `job_id`, repository target, status, timestamps, repository freshness marker, and failure details when applicable.
- **ResearchJobStateSnapshot**: The short-lived polling payload that carries current status, partial deterministic facts, warnings, and the latest update time while background work is still in progress.
- **RepositoryRawContext**: The raw validated snapshot returned from GitHub, including repository metadata, README content, selected file-tree nodes, activity signals, and manifest hints.
- **LLMPromptPayload**: The sanitized, truncated, and instruction-ready object constructed from repository evidence for the AI stage.
- **StructuredAIResponse**: The strict Pydantic model returned by the AI stage, including summary, inferred architecture, categorized tech stack, health observations, risk assessment, confidence or limitation notes, and translation metadata.
- **ResearchReport**: The merged report combining deterministic GitHub-backed facts, AI insights, warnings, evidence boundaries, and render-ready sections for API and UI delivery.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In user acceptance testing, 95% of sampled valid submissions return a `job_id` and deterministic metadata within 2 seconds, and the full AI-enriched report within 15 seconds.
- **SC-002**: The AI stage produces valid JSON conforming to the `StructuredAIResponse` schema in 99% of successful provider calls.
- **SC-003**: Average token consumption per repository analysis stays within the configured budget threshold and is observable through application logging or metrics.
- **SC-004**: In manual review across 20 edge-case repositories, the AI report does not invent dependencies or features not supported by README, manifest, or structure evidence.
- **SC-005**: In simulated timeout, rate-limit, malformed-output, and provider-failure tests, 100% of affected jobs return an API-only fallback report rather than a critical system failure.
- **SC-006**: In reviewer checks across 20 completed reports, deterministic facts and AI-generated insights are visually and programmatically distinguishable every time.
- **SC-007**: In repeated analysis of unchanged repository states, cached or reused results reduce redundant AI invocations for at least 80% of duplicate requests.

## Assumptions

- The MVP analyzes one public GitHub repository per job.
- GitHub GraphQL and selected REST fallbacks provide enough repository evidence for a useful demo-grade report without cloning the full repository.
- The default deployment may continue to use Celery, Redis, and PostgreSQL or SQLite where appropriate, but the domain workflow will be kept behind adapter interfaces so infrastructure choices can change without rewriting business logic.
- AI-generated observations are advisory and must stay grounded in collected repository evidence, explicit limitations, and deterministic fallback behavior.
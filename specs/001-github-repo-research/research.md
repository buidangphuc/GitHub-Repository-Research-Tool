# Phase 0 Research: AI-Native GitHub Repository Research Tool

## Decision 1: Use Progressive Rendering with Short Polling
- **Decision**: Render a single-page Jinja2 dashboard that submits a research job, immediately displays instant deterministic metadata (or skeletons), and polls the job status endpoint every 2 seconds to progressively load AI insights.
- **Rationale**: This delivers the "Optimistic UI" and demo-friendly experience requested without adding heavy client-side framework (React/Vue) complexity or requiring Stateful WebSocket connections.
- **Alternatives considered**:
  - Fully synchronous request: Rejected because it blocks the browser, risks Load Balancer timeouts, and hides the value of the asynchronous worker architecture.
  - Server-Sent Events (SSE) / WebSockets: Rejected for the MVP because short polling is simpler to demo and easier to implement reliably within the current stack.

## Decision 2: Keep FastAPI as the Orchestrator and API Gateway
- **Decision**: FastAPI will act as a stateless Orchestrator. It will accept URLs, generate `job_id` values, enqueue background tasks, expose status polling endpoints, render the Jinja2 page, and publish OpenAPI (Swagger) documentation.
- **Rationale**: FastAPI already exists in the repo, provides automatic OpenAPI schema generation, and is perfectly suited for high-concurrency, I/O-bound orchestration tasks.
- **Alternatives considered**:
  - Separate gateway process: Rejected because it adds deployment overhead without improving the MVP demo value.

## Decision 3: Use Redis as a unified broker and state cache (MVP Tier)
- **Decision**: Redis will play two roles simultaneously: the Celery message broker (task queue) and the short-lived key-value cache for job-state tracking (`pending`, `processing`, `completed`).
- **Rationale**: The repo already uses Redis. Consolidating the queue and state cache into one service keeps the demo architecture compact and lightning-fast.
- **Alternatives considered**:
  - RabbitMQ/SQS plus DynamoDB/Redis: Rejected for the MVP phase as it over-complicates local development and Compose bootstrapping.

## Decision 4: Reuse Celery for asynchronous background execution
- **Decision**: Heavy compute and I/O tasks (GraphQL fetching, LLM inference) will run through Celery workers launched as a separate container role, sharing the same Python codebase.
- **Rationale**: Reusing the existing Celery bootstrap and task registration avoids reinventing the wheel and strictly isolates the API Gateway from blocking operations.
- **Alternatives considered**:
  - FastAPI `BackgroundTasks`: Rejected because it runs in the same event loop/process, preventing horizontal scaling and risking API starvation during heavy LLM tasks.

## Decision 5: Infrastructure Agnosticism via Ports and Adapters
- **Decision**: Core application logic will not directly import specific infrastructure libraries (e.g., calling Redis directly). Instead, it will use abstract interfaces (e.g., `IMessageQueue`, `IStateCache`) and rely on Dependency Injection.
- **Rationale**: This "Hexagonal Architecture" ensures the application is future-proof. Swapping Redis for AWS SQS/RabbitMQ in production requires zero changes to the core business logic.
- **Alternatives considered**:
  - Tightly coupled infrastructure: Rejected because it violates enterprise scalability principles and makes migration difficult.

## Decision 6: Default to PostgreSQL in Compose, with SQLite local fallback
- **Decision**: The primary deployment path will use PostgreSQL via Docker Compose. SQLite will remain an optional, auto-configured fallback for lightweight, local non-container experimentation.
- **Rationale**: PostgreSQL fits the multi-container demo story perfectly and paves the way for future Vector Indexing (`pgvector`), while SQLite ensures a frictionless "clone and run" developer experience.

## Decision 7: Use GitHub GraphQL v4 for deterministic ingestion
- **Decision**: The worker will execute a single GraphQL query to retrieve repository metadata, file-tree cues, and manifest contents.
- **Rationale**: GraphQL significantly reduces network round-trips and protects the application from GitHub's strict REST API rate limits.

## Decision 8: Use fast LLM tiers for probabilistic semantic analysis
- **Decision**: The worker will invoke speed-optimized LLMs (e.g., Gemini 1.5 Flash or GPT-4o-mini) to infer project architecture, purpose, and risks based on sanitized README and file-tree contexts.
- **Rationale**: Fast models are essential to meet the 15-30 second latency budget required for a fluid interactive demo.
- **Alternatives considered**:
  - Heavy reasoning models (e.g., GPT-4o, Gemini 1.5 Pro): Rejected because their high latency destroys the real-time UX feel of the tool.

## Decision 9: Strict Pydantic contracts across all boundaries
- **Decision**: Job submission, Redis state payloads, GraphQL responses, LLM Prompts, structured LLM outputs, and UI responses MUST pass through strict Pydantic validation.
- **Rationale**: In a distributed event-driven system, enforcing data contracts at every boundary is critical to prevent cascading failures and LLM hallucinations from corrupting the database.

## Resolved Clarifications
- **Template engine**: Jinja2 (Progressive rendering).
- **UX mode**: Single-page dashboard with short polling and optimistic UI updates.
- **Gateway pattern**: Stateless FastAPI Orchestrator.
- **Broker and state cache**: Redis (abstracted via interfaces).
- **Background execution**: Celery worker in a dedicated container.
- **Architecture Pattern**: Ports and Adapters / Dependency Injection.
- **Database**: PostgreSQL (Compose) / SQLite (Local fallback).
- **Ingestion boundary**: GitHub GraphQL v4 (Single query).
- **AI tier**: Speed-optimized models (Gemini Flash / GPT-4o-mini) with strict JSON structured outputs.
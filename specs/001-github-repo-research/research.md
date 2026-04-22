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

## Decision 3: Use Redis for job-state cache only; replace queue broker with SQS (ElasticMQ locally)
- **Decision**: Redis retains its single role as a short-lived key-value cache for job-state tracking (`pending`, `processing`, `completed`, `failed`) and AI-result caching. The message queue role previously assigned to Redis-as-Celery-broker is replaced by SQS-compatible messaging: **ElasticMQ** in local/Docker Compose environments and AWS SQS in production. The `IMessageQueue` port abstracts both so business logic is identical in all environments.
- **Rationale**: Separating state cache (Redis) from transport (SQS/ElasticMQ) gives each component a clear, single responsibility. ElasticMQ speaks the full AWS SQS API over HTTP, which means the same `boto3`/`aiobotocore` client code that runs against ElasticMQ in Compose will work unmodified against real AWS SQS in production. Celery is removed because its routing model, beat scheduler, and result-backend plumbing add operational overhead that is unnecessary when the only workflow is a simple linear research pipeline.
- **Alternatives considered**:
  - Keep Redis as unified broker + Celery: Rejected because Celery couples task routing, worker concurrency, and serialization into a single opinionated runtime that is hard to swap or test without a live broker, and its scheduling machinery is unused by this feature.
  - RabbitMQ: Rejected because ElasticMQ/SQS is a more natural fit for AWS-aligned production deployments and has a simpler local Docker image.

## Decision 4: Replace Celery workers with an async SQS-polling worker process
- **Decision**: Background job execution is handled by a lightweight **async worker** (`app/research/worker/sqs_worker.py`) that runs as a separate container process, continuously long-polls the SQS queue (via `aiobotocore`), deserialises each message into a validated `ResearchJobMessage`, runs the research pipeline, and deletes the message on success (or leaves it for DLQ on repeated failure).
- **Rationale**: An explicit polling loop is simpler to reason about, test, and observe than a Celery worker. It has no hidden state machine, no result backend, and no broker-specific serialization format. The entire worker is a single async function that can be unit-tested by injecting a mock SQS port. Visibility timeout and the dead-letter queue (DLQ) replace Celery's retry and ack semantics, giving the same at-least-once delivery guarantee without the Celery runtime.
- **Alternatives considered**:
  - FastAPI `BackgroundTasks`: Rejected because it runs in the same event loop/process, preventing horizontal scaling and risking API starvation during heavy LLM tasks.
  - Keep Celery with SQS broker: Rejected because using Celery only as a thin wrapper around SQS removes the main rationale for keeping Celery while retaining its operational footprint.

## Decision 4b: Use ElasticMQ for local SQS simulation in Docker Compose
- **Decision**: Docker Compose will include an **ElasticMQ** service (`softwaremill/elasticmq-native`) listening on port `9324`. The `IMessageQueue` adapter will point to `http://localhost:9324` in development and to the real AWS SQS endpoint in production, controlled entirely by environment variables (`SQS_ENDPOINT_URL`, `SQS_QUEUE_URL`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`).
- **Rationale**: ElasticMQ provides a complete SQS-compatible REST API with queue creation, send, receive, delete, and DLQ configuration. Developers get a realistic integration surface locally without AWS credentials. The same `aiobotocore` client and `IMessageQueue` adapter code runs in all environments.
- **Alternatives considered**:
  - LocalStack: More comprehensive but heavier and slower to start; ElasticMQ is a single-binary image dedicated to SQS and starts in under 2 seconds.
  - Moto (in-process mock): Useful for unit tests but cannot simulate multi-process Compose deployments where API and worker are separate containers.

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
- **Queue transport**: SQS / ElasticMQ (local) via `IMessageQueue` port and `aiobotocore` adapter.
- **State cache**: Redis (abstracted via `IStateCache` interface, queue role removed).
- **Background execution**: Async SQS-polling worker in a dedicated container (`app/research/worker/sqs_worker.py`).
- **Architecture Pattern**: Ports and Adapters / Dependency Injection.
- **Database**: PostgreSQL (Compose) / SQLite (Local fallback).
- **Ingestion boundary**: GitHub GraphQL v4 (Single query).
- **AI tier**: Speed-optimized models (Gemini Flash / GPT-4o-mini) with strict JSON structured outputs.
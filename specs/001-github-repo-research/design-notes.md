# System Design — AI-Native GitHub Repository Research Tool

## 1. High-Level Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│  Browser / API Client                                                │
│  POST /v1/research        GET /v1/research/{job_id}/status           │
└────────────────┬──────────────────────────┬─────────────────────────┘
                 │ HTTP                      │ HTTP (short-poll, 2 s)
┌────────────────▼──────────────────────────▼─────────────────────────┐
│  FastAPI — Stateless API Process                                     │
│  ┌──────────────┐  ┌─────────────────────────────────────────────┐  │
│  │ URL Validator│  │ ResearchOrchestrationService                │  │
│  │ (sync, pure) │  │  • validate → fetch GitHub (GraphQL)        │  │
│  └──────────────┘  │  • persist initial job record (PostgreSQL)  │  │
│                    │  • write pending state (Redis)              │  │
│                    │  • enqueue ResearchJobMessage (SQS)         │  │
│                    │  • return JobAcceptedResponse + job_id      │  │
│                    └─────────────────────────────────────────────┘  │
└────────────────────────────────┬────────────────────────────────────┘
                                 │ SQS message (JSON, Pydantic-serialised)
                    ┌────────────▼────────────────────────────────────┐
                    │  ElasticMQ (local) / AWS SQS (prod)             │
                    │  main queue  +  dead-letter queue (DLQ)        │
                    └────────────┬────────────────────────────────────┘
                                 │ long-poll receive
┌────────────────────────────────▼────────────────────────────────────┐
│  Async SQS Worker Process  (sqs_worker.py)                          │
│                                                                      │
│  ┌─────────────┐   ┌──────────────────┐   ┌─────────────────────┐  │
│  │ GitHub      │   │ Context          │   │ LLM Adapter         │  │
│  │ Adapter     │──▶│ Sanitizer        │──▶│ (structured output) │  │
│  │ (GraphQL)   │   │ • filter noise   │   │ • GPT-4o-mini /     │  │
│  └─────────────┘   │ • redact inject  │   │   Gemini Flash      │  │
│                    │ • truncate tokens│   └──────────┬──────────┘  │
│                    └──────────────────┘              │ StructuredAIResponse
│                                                      ▼             │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ Report Renderer  →  ResearchReport (Markdown + JSON)         │  │
│  └───────────────────────────┬──────────────────────────────────┘  │
│                               │                                     │
│           ┌───────────────────┼──────────────────┐                 │
│           ▼                   ▼                  ▼                 │
│      PostgreSQL           Redis cache        delete SQS msg        │
│  (final report,          (state snapshot,   (or leave for DLQ)    │
│   job record)             AI result TTL)                           │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 2. Request Lifecycle

```
Client                  API Process              Worker Process
  │                          │                        │
  │─── POST /v1/research ───▶│                        │
  │                          │── validate URL         │
  │                          │── fetch GitHub (GraphQL)│
  │                          │── INSERT job (pending) │
  │                          │── SET Redis state      │
  │                          │── SQS.send_message ───▶│
  │◀── 202 + job_id ─────────│                        │
  │                          │                 │ receive message
  │─── GET /status ─────────▶│                 │ update state → processing
  │◀── {status: processing} ─│                 │ fetch GitHub (full context)
  │                          │                 │ sanitize + truncate
  │─── GET /status ─────────▶│                 │ call LLM → StructuredAIResponse
  │◀── {status: processing} ─│                 │ render ResearchReport
  │                          │                 │ save to PostgreSQL
  │                          │                 │ SET Redis state → completed
  │                          │                 │ delete SQS message
  │─── GET /status ─────────▶│                 │
  │◀── {status: completed,   │                 │
  │     report: ...} ────────│                 │
```

---

## 3. Component Responsibilities

| Component | Single Responsibility |
|---|---|
| `url_validator.py` | Parse and validate GitHub repository URL; reject non-root, gist, issue, or private forms |
| `github_adapter.py` | Execute one GitHub GraphQL query; map response to `RepositoryRawContext` |
| `context_sanitizer.py` | Filter noise, redact prompt injection, deterministically truncate to token budget |
| `llm_adapter.py` | Build structured-output prompt; call LLM; parse and validate `StructuredAIResponse` |
| `orchestration.py` | Accept job, enqueue, return `JobAcceptedResponse`; owned by API process |
| `pipeline.py` | Execute full research workflow end-to-end; owned by worker process |
| `report_renderer.py` | Merge deterministic facts + AI insights into `ResearchReport` |
| `sqs_worker.py` | Long-poll SQS; dispatch messages to `execute_research_pipeline`; handle ack/nack |
| `crud_research.py` | Persist `ResearchJobRecord` and `ResearchReport` to PostgreSQL via SQLAlchemy |
| `redis_adapter.py` | Read/write `ResearchJobStateSnapshot` as short-lived keys for the polling path |

---

## 4. Data Flow and Contracts

Every stage boundary is a typed Pydantic v2 model. No dict is passed between layers.

```
ResearchRequest          (client → API)
    │ url_validator
    ▼
RepositoryTarget         (owner, repo, branch — pure value object)
    │ github_adapter
    ▼
RepositoryRawContext     (metadata, readme_text, tree_entries, commit_sha, ...)
    │ context_sanitizer
    ▼
LLMPromptPayload         (sanitised_readme, filtered_tree, warnings, token_count)
    │ llm_adapter
    ▼
StructuredAIResponse     (summary, architecture, tech_stack, health, risks, confidence)
    │ report_renderer
    ▼
ResearchReport           (deterministic_facts, ai_insights, warnings, markdown_body)
    │ crud / redis
    ▼
ResearchJobStateSnapshot (job_id, status, partial data — Redis, TTL)
ResearchJobRecord        (job_id, status, report FK — PostgreSQL, permanent)
```

---

## 5. Hexagonal Architecture — Ports and Adapters

Domain services depend only on abstract interfaces. Concrete implementations are injected at process startup.

```
app/research/ports/
├── IGitHubClient     fetch_repository_context(target) → RepositoryRawContext
├── ILLMClient        analyze(payload) → StructuredAIResponse
├── IMessageQueue     send_message(msg) / receive_messages() / delete_message()
└── IStateCache       get_state(job_id) / set_state(snapshot)

app/research/adapters/
├── github_adapter.py   → GitHubGraphQLAdapter   implements IGitHubClient
├── llm_adapter.py      → OpenAIAdapter           implements ILLMClient
├── sqs_adapter.py      → SQSAdapter              implements IMessageQueue
└── redis_adapter.py    → RedisStateCache         implements IStateCache
```

Tests inject `InMemoryStateCache`, `StubMessageQueue`, and `FakeGitHubClient` — zero infrastructure required.

---

## 6. Storage Strategy

| Store | What Is Stored | TTL / Retention | Why |
|---|---|---|---|
| **Redis** | `ResearchJobStateSnapshot` | 1 h default | Sub-millisecond hot read for every status poll; evicted once job is terminal |
| **Redis** | AI result cache (keyed by `owner/repo@commit_sha`) | 24 h default | Avoid re-invoking LLM for unchanged repository state |
| **PostgreSQL** | `ResearchJobRecord` + `ResearchReport` | Permanent | Durable source of truth; reloadable after Redis eviction |

---

## 7. Failure Modes and Graceful Degradation

| Failure | System Behaviour |
|---|---|
| GitHub GraphQL error / rate limit | Job marked `failed`; client receives deterministic error response; no LLM spend |
| LLM timeout or quota exhaustion | Deterministic GitHub-backed report returned; AI sections labelled "temporarily unavailable" |
| LLM returns malformed JSON | Up to N repair retries; on exhaustion, fallback report saved |
| Prompt injection in README | `context_sanitizer` redacts matching patterns before prompt construction |
| README or tree exceeds token budget | Deterministically truncated; `PartialAnalysisWarning` appended to report |
| Worker crash mid-pipeline | SQS visibility timeout expires; message re-delivered (at-least-once); idempotent job ID prevents duplicates |
| Repeated failure (N+ redeliveries) | Message routed to DLQ; job surfaced as permanently failed |
| Redis unavailable | Worker falls back to PostgreSQL-only state reads; polling latency degrades gracefully |
| Unknown `job_id` on status poll | 404 returned immediately; no blocking or misreported state |

---

## 8. Design Trade-offs

| Decision | Gained | Sacrificed |
|---|---|---|
| **Short polling** vs. WebSockets | Zero persistent-connection complexity; horizontally scalable API | ~2 s update granularity instead of real-time push |
| **SQS async worker** vs. Celery | Simple linear loop; no result backend; independently scalable | Less built-in queue-depth visibility; DLQ monitoring is manual |
| **Ports & Adapters** vs. direct imports | Full infrastructure replaceability; domain logic testable in isolation | More files and wiring; steeper onboarding curve |
| **GitHub GraphQL v4** vs. REST | Single round-trip; typed schema; lower rate-limit risk | Query complexity; some repo metadata only available via REST |
| **Fast LLM tier** (GPT-4o-mini / Gemini Flash) | Meets 30 s latency budget | Lower reasoning depth for architecturally complex repos |
| **Regex prompt-injection redaction** vs. LLM-based moderation | Deterministic, zero latency, no extra API call | May redact benign README content; acceptable for MVP |
| **Commit-SHA cache key** vs. semantic cache | Exact, zero-cost freshness check | No reuse across repositories with similar profiles |

---

## 9. What Would Be Improved With More Time

1. **Streaming LLM output** — Stream tokens to the browser as they arrive, eliminating the 5–15 s blank wait before the AI section appears.

2. **Manifest-aware context extraction** — Parse `package.json`, `pyproject.toml`, `go.mod`, `Cargo.toml`, and CI YAML to deliver higher-signal, lower-token evidence to the LLM.

3. **Semantic AI result cache with `pgvector`** — Replace SHA-keyed Redis cache with vector similarity lookup so structurally similar repositories reuse prior insights.

4. **DLQ monitoring worker** — Scan the DLQ on a schedule, surface permanently failed jobs in the UI, and emit structured alerts.

5. **Token-bucket rate-limit controller** — Global per-provider budget tracker to prevent LLM quota exhaustion under burst load without relying solely on provider-side errors.

6. **Testcontainers integration tests** — Replace moto-based SQS unit tests with full container-backed tests (ElasticMQ + Redis + PostgreSQL) to eliminate mock drift.

7. **Report diff and history** — Store multiple analysis runs per repository; surface a structured diff so users can observe how a repository evolves between commits.

---

## 10. How AI Tools Were Used

| Stage | Usage |
|---|---|
| **Spec & plan authoring** | GitHub Copilot generated `spec.md`, `plan.md`, `research.md`, and `data-model.md` from a natural language brief via the Speckit workflow |
| **Architecture decisions** | Copilot drafted the nine design decisions in `research.md` from the spec's constraint set; each was reviewed and accepted manually |
| **Service implementation** | Copilot generated initial `orchestration.py`, `pipeline.py`, `context_sanitizer.py`, `report_renderer.py`, and `url_validator.py`; port interfaces and adapter stubs were auto-scaffolded |
| **Prompt engineering** | Copilot drafted the structured-output system prompt in `llm_adapter.py`, including JSON schema anchor and injection-redaction wrapper |
| **Test scaffolding** | Copilot generated `test_adapter_conformance.py` and `conftest.py` fixtures |

Key human decisions: remove Celery in favour of a lightweight async worker; choose ElasticMQ over LocalStack for local SQS simulation; enforce the ports-and-adapters boundary as a non-negotiable rule.

# Data Model: GitHub Repository Research Tool (MVP)

## Overview

This artifact documents the simplified, event-driven data contracts for the MVP architecture. To minimize boilerplate while maintaining strict validation, we use Pydantic to enforce contracts at three primary boundaries: 
1. **API Layer** (Client <-> Gateway)
2. **Worker Layer** (Gateway <-> SQS/ElasticMQ <-> Async Polling Worker)
3. **AI Layer** (Worker <-> LLM).

---

## 1. API Contracts (Client ↔ FastAPI)

### ResearchRequest
The absolute minimum input required from the user.
| Field | Type | Required | Validation |
|-------|------|----------|------------|
| url | string | Yes | Must be a valid `https://github.com/{owner}/{repo}` format. |
| options | object | No | Optional client options for analysis tuning. |

### JobAcceptedResponse
Returned instantly when the Orchestrator accepts the URL.
| Field | Type | Required | Validation |
|-------|------|----------|------------|
| job_id | string | Yes | UUID v4 |
| status | string | Yes | Hardcoded to `pending` |

### PollingStatusResponse
Returned every 2 seconds when the frontend polls `GET /api/status/{job_id}`.
| Field | Type | Required | Validation |
|-------|------|----------|------------|
| job_id | string | Yes | UUID v4 |
| status | string | Yes | `pending`, `processing`, `completed`, or `failed` |
| progress_msg | string | Yes | e.g., "AI is analyzing the README..." |
| instant_data | InstantMetadata | No | Present if basic GitHub GraphQL data is fetched |
| report | FinalResearchReport| No | Present ONLY when status is `completed` |
| ai_fallback | boolean | No | `true` if AI stage failed and deterministic fallback is used |
| ai_fallback_reason | string | No | Present when `ai_fallback` is `true` |
| error | string | No | Present ONLY when status is `failed` |

---

## 2. Internal / Worker Contracts (FastAPI ↔ SQS/ElasticMQ ↔ Async Worker)

### ResearchJobMessage  *(SQS message body — JSON serialised)*
The payload placed on the SQS queue by the API Gateway and consumed by the polling worker. The worker validates this with strict Pydantic parsing before executing any pipeline stage; messages that fail validation are sent directly to the Dead-Letter Queue (DLQ).
| Field | Type | Required | Validation |
|-------|------|----------|------------|
| job_id | string | Yes | UUID v4; must match an existing `ResearchJobRecord` |
| repo_url | string | Yes | Canonical `https://github.com/{owner}/{repo}` URL |
| enqueued_at | datetime | Yes | UTC ISO-8601 timestamp set by Gateway |
| attempt | integer | Yes | Starts at 1; incremented by worker on retry before re-enqueue |
| options | object | No | Optional analysis tuning forwarded from `ResearchRequest` |

**Queue configuration**
- Visibility timeout: 120 s (covers worst-case LLM round-trip)
- Max receive count before DLQ: 3
- DLQ name: `research-jobs-dlq`
- Endpoint (local): `http://elasticmq:9324` (Compose service name)
- Environment variables: `SQS_ENDPOINT_URL`, `SQS_QUEUE_URL`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`

### ParsedRepoTarget
Used internally by the Worker after regex parsing the input URL.
| Field | Type | Required | Validation |
|-------|------|----------|------------|
| owner | string | Yes | GitHub owner slug rules |
| repo | string | Yes | GitHub repo name rules |

### InstantMetadata (Deterministic Data)
The raw, factual data fetched from GitHub GraphQL in Phase 1 of the Worker.
| Field | Type | Required | Validation |
|-------|------|----------|------------|
| name | string | Yes | Non-empty |
| description | string | No | Nullable |
| stars | integer | Yes | >= 0 |
| forks | integer | Yes | >= 0 |
| primary_lang | string | No | e.g., "Python", "TypeScript" |
| last_commit_at| datetime | No | UTC Timestamp |

---

## 3. AI / LLM Contracts (Celery ↔ AI Provider)

### StructuredAIResponse
**CRITICAL:** This is the strictly typed Pydantic model passed to the LLM (using Structured Outputs / JSON Mode) to force the AI to return data in this exact shape.
| Field | Type | Required | Validation |
|-------|------|----------|------------|
| project_purpose| string | Yes | Max 3 sentences explaining what the repo does. |
| tech_stack | list[string] | Yes | Inferred technologies (e.g., ["FastAPI", "Redis"]) |
| architecture | string | Yes | e.g., "Monolith", "Microservices", "Library" |
| risk_level | string | Yes | `Low`, `Medium`, or `High` (based on activity/issues) |
| ai_confidence | string | Yes | `High` or `Low` (Low if README is missing/empty) |
| limitations | list[string] | No | Evidence gaps, truncation notes, or inference limits |

---

## 4. Persistence Model (Database)

### FinalResearchReport
The single, consolidated document saved to PostgreSQL/SQLite (JSONB) and returned to the UI upon completion.
| Field | Type | Required | Validation |
|-------|------|----------|------------|
| job_id | string | Yes | Primary Key / UUID |
| repository_url| string | Yes | Canonical URL |
| deterministic_data | InstantMetadata | Yes | The factual GitHub metrics |
| ai_insights | StructuredAIResponse | No | Present when AI stage succeeds |
| ai_fallback_reason | string | No | Present when deterministic-only fallback is used |
| created_at | datetime | Yes | UTC Timestamp |

---

## Lifecycle States (Simplified)

The MVP limits job states to a simple, linear flow to avoid race conditions:

1. `pending`: URL validated, Job ID generated, `ResearchJobMessage` published to SQS queue, state written to Redis.
2. `processing`: SQS polling worker received the message (visibility timeout active). Worker updates Redis state and progress_msg at key milestones: "Fetching GitHub data" → "Running AI analysis".
3. `completed`: Worker finished both GraphQL and LLM calls, saved `FinalResearchReport` to DB, updated Redis state, and deleted the SQS message (ack).
4. `failed`: Worker hit max retry or unrecoverable error (e.g., invalid repo, LLM timeout after retries). Error message is saved to Redis; SQS message is abandoned to the DLQ after exhausting the max-receive-count.
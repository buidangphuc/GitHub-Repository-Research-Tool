# Data Model: GitHub Repository Research Tool (MVP)

## Overview

This artifact documents the simplified, event-driven data contracts for the MVP architecture. To minimize boilerplate while maintaining strict validation, we use Pydantic to enforce contracts at three primary boundaries: 
1. **API Layer** (Client <-> Gateway)
2. **Worker Layer** (Gateway <-> Redis <-> Celery)
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

## 2. Internal / Worker Contracts (FastAPI ↔ Celery)

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

1. `pending`: URL validated, Job ID generated, task sitting in Redis Queue.
2. `processing`: Celery Worker picked up the task. (Optional: Can update `progress_msg` in Redis to show "Fetching GitHub Data" vs "Running AI Analysis").
3. `completed`: Worker finished both GraphQL and LLM calls, saved `FinalResearchReport` to DB, and updated Redis.
4. `failed`: Celery task threw an exception (e.g., Rate Limit, Invalid Repo, LLM Timeout). Error message is saved to Redis.
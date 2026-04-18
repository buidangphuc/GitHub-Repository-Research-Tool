# Quickstart: GitHub Repository Research Tool

## Goal

Run the event-driven demo locally with one Docker Compose command, open the
Jinja2 dashboard, submit a repository URL, and watch the UI transition from
instant job acceptance to completed AI insight delivery through short polling.

## Prerequisites

- Docker and Docker Compose available locally
- GitHub token for live GitHub GraphQL access
- Optional OpenAI-compatible API key for AI insight generation

## Configuration

For MVP, keep configuration simple and set values in Docker settings (for
example via `.env` used by Docker Compose).

Minimum recommended values:

- `GITHUB_TOKEN` (required)
- `OPENAI_API_KEY` (optional)

All other runtime values can use Docker defaults for local demo.

## Run The Full Demo Stack

```bash
docker compose up --build
```

This should start:

- FastAPI app container
- Celery worker container
- Redis container
- PostgreSQL container

Open the research page in a browser:

```text
http://127.0.0.1:8000/research
```

## Smoke Test Scenarios

### Submit And Poll A Valid Repository

1. Submit a URL such as `https://github.com/tiangolo/fastapi`.
2. Confirm the page immediately renders a dashboard shell with a loading AI
   panel.
3. Confirm the API returns a `job_id` and polling URL without waiting for the
   full worker result.
4. Confirm the browser polls every 2 seconds until the AI panel is replaced by
   completed insights.

### Warm Cache Or Instant Snapshot

1. Submit the same repository twice.
2. Confirm the second run shows instant overview facts more quickly than the
   first run.
3. Confirm the AI panel still follows the background completion flow when the
   final result is not already persisted.

### Missing AI Configuration

1. Leave `OPENAI_API_KEY` unset.
2. Submit a valid public repository.
3. Confirm the job still reaches a terminal state and the UI shows factual
   sections plus an unavailable AI panel instead of hanging forever.

### Invalid Repository URL

1. Submit an invalid value such as `https://github.com/explore`.
2. Confirm no background job is enqueued and the user sees a validation error
   immediately.

### Worker Or Provider Failure

1. Simulate a worker failure or provider failure in tests.
2. Confirm the polling endpoint transitions the job to `failed` and returns a
   clear message instead of leaving the dashboard in a permanent loading state.

## Test Focus

- Route tests for `GET /research`, `POST /api/v1/research/jobs`, and `GET /api/v1/research/jobs/{job_id}`
- Job acceptance and job state transition tests
- Celery task tests for GraphQL ingestion, AI execution, and final persistence
- Redis-backed polling state tests
- Persistence tests for completed research results
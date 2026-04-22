# GitHub Repository Research Tool

FastAPI + Celery application for researching public GitHub repositories. The app accepts a repository URL, returns a background `job_id`, polls status from Redis, and stores the final deterministic + AI-assisted report in PostgreSQL.

## Runtime Model

- Dependencies are managed with `uv`
- The default way to run the stack is Docker Compose
- Compose starts the API app, Celery worker, PostgreSQL, and Redis together

## Requirements

- Docker with Docker Compose
- `uv` for local dependency and test commands

## Quick Start

1. Create a local env file.

```bash
cp .env.example .env
```

2. Fill in at least `GITHUB_TOKEN`. `OPENAI_API_KEY` is optional; without it the app falls back to deterministic-only reports.

3. Start the full stack.

```bash
docker compose up --build
```

4. Open the app.

```text
http://127.0.0.1:8000/research
```

5. Open the API docs.

```text
http://127.0.0.1:8000/docs
```

## Development Compose Override

For bind-mounted code and auto-reload:

```bash
docker compose -f docker-compose.yaml -f docker-compose.local.yaml up --build
```

This keeps infrastructure in containers and runs the API/worker with `uv run` commands against the mounted source tree.

## Local Commands With uv

Install dependencies into the local `.venv`:

```bash
uv sync --dev
```

Run the API outside Docker if you only want infra in Compose:

```bash
uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Run the focused research test suite:

```bash
uv run pytest tests/research -q
```

Regenerate the lock file and exported requirements snapshot after dependency changes:

```bash
uv lock
uv export --no-dev --format requirements-txt -o requirements.txt
```

## Services Started By Compose

- `app`: FastAPI server on port `8000`
- `worker`: Celery worker for background repository analysis
- `postgres`: PostgreSQL primary persistence
- `redis`: Redis for Celery broker/result backend and status snapshots

## Important Environment Variables

- `GITHUB_TOKEN`: required for GitHub GraphQL calls
- `OPENAI_API_KEY`: optional AI analysis provider key
- `POSTGRES_*`: PostgreSQL connection values
- `REDIS_*`: Redis connection values
- `RESEARCH_POLL_INTERVAL_SECONDS`: browser polling cadence
- `RESEARCH_AI_TOKEN_BUDGET`: deterministic truncation budget for AI context

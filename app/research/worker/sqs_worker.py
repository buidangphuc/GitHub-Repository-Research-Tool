from __future__ import annotations

import asyncio

from app.research.adapters.github_adapter import GitHubGraphQLAdapter
from app.research.adapters.llm_adapter import LLMAdapter
from app.research.adapters.redis_adapter import RedisStateCacheAdapter
from app.research.adapters.sqs_adapter import SQSMessageQueueAdapter
from app.research.crud.crud_research import update_job_status
from app.research.schema import ResearchJobStateSnapshot
from app.research.service.pipeline import execute_research_pipeline
from common.log import build_log_context, clear_request_id, log, set_request_id
from core.conf import settings
from database.db import AsyncSessionLocal
from utils.timezone import timezone


async def run_worker() -> None:
    queue = SQSMessageQueueAdapter()
    state_cache = RedisStateCacheAdapter()
    github_client = GitHubGraphQLAdapter()
    llm_client = LLMAdapter()

    await queue.ensure_queues()
    log.info("Research SQS worker started")

    while True:
        received_messages = await queue.receive(
            max_messages=1,
            wait_time_seconds=settings.RESEARCH_SQS_WAIT_TIME_SECONDS,
        )
        if not received_messages:
            continue

        for received in received_messages:
            set_request_id(received.body.job_id)
            try:
                await execute_research_pipeline(
                    received.body,
                    session_factory=AsyncSessionLocal,
                    state_cache=state_cache,
                    github_client=github_client,
                    llm_client=llm_client,
                )
            except Exception as exc:  # noqa: BLE001
                log.error(
                    "Research pipeline failed",
                    extra=build_log_context(
                        job_id=received.body.job_id,
                        stage="worker",
                        failure_reason=str(exc),
                    ),
                )
                if received.receive_count >= settings.RESEARCH_MAX_QUEUE_ATTEMPTS:
                    async with AsyncSessionLocal() as session:
                        await update_job_status(
                            session,
                            received.body.job_id,
                            status="failed",
                            progress_msg="Research failed after maximum retry attempts",
                            error=str(exc),
                        )
                    await state_cache.set_state(
                        ResearchJobStateSnapshot(
                            job_id=received.body.job_id,
                            status="failed",
                            progress_msg="Research failed after maximum retry attempts",
                            updated_at=timezone.now(),
                            error=str(exc),
                        )
                    )
                await queue.change_visibility(received.receipt_handle, 0)
            else:
                await queue.delete(received.receipt_handle)
            finally:
                clear_request_id()


def main() -> None:
    asyncio.run(run_worker())


if __name__ == "__main__":
    main()
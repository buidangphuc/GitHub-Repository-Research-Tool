from __future__ import annotations

from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.research.crud.crud_research import (
    create_job_record,
    save_final_report,
    update_job_status,
)
from app.research.ports import IGitHubClient, IMessageQueue, IStateCache
from app.research.schema import (
    JobAcceptedResponse,
    ResearchJobMessage,
    ResearchJobStateSnapshot,
    ResearchRequest,
)
from app.research.service.report_renderer import build_research_report
from app.research.service.url_validator import parse_github_repository_url
from common.log import build_log_context, log
from utils.timezone import timezone


class ResearchOrchestrationService:
    def __init__(
        self,
        *,
        session: AsyncSession,
        queue: IMessageQueue,
        state_cache: IStateCache,
        github_client: IGitHubClient,
    ):
        self.session = session
        self.queue = queue
        self.state_cache = state_cache
        self.github_client = github_client

    @staticmethod
    def build_ai_cache_key(owner: str, repo: str, commit_sha: str) -> str:
        return f"{owner}/{repo}@{commit_sha}"

    async def submit(self, request: ResearchRequest) -> JobAcceptedResponse:
        target = parse_github_repository_url(request.url)
        raw_context = await self.github_client.fetch_repository_context(target)
        job_id = str(uuid4())
        cache_key = self.build_ai_cache_key(
            target.owner,
            target.repo,
            raw_context.commit_sha,
        )

        await create_job_record(
            self.session,
            job_id=job_id,
            repository_url=raw_context.repository_url,
            owner=target.owner,
            repo=target.repo,
            status="pending",
            commit_sha=raw_context.commit_sha,
            instant_data=raw_context.instant_data.model_dump(mode="json"),
            progress_msg="Repository metadata fetched",
            ai_cache_key=cache_key,
        )

        snapshot = ResearchJobStateSnapshot(
            job_id=job_id,
            status="pending",
            progress_msg="Repository metadata fetched",
            updated_at=timezone.now(),
            instant_data=raw_context.instant_data,
        )
        await self.state_cache.set_state(snapshot)

        cached_ai = await self.state_cache.get_cached_ai_result(cache_key)
        if cached_ai is not None:
            report = build_research_report(
                job_id=job_id,
                raw_context=raw_context,
                ai_insights=cached_ai,
                ai_fallback_reason=None,
            )
            await save_final_report(
                self.session,
                job_id=job_id,
                repository_url=report.repository_url,
                commit_sha=raw_context.commit_sha,
                deterministic_data=report.deterministic_data.model_dump(mode="json"),
                ai_insights=report.ai_insights.model_dump(mode="json"),
                ai_fallback=False,
                ai_fallback_reason=None,
                markdown_report=report.markdown_report,
            )
            await update_job_status(
                self.session,
                job_id,
                status="completed",
                progress_msg="Completed from cache",
            )
            await self.state_cache.set_state(
                snapshot.model_copy(
                    update={
                        "status": "completed",
                        "progress_msg": "Completed from cache",
                        "updated_at": timezone.now(),
                    }
                )
            )
            log.info(
                "Research request completed from cache",
                extra=build_log_context(job_id=job_id, stage="submit"),
            )
            return JobAcceptedResponse(job_id=job_id)

        message = ResearchJobMessage(
            job_id=job_id,
            repo_url=target.canonical_url,
            enqueued_at=timezone.now(),
            attempt=1,
            options=request.options,
        )
        try:
            await self.queue.send(message)
        except Exception as exc:  # noqa: BLE001
            await update_job_status(
                self.session,
                job_id,
                status="failed",
                progress_msg="Queue enqueue failed",
                error=str(exc),
            )
            await self.state_cache.set_state(
                snapshot.model_copy(
                    update={
                        "status": "failed",
                        "progress_msg": "Queue enqueue failed",
                        "updated_at": timezone.now(),
                        "error": str(exc),
                    }
                )
            )
            raise

        log.info(
            "Research request accepted",
            extra=build_log_context(job_id=job_id, stage="submit"),
        )
        return JobAcceptedResponse(job_id=job_id)
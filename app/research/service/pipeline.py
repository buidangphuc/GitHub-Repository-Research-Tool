from __future__ import annotations

from time import perf_counter

from sqlalchemy.ext.asyncio import async_sessionmaker

from app.research.crud.crud_research import save_final_report, update_job_status
from app.research.ports import IGitHubClient, ILLMClient, IStateCache
from app.research.schema import ResearchJobMessage, ResearchJobStateSnapshot
from app.research.service.context_sanitizer import build_prompt_payload
from app.research.service.orchestration import ResearchOrchestrationService
from app.research.service.report_renderer import build_research_report
from app.research.service.url_validator import parse_github_repository_url
from common.exception.errors import ContentPolicyError, LLMUnavailableError
from common.log import build_log_context, log
from utils.timezone import timezone


async def execute_research_pipeline(
    message: ResearchJobMessage,
    *,
    session_factory: async_sessionmaker,
    state_cache: IStateCache,
    github_client: IGitHubClient,
    llm_client: ILLMClient,
) -> None:
    start = perf_counter()
    target = parse_github_repository_url(message.repo_url)
    existing_state = await state_cache.get_state(message.job_id)

    processing_snapshot = ResearchJobStateSnapshot(
        job_id=message.job_id,
        status="processing",
        progress_msg="Fetching GitHub data",
        updated_at=timezone.now(),
        instant_data=existing_state.instant_data if existing_state else None,
    )
    await state_cache.set_state(processing_snapshot)

    async with session_factory() as session:
        await update_job_status(
            session,
            message.job_id,
            status="processing",
            progress_msg="Fetching GitHub data",
            error=None,
        )

        github_started = perf_counter()
        raw_context = await github_client.fetch_repository_context(target)
        github_latency_ms = (perf_counter() - github_started) * 1000
        log.info(
            "Fetched GitHub repository context",
            extra=build_log_context(
                job_id=message.job_id,
                stage="github_fetch",
                latency_ms=github_latency_ms,
            ),
        )

        cache_key = ResearchOrchestrationService.build_ai_cache_key(
            target.owner,
            target.repo,
            raw_context.commit_sha,
        )
        base_snapshot = ResearchJobStateSnapshot(
            job_id=message.job_id,
            status="processing",
            progress_msg="Preparing AI analysis",
            updated_at=timezone.now(),
            instant_data=raw_context.instant_data,
        )
        await state_cache.set_state(base_snapshot)
        await update_job_status(
            session,
            message.job_id,
            commit_sha=raw_context.commit_sha,
            instant_data=raw_context.instant_data.model_dump(mode="json"),
            progress_msg="Preparing AI analysis",
            ai_cache_key=cache_key,
        )

        cached_ai = await state_cache.get_cached_ai_result(cache_key)
        ai_insights = cached_ai
        ai_fallback_reason: str | None = None

        if ai_insights is None:
            prompt_payload = build_prompt_payload(raw_context)
            await state_cache.set_state(
                base_snapshot.model_copy(
                    update={
                        "progress_msg": "Running AI analysis",
                        "updated_at": timezone.now(),
                    }
                )
            )
            llm_started = perf_counter()
            try:
                ai_insights = await llm_client.analyze(prompt_payload)
                if prompt_payload.warnings:
                    existing = list(ai_insights.security_health.limitations)
                    for warning in prompt_payload.warnings:
                        if warning.message not in existing:
                            existing.append(warning.message)
                    ai_insights = ai_insights.model_copy(
                        update={
                            "security_health": ai_insights.security_health.model_copy(
                                update={"limitations": existing}
                            )
                        }
                    )
                await state_cache.set_cached_ai_result(cache_key, ai_insights)
            except (LLMUnavailableError, ContentPolicyError) as exc:
                ai_fallback_reason = str(exc)
                log.warning(
                    "AI analysis fell back to deterministic output",
                    extra=build_log_context(
                        job_id=message.job_id,
                        stage="llm_analysis",
                        failure_reason=ai_fallback_reason,
                    ),
                )
            else:
                llm_latency_ms = (perf_counter() - llm_started) * 1000
                log.info(
                    "Generated structured AI insights",
                    extra=build_log_context(
                        job_id=message.job_id,
                        stage="llm_analysis",
                        latency_ms=llm_latency_ms,
                    ),
                )

        report = build_research_report(
            job_id=message.job_id,
            raw_context=raw_context,
            ai_insights=ai_insights,
            ai_fallback_reason=ai_fallback_reason,
        )
        await save_final_report(
            session,
            job_id=message.job_id,
            repository_url=report.repository_url,
            commit_sha=raw_context.commit_sha,
            deterministic_data=report.deterministic_data.model_dump(mode="json"),
            ai_insights=(
                report.ai_insights.model_dump(mode="json")
                if report.ai_insights is not None
                else None
            ),
            ai_fallback=bool(ai_fallback_reason),
            ai_fallback_reason=ai_fallback_reason,
            markdown_report=report.markdown_report,
        )
        await update_job_status(
            session,
            message.job_id,
            status="completed",
            progress_msg=(
                "Completed with deterministic fallback"
                if ai_fallback_reason
                else "Research completed"
            ),
            error=None,
            ai_cache_key=cache_key,
        )
        await state_cache.set_state(
            ResearchJobStateSnapshot(
                job_id=message.job_id,
                status="completed",
                progress_msg=(
                    "Completed with deterministic fallback"
                    if ai_fallback_reason
                    else "Research completed"
                ),
                updated_at=timezone.now(),
                instant_data=raw_context.instant_data,
                ai_fallback=bool(ai_fallback_reason),
                ai_fallback_reason=ai_fallback_reason,
            )
        )

    total_latency_ms = (perf_counter() - start) * 1000
    log.info(
        "Research pipeline completed",
        extra=build_log_context(
            job_id=message.job_id,
            stage="pipeline",
            latency_ms=total_latency_ms,
            failure_reason=ai_fallback_reason,
        ),
    )
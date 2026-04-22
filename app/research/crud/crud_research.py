from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.research.model.research import FinalResearchReportRecord, ResearchJobRecord

_UNSET = object()


async def create_job_record(
    session: AsyncSession,
    *,
    job_id: str,
    repository_url: str,
    owner: str,
    repo: str,
    status: str = "pending",
    commit_sha: str | None = None,
    instant_data: dict[str, Any] | None = None,
    progress_msg: str = "Repository research queued",
    error: str | None = None,
    ai_cache_key: str | None = None,
) -> ResearchJobRecord:
    record = ResearchJobRecord(
        job_id=job_id,
        repository_url=repository_url,
        owner=owner,
        repo=repo,
        status=status,
        commit_sha=commit_sha,
        instant_data=instant_data,
        progress_msg=progress_msg,
        error=error,
        ai_cache_key=ai_cache_key,
    )
    session.add(record)
    await session.commit()
    await session.refresh(record)
    return record


async def update_job_status(
    session: AsyncSession,
    job_id: str,
    *,
    status: str | object = _UNSET,
    commit_sha: str | None | object = _UNSET,
    instant_data: dict[str, Any] | None | object = _UNSET,
    progress_msg: str | object = _UNSET,
    error: str | None | object = _UNSET,
    ai_cache_key: str | None | object = _UNSET,
) -> ResearchJobRecord | None:
    record = await get_job_by_id(session, job_id)
    if record is None:
        return None

    if status is not _UNSET:
        record.status = status
    if commit_sha is not _UNSET:
        record.commit_sha = commit_sha
    if instant_data is not _UNSET:
        record.instant_data = instant_data
    if progress_msg is not _UNSET:
        record.progress_msg = progress_msg
    if error is not _UNSET:
        record.error = error
    if ai_cache_key is not _UNSET:
        record.ai_cache_key = ai_cache_key

    await session.commit()
    await session.refresh(record)
    return record


async def save_final_report(
    session: AsyncSession,
    *,
    job_id: str,
    repository_url: str,
    commit_sha: str | None,
    deterministic_data: dict[str, Any],
    ai_insights: dict[str, Any] | None,
    ai_fallback: bool,
    ai_fallback_reason: str | None,
    markdown_report: str,
) -> FinalResearchReportRecord:
    stmt = select(FinalResearchReportRecord).where(
        FinalResearchReportRecord.job_id == job_id
    )
    existing = (await session.execute(stmt)).scalar_one_or_none()
    if existing is None:
        existing = FinalResearchReportRecord(
            job_id=job_id,
            repository_url=repository_url,
            commit_sha=commit_sha,
            deterministic_data=deterministic_data,
            ai_insights=ai_insights,
            ai_fallback=ai_fallback,
            ai_fallback_reason=ai_fallback_reason,
            markdown_report=markdown_report,
        )
        session.add(existing)
    else:
        existing.repository_url = repository_url
        existing.commit_sha = commit_sha
        existing.deterministic_data = deterministic_data
        existing.ai_insights = ai_insights
        existing.ai_fallback = ai_fallback
        existing.ai_fallback_reason = ai_fallback_reason
        existing.markdown_report = markdown_report

    await session.commit()
    await session.refresh(existing)
    return existing


async def get_job_by_id(session: AsyncSession, job_id: str) -> ResearchJobRecord | None:
    stmt = select(ResearchJobRecord).where(ResearchJobRecord.job_id == job_id)
    return (await session.execute(stmt)).scalar_one_or_none()
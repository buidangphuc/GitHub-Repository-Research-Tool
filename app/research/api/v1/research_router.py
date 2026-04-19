from __future__ import annotations

from fastapi import APIRouter, Request, status
from fastapi.templating import Jinja2Templates
from sqlalchemy import select

from app.research.dependencies import ResearchServiceDep, StateCacheDep
from app.research.model.research import FinalResearchReportRecord
from app.research.schema import (
    JobAcceptedResponse,
    PollingStatusResponse,
    Problem,
    ResearchJobStateSnapshot,
    ResearchReport,
    ResearchRequest,
)
from common.exception.errors import ResearchProblem
from core.conf import settings
from core.path_conf import BASE_PATH
from database.db import CurrentSession
from utils.request_id import get_request_id
from utils.serializers import MsgSpecJSONResponse

router = APIRouter(tags=["research"])
templates = Jinja2Templates(directory=str(BASE_PATH / "app" / "research" / "templates"))


def _problem_response(problem: ResearchProblem, instance: str) -> MsgSpecJSONResponse:
    payload = problem.to_dict()
    payload.setdefault("instance", instance)
    return MsgSpecJSONResponse(
        status_code=problem.status_code,
        content=payload,
        media_type="application/problem+json",
        headers=problem.headers,
    )


def _unexpected_problem(request: Request, exc: Exception) -> MsgSpecJSONResponse:
    problem = ResearchProblem(
        status_code=500,
        type_="/problems/internal-server-error",
        title="Internal server error",
        detail=str(exc),
        extra={"request_id": get_request_id()},
    )
    return _problem_response(problem, request.url.path)


async def _load_report(
    session: CurrentSession,
    job_id: str,
) -> ResearchReport | None:
    stmt = select(FinalResearchReportRecord).where(
        FinalResearchReportRecord.job_id == job_id
    )
    record = (await session.execute(stmt)).scalar_one_or_none()
    if record is None:
        return None
    return ResearchReport(
        job_id=record.job_id,
        repository_url=record.repository_url,
        deterministic_data=record.deterministic_data,
        ai_insights=record.ai_insights,
        ai_fallback_reason=record.ai_fallback_reason,
        markdown_report=record.markdown_report,
        created_at=record.created_time,
    )


@router.get("/research")
async def research_dashboard(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="research.html",
        context={
            "poll_interval_ms": settings.RESEARCH_POLL_INTERVAL_SECONDS * 1000,
        },
    )


@router.post(
    "/api/v1/research/jobs",
    response_model=JobAcceptedResponse,
    status_code=status.HTTP_202_ACCEPTED,
    responses={
        400: {"model": Problem, "content": {"application/problem+json": {}}},
        404: {"model": Problem, "content": {"application/problem+json": {}}},
        500: {"model": Problem, "content": {"application/problem+json": {}}},
    },
)
async def submit_research_job(
    request: Request,
    payload: ResearchRequest,
    service: ResearchServiceDep,
) -> JobAcceptedResponse | MsgSpecJSONResponse:
    try:
        return await service.submit(payload)
    except ResearchProblem as problem:
        return _problem_response(problem, request.url.path)
    except Exception as exc:  # noqa: BLE001
        return _unexpected_problem(request, exc)


@router.get(
    "/api/v1/research/jobs/{job_id}",
    response_model=PollingStatusResponse,
    responses={
        404: {"model": Problem, "content": {"application/problem+json": {}}},
        500: {"model": Problem, "content": {"application/problem+json": {}}},
    },
)
async def get_research_job_status(
    request: Request,
    job_id: str,
    state_cache: StateCacheDep,
    session: CurrentSession,
) -> PollingStatusResponse | MsgSpecJSONResponse:
    try:
        snapshot = await state_cache.get_state(job_id)
        if snapshot is None:
            report = await _load_report(session, job_id)
            if report is None:
                raise ResearchProblem(
                    status_code=404,
                    type_="/problems/job-not-found",
                    title="Research job not found",
                    detail=f"No research job exists for {job_id}.",
                )
            snapshot = ResearchJobStateSnapshot(
                job_id=job_id,
                status="completed",
                progress_msg="Research completed",
                updated_at=report.created_at,
                instant_data=report.deterministic_data,
                ai_fallback=bool(report.ai_fallback_reason),
                ai_fallback_reason=report.ai_fallback_reason,
            )
        else:
            report = None
            if snapshot.status == "completed":
                report = await _load_report(session, job_id)

        return PollingStatusResponse(
            job_id=snapshot.job_id,
            status=snapshot.status,
            progress_msg=snapshot.progress_msg,
            updated_at=snapshot.updated_at,
            instant_data=snapshot.instant_data,
            report=report,
            ai_fallback=snapshot.ai_fallback,
            ai_fallback_reason=snapshot.ai_fallback_reason,
            error=snapshot.error,
        )
    except ResearchProblem as problem:
        return _problem_response(problem, request.url.path)
    except Exception as exc:  # noqa: BLE001
        return _unexpected_problem(request, exc)
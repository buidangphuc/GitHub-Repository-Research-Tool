from __future__ import annotations

from sqlalchemy import JSON, Boolean, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from common.model import Base, id_key


class ResearchJobRecord(Base):
    __tablename__ = "research_job_records"
    __doc__ = "Research job lifecycle records"

    id: Mapped[id_key] = mapped_column(init=False)
    job_id: Mapped[str] = mapped_column(String(36), unique=True, index=True)
    repository_url: Mapped[str] = mapped_column(String(512), index=True)
    owner: Mapped[str] = mapped_column(String(255), index=True)
    repo: Mapped[str] = mapped_column(String(255), index=True)
    status: Mapped[str] = mapped_column(String(32), index=True, default="pending")
    commit_sha: Mapped[str | None] = mapped_column(String(64), default=None)
    instant_data: Mapped[dict | None] = mapped_column(JSON, default=None)
    progress_msg: Mapped[str] = mapped_column(
        String(255), default="Repository research queued"
    )
    error: Mapped[str | None] = mapped_column(Text, default=None)
    ai_cache_key: Mapped[str | None] = mapped_column(String(512), default=None)


class FinalResearchReportRecord(Base):
    __tablename__ = "final_research_report_records"
    __doc__ = "Persisted final research reports"

    id: Mapped[id_key] = mapped_column(init=False)
    job_id: Mapped[str] = mapped_column(String(36), unique=True, index=True)
    repository_url: Mapped[str] = mapped_column(String(512), index=True)
    deterministic_data: Mapped[dict] = mapped_column(JSON)
    markdown_report: Mapped[str] = mapped_column(Text)
    commit_sha: Mapped[str | None] = mapped_column(String(64), default=None)
    ai_insights: Mapped[dict | None] = mapped_column(JSON, default=None)
    ai_fallback: Mapped[bool] = mapped_column(Boolean, default=False)
    ai_fallback_reason: Mapped[str | None] = mapped_column(Text, default=None)
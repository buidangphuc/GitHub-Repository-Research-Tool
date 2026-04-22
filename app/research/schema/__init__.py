from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

JobStatus = Literal["pending", "processing", "completed", "failed"]
RiskLevel = Literal["Low", "Medium", "High"]
AIConfidence = Literal["High", "Low"]


class ResearchBaseModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Problem(ResearchBaseModel):
    type: str
    title: str
    status: int
    detail: str | None = None
    instance: str | None = None


class ResearchRequest(ResearchBaseModel):
    url: str = Field(min_length=1, max_length=2048)
    options: dict[str, Any] = Field(default_factory=dict)


class JobAcceptedResponse(ResearchBaseModel):
    job_id: str
    status: Literal["pending"] = "pending"


class ParsedRepoTarget(ResearchBaseModel):
    owner: str = Field(min_length=1)
    repo: str = Field(min_length=1)
    canonical_url: str


class LanguageEntry(ResearchBaseModel):
    name: str
    percentage: float  # 0–100, rounded to 1 dp
    color: str | None = None  # GitHub hex color, e.g. "#3178c6"


class CommitEntry(ResearchBaseModel):
    sha: str          # short (7-char) SHA
    message: str      # first line of commit message
    committed_at: datetime
    author_name: str | None = None


class InstantMetadata(ResearchBaseModel):
    name: str = Field(min_length=1)
    description: str | None = None
    stars: int = Field(ge=0)
    forks: int = Field(ge=0)
    primary_lang: str | None = None
    last_commit_at: datetime | None = None
    # --- deterministic fields added from GitHub ---
    owner: str | None = None
    watchers: int | None = None
    open_issues: int | None = None
    license_spdx: str | None = None
    topics: list[str] = Field(default_factory=list)
    languages: list[LanguageEntry] = Field(default_factory=list)
    recent_commits: list[CommitEntry] = Field(default_factory=list)
    is_archived: bool = False
    is_fork: bool = False


class PartialAnalysisWarning(ResearchBaseModel):
    stage: str
    message: str


class RepositoryTreeEntry(ResearchBaseModel):
    name: str
    type: str


class RepositoryRawContext(ResearchBaseModel):
    target: ParsedRepoTarget
    repository_url: str
    default_branch: str
    commit_sha: str
    instant_data: InstantMetadata
    readme_text: str | None = None
    readme_byte_size: int | None = None
    tree_entries: list[RepositoryTreeEntry] = Field(default_factory=list)
    open_issue_count: int | None = None


class LLMPromptPayload(ResearchBaseModel):
    repository_url: str
    cache_key: str
    commit_sha: str
    deterministic_data: InstantMetadata
    prompt_text: str
    warnings: list[PartialAnalysisWarning] = Field(default_factory=list)


class ResearchJobMessage(ResearchBaseModel):
    job_id: str
    repo_url: str
    enqueued_at: datetime
    attempt: int = Field(default=1, ge=1)
    options: dict[str, Any] = Field(default_factory=dict)


class RepoOverview(ResearchBaseModel):
    project_purpose: str
    tech_stack: list[str]
    architecture: str


class SecurityHealth(ResearchBaseModel):
    risk_level: RiskLevel
    ai_confidence: AIConfidence
    findings: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)


class Recommendations(ResearchBaseModel):
    items: list[str]


class StructuredAIResponse(ResearchBaseModel):
    overview: RepoOverview
    security_health: SecurityHealth
    recommendations: Recommendations


class ResearchReport(ResearchBaseModel):
    job_id: str
    repository_url: str
    deterministic_data: InstantMetadata
    ai_insights: StructuredAIResponse | None = None
    ai_fallback_reason: str | None = None
    markdown_report: str
    created_at: datetime


class ResearchJobStateSnapshot(ResearchBaseModel):
    job_id: str
    status: JobStatus
    progress_msg: str
    updated_at: datetime
    instant_data: InstantMetadata | None = None
    ai_fallback: bool | None = None
    ai_fallback_reason: str | None = None
    error: str | None = None


class PollingStatusResponse(ResearchBaseModel):
    job_id: str
    status: JobStatus
    progress_msg: str
    updated_at: datetime
    instant_data: InstantMetadata | None = None
    report: ResearchReport | None = None
    ai_fallback: bool | None = None
    ai_fallback_reason: str | None = None
    error: str | None = None


class ReceivedMessage(ResearchBaseModel):
    receipt_handle: str
    body: ResearchJobMessage
    receive_count: int = Field(ge=1)
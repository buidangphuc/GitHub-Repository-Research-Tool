from __future__ import annotations

from app.research.schema import ResearchReport, RepositoryRawContext, StructuredAIResponse
from utils.timezone import timezone


def build_markdown_report(
    raw_context: RepositoryRawContext,
    ai_insights: StructuredAIResponse | None,
    *,
    ai_fallback_reason: str | None = None,
) -> str:
    d = raw_context.instant_data
    lines = [
        "# Repository Overview",
        f"- Repository: {raw_context.target.owner}/{raw_context.target.repo}",
        f"- Name: {d.name}",
        f"- Description: {d.description or 'No description provided'}",
        f"- Stars: {d.stars}",
        f"- Forks: {d.forks}",
        f"- Watchers: {d.watchers}" if d.watchers is not None else "",
        f"- Open Issues: {d.open_issues}" if d.open_issues is not None else "",
        f"- Primary Language: {d.primary_lang or 'Unknown'}",
        f"- License: {d.license_spdx}" if d.license_spdx else "",
        f"- Archived: Yes" if d.is_archived else "",
        f"- Fork: Yes" if d.is_fork else "",
        f"- Last Commit: {d.last_commit_at or 'Unknown'}",
        "",
    ]
    # Remove blank conditional lines
    lines = [l for l in lines if l != ""]
    lines.append("")

    if d.topics:
        lines.extend(["## Topics", ", ".join(d.topics), ""])

    if d.languages:
        lines.extend(["## Languages"])
        for lang in d.languages:
            lines.append(f"- {lang.name}: {lang.percentage}%")
        lines.append("")

    if d.recent_commits:
        lines.extend(["## Recent Activity"])
        for c in d.recent_commits[:10]:
            author = f" — {c.author_name}" if c.author_name else ""
            lines.append(f"- `{c.sha}` {c.message}{author}")
        lines.append("")

    if ai_insights is not None:
        lines.extend(
            [
                "## Project Insights",
                ai_insights.overview.project_purpose,
                "",
                "## Tech Stack",
            ]
        )
        lines.extend(f"- {item}" for item in ai_insights.overview.tech_stack)
        lines.extend(
            [
                "",
                "## Architecture",
                ai_insights.overview.architecture,
                "",
                "## Security & Health",
                f"- Risk Level: {ai_insights.security_health.risk_level}",
                f"- AI Confidence: {ai_insights.security_health.ai_confidence}",
            ]
        )
        if ai_insights.security_health.findings:
            lines.extend(["", "### Findings"])
            lines.extend(f"- {item}" for item in ai_insights.security_health.findings)
        if ai_insights.security_health.limitations:
            lines.extend(["", "### Limitations"])
            lines.extend(f"- {item}" for item in ai_insights.security_health.limitations)
        if ai_insights.recommendations.items:
            lines.extend(["", "## Recommendations"])
            lines.extend(f"- {item}" for item in ai_insights.recommendations.items)
    else:
        lines.extend(
            [
                "## AI Analysis",
                "AI insights were unavailable for this run.",
                f"- Reason: {ai_fallback_reason or 'No reason provided'}",
            ]
        )

    return "\n".join(lines).strip()


def build_research_report(
    *,
    job_id: str,
    raw_context: RepositoryRawContext,
    ai_insights: StructuredAIResponse | None,
    ai_fallback_reason: str | None,
) -> ResearchReport:
    return ResearchReport(
        job_id=job_id,
        repository_url=raw_context.repository_url,
        deterministic_data=raw_context.instant_data,
        ai_insights=ai_insights,
        ai_fallback_reason=ai_fallback_reason,
        markdown_report=build_markdown_report(
            raw_context,
            ai_insights,
            ai_fallback_reason=ai_fallback_reason,
        ),
        created_at=timezone.now(),
    )
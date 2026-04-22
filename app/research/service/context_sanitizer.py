from __future__ import annotations

import re

from app.research.schema import LLMPromptPayload, PartialAnalysisWarning, RepositoryRawContext
from core.conf import settings

_BLOCKED_PATH_PARTS = {".git", "node_modules", "__pycache__", ".venv", "venv"}
_BLOCKED_SUFFIXES = {
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".webp",
    ".svg",
    ".ico",
    ".pdf",
    ".zip",
    ".tar",
    ".gz",
    ".exe",
    ".bin",
    ".woff",
    ".woff2",
    ".ttf",
}
_UNSAFE_INSTRUCTION_RE = re.compile(
    r"(?i)(ignore\s+previous\s+instructions|system\s*prompt|assistant\s*:|developer\s*:|user\s*:)",
)


def _sanitize_text(value: str) -> str:
    return _UNSAFE_INSTRUCTION_RE.sub("[redacted]", value)


def build_prompt_payload(
    raw_context: RepositoryRawContext,
    *,
    max_context_tokens: int = settings.RESEARCH_AI_TOKEN_BUDGET,
) -> LLMPromptPayload:
    warnings: list[PartialAnalysisWarning] = []
    max_chars = max_context_tokens * 4

    filtered_entries = []
    for entry in raw_context.tree_entries:
        lower_name = entry.name.lower()
        if lower_name in _BLOCKED_PATH_PARTS:
            continue
        if any(lower_name.endswith(suffix) for suffix in _BLOCKED_SUFFIXES):
            continue
        filtered_entries.append(entry)

    readme_text = _sanitize_text((raw_context.readme_text or "").strip())
    tree_text = "\n".join(
        f"- {entry.name} ({entry.type})" for entry in filtered_entries
    )

    header = (
        f"Repository URL: {raw_context.repository_url}\n"
        f"Default branch: {raw_context.default_branch}\n"
        f"Commit SHA: {raw_context.commit_sha}\n"
        f"Stars: {raw_context.instant_data.stars}\n"
        f"Forks: {raw_context.instant_data.forks}\n"
        f"Primary language: {raw_context.instant_data.primary_lang or 'Unknown'}\n"
    )
    template = (
        "<repository_content>\n"
        f"{header}\n"
        "README:\n{readme}\n\n"
        "Top-level structure:\n{tree}\n"
        "</repository_content>"
    )
    prompt_text = template.format(readme=readme_text, tree=tree_text)

    if len(prompt_text) > max_chars and readme_text:
        overflow = len(prompt_text) - max_chars
        readme_budget = max(len(readme_text) - overflow - 64, 256)
        readme_text = readme_text[:readme_budget] + "\n...[truncated]"
        warnings.append(
            PartialAnalysisWarning(
                stage="context_sanitizer",
                message="README content was truncated to stay within the AI context budget.",
            )
        )
        prompt_text = template.format(readme=readme_text, tree=tree_text)

    if len(prompt_text) > max_chars and tree_text:
        overflow = len(prompt_text) - max_chars
        tree_budget = max(len(tree_text) - overflow - 32, 128)
        tree_text = tree_text[:tree_budget] + "\n...[truncated]"
        warnings.append(
            PartialAnalysisWarning(
                stage="context_sanitizer",
                message="Repository structure was truncated to stay within the AI context budget.",
            )
        )
        prompt_text = template.format(readme=readme_text, tree=tree_text)

    return LLMPromptPayload(
        repository_url=raw_context.repository_url,
        cache_key=f"{raw_context.target.owner}/{raw_context.target.repo}@{raw_context.commit_sha}",
        commit_sha=raw_context.commit_sha,
        deterministic_data=raw_context.instant_data,
        prompt_text=prompt_text,
        warnings=warnings,
    )
from __future__ import annotations

import re
from urllib.parse import urlparse

from app.research.schema import ParsedRepoTarget
from common.exception.errors import ResearchProblem

_OWNER_RE = re.compile(r"^[A-Za-z0-9_.-]+$")
_REPO_RE = re.compile(r"^[A-Za-z0-9_.-]+$")


def parse_github_repository_url(url: str) -> ParsedRepoTarget:
    candidate = (url or "").strip()
    parsed = urlparse(candidate)
    if parsed.scheme != "https" or parsed.netloc not in {"github.com", "www.github.com"}:
        raise ResearchProblem(
            status_code=400,
            type_="/problems/invalid-repository-url",
            title="Invalid repository URL",
            detail="Use the canonical repository format https://github.com/{owner}/{repo}.",
        )

    segments = [segment for segment in parsed.path.strip("/").split("/") if segment]
    if len(segments) != 2:
        raise ResearchProblem(
            status_code=400,
            type_="/problems/invalid-repository-url",
            title="Invalid repository URL",
            detail="Only root repository URLs are supported. Branch, tree, gist, and profile URLs are not valid inputs.",
        )

    owner, repo = segments
    if owner in {"orgs", "users", "settings", "explore", "features"}:
        raise ResearchProblem(
            status_code=400,
            type_="/problems/invalid-repository-url",
            title="Invalid repository URL",
            detail="The supplied URL does not point to a repository root.",
        )

    repo = repo.removesuffix(".git")
    if not owner or not repo or not _OWNER_RE.match(owner) or not _REPO_RE.match(repo):
        raise ResearchProblem(
            status_code=400,
            type_="/problems/invalid-repository-url",
            title="Invalid repository URL",
            detail="The repository owner or name contains unsupported characters.",
        )

    return ParsedRepoTarget(
        owner=owner,
        repo=repo,
        canonical_url=f"https://github.com/{owner}/{repo}",
    )
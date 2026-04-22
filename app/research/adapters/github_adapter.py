from __future__ import annotations

import httpx

from app.research.ports import IGitHubClient
from app.research.schema import (
    CommitEntry,
    InstantMetadata,
    LanguageEntry,
    ParsedRepoTarget,
    RepositoryRawContext,
    RepositoryTreeEntry,
)
from common.exception.errors import ResearchProblem
from core.conf import settings


class GitHubGraphQLAdapter(IGitHubClient):
    QUERY = """
    query RepositoryResearch($owner: String!, $name: String!) {
      repository(owner: $owner, name: $name) {
        name
        nameWithOwner
        url
        description
        stargazerCount
        forkCount
        primaryLanguage { name }
        pushedAt
        isArchived
        isFork
        watchers { totalCount }
        openIssues: issues(states: OPEN) { totalCount }
        licenseInfo { spdxId }
        repositoryTopics(first: 10) { nodes { topic { name } } }
        languages(first: 10, orderBy: {field: SIZE, direction: DESC}) {
          edges { size node { name color } }
          totalSize
        }
        defaultBranchRef {
          name
          target {
            ... on Commit {
              oid
              committedDate
              history(first: 90) {
                nodes {
                  oid
                  messageHeadline
                  committedDate
                  author { name }
                }
              }
              tree {
                entries {
                  name
                  type
                }
              }
            }
          }
        }
        readmeLower: object(expression: "HEAD:README.md") {
          ... on Blob {
            text
            byteSize
          }
        }
        readmeUpper: object(expression: "HEAD:README.MD") {
          ... on Blob {
            text
            byteSize
          }
        }
      }
    }
    """

    def __init__(
        self,
        *,
        token: str = settings.GITHUB_TOKEN,
        endpoint_url: str = settings.GITHUB_API_URL,
        timeout_seconds: int = settings.RESEARCH_GITHUB_TIMEOUT,
        max_tree_entries: int = settings.RESEARCH_MAX_TREE_ENTRIES,
    ):
        self.token = token
        self.endpoint_url = endpoint_url
        self.timeout_seconds = timeout_seconds
        self.max_tree_entries = max_tree_entries

    async def fetch_repository_context(
        self, target: ParsedRepoTarget
    ) -> RepositoryRawContext:
        if not self.token:
            raise ResearchProblem(
                status_code=503,
                type_="/problems/github-token-missing",
                title="GitHub token missing",
                detail="GITHUB_TOKEN must be configured before repository analysis can run.",
            )

        headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github+json",
        }
        payload = {
            "query": self.QUERY,
            "variables": {"owner": target.owner, "name": target.repo},
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                response = await client.post(
                    self.endpoint_url,
                    headers=headers,
                    json=payload,
                )
                response.raise_for_status()
                body = response.json()
        except httpx.HTTPStatusError as exc:
            raise ResearchProblem(
                status_code=502,
                type_="/problems/github-upstream-error",
                title="GitHub request failed",
                detail=f"GitHub returned {exc.response.status_code} while fetching repository data.",
            ) from exc
        except httpx.HTTPError as exc:
            raise ResearchProblem(
                status_code=502,
                type_="/problems/github-upstream-error",
                title="GitHub request failed",
                detail=str(exc),
            ) from exc

        errors = body.get("errors", [])
        if errors:
            message = errors[0].get("message", "GitHub GraphQL query failed")
            if "Could not resolve to a Repository" in message:
                raise ResearchProblem(
                    status_code=404,
                    type_="/problems/repository-not-found",
                    title="Repository not found",
                    detail=f"Repository {target.owner}/{target.repo} could not be found or is not public.",
                )
            raise ResearchProblem(
                status_code=502,
                type_="/problems/github-upstream-error",
                title="GitHub query failed",
                detail=message,
            )

        repository = body.get("data", {}).get("repository")
        if repository is None:
            raise ResearchProblem(
                status_code=404,
                type_="/problems/repository-not-found",
                title="Repository not found",
                detail=f"Repository {target.owner}/{target.repo} could not be found or is not public.",
            )

        branch = repository.get("defaultBranchRef") or {}
        commit = branch.get("target") or {}
        tree = commit.get("tree") or {}
        entries = tree.get("entries") or []
        readme = repository.get("readmeLower") or repository.get("readmeUpper") or {}

        # Language breakdown
        langs_data = repository.get("languages") or {}
        langs_total = langs_data.get("totalSize") or 0
        languages: list[LanguageEntry] = []
        if langs_total > 0:
            for edge in langs_data.get("edges") or []:
                sz = edge.get("size", 0)
                node = edge.get("node") or {}
                lang_name = node.get("name")
                if lang_name:
                    languages.append(
                        LanguageEntry(
                            name=lang_name,
                            percentage=round(sz / langs_total * 100, 1),
                            color=node.get("color"),
                        )
                    )

        # Topics
        topics: list[str] = [
            n["topic"]["name"]
            for n in (repository.get("repositoryTopics") or {}).get("nodes", [])
            if n.get("topic", {}).get("name")
        ]

        # Recent commits from branch history
        history_nodes = (commit.get("history") or {}).get("nodes") or []
        recent_commits: list[CommitEntry] = [
            CommitEntry(
                sha=node["oid"][:7],
                message=node.get("messageHeadline") or "",
                committed_at=node["committedDate"],
                author_name=(node.get("author") or {}).get("name"),
            )
            for node in history_nodes
            if node.get("oid") and node.get("committedDate")
        ]

        open_issues = (repository.get("openIssues") or {}).get("totalCount")

        instant_data = InstantMetadata(
            name=repository.get("nameWithOwner") or repository["name"],
            description=repository.get("description"),
            stars=repository.get("stargazerCount", 0),
            forks=repository.get("forkCount", 0),
            primary_lang=(repository.get("primaryLanguage") or {}).get("name"),
            last_commit_at=commit.get("committedDate") or repository.get("pushedAt"),
            owner=target.owner,
            watchers=(repository.get("watchers") or {}).get("totalCount"),
            open_issues=open_issues,
            license_spdx=(repository.get("licenseInfo") or {}).get("spdxId"),
            topics=topics,
            languages=languages,
            recent_commits=recent_commits,
            is_archived=repository.get("isArchived", False),
            is_fork=repository.get("isFork", False),
        )

        return RepositoryRawContext(
            target=target,
            repository_url=repository["url"],
            default_branch=branch.get("name") or "HEAD",
            commit_sha=commit.get("oid") or "unknown",
            instant_data=instant_data,
            readme_text=readme.get("text"),
            readme_byte_size=readme.get("byteSize"),
            tree_entries=[
                RepositoryTreeEntry(name=item["name"], type=item.get("type", "blob"))
                for item in entries[: self.max_tree_entries]
            ],
            open_issue_count=open_issues,
        )
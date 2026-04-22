from __future__ import annotations

from typing import Annotated

from fastapi import Depends

from app.research.adapters.github_adapter import GitHubGraphQLAdapter
from app.research.adapters.llm_adapter import LLMAdapter
from app.research.adapters.redis_adapter import RedisStateCacheAdapter
from app.research.adapters.sqs_adapter import SQSMessageQueueAdapter
from app.research.ports import IGitHubClient, ILLMClient, IMessageQueue, IStateCache
from app.research.service.orchestration import ResearchOrchestrationService
from database.db import CurrentSession


def get_message_queue() -> IMessageQueue:
    return SQSMessageQueueAdapter()


def get_state_cache() -> IStateCache:
    return RedisStateCacheAdapter()


def get_github_client() -> IGitHubClient:
    return GitHubGraphQLAdapter()


def get_llm_client() -> ILLMClient:
    return LLMAdapter()


def get_research_orchestration_service(
    session: CurrentSession,
    queue: Annotated[IMessageQueue, Depends(get_message_queue)],
    state_cache: Annotated[IStateCache, Depends(get_state_cache)],
    github_client: Annotated[IGitHubClient, Depends(get_github_client)],
) -> ResearchOrchestrationService:
    return ResearchOrchestrationService(
        session=session,
        queue=queue,
        state_cache=state_cache,
        github_client=github_client,
    )


MessageQueueDep = Annotated[IMessageQueue, Depends(get_message_queue)]
StateCacheDep = Annotated[IStateCache, Depends(get_state_cache)]
GitHubClientDep = Annotated[IGitHubClient, Depends(get_github_client)]
LLMClientDep = Annotated[ILLMClient, Depends(get_llm_client)]
ResearchServiceDep = Annotated[
    ResearchOrchestrationService,
    Depends(get_research_orchestration_service),
]
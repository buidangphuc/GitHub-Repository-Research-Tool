from __future__ import annotations

from abc import ABC, abstractmethod

from app.research.schema import (
    LLMPromptPayload,
    ParsedRepoTarget,
    ReceivedMessage,
    ResearchJobMessage,
    ResearchJobStateSnapshot,
    RepositoryRawContext,
    StructuredAIResponse,
)


class IMessageQueue(ABC):
    """Queue adapter boundary.

    Implementations must provision queue resources lazily, publish validated
    message contracts, surface receive counts, and raise infrastructure errors
    instead of swallowing delivery failures.
    """

    @abstractmethod
    async def ensure_queues(self) -> None:
        """Provision the main queue and its DLQ if needed."""

    @abstractmethod
    async def send(self, message: ResearchJobMessage) -> None:
        """Publish a validated research job message to the queue."""

    @abstractmethod
    async def receive(
        self, *, max_messages: int = 1, wait_time_seconds: int | None = None
    ) -> list[ReceivedMessage]:
        """Return the next batch of received messages with receipt handles."""

    @abstractmethod
    async def delete(self, receipt_handle: str) -> None:
        """Acknowledge and delete a processed queue message."""

    @abstractmethod
    async def change_visibility(
        self, receipt_handle: str, timeout_seconds: int
    ) -> None:
        """Adjust retry visibility for a queue message."""


class IStateCache(ABC):
    """Cache adapter boundary for transient job state and reusable AI output."""

    @abstractmethod
    async def set_state(self, snapshot: ResearchJobStateSnapshot) -> None:
        """Persist the latest pollable job snapshot."""

    @abstractmethod
    async def get_state(self, job_id: str) -> ResearchJobStateSnapshot | None:
        """Load the latest pollable job snapshot if present."""

    @abstractmethod
    async def delete_state(self, job_id: str) -> None:
        """Remove any cached polling state for a job."""

    @abstractmethod
    async def get_cached_ai_result(
        self, cache_key: str
    ) -> StructuredAIResponse | None:
        """Load a cached structured AI result for a repository state."""

    @abstractmethod
    async def set_cached_ai_result(
        self, cache_key: str, ai_result: StructuredAIResponse
    ) -> None:
        """Persist a structured AI result for reuse across duplicate analyses."""


class IGitHubClient(ABC):
    """GitHub data-ingestion boundary.

    Implementations must validate upstream responses and return canonical
    repository context models instead of raw provider payloads.
    """

    @abstractmethod
    async def fetch_repository_context(
        self, target: ParsedRepoTarget
    ) -> RepositoryRawContext:
        """Fetch deterministic repository data for the supplied repository."""


class ILLMClient(ABC):
    """LLM inference boundary.

    Implementations must return validated structured output or raise a typed
    provider error when inference cannot be used safely.
    """

    @abstractmethod
    async def analyze(self, prompt_payload: LLMPromptPayload) -> StructuredAIResponse:
        """Generate structured repository insights from a sanitized prompt."""
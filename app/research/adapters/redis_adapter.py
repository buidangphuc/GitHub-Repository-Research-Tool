from __future__ import annotations

from app.research.ports import IStateCache
from app.research.schema import ResearchJobStateSnapshot, StructuredAIResponse
from core.conf import settings
from database.redis import redis_client


class RedisStateCacheAdapter(IStateCache):
    def __init__(
        self,
        client=redis_client,
        *,
        status_ttl_seconds: int = settings.RESEARCH_STATUS_TTL_SECONDS,
        ai_cache_ttl_seconds: int = settings.RESEARCH_CACHE_TTL_SECONDS,
    ):
        self.client = client
        self.status_ttl_seconds = status_ttl_seconds
        self.ai_cache_ttl_seconds = ai_cache_ttl_seconds

    @staticmethod
    def _state_key(job_id: str) -> str:
        return f"research:job:{job_id}"

    @staticmethod
    def _ai_cache_key(cache_key: str) -> str:
        return f"research:ai:{cache_key}"

    async def set_state(self, snapshot: ResearchJobStateSnapshot) -> None:
        await self.client.set_json(
            self._state_key(snapshot.job_id),
            snapshot.model_dump(mode="json"),
            expire_seconds=self.status_ttl_seconds,
        )

    async def get_state(self, job_id: str) -> ResearchJobStateSnapshot | None:
        payload = await self.client.get_json(self._state_key(job_id))
        if payload is None:
            return None
        return ResearchJobStateSnapshot.model_validate(payload)

    async def delete_state(self, job_id: str) -> None:
        await self.client.delete(self._state_key(job_id))

    async def get_cached_ai_result(
        self, cache_key: str
    ) -> StructuredAIResponse | None:
        payload = await self.client.get_json(self._ai_cache_key(cache_key))
        if payload is None:
            return None
        return StructuredAIResponse.model_validate(payload)

    async def set_cached_ai_result(
        self, cache_key: str, ai_result: StructuredAIResponse
    ) -> None:
        await self.client.set_json(
            self._ai_cache_key(cache_key),
            ai_result.model_dump(mode="json"),
            expire_seconds=self.ai_cache_ttl_seconds,
        )
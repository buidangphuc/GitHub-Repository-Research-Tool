from __future__ import annotations

from datetime import datetime, timezone
import socket

from moto.server import ThreadedMotoServer
import pytest

from app.research.adapters.redis_adapter import RedisStateCacheAdapter
from app.research.adapters.sqs_adapter import SQSMessageQueueAdapter
from app.research.schema import (
    InstantMetadata,
    ResearchJobMessage,
    ResearchJobStateSnapshot,
    StructuredAIResponse,
)


class InMemoryRedisClient:
    def __init__(self) -> None:
        self._store: dict[str, object] = {}

    async def set_json(
        self, key: str, value: object, expire_seconds: int | None = None
    ) -> None:
        self._store[key] = value

    async def get_json(self, key: str) -> object | None:
        return self._store.get(key)

    async def delete(self, key: str) -> None:
        self._store.pop(key, None)


@pytest.mark.asyncio
async def test_redis_state_cache_adapter_round_trip() -> None:
    adapter = RedisStateCacheAdapter(
        InMemoryRedisClient(),
        status_ttl_seconds=30,
        ai_cache_ttl_seconds=60,
    )
    snapshot = ResearchJobStateSnapshot(
        job_id="job-123",
        status="pending",
        progress_msg="Queued",
        updated_at=datetime.now(timezone.utc),
        instant_data=InstantMetadata(
            name="fastapi",
            description="FastAPI framework",
            stars=1,
            forks=2,
            primary_lang="Python",
            last_commit_at=datetime.now(timezone.utc),
        ),
    )

    await adapter.set_state(snapshot)
    loaded_snapshot = await adapter.get_state(snapshot.job_id)

    assert loaded_snapshot == snapshot

    ai_result = StructuredAIResponse(
        project_purpose="API framework",
        tech_stack=["FastAPI", "Pydantic"],
        architecture="Monolith",
        risk_level="Low",
        ai_confidence="High",
        limitations=["Sample limitation"],
    )
    cache_key = "tiangolo/fastapi@abc123"
    await adapter.set_cached_ai_result(cache_key, ai_result)
    loaded_ai_result = await adapter.get_cached_ai_result(cache_key)

    assert loaded_ai_result == ai_result

    await adapter.delete_state(snapshot.job_id)
    assert await adapter.get_state(snapshot.job_id) is None


@pytest.mark.asyncio
async def test_sqs_message_queue_adapter_round_trip() -> None:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]

    server = ThreadedMotoServer(ip_address="127.0.0.1", port=port)
    server.start()
    try:
        adapter = SQSMessageQueueAdapter(
            endpoint_url=f"http://127.0.0.1:{port}",
            queue_url="",
            dlq_url="",
            region="us-east-1",
            access_key_id="test",
            secret_access_key="test",
        )
        await adapter.ensure_queues()

        message = ResearchJobMessage(
            job_id="job-456",
            repo_url="https://github.com/tiangolo/fastapi",
            enqueued_at=datetime.now(timezone.utc),
            attempt=1,
            options={"mode": "test"},
        )
        await adapter.send(message)

        received = await adapter.receive()

        assert len(received) == 1
        assert received[0].body == message
        assert received[0].receive_count == 1

        await adapter.change_visibility(received[0].receipt_handle, 0)
        await adapter.delete(received[0].receipt_handle)

        assert await adapter.receive() == []
    finally:
        server.stop()
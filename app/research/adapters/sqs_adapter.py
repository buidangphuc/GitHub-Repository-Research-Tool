from __future__ import annotations

import json

from aiobotocore.session import get_session

from app.research.ports import IMessageQueue
from app.research.schema import ReceivedMessage, ResearchJobMessage
from core.conf import settings


def _queue_name_from_url(queue_url: str, default_name: str) -> str:
    if not queue_url:
        return default_name
    return queue_url.rstrip("/").split("/")[-1]


class SQSMessageQueueAdapter(IMessageQueue):
    def __init__(
        self,
        *,
        endpoint_url: str | None = settings.SQS_ENDPOINT_URL,
        queue_url: str = settings.SQS_QUEUE_URL,
        dlq_url: str = settings.SQS_DLQ_URL,
        region: str = settings.AWS_REGION,
        access_key_id: str = settings.AWS_ACCESS_KEY_ID,
        secret_access_key: str = settings.AWS_SECRET_ACCESS_KEY,
        visibility_timeout_seconds: int = settings.RESEARCH_SQS_VISIBILITY_TIMEOUT_SECONDS,
        wait_time_seconds: int = settings.RESEARCH_SQS_WAIT_TIME_SECONDS,
        max_attempts: int = settings.RESEARCH_MAX_QUEUE_ATTEMPTS,
    ):
        self.endpoint_url = endpoint_url
        self.queue_url = queue_url
        self.dlq_url = dlq_url
        self.region = region
        self.access_key_id = access_key_id
        self.secret_access_key = secret_access_key
        self.visibility_timeout_seconds = visibility_timeout_seconds
        self.wait_time_seconds = wait_time_seconds
        self.max_attempts = max_attempts
        self.queue_name = _queue_name_from_url(queue_url, "research-jobs")
        self.dlq_name = _queue_name_from_url(dlq_url, "research-jobs-dlq")
        self._session = get_session()

    def _client_kwargs(self) -> dict[str, str | None]:
        return {
            "service_name": "sqs",
            "endpoint_url": self.endpoint_url or None,
            "region_name": self.region,
            "aws_access_key_id": self.access_key_id,
            "aws_secret_access_key": self.secret_access_key,
        }

    async def ensure_queues(self) -> None:
        async with self._session.create_client(**self._client_kwargs()) as client:
            dlq_response = await client.create_queue(QueueName=self.dlq_name)
            self.dlq_url = dlq_response["QueueUrl"]
            dlq_attributes = await client.get_queue_attributes(
                QueueUrl=self.dlq_url,
                AttributeNames=["QueueArn"],
            )
            dlq_arn = dlq_attributes["Attributes"]["QueueArn"]
            queue_response = await client.create_queue(
                QueueName=self.queue_name,
                Attributes={
                    "VisibilityTimeout": str(self.visibility_timeout_seconds),
                    "ReceiveMessageWaitTimeSeconds": str(self.wait_time_seconds),
                    "RedrivePolicy": json.dumps(
                        {
                            "deadLetterTargetArn": dlq_arn,
                            "maxReceiveCount": str(self.max_attempts),
                        }
                    ),
                },
            )
            self.queue_url = queue_response["QueueUrl"]

    async def send(self, message: ResearchJobMessage) -> None:
        await self.ensure_queues()
        async with self._session.create_client(**self._client_kwargs()) as client:
            await client.send_message(
                QueueUrl=self.queue_url,
                MessageBody=json.dumps(message.model_dump(mode="json")),
            )

    async def receive(
        self, *, max_messages: int = 1, wait_time_seconds: int | None = None
    ) -> list[ReceivedMessage]:
        await self.ensure_queues()
        async with self._session.create_client(**self._client_kwargs()) as client:
            response = await client.receive_message(
                QueueUrl=self.queue_url,
                MaxNumberOfMessages=max_messages,
                WaitTimeSeconds=(
                    self.wait_time_seconds
                    if wait_time_seconds is None
                    else wait_time_seconds
                ),
                AttributeNames=["ApproximateReceiveCount"],
            )

        messages = []
        for item in response.get("Messages", []):
            body = ResearchJobMessage.model_validate_json(item["Body"])
            receive_count = int(
                item.get("Attributes", {}).get("ApproximateReceiveCount", "1")
            )
            messages.append(
                ReceivedMessage(
                    receipt_handle=item["ReceiptHandle"],
                    body=body,
                    receive_count=receive_count,
                )
            )
        return messages

    async def delete(self, receipt_handle: str) -> None:
        await self.ensure_queues()
        async with self._session.create_client(**self._client_kwargs()) as client:
            await client.delete_message(
                QueueUrl=self.queue_url,
                ReceiptHandle=receipt_handle,
            )

    async def change_visibility(
        self, receipt_handle: str, timeout_seconds: int
    ) -> None:
        await self.ensure_queues()
        async with self._session.create_client(**self._client_kwargs()) as client:
            await client.change_message_visibility(
                QueueUrl=self.queue_url,
                ReceiptHandle=receipt_handle,
                VisibilityTimeout=timeout_seconds,
            )
import json
import sys
from typing import Any

from redis.asyncio import Redis
from redis.exceptions import AuthenticationError, TimeoutError

from common.log import log
from core.conf import settings


class RedisCli(Redis):
    def __init__(self):
        super(RedisCli, self).__init__(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            password=settings.REDIS_PASSWORD,
            db=settings.REDIS_DATABASE,
            socket_timeout=settings.REDIS_TIMEOUT,
            decode_responses=True,
        )

    async def open(self):
        """
        Trigger initial connection

        :return:
        """
        try:
            await self.ping()
        except TimeoutError:
            log.error("❌ Database redis connection timeout")
            sys.exit()
        except AuthenticationError:
            log.error("❌ Database redis authentication failed")
            sys.exit()
        except Exception as e:
            log.error("❌ Database redis connection exception {}", e)
            sys.exit()

    async def delete_prefix(self, prefix: str, exclude: str | list = None):
        """
        Delete keys by prefix

        :param prefix:
        :param exclude:
        :return:
        """
        keys = []
        async for key in self.scan_iter(match=f"{prefix}*"):
            if isinstance(exclude, str):
                if key != exclude:
                    keys.append(key)
            elif isinstance(exclude, list):
                if key not in exclude:
                    keys.append(key)
            else:
                keys.append(key)
        if keys:
            await self.delete(*keys)

    async def set_json(
        self, key: str, value: Any, expire_seconds: int | None = None
    ) -> None:
        payload = json.dumps(value, default=str)
        if expire_seconds is None:
            await self.set(key, payload)
            return
        await self.set(key, payload, ex=expire_seconds)

    async def get_json(self, key: str) -> Any | None:
        payload = await self.get(key)
        if payload is None:
            return None
        return json.loads(payload)


# Redis Client
redis_client = RedisCli()

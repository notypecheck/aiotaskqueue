import asyncio
from typing import cast

from aiotaskqueue._types import TResult
from aiotaskqueue.broker.redis import RedisClient
from aiotaskqueue.config import Configuration
from aiotaskqueue.result.abc import ResultBackend
from aiotaskqueue.serialization import SerializationBackendId, serialize
from aiotaskqueue.tasks import RunningTask


class RedisResultBackend(ResultBackend):
    def __init__(
        self,
        redis: RedisClient,
        configuration: Configuration,
    ) -> None:
        self._redis = redis
        self._config = configuration

    async def set(self, task_id: str, value: TResult) -> None:
        backend_id, serialized_value = serialize(
            value=value,
            default_backend=self._config.default_serialization_backend,
            backends=self._config.serialization_backends,
        )
        await self._redis.set(
            name=f"{task_id}-result", value=f"{backend_id},{serialized_value.decode()}"
        )

    async def wait(
        self,
        task: RunningTask[TResult],
        *,
        poll_interval: float = 0.1,
    ) -> TResult:
        while not (raw_value := await self._redis.get(f"{task.id}-result")):  # noqa: ASYNC110
            await asyncio.sleep(poll_interval)

        backend_id, value = raw_value.split(b",", maxsplit=1)
        deserialized = self._config.serialization_backends[
            SerializationBackendId(backend_id.decode())
        ].deserialize(value=value, type=task.instance.task.return_type)
        return cast(TResult, deserialized)

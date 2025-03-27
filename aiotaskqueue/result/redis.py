import asyncio
from datetime import timedelta
from typing import Any, cast

from aiotaskqueue._types import TResult
from aiotaskqueue.broker.redis import RedisClient
from aiotaskqueue.config import Configuration
from aiotaskqueue.result.abc import ResultBackend
from aiotaskqueue.serialization import SerializationBackendId, serialize
from aiotaskqueue.tasks import RunningTask, TaskDefinition
from aiotaskqueue.types import Some


class RedisResultBackend(ResultBackend):
    def __init__(
        self,
        redis: RedisClient,
        configuration: Configuration,
        poll_interval: timedelta = timedelta(milliseconds=100),
    ) -> None:
        self._redis = redis
        self._config = configuration
        self._poll_interval = poll_interval.total_seconds()

    async def set(self, task_id: str, value: TResult) -> None:
        backend_id, serialized_value = serialize(
            value=value,
            default_backend=self._config.default_serialization_backend,
            backends=self._config.serialization_backends,
        )
        await self._redis.set(
            name=self._cache_key(task_id),
            value=f"{backend_id},{serialized_value}",
            ex=self._config.result.result_ttl,
        )

    async def get(
        self,
        task_id: str,
        definition: TaskDefinition[Any, TResult],
    ) -> Some[TResult] | None:
        raw_value = await self._redis.get(self._cache_key(task_id))
        if raw_value is None:
            return None

        result = await self._deserialize(
            raw_value,
            return_type=definition.return_type,
        )
        return Some(cast(TResult, result))

    async def wait(
        self,
        task: RunningTask[TResult],
        *,
        poll_interval: float | None = None,
    ) -> TResult:
        poll_interval = poll_interval or self._poll_interval

        while not (raw_value := await self._redis.get(self._cache_key(task.id))):  # noqa: ASYNC110
            await asyncio.sleep(poll_interval)

        result = await self._deserialize(
            raw_value,
            return_type=task.instance.task.return_type,
        )
        return cast(TResult, result)

    async def _deserialize(
        self,
        raw_value: bytes,
        return_type: type[Any],
    ) -> Any:  # noqa: ANN401
        backend_id, value = raw_value.split(b",", maxsplit=1)
        return self._config.serialization_backends[
            SerializationBackendId(backend_id.decode())
        ].deserialize(value=value.decode(), type=return_type)

    def _cache_key(self, task_id: str) -> str:
        return self._config.result.result_key(task_id)

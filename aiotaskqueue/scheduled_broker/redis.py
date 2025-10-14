import contextlib
import dataclasses
from collections.abc import AsyncIterator, Sequence
from datetime import datetime
from types import TracebackType
from typing import TYPE_CHECKING, Annotated, Self

import msgspec.json
from redis.asyncio import Redis
from typing_extensions import Doc

from aiotaskqueue.scheduled_broker.abc import ScheduledBroker
from aiotaskqueue.serialization import TaskRecord

if TYPE_CHECKING:
    RedisClient = Redis[bytes]
else:
    RedisClient = Redis


@dataclasses.dataclass(kw_only=True, slots=True)
class RedisScheduledBrokerConfig:
    schedule_set_name: Annotated[str, Doc("Schedule set name in redis")] = (
        "schedule-task"
    )


class RedisScheduledBroker(ScheduledBroker):
    def __init__(
        self,
        *,
        redis: Annotated[RedisClient, Doc("Instance of redis")],
        broker_config: Annotated[
            RedisScheduledBrokerConfig | None, Doc("Redis specific configuration")
        ] = None,
    ) -> None:
        self._redis = redis
        self._broker_config = broker_config or RedisScheduledBrokerConfig()

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None: ...

    async def schedule(
        self,
        task: TaskRecord,
        schedule: datetime,
    ) -> None:
        payload = msgspec.json.encode(task)
        await self._redis.zadd(
            self._broker_config.schedule_set_name,
            {payload: schedule.timestamp()},
        )

    @contextlib.asynccontextmanager
    async def get_scheduled_tasks(
        self,
        now: datetime,
    ) -> AsyncIterator[Sequence[TaskRecord]]:
        timestamp = int(now.timestamp())
        raw_records = await self._redis.zrangebyscore(
            name=self._broker_config.schedule_set_name,
            min="-inf",
            max=timestamp,
        )

        yield [msgspec.json.decode(record, type=TaskRecord) for record in raw_records]

        await self._redis.zremrangebyscore(
            name=self._broker_config.schedule_set_name,
            min="-inf",
            max=timestamp,
        )

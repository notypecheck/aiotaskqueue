import asyncio
import contextlib
import dataclasses
import logging
from collections.abc import AsyncIterator
from datetime import timedelta
from types import TracebackType
from typing import TYPE_CHECKING, Annotated, Self

import anyio
import msgspec.json
from redis.asyncio import Redis
from typing_extensions import Doc

from asyncqueue.broker.abc import Broker
from asyncqueue.serialization import TaskRecord

if TYPE_CHECKING:
    RedisClient = Redis[bytes]
else:
    RedisClient = Redis


@dataclasses.dataclass(kw_only=True, slots=True)
class RedisBrokerConfig:
    stream_name: Annotated[str, Doc("Stream name in redis (key name)")] = "async-queue"
    group_name: Annotated[
        str,
        Doc(
            "Redis stream group name."
            "https://redis.io/docs/latest/commands/xgroup-create/"
        ),
    ] = "default"
    xread_block_time: timedelta = timedelta(seconds=1)
    xread_count: Annotated[
        int,
        Doc("Amount of entries to receive from stream at once"),
    ] = 1
    reclaim_time: timedelta = timedelta(seconds=5)
    requeue_interval: Annotated[
        timedelta,
        Doc(
            "The time that task should be not ACKed for to be rescheduled after being read by worker"
        ),
    ] = timedelta(seconds=10)


class RedisBroker(Broker):
    def __init__(
        self,
        *,
        redis: RedisClient,
        config: RedisBrokerConfig | None = None,
        consumer_name: str,
        max_concurrency: int = 20,
    ) -> None:
        self._redis = redis
        self._config = config or RedisBrokerConfig()
        self._consumer_name = consumer_name
        self._task_ids: dict[str, bytes] = {}
        self._sem = asyncio.Semaphore(max_concurrency)

        self._is_initialized = False

    async def enqueue(self, task: TaskRecord) -> None:
        async with self._sem:
            await self._redis.xadd(
                self._config.stream_name,
                {"value": msgspec.json.encode(task)},
            )

    async def __aenter__(self) -> Self:
        if self._is_initialized:
            return self

        stream_exists = await self._redis.exists(self._config.stream_name) != 0
        group_exists = (
            self._config.group_name
            in (
                info["name"].decode()
                for info in await self._redis.xinfo_groups(self._config.stream_name)  # type: ignore[no-untyped-call]
            )
            if stream_exists
            else False
        )
        if not stream_exists or not group_exists:
            await self._redis.xgroup_create(
                self._config.stream_name,
                self._config.group_name,
                mkstream=True,
            )
        await self._redis.xgroup_createconsumer(  # type: ignore[no-untyped-call]
            self._config.stream_name,
            self._config.group_name,
            self._consumer_name,
        )
        self._is_initialized = True
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        pass

    async def listen(self) -> AsyncIterator[TaskRecord]:
        while True:
            xread = await self._redis.xreadgroup(
                self._config.group_name,
                self._consumer_name,
                {self._config.stream_name: ">"},
                count=self._config.xread_count,
                block=int(self._config.xread_block_time.total_seconds() * 1000),
            )
            for _, records in xread:
                for record_id, record in records:
                    task = msgspec.json.decode(record[b"value"], type=TaskRecord)
                    self._task_ids[task.id] = record_id
                    logging.debug(task)
                    yield task

    async def run_worker_maintenance_tasks(self, stop: asyncio.Event) -> None:
        async with anyio.create_task_group() as tg:
            tg.start_soon(self._maintenance_claim_running_tasks_worker, stop)
            tg.start_soon(self._maintenance_claim_pending_records, stop)

    async def _maintenance_claim_running_tasks_worker(
        self, stop: asyncio.Event
    ) -> None:
        """Reclaims owned messages so they don't get collected by other workers."""
        closes = asyncio.create_task(stop.wait())
        while True:
            if self._task_ids:
                await self._redis.xclaim(  # type: ignore[no-untyped-call]
                    self._config.stream_name,
                    self._config.group_name,
                    self._consumer_name,
                    min_idle_time=0,
                    message_ids=tuple(self._task_ids.values()),
                )

            sleep_task = asyncio.create_task(
                asyncio.sleep(self._config.reclaim_time.total_seconds())
            )
            await asyncio.wait(
                {closes, sleep_task}, return_when=asyncio.FIRST_COMPLETED
            )
            if stop.is_set():
                return

    async def _maintenance_claim_pending_records(
        self,
        stop: asyncio.Event,
    ) -> None:
        """Requeues messages that weren't ACKed in time."""
        stop_task = asyncio.create_task(stop.wait())
        while True:
            claimed = await self._redis.xautoclaim(
                self._config.stream_name,
                self._config.group_name,
                self._consumer_name,
                count=1000,
                min_idle_time=int(self._config.requeue_interval.total_seconds() * 1000),
            )
            logging.debug("Claimed %s", claimed)

            _, messages, _ = claimed
            for record_id, record in messages:
                task = msgspec.json.decode(record[b"value"], type=TaskRecord)
                task.requeue_count += 1
                await self.enqueue(task)
                await self._redis.xack(  # type: ignore[no-untyped-call]
                    self._config.stream_name,
                    self._config.group_name,
                    record_id,
                )

            sleep_task = asyncio.create_task(
                asyncio.sleep(self._config.requeue_interval.total_seconds())
            )
            await asyncio.wait(
                {stop_task, sleep_task}, return_when=asyncio.FIRST_COMPLETED
            )
            if stop.is_set():
                return

    @contextlib.asynccontextmanager
    async def ack_context(self, task: TaskRecord) -> AsyncIterator[None]:
        try:
            yield
        except Exception:
            self._task_ids.pop(task.id, None)
            raise
        else:
            record_id = self._task_ids.pop(task.id)
            await self._redis.xack(  # type: ignore[no-untyped-call]
                self._config.stream_name,
                self._config.group_name,
                record_id,
            )
            logging.info("Acked %s", task.id)

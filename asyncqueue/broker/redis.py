import asyncio
import dataclasses
import logging
from collections.abc import AsyncIterator
from datetime import timedelta
from types import TracebackType
from typing import TYPE_CHECKING, Self

import anyio
import msgspec.json
from redis.asyncio import Redis

from asyncqueue.broker.abc import Broker
from asyncqueue.serialization import TaskRecord

if TYPE_CHECKING:
    RedisClient = Redis[bytes]
else:
    RedisClient = Redis


@dataclasses.dataclass(kw_only=True, slots=True)
class RedisBrokerConfig:
    stream_name: str = "async-queue"
    group_name: str = "default"
    block_time: timedelta = timedelta(seconds=1)
    poll_count: int = 10
    reclaim_time: timedelta = timedelta(seconds=5)
    min_idle_time: timedelta = timedelta(seconds=10)

    def __post_init__(self) -> None:
        if self.min_idle_time <= self.block_time:
            msg = "min_idle_time should be larger than block_time"
            raise ValueError(msg)


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

        self._tg = anyio.create_task_group()
        self._is_closing = asyncio.Event()

        self._is_open = False

    async def enqueue(self, task: TaskRecord) -> None:
        async with self._sem:
            await self._redis.xadd(
                self._config.stream_name,
                {"value": msgspec.json.encode(task)},
            )

    async def __aenter__(self) -> Self:
        if self._is_open:
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
        await self._tg.__aenter__()
        self._tg.start_soon(self._claim_running_tasks_worker)
        self._is_open = True
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        if self._is_closing.is_set():
            return

        self._is_closing.set()
        await self._tg.__aexit__(exc_type, exc_val, exc_tb)

    async def listen(self) -> AsyncIterator[TaskRecord]:
        while True:
            claimed_records = await self._claim_pending_records()

            xread = await self._redis.xreadgroup(
                self._config.group_name,
                self._consumer_name,
                {self._config.stream_name: ">"},
                count=self._config.poll_count,
                block=int(self._config.block_time.total_seconds()),
            )
            for _, records in xread:
                for record_id, record in records:
                    task = msgspec.json.decode(record[b"value"], type=TaskRecord)
                    self._task_ids[task.id] = record_id
                    logging.debug(task)
                    yield task

            for stream in claimed_records:
                for record_id, record in stream:
                    task = msgspec.json.decode(record[b"value"], type=TaskRecord)
                    self._task_ids[task.id] = record_id
                    logging.debug(task)
                    yield task

    async def _claim_running_tasks_worker(self) -> None:
        """Reclaims owned messages."""
        closes = asyncio.create_task(self._is_closing.wait())
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
            if self._is_closing.is_set():
                return

    async def _claim_pending_records(
        self,
    ) -> list[list[tuple[bytes, dict[bytes, bytes]]]]:
        consumers = await self._redis.xinfo_consumers(  # type: ignore[no-untyped-call]
            self._config.stream_name,
            self._config.group_name,
        )

        messages = []
        to_claim = self._config.poll_count
        for consumer in consumers:
            claimed = await self._redis.xautoclaim(
                self._config.stream_name,
                self._config.group_name,
                consumer["name"],
                count=to_claim,
                min_idle_time=int(self._config.min_idle_time.total_seconds() * 1000),
            )
            logging.debug("Claimed %s", claimed)

            _, *topic_messages = claimed
            messages.extend(topic_messages)
            to_claim -= len(topic_messages)
            if to_claim <= 0:
                break

        return messages

    async def ack(self, task: TaskRecord) -> None:
        record_id = self._task_ids.pop(task.id)
        await self._redis.xack(  # type: ignore[no-untyped-call]
            self._config.stream_name,
            self._config.group_name,
            record_id,
        )
        logging.info("Acked %s", task.id)

import asyncio
import contextlib
from collections.abc import AsyncIterator, Sequence
from datetime import datetime
from types import TracebackType
from typing import Self

import anyio
import msgspec

from aiotaskqueue.broker.abc import Broker, BrokerAckContextMixin, ScheduledBroker
from aiotaskqueue.config import Configuration
from aiotaskqueue.serialization import TaskRecord
from aiotaskqueue.tasks import BrokerTask


class InMemoryBroker(BrokerAckContextMixin, Broker):
    def __init__(self, max_buffer_size: int) -> None:
        self._send, self._recv = anyio.create_memory_object_stream[BrokerTask[object]](
            max_buffer_size=max_buffer_size,
        )

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        pass

    async def enqueue(self, task: TaskRecord) -> None:
        await self._send.send(BrokerTask(task=task, meta=None))

    async def read(self) -> Sequence[BrokerTask[object]]:
        return (await self._recv.receive(),)

    async def ack(self, task: BrokerTask[object]) -> None:
        pass

    async def run_worker_maintenance_tasks(
        self,
        stop: asyncio.Event,
        config: Configuration,
    ) -> None:  # pragma: no cover
        pass

    async def tasks_healthcheck(
        self,
        *tasks: BrokerTask[object],
    ) -> None:  # pragma: no cover
        pass


class InMemoryScheduledBroker(ScheduledBroker):
    def __init__(self) -> None:
        self.tasks: list[tuple[datetime, bytes]] = []

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        pass

    async def schedule(
        self,
        task: TaskRecord,
        schedule: datetime,
    ) -> None:
        payload = msgspec.json.encode(task)
        self.tasks.append((schedule, payload))

    @contextlib.asynccontextmanager
    async def get_scheduled_tasks(
        self,
        now: datetime,
    ) -> AsyncIterator[Sequence[TaskRecord]]:
        records = [task for scheduled_at, task in self.tasks if scheduled_at <= now]

        yield [msgspec.json.decode(record, type=TaskRecord) for record in records]

        self.tasks = [
            (scheduled_at, task)
            for scheduled_at, task in self.tasks
            if scheduled_at > now
        ]

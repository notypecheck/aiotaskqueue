import asyncio
from collections.abc import Sequence
from types import TracebackType
from typing import Self

import anyio

from aiotaskqueue.broker.abc import Broker, BrokerAckContextMixin
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

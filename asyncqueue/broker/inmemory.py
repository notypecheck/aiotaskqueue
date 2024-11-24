from collections.abc import AsyncIterator
from types import TracebackType
from typing import Self

import anyio

from asyncqueue.broker.abc import Broker
from asyncqueue.serialization import TaskRecord


class InMemoryBroker(Broker):
    def __init__(self, max_buffer_size: int) -> None:
        self._send, self._recv = anyio.create_memory_object_stream[TaskRecord](
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
        await self._send.send(task)

    def listen(self) -> AsyncIterator[TaskRecord]:
        return self._recv

    async def ack(self, task: TaskRecord) -> None:
        pass

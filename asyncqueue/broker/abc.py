from collections.abc import AsyncIterator
from types import TracebackType
from typing import Protocol, Self

from asyncqueue.serialization import TaskRecord


class Broker(Protocol):
    async def enqueue(self, task: TaskRecord) -> None: ...

    async def __aenter__(self) -> Self: ...

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None: ...

    def listen(self) -> AsyncIterator[TaskRecord]: ...

    async def ack(self, task: TaskRecord) -> None: ...

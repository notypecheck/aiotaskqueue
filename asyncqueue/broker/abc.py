from collections.abc import AsyncIterator
from contextlib import AbstractAsyncContextManager
from typing import Protocol, Self

from asyncqueue.serialization import TaskRecord


class Broker(Protocol):
    async def enqueue(self, task: TaskRecord) -> None: ...

    def context(self) -> AbstractAsyncContextManager[Self]: ...

    def listen(self) -> AsyncIterator[TaskRecord]: ...

    async def ack(self, task: TaskRecord) -> None: ...

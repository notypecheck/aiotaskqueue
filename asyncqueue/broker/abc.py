import asyncio
from collections.abc import AsyncIterator
from contextlib import AbstractAsyncContextManager
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

    def ack_context(self, task: TaskRecord) -> AbstractAsyncContextManager[None]: ...

    async def run_worker_maintenance_tasks(self, stop: asyncio.Event) -> None: ...

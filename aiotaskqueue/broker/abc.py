from __future__ import annotations

import asyncio
import contextlib
from collections.abc import AsyncIterator, Sequence
from contextlib import AbstractAsyncContextManager
from types import TracebackType
from typing import TYPE_CHECKING, Any, Protocol, Self

if TYPE_CHECKING:
    from aiotaskqueue.config import Configuration
    from aiotaskqueue.serialization import TaskRecord
    from aiotaskqueue.tasks import BrokerTask


class Broker(Protocol):
    async def enqueue(self, task: TaskRecord) -> None: ...

    async def __aenter__(self) -> Self: ...

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None: ...

    async def read(self) -> Sequence[BrokerTask[Any]]: ...

    async def ack(
        self,
        task: BrokerTask[Any],
    ) -> None: ...

    def ack_context(
        self,
        task: BrokerTask[Any],
    ) -> AbstractAsyncContextManager[None]: ...

    async def run_worker_maintenance_tasks(
        self,
        stop: asyncio.Event,
        config: Configuration,
    ) -> None: ...

    async def tasks_healthcheck(self, *tasks: BrokerTask[Any]) -> None: ...


class BrokerAckContextMixin(Broker):
    @contextlib.asynccontextmanager
    async def ack_context(self, task: BrokerTask[Any]) -> AsyncIterator[None]:
        yield
        await self.ack(task=task)

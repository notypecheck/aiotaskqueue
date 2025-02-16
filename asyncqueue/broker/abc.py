import asyncio
from collections.abc import Sequence
from contextlib import AbstractAsyncContextManager
from types import TracebackType
from typing import Any, Protocol, Self

from asyncqueue.config import Configuration
from asyncqueue.serialization import TaskRecord
from asyncqueue.tasks import BrokerTask


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

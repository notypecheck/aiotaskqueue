from __future__ import annotations

from collections.abc import Sequence
from contextlib import AbstractAsyncContextManager
from datetime import datetime
from types import TracebackType
from typing import TYPE_CHECKING, Protocol, Self

if TYPE_CHECKING:
    from aiotaskqueue.serialization import TaskRecord


class ScheduledBroker(Protocol):
    async def __aenter__(self) -> Self: ...

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None: ...

    async def schedule(
        self,
        task: TaskRecord,
        schedule_at: datetime,
    ) -> None: ...

    def get_scheduled_tasks(
        self,
        now: datetime,
    ) -> AbstractAsyncContextManager[Sequence[TaskRecord]]: ...

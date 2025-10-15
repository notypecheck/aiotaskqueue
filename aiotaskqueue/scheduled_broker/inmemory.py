import contextlib
from collections.abc import AsyncIterator, Sequence
from datetime import datetime
from types import TracebackType
from typing import Self

import msgspec

from aiotaskqueue.scheduled_broker.abc import ScheduledBroker
from aiotaskqueue.serialization import TaskRecord


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

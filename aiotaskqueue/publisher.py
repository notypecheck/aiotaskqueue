from datetime import datetime, timedelta
from typing import cast, overload

from aiotaskqueue._types import P, TResult
from aiotaskqueue._util import utc_now
from aiotaskqueue.broker.abc import Broker, ScheduledBroker
from aiotaskqueue.config import Configuration
from aiotaskqueue.errors import ImproperlyConfiguredError
from aiotaskqueue.serialization import TaskRecord, serialize_task
from aiotaskqueue.tasks import RunningTask, ScheduledTask, TaskInstance


class Publisher:
    def __init__(
        self,
        broker: Broker,
        config: Configuration,
        scheduled_broker: ScheduledBroker | None = None,
    ) -> None:
        self._broker = broker
        self._config = config
        self._scheduled_broker = scheduled_broker

    @overload
    async def enqueue(
        self,
        task: TaskInstance[P, TResult],
        *,
        id: str | None = None,
    ) -> RunningTask[TResult]: ...

    @overload
    async def enqueue(
        self,
        task: TaskInstance[P, TResult],
        *,
        after: timedelta,
        id: str | None = None,
    ) -> ScheduledTask[TResult]: ...

    @overload
    async def enqueue(
        self,
        task: TaskInstance[P, TResult],
        *,
        schedule_at: datetime,
        id: str | None = None,
    ) -> ScheduledTask[TResult]: ...

    async def enqueue(
        self,
        task: TaskInstance[P, TResult],
        *,
        after: timedelta | None = None,
        schedule_at: datetime | None = None,
        id: str | None = None,  # noqa: A002
    ) -> RunningTask[TResult] | ScheduledTask[TResult]:
        record = serialize_task(
            task,
            default_backend=self._config.default_serialization_backend,
            serialization_backends=self._config.serialization_backends,
            id=id,
        )
        if (after or schedule_at) is not None:
            return await self._enqueue_schedule(
                task=task,
                record=record,
                after=after,
                schedule_at=schedule_at,
            )
        return await self._enqueue(task=task, record=record)

    async def _enqueue(
        self,
        task: TaskInstance[P, TResult],
        record: TaskRecord,
    ) -> RunningTask[TResult]:
        await self._broker.enqueue(record)
        return RunningTask(instance=task, id=record.id)

    async def _enqueue_schedule(
        self,
        task: TaskInstance[P, TResult],
        record: TaskRecord,
        *,
        after: timedelta | None = None,
        schedule_at: datetime | None = None,
    ) -> ScheduledTask[TResult]:
        if self._scheduled_broker is None:
            msg = f"{self.__class__.__name__}.scheduled_broker must be set in order to publish scheduled tasks"
            raise ImproperlyConfiguredError(msg)

        if after is None and schedule_at is None:
            # Should be unreachable due to enqueue overloads
            raise ValueError  # pragma: no cover

        if after is not None:
            schedule_at = utc_now() + after

        schedule_at = cast("datetime", schedule_at)
        await self._scheduled_broker.schedule(record, schedule_at)
        return ScheduledTask(instance=task, id=record.id, scheduled_at=schedule_at)

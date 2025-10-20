from __future__ import annotations

import asyncio
import warnings
from asyncio import PriorityQueue
from collections.abc import Callable, Coroutine, Sequence
from datetime import datetime
from typing import TYPE_CHECKING, Any

from aiotaskqueue import Configuration
from aiotaskqueue._util import ShutdownManager, extract_tasks, utc_now
from aiotaskqueue.extensions import OnTaskSchedule
from aiotaskqueue.scheduler.abc import Schedule

if TYPE_CHECKING:
    from aiotaskqueue.publisher import Publisher
    from aiotaskqueue.router import TaskRouter
    from aiotaskqueue.tasks import TaskDefinition


def _extract_schedule_markers(task: TaskDefinition[Any, Any]) -> Sequence[Schedule]:
    return [marker for marker in task.markers if isinstance(marker, Schedule)]


class RecurringScheduler:
    def __init__(
        self,
        publisher: Publisher,
        tasks: TaskRouter | Sequence[TaskDefinition[Any, Any]],
        *,
        configuration: Configuration | None = None,
        sleep: Callable[[float], Coroutine[Any, Any, None]] = asyncio.sleep,
    ) -> None:
        self._publisher = publisher
        self._sleep = sleep

        self._task_definitions = {task.name: task for task in extract_tasks(tasks)}
        self._schedules = [
            (task.name, marker)
            for task in extract_tasks(tasks)
            for marker in _extract_schedule_markers(task)
        ]

        self._scheduled_tasks: PriorityQueue[tuple[datetime, Schedule, str]] = (
            PriorityQueue(
                maxsize=len(self._schedules),
            )
        )

        self._extensions = (
            [ext for ext in configuration.extensions if isinstance(ext, OnTaskSchedule)]
            if configuration
            else ()
        )
        self._shutdown = ShutdownManager()

    async def run(self) -> None:
        stop_task = asyncio.create_task(self._shutdown.event.wait())

        await self._initial_scheduled_tasks()
        while not self._scheduled_tasks.empty():
            (
                schedule_datetime,
                schedule,
                scheduled_task_name,
            ) = await self._scheduled_tasks.get()
            sleep_seconds = (schedule_datetime - utc_now()).total_seconds()

            sleep_task = asyncio.create_task(self._sleep(max(sleep_seconds, 0)))
            await asyncio.wait(
                (stop_task, sleep_task),
                return_when=asyncio.FIRST_COMPLETED,
            )
            if self._shutdown.event.is_set():
                return

            scheduled_task = self._task_definitions[scheduled_task_name]

            await self._publisher.enqueue(scheduled_task())
            now = utc_now()
            next_schedule_time = await self._do_schedule_task(
                task_name=scheduled_task_name,
                schedule=schedule,
                now=now,
            )
            for extension in self._extensions:
                await extension.on_schedule(
                    task=scheduled_task,
                    scheduled_at=now,
                    next_schedule_at=next_schedule_time,
                )

    async def _initial_scheduled_tasks(self) -> None:
        now = utc_now()
        for task_name, schedule in self._schedules:
            await self._do_schedule_task(
                task_name=task_name,
                schedule=schedule,
                now=now,
            )

    async def _do_schedule_task(
        self,
        *,
        task_name: str,
        schedule: Schedule,
        now: datetime,
    ) -> datetime:
        schedule_datetime = schedule.next_schedule(now)
        await self._scheduled_tasks.put((schedule_datetime, schedule, task_name))
        return schedule_datetime


class Scheduler(RecurringScheduler):
    def __init__(
        self,
        publisher: Publisher,
        tasks: TaskRouter | Sequence[TaskDefinition[Any, Any]],
        *,
        configuration: Configuration | None = None,
        sleep: Callable[[float], Coroutine[Any, Any, None]] = asyncio.sleep,
    ) -> None:
        warnings.warn(
            "Scheduler is deprecated. Use RecurringScheduler instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        super().__init__(
            publisher=publisher,
            tasks=tasks,
            configuration=configuration,
            sleep=sleep,
        )

from __future__ import annotations

import asyncio
from asyncio import PriorityQueue
from collections.abc import Callable, Coroutine, Mapping, Sequence
from datetime import datetime
from typing import TYPE_CHECKING, Any

from aiotaskqueue import Configuration
from aiotaskqueue._util import ShutdownManager, extract_tasks, utc_now
from aiotaskqueue.extensions import OnTaskSchedule

if TYPE_CHECKING:
    from aiotaskqueue.publisher import Publisher
    from aiotaskqueue.router import TaskRouter
    from aiotaskqueue.tasks import TaskDefinition


class Scheduler:
    def __init__(
        self,
        publisher: Publisher,
        tasks: TaskRouter | Sequence[TaskDefinition[Any, Any]],
        *,
        configuration: Configuration | None = None,
        sleep: Callable[[float], Coroutine[None, None, None]] = asyncio.sleep,
    ) -> None:
        self.tasks: Mapping[str, TaskDefinition[Any, Any]] = {
            task.name: task for task in extract_tasks(tasks) if task.schedule
        }
        self._publisher = publisher
        self._scheduled_tasks: PriorityQueue[tuple[datetime, str]] = PriorityQueue(
            maxsize=len(self.tasks),
        )
        self._sleep = sleep

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
            schedule_datetime, scheduled_task_name = await self._scheduled_tasks.get()
            sleep_seconds = (schedule_datetime - utc_now()).total_seconds()

            sleep_task = asyncio.create_task(self._sleep(max(sleep_seconds, 0)))
            await asyncio.wait(
                (stop_task, sleep_task),
                return_when=asyncio.FIRST_COMPLETED,
            )
            if self._shutdown.event.is_set():
                return

            scheduled_task = self.tasks[scheduled_task_name]

            await self._publisher.enqueue(scheduled_task())
            now = utc_now()
            next_schedule_time = await self._do_schedule_task(scheduled_task, now)
            for extension in self._extensions:
                await extension.on_schedule(
                    task=scheduled_task,
                    scheduled_at=now,
                    next_schedule_at=next_schedule_time,
                )

    async def _initial_scheduled_tasks(self) -> None:
        now = utc_now()
        for task in self.tasks.values():
            await self._do_schedule_task(task, now)

    async def _do_schedule_task(
        self,
        task: TaskDefinition[Any, Any],
        now: datetime,
    ) -> datetime:
        if task.schedule is None:
            raise ValueError

        schedule_datetime = task.schedule.next_schedule(now)
        await self._scheduled_tasks.put((schedule_datetime, task.name))
        return schedule_datetime

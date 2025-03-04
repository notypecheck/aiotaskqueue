from __future__ import annotations

import asyncio
from asyncio import PriorityQueue
from collections.abc import Awaitable, Callable, Mapping, Sequence
from datetime import datetime
from typing import TYPE_CHECKING, Any

from aiotaskqueue._util import extract_tasks, utc_now

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
        sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
    ) -> None:
        self.tasks: Mapping[str, TaskDefinition[Any, Any]] = {
            task.params.name: task
            for task in extract_tasks(tasks)
            if task.params.schedule
        }
        self._publisher = publisher
        self._scheduled_tasks: PriorityQueue[tuple[datetime, str]] = PriorityQueue(
            maxsize=len(self.tasks),
        )
        self._sleep = sleep

    async def run(self) -> None:
        await self._initial_scheduled_tasks()
        while not self._scheduled_tasks.empty():
            schedule_datetime, scheduled_task_name = await self._scheduled_tasks.get()

            sleep_seconds = (schedule_datetime - utc_now()).total_seconds()

            await self._sleep(max(sleep_seconds, 0))

            scheduled_task = self.tasks[scheduled_task_name]
            await self._publisher.enqueue(scheduled_task())

            await self._schedule_task(scheduled_task, utc_now())

    async def _initial_scheduled_tasks(self) -> None:
        now = utc_now()
        for task in self.tasks.values():
            await self._schedule_task(task, now)

    async def _schedule_task(
        self,
        task: TaskDefinition[Any, Any],
        now: datetime,
    ) -> None:
        if task.params.schedule is None:
            raise ValueError

        schedule_datetime = task.params.schedule.next_schedule(now)
        await self._scheduled_tasks.put((schedule_datetime, task.params.name))

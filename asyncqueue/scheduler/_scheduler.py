from __future__ import annotations

import asyncio
from asyncio import PriorityQueue
from collections.abc import Awaitable, Callable, Mapping, Sequence
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from asyncqueue.publisher import Publisher
    from asyncqueue.task import TaskDefinition


class Scheduler:
    def __init__(
        self,
        publisher: Publisher,
        tasks: Sequence[TaskDefinition[Any, Any]],
        *,
        sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
    ) -> None:
        self.tasks: Mapping[str, TaskDefinition[Any, Any]] = {
            task.params.name: task for task in tasks
        }
        self._publisher = publisher
        self._scheduled_tasks: PriorityQueue[tuple[datetime, str]] = PriorityQueue(
            maxsize=len(tasks),
        )
        self._sleep = sleep

    async def run(self) -> None:
        await self._initial_scheduled_tasks()
        while not self._scheduled_tasks.empty():
            schedule_datetime, scheduled_task_name = await self._scheduled_tasks.get()

            sleep_seconds = (schedule_datetime - datetime.now(tz=UTC)).total_seconds()

            await self._sleep(max(sleep_seconds, 0))

            scheduled_task = self.tasks[scheduled_task_name]
            await self._publisher.enqueue(scheduled_task())

            await self._schedule_task(scheduled_task, datetime.now(tz=UTC))

    async def _initial_scheduled_tasks(self) -> None:
        now = datetime.now(tz=UTC)
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

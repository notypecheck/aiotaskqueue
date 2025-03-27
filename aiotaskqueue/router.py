from __future__ import annotations

from collections.abc import Awaitable, Callable, Sequence
from typing import Any

from aiotaskqueue._types import P, TResult
from aiotaskqueue.scheduler.abc import Schedule
from aiotaskqueue.tasks import Marker, TaskDefinition


class TaskRouter:
    def __init__(self, tasks: Sequence[TaskDefinition[Any, Any]] = ()) -> None:
        self.tasks = {task.name: task for task in tasks}

    def task(
        self,
        name: str,
        markers: Sequence[Marker] = (),
        schedule: Schedule | None = None,
    ) -> Callable[[Callable[P, Awaitable[TResult]]], TaskDefinition[P, TResult]]:
        def inner(func: Callable[P, Awaitable[TResult]]) -> TaskDefinition[P, TResult]:
            instance = task(name=name, markers=markers, schedule=schedule)(func)
            self.tasks[instance.name] = instance
            return instance

        return inner

    def include(self, router: TaskRouter) -> None:
        for task in router.tasks.values():
            existing_task = self.tasks.get(task.name)
            if existing_task and existing_task.func is not task.func:
                msg = f"Task {task!r} already registered"
                raise ValueError(msg)
            self.tasks[task.name] = task


def task(
    name: str,
    markers: Sequence[Marker] = (),
    schedule: Schedule | None = None,
) -> Callable[[Callable[P, Awaitable[TResult]]], TaskDefinition[P, TResult]]:
    def inner(func: Callable[P, Awaitable[TResult]]) -> TaskDefinition[P, TResult]:
        return TaskDefinition(name=name, markers=markers, schedule=schedule, func=func)

    return inner

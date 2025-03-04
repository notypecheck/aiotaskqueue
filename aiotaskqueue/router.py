from __future__ import annotations

from collections.abc import Awaitable, Callable, Sequence
from typing import Any

from aiotaskqueue._types import P, TResult
from aiotaskqueue.tasks import TaskDefinition, TaskParams


class TaskRouter:
    def __init__(self, tasks: Sequence[TaskDefinition[Any, Any]] = ()) -> None:
        self.tasks = {task.params.name: task for task in tasks}

    def task(
        self,
        params: TaskParams,
    ) -> Callable[[Callable[P, Awaitable[TResult]]], TaskDefinition[P, TResult]]:
        def inner(func: Callable[P, Awaitable[TResult]]) -> TaskDefinition[P, TResult]:
            instance = task(params)(func)
            self.tasks[instance.params.name] = instance
            return instance

        return inner

    def include(self, router: TaskRouter) -> None:
        for task in router.tasks.values():
            existing_task = self.tasks.get(task.params.name)
            if existing_task and existing_task.func is not task.func:
                msg = f"Task {task!r} already registered"
                raise ValueError(msg)
            self.tasks[task.params.name] = task


def task(
    params: TaskParams,
) -> Callable[[Callable[P, Awaitable[TResult]]], TaskDefinition[P, TResult]]:
    def inner(func: Callable[P, Awaitable[TResult]]) -> TaskDefinition[P, TResult]:
        return TaskDefinition(params=params, func=func)

    return inner

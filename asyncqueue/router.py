from __future__ import annotations

from collections.abc import Awaitable, Callable, Sequence
from typing import Any

from asyncqueue._types import P, TResult
from asyncqueue.task import TaskDefinition, TaskParams


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
        self.tasks.update(router.tasks)


def task(
    params: TaskParams,
) -> Callable[[Callable[P, Awaitable[TResult]]], TaskDefinition[P, TResult]]:
    def inner(func: Callable[P, Awaitable[TResult]]) -> TaskDefinition[P, TResult]:
        return TaskDefinition(params=params, func=func)

    return inner

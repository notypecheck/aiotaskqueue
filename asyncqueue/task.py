from __future__ import annotations

import dataclasses
from collections.abc import Awaitable, Callable
from typing import Generic

from asyncqueue._types import P, TResult
from asyncqueue.scheduler.abc import Schedule


@dataclasses.dataclass(slots=True, kw_only=True)
class TaskParams:
    name: str
    schedule: Schedule | None = None


@dataclasses.dataclass(slots=True, kw_only=True)
class TaskDefinition(Generic[P, TResult]):
    params: TaskParams
    func: Callable[P, Awaitable[TResult]]

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> TaskInstance[P, TResult]:
        return TaskInstance(
            task=self,
            args=args,
            kwargs=kwargs,
        )


@dataclasses.dataclass(slots=True, kw_only=True, frozen=True)
class TaskInstance(Generic[P, TResult]):
    task: TaskDefinition[P, TResult]
    args: P.args
    kwargs: P.kwargs

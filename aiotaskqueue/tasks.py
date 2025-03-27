from __future__ import annotations

import dataclasses
import inspect
import typing
from collections.abc import Awaitable, Callable, Mapping, Sequence
from functools import cached_property
from typing import TYPE_CHECKING, Any, Generic, TypeVar

from aiotaskqueue._types import P, TResult

if TYPE_CHECKING:
    from aiotaskqueue.scheduler.abc import Schedule
    from aiotaskqueue.serialization import TaskRecord


class Marker:
    pass


@dataclasses.dataclass(kw_only=True)
class TaskDefinition(Generic[P, TResult]):
    name: str
    markers: Sequence[Marker] = ()
    schedule: Schedule | None = None
    func: Callable[P, Awaitable[TResult]]

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> TaskInstance[P, TResult]:
        return TaskInstance(
            task=self,
            args=args,
            kwargs=kwargs,
        )

    @cached_property
    def return_type(self) -> type:
        return typing.get_type_hints(self.func).get("return")  # type: ignore[return-value]

    @cached_property
    def arg_types(self) -> Sequence[type[object]]:
        sig = inspect.signature(self.func)
        return tuple(p.annotation for p in sig.parameters.values())

    @cached_property
    def kwarg_types(self) -> Mapping[str, type[object]]:
        sig = inspect.signature(self.func)
        return {p.name: p.annotation for p in sig.parameters.values()}


@dataclasses.dataclass(slots=True, kw_only=True, frozen=True)
class TaskInstance(Generic[P, TResult]):
    task: TaskDefinition[P, TResult]
    # It doesn't seem to be possible to type args and kwargs here:
    # https://peps.python.org/pep-0612/#id1
    # https://github.com/python/mypy/pull/18278
    args: tuple[object, ...]
    kwargs: Mapping[str, object]


@dataclasses.dataclass(slots=True, kw_only=True, frozen=True)
class RunningTask(Generic[TResult]):
    id: str
    instance: TaskInstance[Any, TResult]


_TBrokerMeta = TypeVar("_TBrokerMeta")


@dataclasses.dataclass(slots=True, kw_only=True, frozen=True)
class BrokerTask(Generic[_TBrokerMeta]):
    meta: _TBrokerMeta
    task: TaskRecord

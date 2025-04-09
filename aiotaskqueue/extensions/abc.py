from __future__ import annotations

import typing
from collections.abc import Awaitable, Callable
from datetime import datetime
from typing import TYPE_CHECKING, Any, Protocol, TypeVar

if TYPE_CHECKING:
    from aiotaskqueue.serialization import TaskRecord
    from aiotaskqueue.tasks import TaskDefinition
    from aiotaskqueue.worker import ExecutionContext

T = TypeVar("T")


@typing.runtime_checkable
class OnTaskSchedule(Protocol):
    """Called when task is scheduled and added to the queue."""

    async def on_schedule(
        self,
        task: TaskDefinition[Any, Any],
        scheduled_at: datetime,
        next_schedule_at: datetime,
    ) -> None: ...


@typing.runtime_checkable
class OnTaskException(Protocol):
    """Called when an exception was raised during task execution."""

    async def on_task_exception(
        self,
        task: TaskRecord,
        definition: TaskDefinition[Any, Any],
        context: ExecutionContext,
        exception: Exception,
    ) -> None: ...


@typing.runtime_checkable
class OnTaskCompletion(Protocol):
    """Called when task is successfully completed and the result is already stored in the ResultBackend."""

    async def on_task_completion(
        self,
        task: TaskRecord,
        definition: TaskDefinition[Any, Any],
        context: ExecutionContext,
        result: Any,  # noqa: ANN401
    ) -> None: ...


@typing.runtime_checkable
class OnTaskExecution(Protocol):
    """Wraps task execution, working similarly to a middleware, it should return a value compatible with task return type."""

    async def on_task_execution(
        self,
        args: Any,  # noqa: ANN401
        kwargs: Any,  # noqa: ANN401
        definition: TaskDefinition[Any, T],
        context: ExecutionContext,
        call_next: Callable[
            [tuple[Any], dict[str, Any], ExecutionContext], Awaitable[T]
        ],
    ) -> T: ...


AnyExtension = OnTaskSchedule | OnTaskExecution | OnTaskException | OnTaskCompletion

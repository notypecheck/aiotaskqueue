from __future__ import annotations

import typing
from datetime import datetime
from typing import TYPE_CHECKING, Any, Protocol

if TYPE_CHECKING:
    from aiotaskqueue.serialization import TaskRecord
    from aiotaskqueue.tasks import TaskDefinition
    from aiotaskqueue.worker import ExecutionContext


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


AnyExtension = OnTaskSchedule | OnTaskException | OnTaskCompletion

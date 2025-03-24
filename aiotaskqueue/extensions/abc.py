from __future__ import annotations

import typing
from datetime import datetime
from typing import TYPE_CHECKING, Any, Protocol

if TYPE_CHECKING:
    from aiotaskqueue.serialization import TaskRecord
    from aiotaskqueue.tasks import TaskDefinition
    from aiotaskqueue.worker import ExecutionContext


@typing.runtime_checkable
class OnScheduleExtension(Protocol):
    async def on_schedule(
        self,
        task: TaskDefinition[Any, Any],
        scheduled_at: datetime,
        next_schedule_at: datetime,
    ) -> None: ...


@typing.runtime_checkable
class OnTaskException(Protocol):
    async def on_task_exception(
        self,
        task: TaskRecord,
        definition: TaskDefinition[Any, Any],
        context: ExecutionContext,
        exception: Exception,
    ) -> None: ...


@typing.runtime_checkable
class OnTaskCompletion(Protocol):
    async def on_task_completion(
        self,
        task: TaskRecord,
        definition: TaskDefinition[Any, Any],
        context: ExecutionContext,
        result: Any,  # noqa: ANN401
    ) -> None: ...


AnyExtension = OnScheduleExtension | OnTaskException | OnTaskCompletion

import typing
from datetime import datetime
from typing import Any, Protocol

from aiotaskqueue.serialization import TaskRecord
from aiotaskqueue.tasks import TaskDefinition


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
        exception: Exception,
    ) -> None: ...


@typing.runtime_checkable
class OnTaskCompletion(Protocol):
    async def on_task_completion(
        self,
        task: TaskRecord,
        definition: TaskDefinition[Any, Any],
        result: Any,  # noqa: ANN401
    ) -> None: ...


AnyExtension = OnScheduleExtension | OnTaskException | OnTaskCompletion

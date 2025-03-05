import typing
from datetime import datetime
from typing import Any, Protocol

from aiotaskqueue.tasks import TaskDefinition


@typing.runtime_checkable
class OnScheduleExtension(Protocol):
    async def on_schedule(
        self,
        task: TaskDefinition[Any, Any],
        scheduled_at: datetime,
        next_schedule_at: datetime,
    ) -> None: ...


AnyExtension = OnScheduleExtension

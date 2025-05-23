import dataclasses
from typing import Any

from aiotaskqueue.extensions import OnTaskException
from aiotaskqueue.serialization import TaskRecord
from aiotaskqueue.tasks import Marker, TaskDefinition
from aiotaskqueue.worker import ExecutionContext


@dataclasses.dataclass(slots=True, frozen=True, kw_only=True)
class Retry(Marker):
    max_retries: int


class RetryExtension(OnTaskException):
    _KEY = "retry_count"

    async def on_task_exception(
        self,
        task: TaskRecord,
        definition: TaskDefinition[Any, Any],
        context: ExecutionContext,
        exception: Exception,  # noqa: ARG002
    ) -> None:
        marker = next(
            (marker for marker in definition.markers if isinstance(marker, Retry)),
            None,
        )
        if not marker:
            return

        if (retry_count := task.meta.get(self._KEY, 0)) >= marker.max_retries:
            return

        task.meta[self._KEY] = retry_count + 1
        await context.broker.enqueue(task)

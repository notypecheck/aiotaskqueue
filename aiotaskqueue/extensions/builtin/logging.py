import logging
from datetime import datetime
from typing import Any, final

from aiotaskqueue.extensions import OnTaskCompletion, OnTaskException, OnTaskSchedule
from aiotaskqueue.serialization import TaskRecord
from aiotaskqueue.tasks import TaskDefinition
from aiotaskqueue.worker import ExecutionContext


@final
class LoggingExtension(OnTaskSchedule, OnTaskException, OnTaskCompletion):
    def __init__(self, logger: logging.Logger | None = None) -> None:
        self.logger = logger or logging.getLogger("aiotaskqueue")

    async def on_schedule(
        self,
        task: TaskDefinition[Any, Any],
        scheduled_at: datetime,
        next_schedule_at: datetime,
    ) -> None:
        self.logger.info(
            "Scheduled task[%s] at %s, next schedule at %s",
            task.name,
            scheduled_at,
            next_schedule_at,
        )

    async def on_task_exception(
        self,
        task: TaskRecord,  # noqa: ARG002
        definition: TaskDefinition[Any, Any],
        context: ExecutionContext,  # noqa: ARG002
        exception: Exception,  # noqa: ARG002
    ) -> None:
        self.logger.exception("Error while handling task[%s]", definition.name)

    async def on_task_completion(
        self,
        task: TaskRecord,
        definition: TaskDefinition[Any, Any],
        context: ExecutionContext,  # noqa: ARG002
        result: object,  # noqa: ARG002
    ) -> None:
        self.logger.info("Completed task[%s] %s", definition.name, task.id)

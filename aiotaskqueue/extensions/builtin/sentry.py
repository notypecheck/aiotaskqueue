from typing import Any, TypeVar

import sentry_sdk

from aiotaskqueue.extensions import OnTaskException
from aiotaskqueue.serialization import TaskRecord
from aiotaskqueue.tasks import TaskDefinition
from aiotaskqueue.worker import ExecutionContext

T = TypeVar("T")


class SentryExtension(OnTaskException):
    def __init__(self, context_task_key: str = "aiotaskqueue_task") -> None:
        self._context_key = context_task_key

    async def on_task_exception(
        self,
        task: TaskRecord,
        definition: TaskDefinition[Any, Any],
        context: ExecutionContext,  # noqa: ARG002
        exception: Exception,
    ) -> None:
        sentry_sdk.set_context(
            self._context_key,
            {
                "id": task.id,
                "name": definition.name,
                "args": task.args,
                "kwargs": task.kwargs,
            },
        )

        sentry_sdk.capture_exception(exception)

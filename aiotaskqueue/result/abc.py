from typing import Annotated, Any, Protocol

from typing_extensions import Doc

from aiotaskqueue._types import TResult
from aiotaskqueue.tasks import RunningTask, TaskDefinition
from aiotaskqueue.types import Some


class ResultBackend(Protocol):
    async def set(
        self,
        task_id: Annotated[
            str,
            Doc("Task id"),
        ],
        value: Annotated[
            TResult,
            Doc(
                "Result value, supported by any of serialization backends in your config."
            ),
        ],
    ) -> None:
        """Set execution result."""

    async def get(
        self,
        task_id: Annotated[
            str,
            Doc("Task id"),
        ],
        definition: Annotated[
            TaskDefinition[Any, TResult],
            Doc("Task definition for the task you're trying to retrieve."),
        ],
    ) -> Some[TResult] | None:
        """Immediately try to retrieve execution result of task, returns Some(result) if result was stored, None otherwise."""

    async def wait(self, task: RunningTask[TResult]) -> TResult:
        """Wait on the task to finish and return the result."""

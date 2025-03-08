from typing import Any, Protocol

from aiotaskqueue._types import TResult
from aiotaskqueue.tasks import RunningTask, TaskDefinition
from aiotaskqueue.types import Some


class ResultBackend(Protocol):
    async def set(self, task_id: str, value: TResult) -> None: ...

    async def get(
        self,
        task_id: str,
        definition: TaskDefinition[Any, TResult],
    ) -> Some[TResult] | None: ...

    async def wait(self, task: RunningTask[TResult]) -> TResult: ...

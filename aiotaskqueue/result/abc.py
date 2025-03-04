from typing import Protocol

from aiotaskqueue._types import TResult
from aiotaskqueue.tasks import RunningTask


class ResultBackend(Protocol):
    async def set(self, task_id: str, value: TResult) -> None: ...

    async def wait(self, task: RunningTask[TResult]) -> TResult: ...

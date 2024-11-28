from typing import Protocol

from asyncqueue._types import TResult
from asyncqueue.task import RunningTask


class ResultBackend(Protocol):
    async def set(self, task_id: str, value: TResult) -> None: ...

    async def wait(self, task: RunningTask[TResult]) -> TResult: ...

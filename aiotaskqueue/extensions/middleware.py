from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING, Any, Generic, TypeVar

if TYPE_CHECKING:
    from aiotaskqueue.extensions.abc import OnTaskExecution
    from aiotaskqueue.tasks import TaskDefinition
    from aiotaskqueue.worker import ExecutionContext

T = TypeVar("T")


class MiddlewareStack(Generic[T]):
    def __init__(
        self,
        middlewares: Sequence[OnTaskExecution],
        task_definition: TaskDefinition[Any, T],
    ) -> None:
        self._middlewares = middlewares
        self._index = 0
        self._task_definition = task_definition

    async def call(
        self,
        args: Any,  # noqa: ANN401
        kwargs: Any,  # noqa: ANN401
        context: ExecutionContext,
    ) -> T:
        if self._index >= len(self._middlewares):
            return await self._task_definition.func(*args, **kwargs)

        middleware = self._middlewares[self._index]
        self._index += 1
        return await middleware.on_task_execution(
            args=args,
            kwargs=kwargs,
            definition=self._task_definition,
            context=context,
            call_next=self.call,
        )

import asyncio
from collections.abc import Awaitable, Callable
from datetime import timedelta
from typing import Any

from aiotaskqueue.extensions import OnTaskExecution
from aiotaskqueue.extensions.abc import T
from aiotaskqueue.tasks import Marker, TaskDefinition
from aiotaskqueue.worker import ExecutionContext


class TimeLimit(Marker):
    limit: timedelta


class TimeLimitExtension(OnTaskExecution):
    def __init__(
        self,
        default_time_limit: timedelta | None = None,
    ) -> None:
        self.default_time_limit = default_time_limit

    async def on_task_execution(
        self,
        args: Any,  # noqa: ANN401
        kwargs: Any,  # noqa: ANN401
        definition: TaskDefinition[Any, T],
        context: ExecutionContext,
        call_next: Callable[
            [tuple[Any], dict[str, Any], ExecutionContext], Awaitable[T]
        ],
    ) -> T:
        marker = next(
            (marker for marker in definition.markers if isinstance(marker, TimeLimit)),
            None,
        )
        limit = marker.limit if marker else self.default_time_limit
        if not limit:
            return await call_next(args, kwargs, context)

        async with asyncio.timeout(limit.total_seconds()):
            return await call_next(args, kwargs, context)
